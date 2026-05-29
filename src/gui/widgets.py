"""Reusable touch-friendly widgets for the native GUI.

Appearance (backgrounds, rounded corners) is defined in ``vivisect.kv``; this
module holds the behavior. Everything here runs on the Kivy main thread.
"""

import json
from datetime import datetime

from kivy.metrics import dp
from kivy.properties import StringProperty, ListProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

from . import theme


class BigButton(Button):
    """Primary touch button. Variant controlled via ``role`` (styled in kv)."""

    role = StringProperty('primary')  # 'primary' | 'danger' | 'neutral'


class SectionCard(BoxLayout):
    """A titled card. Add content widgets to ``.body``."""

    title = StringProperty('')

    def __init__(self, title='', **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = theme.PAD
        self.spacing = theme.GAP
        self.size_hint_y = None
        self._title_lbl = Label(
            text=title, color=theme.TEXT, font_size=theme.SECTION_FS,
            bold=True, halign='left', valign='middle', size_hint_y=None,
            height=dp(28),
        )
        self._title_lbl.bind(size=self._sync_text_size)
        self.add_widget(self._title_lbl)
        self.title = title

        self.body = BoxLayout(orientation='vertical', spacing=theme.GAP,
                              size_hint_y=None)
        self.body.bind(minimum_height=self.body.setter('height'))
        self.add_widget(self.body)
        self.body.bind(minimum_height=self._resize)
        self.bind(title=lambda _i, v: setattr(self._title_lbl, 'text', v))

    def _sync_text_size(self, inst, _v):
        inst.text_size = (inst.width, None)

    def _resize(self, _inst, _v):
        self.height = self._title_lbl.height + self.body.height + self.padding[1] * 2 + self.spacing


class LabeledInput(BoxLayout):
    """A label above a single-line text input. Read ``.value``."""

    def __init__(self, label, hint='', input_filter=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.spacing = dp(4)
        self.height = dp(22) + theme.INPUT_HEIGHT
        cap = Label(text=label, color=theme.TEXT_DIM, font_size=theme.SMALL_FS,
                    halign='left', valign='middle', size_hint_y=None, height=dp(20))
        cap.bind(size=lambda i, _v: setattr(i, 'text_size', (i.width, None)))
        self.input = TextInput(
            hint_text=hint, multiline=False, input_filter=input_filter,
            size_hint_y=None, height=theme.INPUT_HEIGHT, font_size=theme.BODY_FS,
            background_color=theme.SURFACE_ALT, foreground_color=theme.TEXT,
            cursor_color=theme.ACCENT, padding=(dp(10), dp(12)),
        )
        self.add_widget(cap)
        self.add_widget(self.input)

    @property
    def value(self):
        return self.input.text.strip()

    @value.setter
    def value(self, v):
        self.input.text = v or ''


class ActivityLog(BoxLayout):
    """Scrolling, newest-first activity log (capped at 50 entries)."""

    MAX = 50

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self._entries = []
        self._scroll = ScrollView()
        self._label = Label(
            text='', color=theme.TEXT_DIM, font_size=theme.SMALL_FS,
            halign='left', valign='top', size_hint_y=None, markup=True,
        )
        self._label.bind(
            width=lambda i, w: setattr(i, 'text_size', (w, None)),
            texture_size=lambda i, ts: setattr(i, 'height', ts[1]),
        )
        self._scroll.add_widget(self._label)
        self.add_widget(self._scroll)

    def add(self, message, level='info'):
        ts = datetime.now().strftime('%H:%M:%S')
        color = {'info': '8a9099', 'ok': '33b366', 'err': 'd94040',
                 'warn': 'e6a633'}.get(level, '8a9099')
        self._entries.insert(0, '[color=#%s][%s] %s[/color]' % (color, ts, message))
        del self._entries[self.MAX:]
        self._label.text = '\n'.join(self._entries)


class ResultPanel(ScrollView):
    """Renders a result envelope's ``data`` as a compact, scrollable summary.

    Lists are summarized by count (matching the web UI), scalars shown inline.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._box = BoxLayout(orientation='vertical', size_hint_y=None,
                              spacing=dp(2), padding=(0, dp(4)))
        self._box.bind(minimum_height=self._box.setter('height'))
        self.add_widget(self._box)

    def _line(self, text, color):
        lbl = Label(text=text, color=color, font_size=theme.BODY_FS,
                    halign='left', valign='top', size_hint_y=None, markup=True)
        lbl.bind(width=lambda i, w: setattr(i, 'text_size', (w, None)),
                 texture_size=lambda i, ts: setattr(i, 'height', max(ts[1], dp(20))))
        self._box.add_widget(lbl)

    def show_envelope(self, envelope):
        self._box.clear_widgets()
        if not envelope.get('success'):
            self._line('[b]Error:[/b] %s' % (envelope.get('error') or 'unknown'),
                       theme.DANGER)
            return
        self._render(envelope.get('data'))

    def _render(self, data):
        if isinstance(data, dict):
            if not data:
                self._line('(empty result)', theme.TEXT_DIM)
                return
            for key, val in data.items():
                self._line('[b]%s:[/b] %s' % (key, self._summarize(val)), theme.TEXT)
        elif isinstance(data, list):
            self._line('%d item(s)' % len(data), theme.TEXT)
            for item in data[:50]:
                self._line('• %s' % self._summarize(item), theme.TEXT_DIM)
        else:
            self._line(str(data), theme.TEXT)

    @staticmethod
    def _summarize(val):
        if isinstance(val, list):
            return '%d item(s)' % len(val)
        if isinstance(val, dict):
            return '{%d field(s)}' % len(val)
        text = str(val)
        return text if len(text) <= 200 else text[:200] + '…'


class SelectableList(ScrollView):
    """A scrollable list of tappable rows. ``on_select(item)`` fires on tap."""

    def __init__(self, on_select=None, **kwargs):
        super().__init__(**kwargs)
        self._on_select = on_select
        self._box = BoxLayout(orientation='vertical', size_hint_y=None,
                              spacing=theme.GAP)
        self._box.bind(minimum_height=self._box.setter('height'))
        self.add_widget(self._box)

    def populate(self, items, format_row):
        """``items``: list of dicts. ``format_row(item) -> str`` for the label."""
        self._box.clear_widgets()
        if not items:
            placeholder = Label(text='(none found)', color=theme.TEXT_DIM,
                                font_size=theme.BODY_FS, size_hint_y=None,
                                height=theme.ROW_HEIGHT)
            self._box.add_widget(placeholder)
            return
        for item in items:
            btn = BigButton(text=format_row(item), role='neutral',
                            halign='left', valign='middle')
            btn.bind(size=lambda i, _v: setattr(i, 'text_size', (i.width - dp(20), None)))
            btn.bind(on_release=lambda _b, it=item: self._select(it))
            self._box.add_widget(btn)

    def _select(self, item):
        if self._on_select:
            self._on_select(item)


def confirm(title, message, on_yes, danger=True):
    """Modal confirm dialog for destructive/outward actions."""
    root = BoxLayout(orientation='vertical', spacing=theme.GAP, padding=theme.PAD)
    msg = Label(text=message, color=theme.TEXT, font_size=theme.BODY_FS,
                halign='left', valign='top')
    msg.bind(size=lambda i, _v: setattr(i, 'text_size', (i.width, None)))
    root.add_widget(msg)

    buttons = BoxLayout(orientation='horizontal', spacing=theme.GAP,
                        size_hint_y=None, height=theme.BTN_HEIGHT)
    cancel_btn = BigButton(text='Cancel', role='neutral')
    yes_btn = BigButton(text='Confirm', role='danger' if danger else 'primary')
    buttons.add_widget(cancel_btn)
    buttons.add_widget(yes_btn)
    root.add_widget(buttons)

    popup = Popup(title=title, content=root, size_hint=(0.8, 0.5),
                  title_color=theme.TEXT, separator_color=theme.ACCENT)
    cancel_btn.bind(on_release=popup.dismiss)

    def _do(_btn):
        popup.dismiss()
        on_yes()

    yes_btn.bind(on_release=_do)
    popup.open()
    return popup
