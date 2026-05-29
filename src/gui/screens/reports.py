"""Reports tab: list generated reports and open them with the OS default handler.

HTML reports (Chart.js) are inherently browser content; rather than embedding a
web engine in the GUI, we hand the file to the OS default application. The GUI
itself stays web-engine-free.
"""

import os
import subprocess
import sys
from datetime import datetime

from kivy.metrics import dp

from .base import ScreenBase
from ..widgets import BigButton, SectionCard, SelectableList


class ReportsScreen(ScreenBase):
    title = 'Reports'

    def build(self):
        card = SectionCard(title='Reports')
        card.body.add_widget(BigButton(text='Refresh Reports', role='neutral',
                                       on_release=lambda _b: self.list_reports()))
        self.reports = SelectableList(on_select=self._open_report,
                                      size_hint_y=None, height=dp(380))
        card.body.add_widget(self.reports)
        self.content_box.add_widget(card)
        self.list_reports()

    def list_reports(self):
        self.run('List reports', self._gather_reports, on_result=self._show_reports)

    def _gather_reports(self):
        out_dir = self.engine.config.get('output_dir') or '.'
        items = []
        if os.path.isdir(out_dir):
            for name in os.listdir(out_dir):
                path = os.path.join(out_dir, name)
                if not os.path.isfile(path):
                    continue
                st = os.stat(path)
                items.append({
                    'filename': name,
                    'path': path,
                    'size_kb': round(st.st_size / 1024.0, 1),
                    'modified': datetime.fromtimestamp(st.st_mtime).strftime('%Y-%m-%d %H:%M'),
                })
        items.sort(key=lambda d: d['modified'], reverse=True)
        return items

    def _show_reports(self, envelope):
        items = envelope.get('data')
        items = items if isinstance(items, list) else []
        self.reports.populate(
            items,
            lambda r: '📄 %s   %s KB   %s' % (r['filename'], r['size_kb'], r['modified']))

    def _open_report(self, report):
        path = report.get('path')
        try:
            if sys.platform.startswith('win'):
                os.startfile(path)  # noqa: B606 (Windows-only)
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', path])
            else:
                subprocess.Popen(['xdg-open', path])
            self.log('Opened %s' % report.get('filename'), 'ok')
        except Exception as exc:
            self.log('Could not open report: %s' % exc, 'err')
