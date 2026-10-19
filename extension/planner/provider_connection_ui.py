"""Private provider connection dialogs; cancellation owns post-connect rollback."""
import threading
import time
from urllib.parse import urlsplit


def launch_google_auth(url, launch):
    parsed = urlsplit(url)
    if parsed.scheme != 'https' or parsed.hostname != 'accounts.google.com' or parsed.port not in (None,443) or parsed.username or parsed.password:
        raise ValueError('O endereço de autorização Google foi recusado.')
    if launch(url) is False:
        raise ValueError('Não foi possível abrir o navegador para autorizar o Google.')
    return True


class ConnectionAttempt:
    def __init__(self, service, provider, cancel_event=None):
        self.service, self.provider = service, provider
        self.cancelled = cancel_event or threading.Event()
        self.accepted = threading.Event()
        self.lock = threading.Lock()
        self.finished = False

    def accept(self):
        with self.lock:
            if not self.cancelled.is_set() and not self.finished:
                self.accepted.set();return True
            return False

    def connect(self, label, secret_or_path, deliver, open_browser=None, acknowledge_timeout=10):
        if self.cancelled.is_set():return None
        if self.provider == 'google':
            account = self.service.connect_google(secret_or_path,label,cancel_event=self.cancelled,open_browser=open_browser)
        elif self.provider == 'calendly':
            account = self.service.connect_calendly(secret_or_path,label,cancel_event=self.cancelled)
        else:raise ValueError('Provedor de calendário inválido.')
        if account is None:return None
        committed = False
        try:
            if not self.cancelled.is_set():
                deliver(account)
                deadline = time.monotonic() + acknowledge_timeout
                while not self.accepted.wait(.05):
                    if self.cancelled.is_set() or time.monotonic() >= deadline:break
                with self.lock:
                    committed = self.accepted.is_set()
                    self.finished = True
                    if not committed:self.cancelled.set()
            return account if committed else None
        finally:
            if not committed:
                with self.lock:self.finished = True;self.cancelled.set()
                self.service.disconnect(account)


def connect_provider(controller, provider):
    import calendar_accounts
    from gi.repository import Gtk, Gio, GLib, Pango
    google = provider == 'google'
    dialog = Gtk.Dialog(title='Conectar Google Calendar' if google else 'Conectar Calendly',
        transient_for=controller.window,modal=True)
    dialog.add_buttons('Cancelar',Gtk.ResponseType.CANCEL,'Conectar',Gtk.ResponseType.OK)
    dialog.set_default_size(560,360)
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=10,margin=18)
    dialog.get_content_area().add(box)
    info = Gtk.Label(label=('Leitura apenas. Escolha seu arquivo OAuth de cliente para aplicativo de computador. '
        'A autorização e o login ocorrem no navegador Google, com retorno local temporário. Não informe senhas aqui.'
        if google else 'Leitura apenas. Cole um Personal Access Token do Calendly com users:read e scheduled_events:read. '
        'O token fica no cofre local; não é salvo no JSON de calendários.'),xalign=0,wrap=True)
    info.set_max_width_chars(58);info.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR);box.add(info)
    box.add(Gtk.Label(label='Nome da conexão',xalign=0))
    name = Gtk.Entry();name.set_max_length(100);name.get_accessible().set_name('Nome da conexão');box.add(name)
    if google:
        credential = Gtk.FileChooserButton(title='Escolher cliente OAuth desktop',action=Gtk.FileChooserAction.OPEN)
        file_filter=Gtk.FileFilter();file_filter.set_name('Configuração JSON');file_filter.add_pattern('*.json');credential.add_filter(file_filter)
        credential.get_accessible().set_name('Arquivo JSON de cliente OAuth desktop');box.add(credential)
    else:
        credential = Gtk.Entry(visibility=False)
        credential.set_input_purpose(Gtk.InputPurpose.PASSWORD)
        credential.set_max_length(8192);credential.get_accessible().set_name('Personal Access Token do Calendly');box.add(credential)
    status=Gtk.Label(xalign=0,wrap=True);status.set_max_width_chars(58);status.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR);box.add(status)
    pending=[None];result=[None]

    def alive():return controller.alive and dialog.get_visible()
    def complete(attempt, account):
        if alive() and attempt.accept():
            result[0]=account;dialog.response(Gtk.ResponseType.ACCEPT)
        else:attempt.cancelled.set()
        return False
    def failed(attempt, error):
        if alive() and pending[0] is attempt:
            pending[0]=None
            status.set_text(str(error) if isinstance(error,ValueError) else 'Não foi possível conectar. Verifique a configuração, a rede e o cofre local.')
            dialog.set_response_sensitive(Gtk.ResponseType.OK,True);name.set_sensitive(True);credential.set_sensitive(True)
        return False
    def start(label,value):
        attempt=ConnectionAttempt(calendar_accounts,provider)
        pending[0]=attempt;controller.cancel_events.append(attempt.cancelled)
        def worker():
            try:
                connected=attempt.connect(label,value,lambda account:GLib.idle_add(complete,attempt,account),
                    open_browser=lambda url:launch_google_auth(url,lambda target:Gio.AppInfo.launch_default_for_uri(target,None)))
                if connected is None:GLib.idle_add(failed,attempt,ValueError('A conexão não foi concluída. Tente novamente ou cancele.'))
            except Exception as error:GLib.idle_add(failed,attempt,error)
        try:controller.executor.submit(worker)
        except RuntimeError:
            attempt.cancelled.set()
            GLib.idle_add(failed,attempt,ValueError('O serviço de conexão foi encerrado. Reabra o Workspace para tentar novamente.'))

    dialog.show_all();name.grab_focus()
    try:
        while True:
            response=dialog.run()
            if response==Gtk.ResponseType.ACCEPT:break
            if response!=Gtk.ResponseType.OK:break
            if pending[0] is not None:continue
            label=name.get_text().strip()
            value=credential.get_filename() if google else credential.get_text().strip()
            if not google:credential.set_text('')
            if not label or not value:
                status.set_text('Informe o nome e escolha o arquivo OAuth.' if google else 'Informe o nome e o token privado.');continue
            name.set_sensitive(False);credential.set_sensitive(False);dialog.set_response_sensitive(Gtk.ResponseType.OK,False)
            status.set_text('Autorize no navegador. Cancelar encerra o retorno local e desfaz a conexão.' if google else 'Conectando ao Calendly…')
            start(label,value)
    finally:
        if pending[0] is not None and not pending[0].accepted.is_set():pending[0].cancelled.set()
        if not google:credential.set_text('')
        dialog.destroy()
    if result[0]:
        account=result[0]
        if account.get('calendars'):
            controller.populate(account['id']+'|'+account['calendars'][0]['id'])
        else:controller.populate()
        controller.selection_changed();controller.window.show_area('events')
