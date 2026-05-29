#!/usr/bin/env python3
"""Textual terminal UI for Vivisect.

A browser-free front end that runs in any terminal — the on-device console,
an SSH session, or the USB serial gadget the device already exposes. It talks
directly to :class:`VivisectEngine`, so it shares the same wiring and workflows
as the CLI and the web GUI (no network service, minimal attack surface).

Run with::

    python src/tui/app.py
    # or, once installed:  vivisect-tui

Long-running operations (device enumeration, full collection) run on worker
threads so the UI stays responsive; results are marshalled back to the UI
thread via ``call_from_thread``.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime

# Resolve symlinks and put the src dir on the path for direct execution.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from textual import work
from textual.app import App, ComposeResult
from textual.widgets import (
    Header, Footer, Static, Button, Input, Label, DataTable, RichLog,
    TabbedContent, TabPane,
)

from core.engine import VivisectEngine


LEVEL_COLOR = {'info': 'white', 'success': 'green', 'error': 'red', 'warn': 'yellow'}


class VivisectTUI(App):
    """Terminal control panel for the Vivisect forensics engine."""

    TITLE = 'Vivisect Forensics'
    SUB_TITLE = 'Terminal UI'

    CSS = """
    #status { padding: 1; height: auto; }
    .section-title { text-style: bold; color: $accent; padding: 1 0 0 1; }
    DataTable { height: auto; max-height: 12; margin: 0 1; }
    #collect-status { padding: 1; color: $text-muted; }
    #log { height: 10; border: round $accent; margin: 1; }
    Input, Button { margin: 1; }
    """

    BINDINGS = [
        ('r', 'refresh', 'Refresh'),
        ('c', 'collect', 'Collect'),
        ('q', 'quit', 'Quit'),
    ]

    def __init__(self, engine: VivisectEngine = None):
        super().__init__()
        self.engine = engine or VivisectEngine()

    # ── layout ────────────────────────────────────────────────────────────────
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with TabbedContent(initial='dashboard'):
            with TabPane('Dashboard', id='dashboard'):
                yield Static(id='status')
            with TabPane('Devices', id='devices'):
                yield Static('Block devices', classes='section-title')
                yield DataTable(id='disk-table')
                yield Static('Network interfaces', classes='section-title')
                yield DataTable(id='net-table')
            with TabPane('Collect', id='collect'):
                yield Label('Case ID (blank = auto):')
                yield Input(placeholder='CASE-001', id='case-id')
                yield Button('Run full collection', id='run-collect', variant='primary')
                yield Static(id='collect-status')
            with TabPane('Tasks', id='tasks'):
                yield DataTable(id='task-table')
        yield RichLog(id='log', highlight=True, markup=True)
        yield Footer()

    def on_mount(self) -> None:
        self.query_one('#disk-table', DataTable).add_columns('Name', 'Size', 'Type')
        self.query_one('#net-table', DataTable).add_columns('Interface', 'State', 'MAC')
        self.query_one('#task-table', DataTable).add_columns('Task', 'State', 'Detail')
        self.log_line('Vivisect TUI started', 'success')
        self.refresh_all()

    # ── helpers ─────────────────────────────────────────────────────────────────
    def log_line(self, message: str, level: str = 'info') -> None:
        ts = datetime.now().strftime('%H:%M:%S')
        color = LEVEL_COLOR.get(level, 'white')
        self.query_one('#log', RichLog).write(f'[{color}]{ts}  {message}[/]')

    def refresh_all(self) -> None:
        self.update_status()
        self.load_tasks()
        self.load_devices()  # worker thread

    def update_status(self) -> None:
        lines = ['[b]Modules[/b]']
        for name, enabled in self.engine.module_status().items():
            flag = '[green]on [/]' if enabled else '[red]off[/]'
            lines.append(f'  {flag} {name}')
        lines.append('')
        lines.append(f'Output dir : {self.engine.config.get("output_dir")}')
        lines.append(f'Log dir    : {self.engine.config.get("log_dir")}')
        lines.append(f'Max workers: {self.engine.config.get("max_workers", 2)}')
        self.query_one('#status', Static).update('\n'.join(lines))

    def load_tasks(self) -> None:
        table = self.query_one('#task-table', DataTable)
        table.clear()
        for task in self.engine.tasks.list():
            detail = task.get('error') or ''
            table.add_row(task['name'], task['state'], detail[:48])

    @work(thread=True, exclusive=True, group='devices')
    def load_devices(self) -> None:
        # lsblk / ip shell out, so do it off the UI thread.
        try:
            devices = self.engine.disk.list_devices()
            interfaces = self.engine.network.list_interfaces()
        except Exception as exc:
            self.call_from_thread(self.log_line, f'Device scan failed: {exc}', 'error')
            return
        self.call_from_thread(self._populate_devices, devices, interfaces)

    def _populate_devices(self, devices, interfaces) -> None:
        disk_table = self.query_one('#disk-table', DataTable)
        disk_table.clear()
        for d in devices:
            disk_table.add_row(d.get('name', '?'), d.get('size', '?'), d.get('type', '?'))
        net_table = self.query_one('#net-table', DataTable)
        net_table.clear()
        for i in interfaces:
            net_table.add_row(i.get('name', '?'), i.get('state', '?'), i.get('mac', '?'))
        self.log_line(f'Loaded {len(devices)} device(s), {len(interfaces)} interface(s)',
                      'success')

    # ── actions / events ─────────────────────────────────────────────────────────
    def action_refresh(self) -> None:
        self.log_line('Refreshing…')
        self.refresh_all()

    def action_collect(self) -> None:
        self.query_one(TabbedContent).active = 'collect'
        self.query_one('#case-id', Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == 'run-collect':
            case_id = self.query_one('#case-id', Input).value.strip()
            if not case_id:
                case_id = f'CASE-{datetime.now():%Y%m%d-%H%M%S}'
            self.run_collection(case_id)

    @work(thread=True, exclusive=True, group='collect')
    def run_collection(self, case_id: str) -> None:
        self.call_from_thread(self.log_line, f'Starting collection {case_id}…')
        self.call_from_thread(self._set_collect_status, 'running…')

        def progress(step, status='running'):
            self.call_from_thread(self._on_progress, step, status)

        try:
            result = self.engine.collect(case_id, progress=progress)
            msg = f'Collection complete → {result["json_report"]}'
            self.call_from_thread(self.log_line, msg, 'success')
            self.call_from_thread(self._set_collect_status, msg)
            self.call_from_thread(self.load_tasks)
        except Exception as exc:
            self.call_from_thread(self.log_line, f'Collection failed: {exc}', 'error')
            self.call_from_thread(self._set_collect_status, f'failed: {exc}')

    def _on_progress(self, step: str, status: str) -> None:
        self.log_line(f'  {step}: {status}')
        self._set_collect_status(f'{step}: {status}')

    def _set_collect_status(self, text: str) -> None:
        self.query_one('#collect-status', Static).update(text)


def main():
    VivisectTUI().run()


if __name__ == '__main__':
    main()
