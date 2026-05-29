"""Memory tab: analyze the running system, create a memory dump."""

from kivy.metrics import dp
from kivy.uix.spinner import Spinner

from .base import ScreenBase
from .. import theme
from ..widgets import BigButton, LabeledInput, ResultPanel, SectionCard, confirm


class MemoryScreen(ScreenBase):
    title = 'Memory'

    def build(self):
        # --- Live analysis ---
        live = SectionCard(title='Live System')
        live.body.add_widget(BigButton(text='Analyze Running System', role='primary',
                                       on_release=lambda _b: self.analyze_live()))
        self.result = ResultPanel(size_hint_y=None, height=dp(220))
        live.body.add_widget(self.result)
        self.content_box.add_widget(live)

        # --- Memory dump ---
        dump = SectionCard(title='Create Memory Dump')
        self.output_input = LabeledInput('Output File', hint='memory.raw')
        self.method = Spinner(text='auto', values=('auto', 'lime', 'avml', 'dd'),
                              size_hint_y=None, height=theme.INPUT_HEIGHT,
                              background_color=theme.SURFACE_ALT, color=theme.TEXT)
        dump.body.add_widget(self.output_input)
        dump.body.add_widget(self.method)
        dump.body.add_widget(BigButton(text='Create Memory Dump', role='danger',
                                       on_release=lambda _b: self.create_dump()))
        self.content_box.add_widget(dump)

    def analyze_live(self):
        self.run('Analyze running system',
                 self.engine.memory.analyze_running_system,
                 on_result=self.result.show_envelope)

    def create_dump(self):
        output = self.output_input.value
        if not output:
            self.log('Output file is required', 'warn')
            return
        method = self.method.text
        confirm(
            'Create Memory Dump',
            'Dump system memory to %s using "%s"? This can be large and slow.'
            % (output, method),
            lambda: self.run('Memory dump (%s)' % method,
                             lambda: self.engine.memory.create_memory_dump(output, method)),
        )
