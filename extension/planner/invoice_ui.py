"""Review a service invoice and explicitly export a private local PDF."""
from copy import deepcopy
from datetime import date
from pathlib import Path
from uuid import uuid4
import invoice
import invoice_profiles
import store
from invoice_period_ui import InvoicePeriodPicker
from workspace_ui import context_text


def check_external_destination(filename):
    """Keep user exports outside both lexical and resolved history boundaries."""
    try:
        import invoice_history
        root = Path(invoice_history.ROOT).expanduser().absolute()
        target = Path(filename).expanduser().absolute()
        managed = target.is_relative_to(root) or target.resolve().is_relative_to(root.resolve())
    except (ImportError, OSError, RuntimeError, TypeError, AttributeError):
        raise ValueError('Não foi possível verificar o destino do PDF. Escolha uma pasta fora do histórico de invoices.') from None
    if managed:
        raise ValueError('Escolha uma pasta fora do histórico de invoices para salvar o PDF.')



class ReissueConfirmation(ValueError):
    def __init__(self, result):
        super().__init__('Possível reemissão de horas já faturadas. Confirme a intenção antes de salvar.')
        self.result = result


class InvoiceSession:
    """Keep a reviewed snapshot separate from editable fields and saved profiles."""
    def __init__(self, read_data=None):
        self.read_data = read_data or (lambda: store.modify({'action': 'get'}))
        self.snapshot = None
        self.profile = None
        self.sheet_id = None

    def invalidate(self):
        self.snapshot = None
        self.profile = None

    def prepare(self, sheet_id, values):
        self.invalidate()
        sheet = next((s for s in self.read_data().get('timesheets', []) if s['id'] == sheet_id), None)
        if sheet is None:
            raise ValueError('Esta timesheet não está mais disponível.')
        snapshot = invoice.build_snapshot(sheet, issuer=values['issuer'], client=values['client'],
            rate=values['rate'], currency=values['currency'], language=values['language'],
            reference=values['reference'], issued_on=values['issued_on'],
            start=values.get('start'), end=values.get('end'))
        self.snapshot = deepcopy(snapshot)
        self.profile = deepcopy({key: values[key] for key in ('issuer', 'client', 'rate', 'currency', 'language')})
        self.sheet_id = sheet_id
        return deepcopy(snapshot)

    def duplicate_check(self):
        try:
            import invoice_history
            return invoice_history.possible_duplicates(deepcopy(self.snapshot))
        except Exception:
            return {'matches': [], 'warnings': ['Não foi possível conferir todo o histórico de invoices.'], 'incomplete': True}

    def export(self, filename, overwrite=False, confirmed_reissue=False):
        if self.snapshot is None:
            raise ValueError('Revise a prévia antes de salvar o PDF.')
        check_external_destination(filename)
        duplicates = self.duplicate_check()
        if (duplicates['matches'] or duplicates['warnings'] or duplicates['incomplete']) and not confirmed_reissue:
            raise ReissueConfirmation(duplicates)
        try:
            import invoice_pdf
            path = invoice_pdf.write(deepcopy(self.snapshot), filename, overwrite=overwrite)
        except ImportError:
            raise ValueError('A exportação PDF requer ReportLab. Instale a dependência para gerar a invoice.') from None
        warnings = []
        try:
            import invoice_history
            invoice_history.record(deepcopy(self.snapshot), path)
        except Exception:
            warnings.append('O PDF foi salvo, mas não foi possível guardar a cópia no histórico de invoices.')
        try:
            invoice_profiles.save(self.sheet_id, deepcopy(self.profile))
        except Exception:
            warnings.append('O PDF foi salvo, mas não foi possível salvar os dados para a próxima invoice.')
        return path, '\n'.join(warnings)


def open_invoice(window):
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, Pango

    try:
        data = store.modify({'action': 'get'})
        sheets = data.get('timesheets', [])
        if not sheets:
            window.status.set_text('Crie uma timesheet para gerar uma invoice de serviços.')
            return
        session = InvoiceSession()
        preferred = getattr(window, 'selected_sheet_id', None) or window.last_tab
        first = next((s['id'] for s in sheets if s['id'] == preferred), sheets[0]['id'])
        first_sheet = next(s for s in sheets if s['id'] == first)
        initial = invoice_profiles.load(first, context=first_sheet.get('context', {}))
    except Exception:
        window.status.set_text('Não foi possível carregar os dados da invoice. Os dados locais foram preservados.')
        return

    dialog = Gtk.Dialog(title='Gerar invoice de serviços / PDF', transient_for=window, modal=True)
    dialog.add_buttons('Cancelar', Gtk.ResponseType.CANCEL, 'Revisar prévia', Gtk.ResponseType.APPLY,
        'Salvar PDF…', Gtk.ResponseType.OK)
    width, height = 640, 680
    parent_window = window.get_window()
    monitor = window.get_display().get_monitor_at_window(parent_window) if parent_window else None
    if monitor:
        area = monitor.get_workarea()
        width, height = min(width, max(360, area.width - 48)), min(height, max(280, area.height - 64))
    dialog.set_default_size(width, height)
    dialog.set_size_request(360, 280)
    dialog.set_default_response(Gtk.ResponseType.APPLY)
    dialog.set_response_sensitive(Gtk.ResponseType.OK, False)
    scroll = Gtk.ScrolledWindow()
    scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    dialog.get_content_area().pack_start(scroll, True, True, 0)
    form = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, margin=16)
    scroll.add(form)
    fields = {}

    def caption(text, widget):
        label = Gtk.Label.new_with_mnemonic(text)
        label.set_xalign(0)
        label.set_line_wrap(True)
        label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        label.set_max_width_chars(58)
        label.set_mnemonic_widget(widget)
        form.pack_start(label, False, False, 0)
        widget.get_accessible().set_name(text.replace('_', ''))

    def field(key, title, value='', maximum=200):
        entry = Gtk.Entry(text=value, hexpand=True)
        entry.set_max_length(maximum)
        caption(title, entry)
        form.pack_start(entry, False, False, 0)
        fields[key] = entry
        return entry

    sheet_choice = Gtk.ComboBoxText(hexpand=True)
    for renderer in sheet_choice.get_cells():
        renderer.set_property('ellipsize', Pango.EllipsizeMode.END)
        renderer.set_property('max-width-chars', 36)
    for sheet in sheets:
        sheet_choice.append(sheet['id'], 'TS - ' + sheet['name'] + (' · arquivada' if sheet['archived'] else ''))
    caption('_Timesheet', sheet_choice)
    form.add(sheet_choice)
    sheet_context = Gtk.Label(xalign=0, wrap=True, selectable=True)
    sheet_context.set_max_width_chars(58);sheet_context.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR);form.add(sheet_context)
    field('reference', '_Referência do documento', 'INV-' + date.today().strftime('%Y%m%d') + '-' + uuid4().hex[:8], 80)
    field('issued_on', '_Data de emissão · AAAA-MM-DD', date.today().isoformat(), 10)
    field('issuer_name', 'Nome do _emitente', initial.get('issuer', {}).get('name', ''))
    field('issuer_tax_id', 'CPF/CNPJ do emitente', initial.get('issuer', {}).get('tax_id', ''), 30)
    field('client_name', 'Nome do _cliente / destinatário fiscal')
    field('client_tax_id', 'CPF/CNPJ do cliente', maximum=30)
    address = Gtk.TextView(wrap_mode=Gtk.WrapMode.WORD_CHAR)
    address.set_accepts_tab(False)
    address_scroll = Gtk.ScrolledWindow()
    address_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    address_scroll.set_min_content_height(74)
    address_scroll.set_max_content_height(130)
    address_scroll.add(address)
    caption('Endereço _fiscal do cliente', address)
    form.pack_start(address_scroll, False, False, 0)
    field('rate', '_Valor por hora', maximum=24)
    field('currency', '_Moeda · código de 3 letras (ex.: BRL, USD)', 'BRL', 3)
    language = Gtk.ComboBoxText()
    language.append('pt', 'Português')
    language.append('en', 'English')
    language.set_active_id(initial.get('language', 'pt'))
    caption('_Idioma do PDF', language)
    form.add(language)
    notice = Gtk.Label(label='Fatura de serviços, sem emissão de nota fiscal eletrônica.\n'
        'O cronômetro em andamento não entra no PDF; somente registros concluídos.\n'
        'Os dados serão lembrados somente após salvar o PDF.\n'
        'Uma cópia privada do PDF será guardada no Histórico de invoices.\n'
        'Emitente e idioma são globais; cliente, taxa e moeda são lembrados por timesheet.', xalign=0, wrap=True)
    notice.set_max_width_chars(58)
    notice.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
    form.add(notice)
    preview = Gtk.Label(label='Preencha os dados e revise a prévia.', xalign=0, wrap=True, selectable=True)
    preview.set_max_width_chars(58)
    preview.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
    form.add(preview)
    error = Gtk.Label(xalign=0, wrap=True, selectable=True)
    error.set_max_width_chars(58)
    error.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
    dialog.get_content_area().pack_end(error, False, False, 8)
    drafts = {}
    selected = [None]
    loading = [False]

    def invalidate(*_):
        if loading[0]:
            return
        session.invalidate()
        dialog.set_response_sensitive(Gtk.ResponseType.OK, False)
        preview.set_text('Dados alterados · revise novamente antes de salvar.')
        error.set_text('')
        dialog.set_response_sensitive(Gtk.ResponseType.APPLY, period.model.ready)

    def client_values():
        buffer = address.get_buffer()
        return {'name': fields['client_name'].get_text(), 'tax_id': fields['client_tax_id'].get_text(),
            'address': buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), True)}

    def change_sheet(*_):
        previous = selected[0]
        if previous:
            drafts[previous] = {'client': client_values(), 'rate': fields['rate'].get_text(),
                'currency': fields['currency'].get_text()}
        identity = sheet_choice.get_active_id()
        current = next((sheet for sheet in sheets if sheet['id'] == identity), None)
        sheet_choice.set_tooltip_text(current['name'] if current else '')
        sheet_context.set_text(context_text(current) if current else '')
        try:
            profile = drafts.get(identity) or invoice_profiles.load(identity, context=current.get('context', {}) if current else {})
        except Exception:
            error.set_text('Não foi possível carregar o perfil desta timesheet.')
            session.invalidate()
            dialog.set_response_sensitive(Gtk.ResponseType.OK, False)
            return
        loading[0] = True
        client = profile.get('client', {})
        fields['client_name'].set_text(client.get('name', ''))
        fields['client_tax_id'].set_text(client.get('tax_id', ''))
        address.get_buffer().set_text(client.get('address', ''))
        fields['rate'].set_text(profile.get('rate', ''))
        fields['currency'].set_text(profile.get('currency', 'BRL'))
        selected[0] = identity
        loading[0] = False
        invalidate()

    period = InvoicePeriodPicker(getattr(window, 'day', None), invalidate)
    form.pack_start(period.widget, False, False, 0)
    form.reorder_child(period.widget, form.get_children().index(notice))

    def values():
        start, end = period.model.bounds()
        return {'issuer': {'name': fields['issuer_name'].get_text(), 'tax_id': fields['issuer_tax_id'].get_text()},
            'client': client_values(), 'rate': fields['rate'].get_text(), 'currency': fields['currency'].get_text(),
            'language': language.get_active_id(), 'reference': fields['reference'].get_text(),
            'issued_on': fields['issued_on'].get_text(),
            'start': start, 'end': end}

    for entry in fields.values():
        entry.connect('changed', invalidate)
    address.get_buffer().connect('changed', invalidate)
    language.connect('changed', invalidate)
    sheet_choice.connect('changed', change_sheet)
    sheet_choice.set_active_id(first)
    invalidate()
    dialog.show_all()
    fields['issuer_name'].grab_focus()
    try:
        while True:
            response = dialog.run()
            if response not in (Gtk.ResponseType.APPLY, Gtk.ResponseType.OK):
                break
            if response == Gtk.ResponseType.APPLY:
                dialog.set_response_sensitive(Gtk.ResponseType.OK, False)
                preview.set_text('Validando os dados da prévia…')
                try:
                    if selected[0] != sheet_choice.get_active_id():
                        raise ValueError('Selecione novamente a timesheet para carregar os dados.')
                    snapshot = session.prepare(sheet_choice.get_active_id(), values())
                    duplicate_result = session.duplicate_check()
                    preview.set_text(context_text({'name': snapshot['sheet_name'], 'context': snapshot.get('context', {})}) + '\n' + f"Período: {'Todo o histórico · ' if snapshot['period']['all_history'] else ''}{snapshot['period']['start']} a {snapshot['period']['end']}\n"
                        f"Horas: {snapshot['hours']} ({snapshot['minutes']} minutos)\n"
                        f"Taxa/hora: {snapshot['currency']} {invoice.format_money(snapshot['rate'], 'pt')}\n"
                        f"Total: {snapshot['currency']} {invoice.format_money(snapshot['total'], 'pt')}\n"
                        'Confira os dados antes de escolher onde salvar o PDF.' +
                        ('\n' + '\n'.join(snapshot['warnings']) if snapshot.get('warnings') else '') +
                        ('\nAtenção: possível reemissão ou conferência incompleta; será solicitada confirmação.'
                         if duplicate_result['matches'] or duplicate_result['warnings'] or duplicate_result['incomplete'] else ''))
                    dialog.set_response_sensitive(Gtk.ResponseType.OK, True)
                    error.set_text('')
                    preview.grab_focus()
                except Exception as failure:
                    session.invalidate()
                    dialog.set_response_sensitive(Gtk.ResponseType.OK, False)
                    preview.set_text('Prévia indisponível · corrija os dados e revise novamente.')
                    error.set_text(str(failure))
                    error.grab_focus()
                continue
            chooser = Gtk.FileChooserDialog(title='Salvar invoice em PDF', transient_for=dialog,
                modal=True, action=Gtk.FileChooserAction.SAVE)
            chooser.add_buttons('Cancelar', Gtk.ResponseType.CANCEL, 'Salvar PDF', Gtk.ResponseType.ACCEPT)
            chooser.set_do_overwrite_confirmation(True)
            overwrite_target = [None]
            def confirm_overwrite(file_chooser):
                overwrite_target[0] = file_chooser.get_filename()
                return Gtk.FileChooserConfirmation.CONFIRM
            chooser.connect('confirm-overwrite', confirm_overwrite)
            chooser.set_current_name('invoice-' + date.today().isoformat() + '.pdf')
            pdf_filter = Gtk.FileFilter()
            pdf_filter.set_name('Documento PDF')
            pdf_filter.add_pattern('*.pdf')
            chooser.add_filter(pdf_filter)
            try:
                if chooser.run() != Gtk.ResponseType.ACCEPT:
                    continue
                filename = chooser.get_filename()
                if not filename or not filename.lower().endswith('.pdf'):
                    raise ValueError('Escolha um arquivo local com nome terminado em .pdf.')
                try:
                    result, warning = session.export(filename, overwrite=overwrite_target[0] == filename)
                except ReissueConfirmation as duplicate:
                    confirm = Gtk.MessageDialog(transient_for=chooser, modal=True, message_type=Gtk.MessageType.WARNING,
                        buttons=Gtk.ButtonsType.YES_NO, text='Reemitir estas horas intencionalmente?')
                    confirm.set_default_response(Gtk.ResponseType.NO)
                    matches = duplicate.result['matches']
                    reasons={'entry_id_and_time':'mesmos registros e horários','time_overlap_legacy':'horários de invoice antiga','time_overlap':'horários sobrepostos'}
                    lines = [f"{item['reference']} · {item['minutes']} minutos · {reasons.get(item['basis'],'conferência de horas')}" for item in matches[:12]]
                    lines += duplicate.result['warnings']
                    confirm.format_secondary_text('\n'.join(lines) + '\nA nova invoice não substituirá as anteriores. Confirme somente se a reemissão ou correção for intencional.')
                    accepted = confirm.run() == Gtk.ResponseType.YES;confirm.destroy()
                    if not accepted:continue
                    result, warning = session.export(filename, overwrite=overwrite_target[0] == filename, confirmed_reissue=True)
                window.status.set_text(warning or 'Invoice em PDF salva e guardada no histórico.')
                if warning:
                    info = Gtk.MessageDialog(transient_for=dialog, modal=True,
                        message_type=Gtk.MessageType.WARNING, buttons=Gtk.ButtonsType.CLOSE,
                        text=warning)
                    info.run()
                    info.destroy()
                break
            except Exception as failure:
                error.set_text(str(failure))
            finally:
                chooser.destroy()
            error.grab_focus()
    finally:
        dialog.destroy()
