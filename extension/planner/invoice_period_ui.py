"""One-calendar invoice periods, with a pure date controller for validation."""
import calendar
from datetime import date, timedelta

MONTHS = ('janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho',
    'agosto', 'setembro', 'outubro', 'novembro', 'dezembro')


class PeriodSelection:
    def __init__(self, initial=None):
        try:
            initial = date.fromisoformat(initial) if isinstance(initial, str) else initial
            if not isinstance(initial, date):
                initial = date.today()
        except ValueError:
            initial = date.today()
        self.year, self.month = initial.year, initial.month
        self.mode = 'all'
        self.start = self.end = None

    def set_mode(self, mode):
        if mode not in ('all', 'month', 'range'):
            raise ValueError('Escolha um tipo de período válido.')
        if mode != self.mode:
            self.start = self.end = None
        self.mode = mode

    def navigate(self, months):
        total = self.year * 12 + self.month - 1 + months
        year, month = divmod(total, 12)
        if 1 <= year <= 9999:
            self.year, self.month = year, month + 1

    def choose(self, day):
        if not isinstance(day, date):
            raise ValueError('Escolha uma data no calendário.')
        if self.mode == 'range':
            if self.start is None or self.end is not None:
                self.start, self.end = day, None
            else:
                self.start, self.end = sorted((self.start, day))
        elif self.mode == 'month':
            self.year, self.month = day.year, day.month

    def clear(self):
        self.start = self.end = None

    @property
    def ready(self):
        return self.mode != 'range' or (self.start is not None and self.end is not None)

    def selection_key(self):
        if self.mode == 'month':
            return self.mode, self.year, self.month
        if self.mode == 'range':
            return self.mode, self.start, self.end
        return (self.mode,)

    def bounds(self):
        if self.mode == 'all':
            return None, None
        if self.mode == 'month':
            return date(self.year, self.month, 1).isoformat(), date(self.year, self.month,
                calendar.monthrange(self.year, self.month)[1]).isoformat()
        if not self.ready:
            raise ValueError('Escolha o início e o fim do período no calendário.')
        return self.start.isoformat(), self.end.isoformat()

    def includes(self, day):
        if self.mode == 'all':
            return False
        if self.mode == 'month':
            return (day.year, day.month) == (self.year, self.month)
        return self.start is not None and self.start <= day <= (self.end or self.start)

    def summary(self):
        if self.mode == 'all':
            return 'Todo o histórico registrado desta timesheet.'
        if self.mode == 'month':
            start, end = (date.fromisoformat(value).strftime('%d/%m/%Y') for value in self.bounds())
            return f'Mês civil: {start} até {end}, inclusive.'
        if self.start is None:
            return 'Escolha a data inicial. Depois, escolha a data final no mesmo calendário.'
        if self.end is None:
            return f'Primeira data: {self.start:%d/%m/%Y}. Falta escolher a segunda data.'
        return f'Início: {self.start:%d/%m/%Y} · Fim: {self.end:%d/%m/%Y}, inclusive. Novo clique recomeça.'


class InvoicePeriodPicker:
    def __init__(self, initial, changed):
        import gi
        gi.require_version('Gtk', '3.0')
        from gi.repository import Gtk, Gdk
        self.Gtk, self.Gdk = Gtk, Gdk
        self.model = PeriodSelection(initial)
        self.changed = changed
        self.widget = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.choice = Gtk.ComboBoxText()
        for mode, title in [('month', 'Período de 1 mês'), ('all', 'Todo o histórico'), ('range', 'Período específico')]:
            self.choice.append(mode, title)
        self.choice.set_active_id('all')
        label = Gtk.Label.new_with_mnemonic('_Período da invoice')
        label.set_xalign(0)
        label.set_mnemonic_widget(self.choice)
        self.choice.get_accessible().set_name('Período da invoice')
        self.widget.pack_start(label, False, False, 0)
        self.widget.pack_start(self.choice, False, False, 0)
        self.calendar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.calendar.set_no_show_all(True)
        self.widget.pack_start(self.calendar, False, False, 0)
        navigation = Gtk.Box(spacing=4)
        self.calendar.pack_start(navigation, False, False, 0)
        self.nav_buttons = []
        for text, amount, name in [('«', -12, 'Ano anterior'), ('‹', -1, 'Mês anterior')]:
            self._nav(navigation, text, amount, name)
        self.title = Gtk.Label(hexpand=True)
        navigation.pack_start(self.title, True, True, 0)
        for text, amount, name in [('›', 1, 'Próximo mês'), ('»', 12, 'Próximo ano')]:
            self._nav(navigation, text, amount, name)
        grid = Gtk.Grid(column_homogeneous=True, row_spacing=2, column_spacing=2)
        self.calendar.pack_start(grid, False, False, 0)
        for column, text in enumerate(('dom', 'seg', 'ter', 'qua', 'qui', 'sex', 'sáb')):
            grid.attach(Gtk.Label(label=text), column, 0, 1, 1)
        self.buttons = []
        self.days = [None] * 42
        css = Gtk.CssProvider()
        css.load_from_data(b'''
button.invoice-period-day {padding: 3px; min-width: 22px; min-height: 24px;}
button.invoice-period-day.in-range {background-image: none; background-color: @theme_selected_bg_color; color: @theme_selected_fg_color;}
button.invoice-period-day.range-edge {border: 2px solid @theme_selected_bg_color; font-weight: bold;}
''')
        for index in range(42):
            button = Gtk.Button()
            button.get_style_context().add_class('invoice-period-day')
            button.get_style_context().add_provider(css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
            button.connect('clicked', lambda _, i=index: self._choose(i))
            button.connect('key-press-event', lambda _, event, i=index: self._key(event, i))
            grid.attach(button, index % 7, index // 7 + 1, 1, 1)
            self.buttons.append(button)
        self.clear_button = Gtk.Button(label='Limpar / recomeçar seleção')
        self.clear_button.connect('clicked', self._clear)
        self.calendar.pack_start(self.clear_button, False, False, 0)
        self.help = Gtk.Label(label='No período específico, faça dois cliques. Se clicar na data final primeiro, '
            'as duas datas serão ordenadas. Use as setas do teclado para mover o foco e Enter/Espaço para escolher.',
            xalign=0, wrap=True)
        self.help.set_max_width_chars(52)
        self.calendar.pack_start(self.help, False, False, 0)
        self.summary = Gtk.Label(xalign=0, wrap=True, selectable=True)
        self.summary.set_max_width_chars(52)
        self.widget.pack_start(self.summary, False, False, 0)
        self.choice.connect('changed', self._mode)
        self.calendar.set_no_show_all(False)
        self.calendar.show_all()
        self.calendar.set_no_show_all(True)
        self._refresh()

    def _nav(self, container, text, amount, name):
        button = self.Gtk.Button(label=text)
        button.set_tooltip_text(name)
        button.get_accessible().set_name(name)
        button.connect('clicked', lambda *_: self._navigate(amount))
        container.pack_start(button, False, False, 0)
        self.nav_buttons.append((button, amount))

    def _refresh(self):
        model = self.model
        self.calendar.set_visible(model.mode != 'all')
        self.title.set_text(f'{MONTHS[model.month - 1]} de {model.year}')
        offset = (date(model.year, model.month, 1).weekday() + 1) % 7
        last = calendar.monthrange(model.year, model.month)[1]
        for index, button in enumerate(self.buttons):
            number = index - offset + 1
            day = date(model.year, model.month, number) if 1 <= number <= last else None
            self.days[index] = day
            button.set_label(str(number) if day else '')
            button.set_sensitive(day is not None)
            style = button.get_style_context()
            for name in ('in-range', 'range-edge'):
                style.remove_class(name)
            if day and model.includes(day):
                style.add_class('in-range')
                if model.mode == 'range' and day in (model.start, model.end):
                    style.add_class('range-edge')
            name = day.strftime('%d/%m/%Y') if day else 'Fora do mês'
            if day and model.includes(day):
                name += ' · selecionado'
                if day == model.start:
                    name += ' · início'
                if day == model.end:
                    name += ' · fim'
            button.get_accessible().set_name(name)
            button.set_tooltip_text(name)
        for button, amount in self.nav_buttons:
            year = (model.year * 12 + model.month - 1 + amount) // 12
            button.set_sensitive(1 <= year <= 9999)
        self.clear_button.set_sensitive(model.mode == 'range')
        self.summary.set_text(model.summary())

    def _notify(self, before):
        if self.model.selection_key() != before:
            self.changed()

    def _mode(self, *_):
        before = self.model.selection_key()
        self.model.set_mode(self.choice.get_active_id())
        self._refresh()
        self._notify(before)

    def _navigate(self, months):
        before = self.model.selection_key()
        self.model.navigate(months)
        self._refresh()
        self._notify(before)

    def _choose(self, index):
        if self.days[index]:
            before = self.model.selection_key()
            self.model.choose(self.days[index])
            self._refresh()
            self._notify(before)

    def _clear(self, *_):
        before = self.model.selection_key()
        self.model.clear()
        self._refresh()
        self._notify(before)

    def _key(self, event, index):
        if not self.days[index]:
            return False
        key = event.keyval
        Gdk = self.Gdk
        shifts = {Gdk.KEY_Left: -1, Gdk.KEY_Right: 1, Gdk.KEY_Up: -7, Gdk.KEY_Down: 7}
        if key in shifts:
            before = self.model.selection_key()
            try:
                target = self.days[index] + timedelta(days=shifts[key])
            except OverflowError:
                return True
            self.model.year, self.model.month = target.year, target.month
            self._refresh()
            self.buttons[self.days.index(target)].grab_focus()
            self._notify(before)
            return True
        if key in (Gdk.KEY_Page_Up, Gdk.KEY_Page_Down):
            number = self.days[index].day
            self._navigate(-1 if key == Gdk.KEY_Page_Up else 1)
            number = min(number, calendar.monthrange(self.model.year, self.model.month)[1])
            self.buttons[self.days.index(date(self.model.year, self.model.month, number))].grab_focus()
            return True
        return False
