"""Manual gov.br signing assistance; never uploads files or verifies signatures."""
from datetime import date
import importlib

SIGN_URL = 'https://assinador.iti.br/'
VALIDATE_URL = 'https://validar.iti.gov.br/'
PENDING_LABEL = 'Importada — validação pendente'


def version_label(version):
    return f"{version['created_at']} · versão {version['id'][:8]} · {PENDING_LABEL}"


def assist_sign(save_copy, launch):
    """Open only the fixed portal, and only after a confirmed copy succeeded."""
    saved = save_copy()
    if saved is None:
        return None, False
    try:
        if launch(SIGN_URL) is False:
            return saved, False
    except Exception:
        return saved, False
    return saved, True


def open_validator(launch):
    if launch(VALIDATE_URL) is False:
        raise ValueError('Não foi possível abrir o portal VALIDAR.')


class SignatureSession:
    def __init__(self, invoice_id, archive=None, signatures=None):
        self.invoice_id = invoice_id
        self.archive = archive or importlib.import_module('invoice_history')
        self.signatures = signatures or importlib.import_module('invoice_signatures')
        self.versions = {}
        self.selected = None

    def reload(self):
        self.selected = None
        self.versions = {}
        result = self.signatures.list_versions(self.invoice_id)
        self.versions = {version['id']: version for version in result['versions']}
        return result

    def select(self, version_id):
        self.selected = version_id if version_id == 'original' or version_id in self.versions else None
        return self.selected is not None

    def path(self):
        if self.selected == 'original':
            return self.archive.get_path(self.invoice_id)
        if self.selected in self.versions:
            return self.signatures.resolve_pdf(self.invoice_id, self.selected)
        raise ValueError('Selecione uma versão do PDF.')

    def export(self, target, overwrite=False):
        if self.selected == 'original':
            return self.archive.export_copy(self.invoice_id, target, overwrite=overwrite)
        if self.selected in self.versions:
            return self.signatures.export_copy(self.invoice_id, self.selected, target, overwrite=overwrite)
        raise ValueError('Selecione uma versão do PDF.')

    def import_pdf(self, path, confirmed=False):
        if not confirmed:
            return None
        return self.signatures.import_version(self.invoice_id, path)


def save_copy(parent, exporter, title='Salvar cópia do PDF'):
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk
    chooser = Gtk.FileChooserDialog(title=title, transient_for=parent, modal=True,
        action=Gtk.FileChooserAction.SAVE)
    chooser.add_buttons('Cancelar', Gtk.ResponseType.CANCEL, 'Salvar cópia', Gtk.ResponseType.ACCEPT)
    chooser.set_current_name('invoice-' + date.today().isoformat() + '.pdf')
    chooser.set_do_overwrite_confirmation(True)
    allowed = [None]
    def confirm(file_chooser):
        allowed[0] = file_chooser.get_filename()
        return Gtk.FileChooserConfirmation.CONFIRM
    chooser.connect('confirm-overwrite', confirm)
    pdf_filter = Gtk.FileFilter()
    pdf_filter.set_name('Documento PDF')
    pdf_filter.add_pattern('*.pdf')
    chooser.add_filter(pdf_filter)
    try:
        if chooser.run() != Gtk.ResponseType.ACCEPT:
            return None
        filename = chooser.get_filename()
        if not filename or not filename.lower().endswith('.pdf'):
            raise ValueError('Escolha um arquivo local terminado em .pdf.')
        return exporter(filename, overwrite=allowed[0] == filename)
    finally:
        chooser.destroy()


def add_version(parent, record):
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk
    chooser = Gtk.FileChooserDialog(title='Adicionar versão assinada — importação manual',
        transient_for=parent, modal=True, action=Gtk.FileChooserAction.OPEN)
    chooser.add_buttons('Cancelar', Gtk.ResponseType.CANCEL, 'Escolher PDF', Gtk.ResponseType.ACCEPT)
    pdf_filter = Gtk.FileFilter()
    pdf_filter.set_name('Documento PDF')
    pdf_filter.add_pattern('*.pdf')
    chooser.add_filter(pdf_filter)
    try:
        if chooser.run() != Gtk.ResponseType.ACCEPT:
            return None
        filename = chooser.get_filename()
    finally:
        chooser.destroy()
    if not filename or not filename.lower().endswith('.pdf'):
        raise ValueError('Escolha um arquivo PDF local.')
    snapshot = record['snapshot']
    period = snapshot['period']
    confirm = Gtk.MessageDialog(transient_for=parent, modal=True, message_type=Gtk.MessageType.QUESTION,
        buttons=Gtk.ButtonsType.OK_CANCEL, text='Vincular este PDF à invoice selecionada?')
    confirm.set_default_response(Gtk.ResponseType.CANCEL)
    confirm.format_secondary_text(f"{snapshot['reference']} · registro {record['id'][:8]}\n"
        f"Cliente: {snapshot['client']['name']} · serviços: {period['start']} a {period['end']}\n\n"
        'Não há verificação criptográfica nem correspondência automática com esta invoice. '
        'O arquivo pode não estar assinado. Ele será guardado como “Importada — validação pendente”. '
        'O original e as versões anteriores serão preservados.')
    try:
        accepted = confirm.run() == Gtk.ResponseType.OK
    finally:
        confirm.destroy()
    return SignatureSession(record['id']).import_pdf(filename, confirmed=accepted) if accepted else None


def show_versions(parent, record):
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, Gio, Pango
    session = SignatureSession(record['id'])
    dialog = Gtk.Dialog(title='Versões da invoice · ' + record['snapshot']['reference'],
        transient_for=parent, modal=True)
    dialog.add_button('Fechar', Gtk.ResponseType.CLOSE)
    width, height = 680, 480
    if parent.get_window():
        monitor = parent.get_display().get_monitor_at_window(parent.get_window())
        if monitor:
            area = monitor.get_workarea()
            width, height = min(width, max(400, area.width - 48)), min(height, max(280, area.height - 64))
    dialog.set_default_size(width, height)
    dialog.set_size_request(400, 280)
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, margin=16)
    dialog.get_content_area().pack_start(box, True, True, 0)
    note = Gtk.Label(label='Importação não comprova assinatura nem correspondência com o original. '
        'Use o VALIDAR e envie o arquivo manualmente; abrir o portal não altera o status local.', xalign=0, wrap=True)
    note.set_max_width_chars(60)
    box.add(note)
    model = Gtk.ListStore(str, str)
    tree = Gtk.TreeView(model=model)
    tree.get_accessible().set_name('Original e versões importadas da invoice')
    renderer = Gtk.CellRendererText(wrap_mode=Pango.WrapMode.WORD_CHAR, wrap_width=500)
    tree.append_column(Gtk.TreeViewColumn('Versão / estado', renderer, text=0))
    scroll = Gtk.ScrolledWindow()
    scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    scroll.add(tree)
    box.pack_start(scroll, True, True, 0)
    actions = Gtk.FlowBox()
    actions.set_selection_mode(Gtk.SelectionMode.NONE)
    actions.set_min_children_per_line(1)
    actions.set_max_children_per_line(3)
    box.add(actions)
    view = Gtk.Button(label='Consultar PDF', sensitive=False)
    copy = Gtk.Button(label='Salvar cópia…', sensitive=False)
    validate = Gtk.Button(label='Verificar no VALIDAR', sensitive=False)
    for button in (view, copy, validate):
        actions.add(button)
    feedback = Gtk.Label(xalign=0, wrap=True, selectable=True)
    feedback.set_max_width_chars(60)
    box.add(feedback)
    def selected(*_):
        current, row = tree.get_selection().get_selected()
        enabled = session.select(current[row][1] if row is not None else None)
        for button in (view, copy, validate):
            button.set_sensitive(enabled)
    def consult(*_):
        try:
            uri = Gio.File.new_for_path(str(session.path())).get_uri()
            Gio.AppInfo.launch_default_for_uri(uri, None)
        except Exception:
            feedback.set_text('Não foi possível abrir esta versão. Os arquivos foram preservados.')
            feedback.grab_focus()
    def download(*_):
        try:
            if save_copy(dialog, session.export) is None:
                copy.grab_focus()
                return
            feedback.set_text('Cópia salva sem alterar os bytes da versão guardada.')
        except Exception:
            feedback.set_text('Não foi possível concluir a cópia; confira o destino. A versão guardada foi preservada.')
        feedback.grab_focus()
    def validator(*_):
        try:
            open_validator(lambda url: Gio.AppInfo.launch_default_for_uri(url, None))
            feedback.set_text('Envie o PDF manualmente no VALIDAR. O status local permanece sem validação.')
        except Exception:
            feedback.set_text('Não foi possível abrir o VALIDAR. Nenhum arquivo foi enviado.')
        feedback.grab_focus()
    def resized(_tree, allocation):
        width = max(180, allocation.width - 24)
        if renderer.get_property('wrap-width') != width:
            renderer.set_property('wrap-width', width)

    tree.connect('size-allocate', resized)
    tree.get_selection().connect('changed', selected)
    view.connect('clicked', consult)
    copy.connect('clicked', download)
    validate.connect('clicked', validator)
    try:
        result = session.reload()
        model.append(['Original · PDF gerado da invoice', 'original'])
        for version in result['versions']:
            model.append([version_label(version), version['id']])
        if result['errors']:
            feedback.set_text(f"{len(result['errors'])} versão(ões) não puderam ser lidas; arquivos preservados.")
        dialog.show_all()
        dialog.run()
    finally:
        dialog.destroy()


def sign_invoice(parent, exporter):
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, Gio
    instructions = Gtk.MessageDialog(transient_for=parent, modal=True,
        message_type=Gtk.MessageType.INFO, buttons=Gtk.ButtonsType.OK_CANCEL,
        text='Salvar uma cópia e continuar no assinador gov.br?')
    instructions.set_default_response(Gtk.ResponseType.CANCEL)
    instructions.format_secondary_text('1. Salve uma cópia do PDF.\n'
        '2. No portal oficial, entre com sua conta gov.br prata ou ouro.\n'
        '3. Envie o PDF manualmente, assine e baixe o resultado.\n'
        '4. Volte ao Orbitz e escolha “Adicionar versão assinada…”.\n\n'
        'O Orbitz não envia arquivos, não acessa sua conta e não guarda credenciais. '
        'O login é feito somente no portal externo.')
    try:
        accepted = instructions.run() == Gtk.ResponseType.OK
    finally:
        instructions.destroy()
    if not accepted:
        return None, False
    return assist_sign(lambda: save_copy(parent, exporter, 'Salvar cópia para assinar no gov.br'),
        lambda url: Gio.AppInfo.launch_default_for_uri(url, None))
