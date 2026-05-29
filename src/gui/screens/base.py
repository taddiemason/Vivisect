"""Shared base for tab screens.

Wraps content in a scroll view and provides the engine/bridge handles plus
``run()`` — the one path every backend call takes (logs start, runs async on the
task pool, logs success/failure, then forwards the result envelope).
"""

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView

from .. import theme


class ScreenBase(BoxLayout):
    title = 'Tab'

    def __init__(self, app, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.app = app
        self.engine = app.engine
        self.bridge = app.bridge

        scroll = ScrollView()
        self.content_box = BoxLayout(
            orientation='vertical', spacing=theme.GAP,
            padding=theme.PAD, size_hint_y=None,
        )
        self.content_box.bind(minimum_height=self.content_box.setter('height'))
        scroll.add_widget(self.content_box)
        self.add_widget(scroll)

        self.build()

    def build(self):
        """Subclasses populate ``self.content_box`` here."""

    def log(self, message, level='info'):
        self.app.activity.add(message, level)

    def run(self, name, fn, *args, on_result=None):
        """Run a backend call through the bridge with start/end logging."""
        self.log('%s…' % name)

        def _result(envelope):
            if envelope.get('success'):
                self.log('%s ✓' % name, 'ok')
            else:
                self.log('%s ✗ %s' % (name, envelope.get('error') or ''), 'err')
            if on_result is not None:
                on_result(envelope)

        self.bridge.run_async(name, fn, *args, on_result=_result)
