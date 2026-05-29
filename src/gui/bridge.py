"""Threading bridge between the Kivy UI thread and the engine's task pool.

The engine already owns a thread pool (``engine.tasks`` / TaskManager). We submit
work there and use its ``on_done`` callback, then re-marshal the result onto the
Kivy main thread via ``Clock.schedule_once`` — Kivy widgets must only ever be
touched from the main thread.

Result normalization
---------------------
``TaskManager`` stores the task and exposes ``task.to_dict()`` which flattens the
return value through ``to_jsonable`` (so an ``OperationResult`` becomes its dict
form). We collapse all the shapes the modules return — ``OperationResult``,
plain success/error dicts, plain data dicts, and task-level exceptions — into one
envelope: ``{'success': bool, 'error': str|None, 'data': Any}``.
"""

from kivy.clock import Clock


def normalize(task_dict):
    """Collapse a TaskManager ``to_dict()`` payload into a uniform envelope."""
    if not isinstance(task_dict, dict):
        return {'success': True, 'error': None, 'data': task_dict}

    state = task_dict.get('state')
    result = task_dict.get('result')
    task_error = task_dict.get('error')

    # Task-level failure (the work function raised).
    if state in ('failed', 'cancelled') or task_error:
        return {
            'success': False,
            'error': task_error or 'Task {}'.format(state or 'failed'),
            'data': result,
        }

    # OperationResult.to_dict() / a module dict carrying an explicit success flag.
    if isinstance(result, dict) and 'success' in result:
        return {
            'success': bool(result.get('success', True)),
            'error': result.get('error'),
            'data': result,
        }

    # Plain data dict / list / scalar — the call completed without an error flag.
    return {'success': True, 'error': None, 'data': result}


class TaskBridge:
    """Submits work to the engine pool and delivers results on the UI thread."""

    def __init__(self, engine):
        self.engine = engine

    def run_async(self, name, fn, *args, on_result=None, **kwargs):
        """Run ``fn(*args, **kwargs)`` on the task pool.

        ``on_result(envelope)`` is invoked on the Kivy main thread when the task
        finishes. Returns the task id immediately.
        """

        def _on_done(task_dict):
            # Runs on a worker thread — bounce to the main thread before any UI work.
            envelope = normalize(task_dict)
            if on_result is not None:
                Clock.schedule_once(lambda _dt: on_result(envelope), 0)

        return self.engine.tasks.submit(name, fn, *args, on_done=_on_done, **kwargs)

    @staticmethod
    def marshal(fn):
        """Wrap ``fn`` so calls from a worker thread run on the Kivy main thread.

        Used for progress callbacks (e.g. ``engine.collect(progress=...)``) which
        the engine invokes from inside the worker.
        """

        def _wrapped(*args, **kwargs):
            Clock.schedule_once(lambda _dt: fn(*args, **kwargs), 0)

        return _wrapped
