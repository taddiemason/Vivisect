"""HID Keyboard tab: status, mode switch, send string, execute payload.

Carries the same security warning as the web GUI — HID injection is dual-use and
only legitimate with authorization (pentest / forensics / CTF / education).
"""

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput

from .base import ScreenBase
from .. import theme
from ..widgets import BigButton, LabeledInput, SectionCard, confirm

WARNING_TEXT = (
    '[b]Authorized use only.[/b] HID keyboard injection sends keystrokes to a '
    'connected host as if typed by a user. Legitimate uses: authorized '
    'penetration testing, incident response/forensics, CTF, and education. '
    'Unauthorized access, malware delivery, or privacy violations are '
    'prohibited and may be illegal. You are responsible for having permission '
    'to act on the target host.'
)


class HIDScreen(ScreenBase):
    title = 'HID'

    def build(self):
        # --- Warning ---
        warn = SectionCard(title='⚠ Security Warning')
        warn_lbl = Label(text=WARNING_TEXT, color=theme.WARN, font_size=theme.SMALL_FS,
                         halign='left', valign='top', size_hint_y=None, markup=True)
        warn_lbl.bind(width=lambda i, w: setattr(i, 'text_size', (w, None)),
                      texture_size=lambda i, ts: setattr(i, 'height', ts[1]))
        warn.body.add_widget(warn_lbl)
        self.content_box.add_widget(warn)

        # --- Status ---
        status = SectionCard(title='HID Status')
        self.status_lbl = Label(text='Unknown — tap Refresh', color=theme.TEXT_DIM,
                                font_size=theme.BODY_FS, halign='left', valign='middle',
                                size_hint_y=None, height=dp(28), markup=True)
        self.status_lbl.bind(width=lambda i, w: setattr(i, 'text_size', (w, None)))
        status.body.add_widget(self.status_lbl)
        status.body.add_widget(BigButton(text='Refresh Status', role='neutral',
                                         on_release=lambda _b: self.refresh_status()))
        status.body.add_widget(BigButton(text='Switch to HID Mode', role='neutral',
                                         on_release=lambda _b: self.switch_mode()))
        self.content_box.add_widget(status)

        # --- Send string ---
        send = SectionCard(title='Send HID String')
        self.text_input = TextInput(
            hint_text='Text to type on the host (max 500 chars)…', multiline=True,
            size_hint_y=None, height=dp(96), font_size=theme.BODY_FS,
            background_color=theme.SURFACE_ALT, foreground_color=theme.TEXT,
            cursor_color=theme.ACCENT)
        self.text_input.bind(text=self._cap_text)
        self.delay_input = LabeledInput('Delay between keys (ms)', hint='50',
                                        input_filter='int')
        self.delay_input.value = '50'
        send.body.add_widget(self.text_input)
        send.body.add_widget(self.delay_input)
        send.body.add_widget(BigButton(text='Send HID String', role='danger',
                                       on_release=lambda _b: self.send_string()))
        self.content_box.add_widget(send)

        # --- Execute payload ---
        payload = SectionCard(title='Execute HID Payload')
        self.payload_spinner = Spinner(
            text='(refresh to load)', values=(), size_hint_y=None,
            height=theme.INPUT_HEIGHT, background_color=theme.SURFACE_ALT,
            color=theme.TEXT)
        payload.body.add_widget(self.payload_spinner)
        payload.body.add_widget(BigButton(text='Load Payloads', role='neutral',
                                          on_release=lambda _b: self.load_payloads()))
        payload.body.add_widget(BigButton(text='Execute Payload', role='danger',
                                          on_release=lambda _b: self.execute_payload()))
        self.content_box.add_widget(payload)

        self.refresh_status()

    def _cap_text(self, instance, value):
        if len(value) > 500:
            instance.text = value[:500]

    # --- actions ---
    def refresh_status(self):
        self.run('HID status', self._gather_status, on_result=self._show_status)

    def _gather_status(self):
        try:
            available = bool(self.engine.usb.is_hid_available())
        except Exception as exc:
            return {'available': False, 'note': type(exc).__name__}
        return {'available': available}

    def _show_status(self, envelope):
        data = envelope.get('data') or {}
        if data.get('available'):
            self.status_lbl.text = '[color=#33b366]✓ HID device available[/color]'
        else:
            note = data.get('note', '')
            self.status_lbl.text = (
                '[color=#d94040]✗ HID not available[/color] '
                '(run setup-usb-hid.sh on the device) %s' % note)

    def switch_mode(self):
        confirm(
            'Switch to HID Mode',
            'Reconfigure the USB gadget as a HID keyboard? The device will present '
            'as a keyboard to any connected host.',
            lambda: self.run('Switch to HID mode',
                             self.engine.usb.switch_to_hid_mode,
                             on_result=lambda _e: self.refresh_status()),
        )

    def send_string(self):
        text = self.text_input.text
        if not text:
            self.log('Enter text to send', 'warn')
            return
        delay = int(self.delay_input.value or '50')
        confirm(
            'Send HID String',
            'AUTHORIZED USE ONLY. Type %d characters into the connected host now?'
            % len(text),
            lambda: self.run('Send HID string',
                             lambda: self.engine.usb.send_hid_string(text, delay_ms=delay)),
        )

    def load_payloads(self):
        self.run('Load HID payloads', self._gather_payloads,
                 on_result=self._show_payloads)

    def _gather_payloads(self):
        # _get_hid_payloads returns {name: callable}; we only need the names.
        return sorted(self.engine.usb._get_hid_payloads().keys())

    def _show_payloads(self, envelope):
        names = envelope.get('data') or []
        if isinstance(names, list) and names:
            self.payload_spinner.values = tuple(names)
            self.payload_spinner.text = names[0]
        else:
            self.payload_spinner.values = ()
            self.payload_spinner.text = '(none available)'

    def execute_payload(self):
        name = self.payload_spinner.text
        if not name or name.startswith('('):
            self.log('Load and select a payload first', 'warn')
            return
        confirm(
            'Execute HID Payload',
            'AUTHORIZED USE ONLY. Execute payload "%s" against the connected host?'
            % name,
            lambda: self.run('Execute payload %s' % name,
                             lambda: self.engine.usb.execute_hid_payload(name)),
        )
