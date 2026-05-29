"""Background task management for long-running forensic operations.

Replaces the ad-hoc ``threading.Thread`` objects that the web GUI previously
stored in an unbounded ``active_tasks`` dict. A :class:`TaskManager`:

* runs work on a bounded thread pool (a concurrency cap, so two disk images
  cannot thrash the device),
* records each job (id, state, result, error, timings) so a client that
  missed the completion event can still retrieve the outcome,
* evicts old finished jobs so the record set stays bounded,
* supports cooperative cancellation of jobs that have not started yet.
"""

from __future__ import annotations

import time
import uuid
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class TaskState(str, Enum):
    PENDING = 'pending'
    RUNNING = 'running'
    DONE = 'done'
    FAILED = 'failed'
    CANCELLED = 'cancelled'


_TERMINAL = (TaskState.DONE, TaskState.FAILED, TaskState.CANCELLED)


@dataclass
class Task:
    """A single unit of background work and its outcome."""

    id: str
    name: str
    state: TaskState = TaskState.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    finished_at: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['state'] = self.state.value
        return data


class TaskManager:
    """Bounded background executor with retrievable per-job records."""

    def __init__(self, max_workers: int = 2, retain: int = 200, logger=None):
        self._pool = ThreadPoolExecutor(
            max_workers=max(1, max_workers),
            thread_name_prefix='vivisect-task',
        )
        self._tasks: Dict[str, Task] = {}
        self._cancelled = set()
        self._lock = threading.Lock()
        self._retain = max(1, retain)
        self._logger = logger

    def submit(self, name: str, fn: Callable, *args,
               on_done: Optional[Callable[[Dict[str, Any]], None]] = None,
               **kwargs) -> str:
        """Schedule ``fn(*args, **kwargs)`` and return a task id immediately.

        ``on_done`` (if given) is called with the task's ``to_dict()`` once the
        job finishes — used by the web layer to emit a socket event. It runs on
        the worker thread, mirroring the previous behaviour.
        """
        task = Task(id=uuid.uuid4().hex, name=name)
        with self._lock:
            self._tasks[task.id] = task
            self._evict_locked()

        def _run():
            if task.id in self._cancelled:
                self._finish(task, TaskState.CANCELLED)
            else:
                task.state = TaskState.RUNNING
                task.started_at = time.time()
                try:
                    result = fn(*args, **kwargs)
                    self._finish(task, TaskState.DONE, result=result)
                except Exception as exc:  # surfaced via the task record, not swallowed
                    if self._logger:
                        self._logger.error(
                            f"Task {name} ({task.id}) failed: {exc}", exc_info=True)
                    self._finish(task, TaskState.FAILED, error=str(exc))
            if on_done:
                try:
                    on_done(task.to_dict())
                except Exception:
                    if self._logger:
                        self._logger.error(
                            f"on_done callback for task {task.id} failed", exc_info=True)

        self._pool.submit(_run)
        return task.id

    def _finish(self, task: Task, state: TaskState,
                result: Any = None, error: Optional[str] = None) -> None:
        task.result = result
        task.error = error
        task.finished_at = time.time()
        task.state = state

    def _evict_locked(self) -> None:
        """Drop the oldest finished tasks once the retention cap is exceeded."""
        if len(self._tasks) <= self._retain:
            return
        finished = [t for t in self._tasks.values() if t.state in _TERMINAL]
        finished.sort(key=lambda t: t.finished_at or 0)
        for task in finished[:len(self._tasks) - self._retain]:
            self._tasks.pop(task.id, None)

    def get(self, task_id: str) -> Optional[Task]:
        return self._tasks.get(task_id)

    def list(self) -> List[Dict[str, Any]]:
        with self._lock:
            tasks = list(self._tasks.values())
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        return [t.to_dict() for t in tasks]

    def active_count(self) -> int:
        return sum(1 for t in self._tasks.values()
                   if t.state in (TaskState.PENDING, TaskState.RUNNING))

    def cancel(self, task_id: str) -> bool:
        """Request cancellation.

        A job that has not started yet is cancelled before it runs. A job
        already executing cannot be force-killed (e.g. a thread blocked in
        ``dd``); the request is recorded but takes effect only if the work
        cooperatively checks for it. Returns True if cancellation was applied
        or is still possible.
        """
        task = self._tasks.get(task_id)
        if task is None:
            return False
        self._cancelled.add(task_id)
        return task.state in (TaskState.PENDING, TaskState.RUNNING)

    def shutdown(self, wait: bool = False) -> None:
        self._pool.shutdown(wait=wait)
