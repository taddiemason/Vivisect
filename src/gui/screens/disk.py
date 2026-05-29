"""Disk Imaging tab: list devices, create forensic image (dd / dcfldd)."""

from kivy.metrics import dp
from kivy.uix.spinner import Spinner

from .base import ScreenBase
from .. import theme
from ..widgets import BigButton, LabeledInput, SectionCard, SelectableList, confirm


class DiskScreen(ScreenBase):
    title = 'Disk'

    def build(self):
        # --- Devices ---
        dev = SectionCard(title='Devices')
        dev.body.add_widget(BigButton(text='Refresh Devices', role='neutral',
                                      on_release=lambda _b: self.list_devices()))
        self.devices = SelectableList(on_select=self._pick_device,
                                      size_hint_y=None, height=dp(200))
        dev.body.add_widget(self.devices)
        self.content_box.add_widget(dev)

        # --- Create Image ---
        ci = SectionCard(title='Create Disk Image')
        self.device_input = LabeledInput('Device', hint='/dev/sdb')
        self.output_input = LabeledInput('Output File', hint='evidence.img')
        self.method = Spinner(text='dd', values=('dd', 'dcfldd'),
                              size_hint_y=None, height=theme.INPUT_HEIGHT,
                              background_color=theme.SURFACE_ALT, color=theme.TEXT)
        ci.body.add_widget(self.device_input)
        ci.body.add_widget(self.output_input)
        ci.body.add_widget(self.method)
        ci.body.add_widget(BigButton(text='Create Disk Image', role='danger',
                                     on_release=lambda _b: self.create_image()))
        self.content_box.add_widget(ci)

    def list_devices(self):
        self.run('List devices', self.engine.disk.list_devices,
                 on_result=self._show_devices)

    def _show_devices(self, envelope):
        data = envelope.get('data')
        devices = data if isinstance(data, list) else []
        self.devices.populate(
            devices,
            lambda d: '💿 %s   %s   %s' % (d.get('name', '?'), d.get('size', ''),
                                           d.get('type', '')))

    def _pick_device(self, device):
        self.device_input.value = device.get('name', '')

    def create_image(self):
        device = self.device_input.value
        output = self.output_input.value
        if not device or not output:
            self.log('Device and output file are required', 'warn')
            return
        method = self.method.text
        if method == 'dcfldd':
            fn = lambda: self.engine.disk.create_image_dcfldd(device, output)
        else:
            fn = lambda: self.engine.disk.create_image_dd(device, output)
        confirm(
            'Create Disk Image',
            'Image %s → %s using %s? This reads the entire device and may take a '
            'long time.' % (device, output, method),
            lambda: self.run('Disk image %s' % device, fn),
        )
