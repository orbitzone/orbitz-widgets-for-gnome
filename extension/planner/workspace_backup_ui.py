"""Explicit full Workspace backup and quiescent restore; no credential scope."""
from datetime import date
import importlib

SCOPE_TEXT = ('Inclui tarefas/notas legadas, timesheets, contextos, cópias anteriores da agenda, perfis de invoice, PDFs e versões, '
    'pagamentos manuais e estado de interface. Não inclui credenciais, calendários externos, Sticky Notes ou GSettings.')


def apply_restore(service, filename, preview, quiesce, confirmed=False):
    if not confirmed:
        return None
    if preview['current_active_timer']:
        raise ValueError('Encerre os cronômetros antes de restaurar o Workspace.')
    quiesce()
    return service.restore_backup(filename, confirmed=True, expected=preview['token'], quiescent=True)


def export_backup(window):
    from gi.repository import Gtk
    try:backend = importlib.import_module('workspace_backup')
    except ImportError:
        window.status.set_text('O serviço de backup completo não está disponível nesta instalação.');return
    confirm=Gtk.MessageDialog(transient_for=window,modal=True,message_type=Gtk.MessageType.INFO,
        buttons=Gtk.ButtonsType.OK_CANCEL,text='Exportar backup completo do Workspace?')
    confirm.set_default_response(Gtk.ResponseType.CANCEL)
    confirm.format_secondary_text(SCOPE_TEXT+'\nO arquivo contém dados privados. Encerre os cronômetros antes de exportar e guarde a cópia em local seguro.')
    accepted=confirm.run()==Gtk.ResponseType.OK;confirm.destroy()
    if not accepted:return
    if not window.flush_workspace_drafts():return
    chooser = Gtk.FileChooserDialog(title='Exportar backup completo do Workspace', transient_for=window,
        modal=True, action=Gtk.FileChooserAction.SAVE)
    chooser.add_buttons('Cancelar',Gtk.ResponseType.CANCEL,'Exportar backup',Gtk.ResponseType.ACCEPT)
    chooser.set_current_name('orbitz-workspace-'+date.today().isoformat()+'.zip')
    chooser.set_do_overwrite_confirmation(True)
    confirmed=[None]
    def overwrite(widget):
        confirmed[0]=widget.get_filename()
        return Gtk.FileChooserConfirmation.CONFIRM
    chooser.connect('confirm-overwrite',overwrite)
    try:
        if chooser.run()!=Gtk.ResponseType.ACCEPT:return
        filename=chooser.get_filename()
        if not filename or not filename.lower().endswith('.zip'):raise ValueError('Escolha um arquivo local .zip.')
        backend.export_backup(filename,overwrite=filename==confirmed[0])
        window.status.set_text('Backup completo do Workspace exportado. Guarde-o em local privado.')
    except Exception as failure:window.status.set_text(str(failure))
    finally:chooser.destroy()


def restore_backup(window):
    from gi.repository import Gtk
    try:backend = importlib.import_module('workspace_backup')
    except ImportError:
        window.status.set_text('O serviço de backup completo não está disponível nesta instalação.');return
    chooser = Gtk.FileChooserDialog(title='Escolher backup completo do Workspace', transient_for=window,
        modal=True, action=Gtk.FileChooserAction.OPEN)
    chooser.add_buttons('Cancelar',Gtk.ResponseType.CANCEL,'Revisar backup',Gtk.ResponseType.ACCEPT)
    try:
        if chooser.run()!=Gtk.ResponseType.ACCEPT:return
        filename=chooser.get_filename()
    finally:chooser.destroy()
    quiesced=False
    app=None
    try:
        if not filename:raise ValueError('Escolha um arquivo de backup local.')
        if not window.flush_workspace_drafts():return
        preview=backend.inspect_backup(filename)
        if preview['current_active_timer']:
            raise ValueError('Encerre os cronômetros antes de restaurar o Workspace.')
        confirm=Gtk.MessageDialog(transient_for=window,modal=True,message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.OK_CANCEL,text='Restaurar o backup completo e fechar o Workspace?')
        confirm.set_default_response(Gtk.ResponseType.CANCEL)
        confirm.format_secondary_text(SCOPE_TEXT + f"\n\n{preview['files']} arquivos · {preview['bytes']} bytes.\n" +
            'Os dados locais incluídos serão substituídos. Um backup privado do estado atual será criado antes da restauração, '
            'com recuperação em caso de falha. O Workspace será fechado; reabra-o depois para carregar o estado restaurado. '
            'Feche outros editores do Workspace antes de continuar. Alterações concorrentes ou cronômetros ativos impedem a operação.')
        accepted=confirm.run()==Gtk.ResponseType.OK;confirm.destroy()
        if not accepted:return
        app=window.get_application()
        quiesced=True
        message=''
        try:
            result=apply_restore(backend,filename,preview,window.quiesce_for_restore,confirmed=True)
            message='Workspace restaurado. Backup anterior privado: '+str(result['previous_backup'])+'\nReabra o Orbitz Workspace.'
        except Exception as failure:
            message='A restauração não foi concluída. '+str(failure)+'\nO Workspace será fechado; reabra para conferir o estado preservado.'
        info=Gtk.MessageDialog(transient_for=window,modal=True,message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.CLOSE,text=message)
        info.run();info.destroy()
    except Exception as failure:window.status.set_text(str(failure))
    finally:
        if quiesced:
            window.destroy()
            if app:app.quit()
