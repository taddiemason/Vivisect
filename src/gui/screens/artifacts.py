"""Artifacts tab: extract browser history, system logs, persistence mechanisms."""

from kivy.metrics import dp

from .base import ScreenBase
from ..widgets import BigButton, ResultPanel, SectionCard


class ArtifactsScreen(ScreenBase):
    title = 'Artifacts'

    def build(self):
        actions = SectionCard(title='Extract Artifacts')
        actions.body.add_widget(BigButton(text='Browser History', role='neutral',
                                          on_release=lambda _b: self.extract_browser()))
        actions.body.add_widget(BigButton(text='System Logs', role='neutral',
                                          on_release=lambda _b: self.extract_logs()))
        actions.body.add_widget(BigButton(text='Persistence Mechanisms', role='neutral',
                                          on_release=lambda _b: self.extract_persistence()))
        self.content_box.add_widget(actions)

        results = SectionCard(title='Results')
        self.result = ResultPanel(size_hint_y=None, height=dp(320))
        results.body.add_widget(self.result)
        self.content_box.add_widget(results)

    def extract_browser(self):
        self.run('Extract browser history',
                 self.engine.artifacts.extract_browser_history,
                 on_result=self.result.show_envelope)

    def extract_logs(self):
        self.run('Extract system logs',
                 self.engine.artifacts.extract_system_logs,
                 on_result=self.result.show_envelope)

    def extract_persistence(self):
        self.run('Extract persistence mechanisms',
                 self.engine.artifacts.extract_persistence_mechanisms,
                 on_result=self.result.show_envelope)
