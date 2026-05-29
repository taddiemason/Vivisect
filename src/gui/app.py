"""Application shell for the native Vivisect GUI.

Owns the single VivisectEngine instance, the task bridge, the shared activity log,
the status bar, and the 7-tab layout. Opens a native window — no Flask, no socket,
no browser.
"""

import os
import sys
from datetime import datetime

# Make sibling packages (core, modules) importable whether run via ``python -m gui``
# from src/ or via the installed console entry point.
_SRC = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

# Kivy graphics config MUST be set before the Window is created.
from kivy.config import Config  # noqa: E402

if os.environ.get('VIVISECT_GUI_FULLSCREEN', '0') == '1':
    # Kiosk on the onboard display.
    Config.set('graphics', 'fullscreen', 'auto')
else:
    Config.set('graphics', 'width', '1024')
    Config.set('graphics', 'height', '640')

from kivy.app import App  # noqa: E402
from kivy.clock import Clock  # noqa: E402
from kivy.core.window import Window  # noqa: E402
from kivy.graphics import Color, Rectangle  # noqa: E402
from kivy.lang import Builder  # noqa: E402
from kivy.metrics import dp  # noqa: E402
from kivy.uix.boxlayout import BoxLayout  # noqa: E402
from kivy.uix.label import Label  # noqa: E402
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem  # noqa: E402

from core.engine import VivisectEngine  # noqa: E402

from . import theme  # noqa: E402
from .bridge import TaskBridge  # noqa: E402
from .screens import SCREEN_CLASSES  # noqa: E402
from .widgets import ActivityLog  # noqa: E402


class VivisectGUIApp(App):
    title = 'Vivisect Forensics'

    def build(self):
        Window.clearcolor = theme.BG
        Builder.load_file(os.path.join(os.path.dirname(__file__), 'vivisect.kv'))

        # Shared composition root — same engine the CLI uses.
        self.engine = VivisectEngine()
        self.bridge = TaskBridge(self.engine)
        self.activity = ActivityLog()

        root = BoxLayout(orientation='vertical')
        root.add_widget(self._build_status_bar())

        self.tabs = TabbedPanel(do_default_tab=False, tab_width=dp(132),
                                tab_height=dp(50))
        self.screens = {}
        for cls in SCREEN_CLASSES:
            screen = cls(self)
            item = TabbedPanelItem(text=screen.title)
            item.add_widget(screen)
            self.tabs.add_widget(item)
            screen._tab_item = item
            self.screens[screen.title] = screen
        root.add_widget(self.tabs)

        # Open on the Dashboard.
        self.tabs.switch_to(self.screens['Dashboard']._tab_item)

        Clock.schedule_interval(self._tick, 1)
        self.activity.add('Native GUI started — no network listener open', 'ok')
        return root

    def goto(self, name):
        """Switch to a tab by title and return its screen (for quick actions)."""
        screen = self.screens[name]
        self.tabs.switch_to(screen._tab_item)
        return screen

    def _build_status_bar(self):
        bar = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40),
                        padding=(dp(12), 0), spacing=dp(10))
        with bar.canvas.before:
            Color(*theme.SURFACE)
            self._bar_rect = Rectangle(pos=bar.pos, size=bar.size)
        bar.bind(pos=lambda _i, v: setattr(self._bar_rect, 'pos', v),
                 size=lambda _i, v: setattr(self._bar_rect, 'size', v))

        title_lbl = Label(text='[b]Vivisect[/b]  ·  native (no listener)', markup=True,
                          color=theme.TEXT, font_size=theme.BODY_FS,
                          halign='left', valign='middle')
        title_lbl.bind(size=lambda i, _v: setattr(i, 'text_size', i.size))
        self.clock_lbl = Label(text='', color=theme.TEXT_DIM, font_size=theme.SMALL_FS,
                               halign='right', valign='middle')
        self.clock_lbl.bind(size=lambda i, _v: setattr(i, 'text_size', i.size))
        bar.add_widget(title_lbl)
        bar.add_widget(self.clock_lbl)
        return bar

    def _tick(self, _dt):
        try:
            active = self.engine.tasks.active_count()
        except Exception:
            active = '?'
        self.clock_lbl.text = '%s task(s) active  ·  %s' % (
            active, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    def on_stop(self):
        try:
            self.engine.tasks.shutdown(wait=False)
        except Exception:
            pass


def main():
    VivisectGUIApp().run()
    return 0


if __name__ == '__main__':
    sys.exit(main())
