"""Read, download and explicitly delete private invoice history copies."""
from collections import OrderedDict
import importlib
import invoice_signatures_ui as signatures_ui


def group_records(records):
    """Group by stable identities, never by customer or company names alone."""
    companies = OrderedDict()
    for record in records:
        snapshot = record['snapshot']
        company = companies.setdefault(snapshot['sheet_id'], {
            'label': 'TS - ' + snapshot['sheet_name'], 'clients': OrderedDict()})
        client = company['clients'].setdefault(record['client_key'], {
            'label': snapshot['client']['name'] + ' · CPF/CNPJ ' + snapshot['client']['tax_id'],
            'months': OrderedDict()})
        period = (record['issued_year'], record['issued_month'])
        client['months'].setdefault(period, []).append(record)
    return companies


class HistorySession:
    def __init__(self, archive=None, payments=None):
        self.archive = archive or importlib.import_module('invoice_history')
        self.records = {}
        self.selected_id = None
        self.payments = payments

    def reload(self):
        self.records = {}
        self.selected_id = None
        result = self.archive.list_records()
        self.records = {record['id']: record for record in result['records']}
        return result

    def select(self, record_id):
        self.selected_id = record_id if record_id in self.records else None
        return self.records.get(self.selected_id)

    def _selected(self):
        if self.selected_id is None:
            raise ValueError('Selecione uma invoice, não um cabeçalho do histórico.')
        return self.selected_id

    def path(self):
        return self.archive.get_path(self._selected())

    def export(self, filename, overwrite=False):
        return self.archive.export_copy(self._selected(), filename, overwrite=overwrite)

    def payment(self):
        service = self.payments or importlib.import_module('invoice_payments')
        return service.get(self._selected())

    def report_paid(self, paid, confirmed=False):
        if not confirmed:
            return None
        service = self.payments or importlib.import_module('invoice_payments')
        return service.set_paid(self._selected(), paid)

    def delete(self, confirmed=False):
        if not confirmed:
            return False
        self.archive.delete(self._selected())
        self.selected_id = None
        return True


def describe(record):
    snapshot = record['snapshot']
    period = snapshot['period']
    interval = f"{period['start']} a {period['end']}"
    if period['all_history']:
        interval = 'Todo o histórico · ' + interval
    return (f"Referência: {snapshot['reference']}\n"
        f"Empresa / timesheet: {snapshot['sheet_name']}\n"
        f"Cliente: {snapshot['client']['name']} · CPF/CNPJ {snapshot['client']['tax_id']}\n"
        f"Emissão: {snapshot['issued_on']} · agrupamento por mês de emissão\n"
        f"Período dos serviços: {interval}\n"
        f"Horas: {snapshot['hours']} · Total: {snapshot['currency']} {snapshot['total']}\n"
        f"Idioma: {'Português' if snapshot['language'] == 'pt' else 'English'}\n"
        f"Guardada no histórico: {record['created_at']}")


def list_feedback(records, errors):
    if not records:
        if errors:
            return f'Nenhuma invoice pôde ser exibida. {len(errors)} item(ns) do histórico não puderam ser lidos; arquivos preservados.'
        return 'Nenhuma invoice guardada no histórico.'
    if errors:
        return f'{len(errors)} item(ns) do histórico não puderam ser lidos; arquivos preservados. As invoices válidas continuam disponíveis.'
    return f'{len(records)} invoice(s) disponíveis no histórico.'


def create_history_content(window, parent=None):
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, Gio, Pango

    session = HistorySession()
    dialog = parent or window
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, margin=16)
    note = Gtk.Label(label='Empresa → cliente → ano/mês de emissão → invoice.\n'
        'Somente PDFs gerados e guardados desde esta atualização aparecem aqui; arquivos antigos não são importados.',
        xalign=0, wrap=True)
    note.set_max_width_chars(68)
    box.pack_start(note, False, False, 0)
    tree_model = Gtk.TreeStore(str, str)
    tree = Gtk.TreeView(model=tree_model, headers_visible=True)
    tree.get_accessible().set_name('Invoices por empresa, cliente e mês de emissão')
    renderer = Gtk.CellRendererText(wrap_mode=Pango.WrapMode.WORD_CHAR, wrap_width=420)
    column = Gtk.TreeViewColumn('Empresa / cliente / emissão / invoice', renderer, text=0)
    column.set_expand(True)
    tree.append_column(column)
    scroll = Gtk.ScrolledWindow()
    scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    scroll.add(tree)
    box.pack_start(scroll, True, True, 0)
    details = Gtk.Label(label='Selecione uma invoice para consultar os detalhes e as ações.', xalign=0,
        wrap=True, selectable=True)
    details.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
    details.set_max_width_chars(68)
    detail_scroll = Gtk.ScrolledWindow()
    detail_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    detail_scroll.set_min_content_height(100)
    detail_scroll.set_max_content_height(190)
    detail_scroll.add(details)
    box.pack_start(detail_scroll, False, True, 0)
    actions = Gtk.FlowBox()
    actions.set_selection_mode(Gtk.SelectionMode.NONE)
    actions.set_min_children_per_line(1)
    actions.set_max_children_per_line(4)
    actions.set_row_spacing(6)
    actions.set_column_spacing(8)
    box.pack_start(actions, False, False, 0)
    buttons = {}
    for key, label in [('view', 'Consultar original'), ('copy', 'Salvar cópia do original…'),
            ('sign', 'Assinar com gov.br…'), ('import', 'Adicionar versão assinada…'),
            ('versions', 'Original e versões…'), ('payment', 'Informar pagamento…'), ('delete', 'Excluir do histórico…')]:
        button = Gtk.Button(label=label, sensitive=False)
        button.get_accessible().set_name(label.replace('…', ''))
        actions.add(button)
        buttons[key] = button
    refresh = Gtk.Button(label='Atualizar')
    actions.add(refresh)
    feedback = Gtk.Label(xalign=0, wrap=True, selectable=True)
    feedback.set_max_width_chars(68)
    box.pack_start(feedback, False, False, 0)

    def set_enabled(enabled):
        for button in buttons.values():
            button.set_sensitive(enabled)

    def selected(*_):
        model, row = tree.get_selection().get_selected()
        record = session.select(model[row][1] if row is not None else None)
        set_enabled(record is not None)
        text = describe(record) if record else 'Selecione uma invoice; cabeçalhos não possuem ações de arquivo.'
        if record:
            try:
                payment = session.payment()
                text += '\nPagamento (informação manual): ' + ('informado como pago' if payment['status'] == 'reported_paid' else 'não informado')
            except Exception:text += '\nInformação de pagamento indisponível.'
        details.set_text(text)

    def reload(*_):
        set_enabled(False)
        tree_model.clear()
        details.set_text('Selecione uma invoice para consultar os detalhes e as ações.')
        try:
            result = session.reload()
            for company in group_records(result['records']).values():
                company_row = tree_model.append(None, [company['label'], ''])
                for client in company['clients'].values():
                    client_row = tree_model.append(company_row, [client['label'], ''])
                    for (year, month), records in sorted(client['months'].items(), reverse=True):
                        month_row = tree_model.append(client_row, [f'Emissão: {year:04d}/{month:02d}', ''])
                        for record in records:
                            snapshot = record['snapshot']
                            label = f"Invoice · {snapshot['reference']} · {snapshot['currency']} {snapshot['total']} · registro {record['id'][:8]}"
                            tree_model.append(month_row, [label, record['id']])
            feedback.set_text(list_feedback(result['records'], result['errors']))
        except Exception:
            session.records = {}
            session.selected_id = None
            feedback.set_text('Não foi possível carregar o histórico. Os arquivos foram preservados.')

    def show_error(message):
        feedback.set_text(message)
        feedback.grab_focus()

    def view(*_):
        try:
            uri = Gio.File.new_for_path(str(session.path())).get_uri()
            Gio.AppInfo.launch_default_for_uri(uri, None)
        except Exception:
            show_error('Não foi possível abrir o PDF selecionado. O registro foi preservado.')

    def copy(*_):
        if session.selected_id is None:
            return
        try:
            if signatures_ui.save_copy(dialog, session.export) is None:
                buttons['copy'].grab_focus()
                return
            feedback.set_text('Cópia do PDF salva; o histórico permanece intacto.')
        except Exception:
            show_error('Não foi possível concluir a cópia. O histórico permanece disponível; confira o arquivo de destino.')
        feedback.grab_focus()

    def sign(*_):
        if session.selected_id is None:
            return
        try:
            saved, opened = signatures_ui.sign_invoice(dialog, session.export)
            if saved is None:
                feedback.set_text('Ação cancelada. Nenhum portal foi aberto.')
            elif opened:
                feedback.set_text('Cópia salva e portal gov.br aberto. Envie e assine manualmente; depois importe a versão baixada.')
            else:
                feedback.set_text('Cópia salva, mas não foi possível abrir o portal gov.br. Nenhum PDF foi enviado.')
        except Exception:
            show_error('Não foi possível salvar a cópia para assinatura. O portal não foi aberto.')
        feedback.grab_focus()

    def import_version(*_):
        record = session.records.get(session.selected_id)
        if record is None:
            return
        try:
            if signatures_ui.add_version(dialog, record) is not None:
                feedback.set_text('Versão importada — validação pendente. O original e as versões anteriores foram preservados.')
        except Exception:
            show_error('Não foi possível importar a versão. Atualize o histórico antes de tentar novamente.')
        feedback.grab_focus()

    def versions(*_):
        record = session.records.get(session.selected_id)
        if record is None:
            return
        try:
            signatures_ui.show_versions(dialog, record)
        except Exception:
            show_error('Não foi possível listar as versões desta invoice. Os arquivos foram preservados.')

    def payment(*_):
        record = session.records.get(session.selected_id)
        if not record:return
        snapshot = record['snapshot']
        confirm = Gtk.MessageDialog(transient_for=dialog, modal=True, message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.NONE, text='Informação manual de pagamento')
        confirm.add_buttons('Cancelar', Gtk.ResponseType.CANCEL, 'Informar como pago', 1, 'Remover informação', 2)
        confirm.set_default_response(Gtk.ResponseType.CANCEL)
        confirm.format_secondary_text(snapshot['reference'] + ' · registro ' + record['id'][:8] + ' · ' + snapshot['client']['name'] + '\n' +
            snapshot['issued_on'] + ' · ' + snapshot['currency'] + ' ' + snapshot['total'] + '\n' +
            'Esta informação não é conciliação bancária, não altera o PDF e não valida assinatura.')
        answer = confirm.run();confirm.destroy()
        if answer not in (1,2):return
        try:
            session.report_paid(answer == 1, confirmed=True)
            selected()
            feedback.set_text('Pagamento informado manualmente; PDF e estado de assinatura preservados.')
        except Exception:show_error('Não foi possível salvar a informação de pagamento.')

    def delete(*_):
        record = session.records.get(session.selected_id)
        if record is None:
            return
        snapshot = record['snapshot']
        confirm = Gtk.MessageDialog(transient_for=dialog, modal=True, message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.OK_CANCEL, text='Excluir esta invoice do histórico?')
        confirm.set_default_response(Gtk.ResponseType.CANCEL)
        confirm.format_secondary_text(f"{snapshot['reference']} · {snapshot['client']['name']} · emissão {snapshot['issued_on']}\n"
            f"Registro {record['id'][:8]} · guardado {record['created_at']}\n"
            'O original, todas as versões importadas e o registro desta invoice no histórico serão excluídos. O PDF salvo fora do histórico e os registros de horas não serão alterados.')
        answer = confirm.run()
        confirm.destroy()
        if answer != Gtk.ResponseType.OK:
            return
        try:
            session.delete(confirmed=True)
            reload()
            previous = feedback.get_text()
            feedback.set_text('Invoice excluída do histórico. PDF externo e registros de horas preservados.' +
                ('\n' + previous if previous else ''))
        except Exception as failure:
            reload()
            show_error('Não foi possível concluir a exclusão. ' + str(failure)[:300])

    def resized(_tree, allocation):
        width = max(180, allocation.width - 80)
        if renderer.get_property('wrap-width') != width:
            renderer.set_property('wrap-width', width)

    tree.connect('size-allocate', resized)
    def activated(_tree, path, _column):
        if tree_model[path][1]:
            tree.get_selection().select_path(path)
            view()

    tree.connect('row-activated', activated)
    tree.get_selection().connect('changed', selected)
    buttons['view'].connect('clicked', view)
    buttons['copy'].connect('clicked', copy)
    buttons['sign'].connect('clicked', sign)
    buttons['import'].connect('clicked', import_version)
    buttons['versions'].connect('clicked', versions)
    buttons['payment'].connect('clicked', payment)
    buttons['delete'].connect('clicked', delete)
    refresh.connect('clicked', reload)
    reload()
    return box, reload


def open_history(window):
    from gi.repository import Gtk
    dialog = Gtk.Dialog(title='Histórico de invoices', transient_for=window, modal=True)
    dialog.add_button('Fechar', Gtk.ResponseType.CLOSE)
    dialog.set_default_size(820, 620)
    dialog.set_size_request(420, 300)
    try:
        content, _refresh = create_history_content(window, dialog)
        dialog.get_content_area().pack_start(content, True, True, 0)
        dialog.show_all()
        dialog.run()
    except Exception:
        window.status.set_text('Não foi possível abrir o histórico de invoices. Os arquivos foram preservados.')
    finally:
        dialog.destroy()
