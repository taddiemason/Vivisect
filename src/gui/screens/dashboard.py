"""Dashboard tab: quick collection, system status, quick actions, USB mode, log."""

from datetime import datetime

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label

from .base import ScreenBase
from .. import theme
from ..widgets import BigButton, LabeledInput, SectionCard, confirm


class DashboardScreen(ScreenBase):
    title = 'Dashboard'

    # USB mode buttons -> (label, engine call factory, confirm message)
    USB_MODES = [
        ('Multi-Function', 'multi'),
        ('USB Drive (RW)', 'mass_storage'),
        ('USB Drive (RO)', 'mass_storage_ro'),
        ('Network Only', 'network'),
    ]

    def build(self):
        # --- Quick Collection ---
        qc = SectionCard(title='Quick Collection')
        self.case_input = LabeledInput('Case ID (optional)', hint='auto-generated if blank')
        qc.body.add_widget(self.case_input)
        qc.body.add_widget(BigButton(text='Start Collection', role='primary',
                                     on_release=lambda _b: self.start_collection()))
        self.content_box.add_widget(qc)

        # --- System Status ---
        ss = SectionCard(title='System Status')
        self.status_lbl = Label(text='Loading…', color=theme.TEXT_DIM,
                                font_size=theme.BODY_FS, halign='left', valign='top',
                                size_hint_y=None, markup=True)
        self.status_lbl.bind(
            width=lambda i, w: setattr(i, 'text_size', (w, None)),
            texture_size=lambda i, ts: setattr(i, 'height', ts[1]))
        ss.body.add_widget(self.status_lbl)
        ss.body.add_widget(BigButton(text='Refresh Status', role='neutral',
                                     on_release=lambda _b: self.refresh_status()))
        self.content_box.add_widget(ss)

        # --- Quick Actions ---
        qa = SectionCard(title='Quick Actions')
        qa.body.add_widget(BigButton(text='Analyze Memory', role='neutral',
                                     on_release=lambda _b: self._quick('Memory', 'analyze_live')))
        qa.body.add_widget(BigButton(text='Extract Browser History', role='neutral',
                                     on_release=lambda _b: self._quick('Artifacts', 'extract_browser')))
        qa.body.add_widget(BigButton(text='Extract System Logs', role='neutral',
                                     on_release=lambda _b: self._quick('Artifacts', 'extract_logs')))
        self.content_box.add_widget(qa)

        # --- USB Gadget Mode ---
        um = SectionCard(title='USB Gadget Mode')
        for label, mode in self.USB_MODES:
            um.body.add_widget(BigButton(
                text=label, role='neutral',
                on_release=lambda _b, m=mode, lbl=label: self.switch_usb(m, lbl)))
        self.content_box.add_widget(um)

        # --- Activity Log (shared, global) ---
        al = SectionCard(title='Activity Log')
        self.app.activity.size_hint_y = None
        self.app.activity.height = dp(200)
        al.body.add_widget(self.app.activity)
        self.content_box.add_widget(al)

        self.refresh_status()

    # --- actions ---
    def start_collection(self):
        case = self.case_input.value or ('CASE-' + datetime.now().strftime('%Y%m%d-%H%M%S'))
        progress = self.bridge.marshal(
            lambda step, status: self.log('collect: %s — %s' % (step, status)))
        self.run('Quick collection (%s)' % case,
                 lambda: self.engine.collect(case, None, progress))

    def refresh_status(self):
        self.bridge.run_async('System status', self._gather_status,
                              on_result=self._show_status)

    def _gather_status(self):
        eng = self.engine
        out = {}

        def safe(fn, default='n/a'):
            try:
                return fn()
            except Exception as exc:  # field device: many calls are Linux-only
                return '%s (%s)' % (default, type(exc).__name__)

        out['Active tasks'] = safe(eng.tasks.active_count, '0')
        out['USB mode'] = safe(eng.usb.get_current_mode)
        info = safe(lambda: eng.usb.get_connection_info(), {})
        out['USB connected'] = info.get('connected') if isinstance(info, dict) else info
        out['Output dir'] = safe(lambda: eng.config.get('output_dir'), '')
        out['Modules enabled'] = safe(
            lambda: ', '.join(k for k, v in eng.module_status().items() if v), '')
        return out

    def _show_status(self, envelope):
        data = envelope.get('data') or {}
        if not envelope.get('success') or not isinstance(data, dict):
            self.status_lbl.text = '[color=#d94040]Status unavailable: %s[/color]' % (
                envelope.get('error') or 'unknown')
            return
        self.status_lbl.text = '\n'.join(
            '[b]%s:[/b] %s' % (k, v) for k, v in data.items())

    def _quick(self, tab, method):
        screen = self.app.goto(tab)
        getattr(screen, method)()

    def switch_usb(self, mode, label):
        calls = {
            'multi': lambda: self.engine.usb.switch_to_multi_function(),
            'mass_storage': lambda: self.engine.usb.switch_to_mass_storage_only(False),
            'mass_storage_ro': lambda: self.engine.usb.switch_to_mass_storage_only(True),
            'network': lambda: self.engine.usb.switch_to_network_only(),
        }
        confirm(
            'Switch USB Mode',
            'Switch the USB gadget to "%s"? This reconfigures how this device '
            'presents to a connected host.' % label,
            lambda: self.run('USB → %s' % label, calls[mode],
                             on_result=lambda _e: self.refresh_status()),
        )
