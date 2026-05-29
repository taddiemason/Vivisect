"""Network tab: list interfaces, capture traffic to a PCAP."""

from kivy.metrics import dp

from .base import ScreenBase
from ..widgets import BigButton, LabeledInput, SectionCard, SelectableList


class NetworkScreen(ScreenBase):
    title = 'Network'

    def build(self):
        # --- Interfaces ---
        ifc = SectionCard(title='Interfaces')
        ifc.body.add_widget(BigButton(text='Refresh Interfaces', role='neutral',
                                      on_release=lambda _b: self.list_interfaces()))
        self.interfaces = SelectableList(on_select=self._pick_interface,
                                         size_hint_y=None, height=dp(200))
        ifc.body.add_widget(self.interfaces)
        self.content_box.add_widget(ifc)

        # --- Capture ---
        cap = SectionCard(title='Capture Traffic')
        self.iface_input = LabeledInput('Interface', hint='eth0')
        self.output_input = LabeledInput('Output File', hint='capture.pcap')
        self.duration_input = LabeledInput('Duration (seconds)', hint='60',
                                           input_filter='int')
        self.duration_input.value = '60'
        cap.body.add_widget(self.iface_input)
        cap.body.add_widget(self.output_input)
        cap.body.add_widget(self.duration_input)
        cap.body.add_widget(BigButton(text='Start Capture', role='primary',
                                      on_release=lambda _b: self.start_capture()))
        self.content_box.add_widget(cap)

    def list_interfaces(self):
        self.run('List interfaces', self.engine.network.list_interfaces,
                 on_result=self._show_interfaces)

    def _show_interfaces(self, envelope):
        data = envelope.get('data')
        items = data if isinstance(data, list) else []
        self.interfaces.populate(
            items,
            lambda i: '📡 %s   %s   %s' % (i.get('name', '?'), i.get('state', ''),
                                           i.get('mac', '')))

    def _pick_interface(self, iface):
        self.iface_input.value = iface.get('name', '')

    def start_capture(self):
        iface = self.iface_input.value
        output = self.output_input.value
        if not iface or not output:
            self.log('Interface and output file are required', 'warn')
            return
        duration = int(self.duration_input.value or '60')
        self.run('Capture %s (%ss)' % (iface, duration),
                 lambda: self.engine.network.capture_traffic(iface, output, duration=duration))
