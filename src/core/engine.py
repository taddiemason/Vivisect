"""Composition root and workflow orchestration for Vivisect.

:class:`VivisectEngine` builds the config, logger, report generator, forensic
modules, and background task manager exactly once, so the CLI and the web GUI
share a single wiring and — importantly — a single definition of multi-step
workflows such as :meth:`collect`. Previously each entry point constructed these
components independently and re-implemented ``collect``, and the two
implementations had drifted apart.
"""

from .config import Config
from .logger import ForensicsLogger
from .report import ReportGenerator
from .tasks import TaskManager
from modules import (
    DiskImaging,
    FileAnalysis,
    NetworkForensics,
    MemoryAnalysis,
    ArtifactExtraction,
    USBGadget,
)


class VivisectEngine:
    """Owns shared components and defines cross-cutting workflows."""

    # Module registry: config key -> implementation class. Keys match the
    # ``modules.<key>.enabled`` config flags and the /api/status payload.
    MODULE_CLASSES = {
        'disk_imaging': DiskImaging,
        'file_analysis': FileAnalysis,
        'network_forensics': NetworkForensics,
        'memory_analysis': MemoryAnalysis,
        'artifact_extraction': ArtifactExtraction,
        'usb_gadget': USBGadget,
    }

    # Steps that require an operator-supplied target (device / path / interface)
    # and therefore cannot run in an unattended full collection.
    PARAMETERIZED_STEPS = ('disk', 'file', 'network')
    DEFAULT_COLLECT_STEPS = ('memory', 'artifacts')

    def __init__(self, config=None):
        self.config = config or Config()
        self.config.ensure_directories()
        self.logger = ForensicsLogger(self.config.get('log_dir'))
        self.report_gen = ReportGenerator(self.config.get('output_dir'))
        self.modules = {
            key: cls(self.logger, self.config)
            for key, cls in self.MODULE_CLASSES.items()
        }
        self.tasks = TaskManager(
            max_workers=int(self.config.get('max_workers', 2)),
            logger=self.logger.get_logger('tasks'),
        )

    # ── convenience accessors ────────────────────────────────────────────────
    @property
    def disk(self):
        return self.modules['disk_imaging']

    @property
    def file(self):
        return self.modules['file_analysis']

    @property
    def network(self):
        return self.modules['network_forensics']

    @property
    def memory(self):
        return self.modules['memory_analysis']

    @property
    def artifacts(self):
        return self.modules['artifact_extraction']

    @property
    def usb(self):
        return self.modules['usb_gadget']

    def module_status(self):
        """Return the enabled flag per module (for /api/status)."""
        return {
            key: bool(self.config.get(f'modules.{key}.enabled', True))
            for key in self.MODULE_CLASSES
        }

    # ── workflows ─────────────────────────────────────────────────────────────
    def collect(self, case_id, modules=None, progress=None):
        """Run a full forensic collection — the single shared definition.

        ``modules`` is an optional list of step names; it defaults to the steps
        that run without an operator-supplied target (memory + artifacts).
        ``progress(step, status)`` is an optional callback for UI updates
        (the web GUI emits a socket event; the CLI prints).

        Returns ``{case_id, report, json_report, html_report}``. A failing step
        is logged and reported via ``progress(step, 'error')`` but does not
        abort the rest of the collection.
        """
        notify = progress or (lambda step, status='running': None)
        report = self.report_gen.create_report(case_id)
        steps = list(modules) if modules else list(self.DEFAULT_COLLECT_STEPS)

        for step in steps:
            if step in self.PARAMETERIZED_STEPS:
                self.logger.main_logger.info(
                    f"collect: step '{step}' needs a target and was skipped")
                notify(step, 'skipped')
                continue
            notify(step, 'running')
            try:
                for finding in self._collect_step(step):
                    self.report_gen.add_finding(report, finding['module'], finding)
                notify(step, 'done')
            except Exception as exc:
                self.logger.main_logger.error(
                    f"collect: step '{step}' failed: {exc}", exc_info=True)
                notify(step, 'error')

        return {
            'case_id': case_id,
            'report': report,
            'json_report': self.report_gen.save_report(report, 'json'),
            'html_report': self.report_gen.save_report(report, 'html'),
        }

    def _collect_step(self, step):
        """Yield the findings produced by a single collection step."""
        if step == 'memory':
            yield {
                'module': 'memory', 'type': 'live_analysis',
                'description': 'Live system memory analysis',
                'data': self.memory.analyze_running_system(),
            }
        elif step == 'artifacts':
            yield {
                'module': 'artifacts', 'type': 'browser_history',
                'description': 'Browser history extraction',
                'data': self.artifacts.extract_browser_history(),
            }
            yield {
                'module': 'artifacts', 'type': 'system_logs',
                'description': 'System logs extraction',
                'data': self.artifacts.extract_system_logs(),
            }
            yield {
                'module': 'artifacts', 'type': 'user_artifacts',
                'description': 'User artifacts extraction',
                'data': self.artifacts.extract_user_artifacts(),
            }
            yield {
                'module': 'artifacts', 'type': 'persistence',
                'description': 'Persistence mechanisms',
                'data': self.artifacts.extract_persistence_mechanisms(),
            }
        else:
            self.logger.main_logger.info(f"collect: unknown step '{step}' ignored")
