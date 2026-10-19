"""Bounded private backups of an explicit app-data whitelist; no credentials."""
from contextlib import contextmanager
from datetime import datetime,timezone
import fcntl
import hashlib
import io
import json
import os
from pathlib import Path,PurePosixPath
import re
import stat
import struct
import tempfile
import zipfile
import invoice_history as history

DATA = Path(os.environ.get('XDG_DATA_HOME') or Path.home()/'.local/share')/'orbitz-widgets'
MAX_TOTAL=512*1024*1024
MAX_ARCHIVE=MAX_TOTAL+16*1024*1024
MAX_FILES=10000
FLAT={'notes.json':64*1024*1024,'invoice-profiles.json':2*1024*1024,'planner-ui.json':8*1024*1024}
SCOPE=['notes.json','invoice-profiles.json','planner-ui.json','planner-backups/*.json','invoices (originais, versões e pagamento manual)']


def _directory(value):
    value=Path(value) if value is not None else DATA
    value=value.absolute()
    if value.resolve()!=value:raise ValueError('Diretório de dados vinculado recusado.')
    return value


def _limit(name):
    path=PurePosixPath(name)
    if path.is_absolute() or '\\' in name or '..' in path.parts or path.as_posix()!=name:
        raise ValueError('Caminho de backup inválido.')
    if name in FLAT:return FLAT[name]
    parts=path.parts
    if len(parts)==2 and parts[0]=='planner-backups' and re.fullmatch(r'[A-Za-z0-9_.-]{1,160}\.json',parts[1]) and not parts[1].startswith('.'):
        return FLAT['notes.json']
    if len(parts) in (3,5) and parts[0]=='invoices' and re.fullmatch('[0-9a-f]{32}',parts[1]):
        if len(parts)==5 and (parts[2]!='versions' or not re.fullmatch('[0-9a-f]{32}',parts[3])):raise ValueError('Versão de backup inválida.')
        if parts[-1]=='invoice.pdf':return history.MAX_PDF
        if parts[-1]=='metadata.json':return history.MAX_METADATA
        if len(parts)==3 and parts[-1]=='payment.json':return 32768
    raise ValueError('Arquivo fora do escopo do backup.')


@contextmanager
def _locks(directory):
    directory.mkdir(parents=True,exist_ok=True,mode=0o700)
    invoices=directory/'invoices'
    if invoices.is_symlink():raise ValueError('Acervo vinculado recusado.')
    invoices.mkdir(exist_ok=True,mode=0o700)
    paths=[directory/'.workspace-backup.lock',directory/'notes.json.lock',directory/'invoice-profiles.json.lock',directory/'planner-ui.json.lock',invoices/'.lock']
    descriptors=[]
    try:
        for path in paths:
            fd=os.open(path,os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW|os.O_NONBLOCK,0o600)
            descriptors.append(fd)
            if not stat.S_ISREG(os.fstat(fd).st_mode):raise ValueError('Lock de dados inválido.')
            os.fchmod(fd,0o600)
            try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:raise ValueError('Há outra operação de dados em andamento; tente com o aplicativo fechado.') from None
        yield
    finally:
        for fd in reversed(descriptors):os.close(fd)


def _collect(directory):
    names=set()
    for name in FLAT:
        if os.path.lexists(directory/name):names.add(name)
    for folder_name in ('invoices','planner-backups'):
        folder=directory/folder_name
        if folder.is_symlink():raise ValueError('Diretório do backup vinculado recusado.')
        if not folder.exists():continue
        if not folder.is_dir():raise ValueError('Diretório do backup inválido.')
        for current,dirs,files in os.walk(folder,followlinks=False):
            for name in dirs+files:
                path=Path(current)/name
                if path.is_symlink():raise ValueError('Link simbólico no escopo do backup; arquivos preservados.')
                if name.startswith(('.record-','.version-','.deleted-','.payment-')):
                    raise ValueError('Operação de fatura pendente; resolva antes do backup/restauração.')
            for name in files:
                relative=(Path(current)/name).relative_to(directory).as_posix()
                try:_limit(relative)
                except ValueError:continue  # Unknown files are never read/replaced/removed.
                names.add(relative)
    if len(names)>MAX_FILES:raise ValueError('Quantidade de arquivos excede o limite do backup.')
    result={};total=0
    for name in sorted(names):
        value=history._read(directory/name,_limit(name))
        total+=len(value)
        if total>MAX_TOTAL:raise ValueError('Dados excedem o limite total do backup.')
        result[name]=value
    return result


def _fingerprint(files):
    return hashlib.sha256(json.dumps({name:hashlib.sha256(value).hexdigest() for name,value in sorted(files.items())},sort_keys=True).encode()).hexdigest()


def _token(archive_hash,current):
    return hashlib.sha256((archive_hash+'|'+_fingerprint(current)).encode()).hexdigest()


def _timer(files):
    if 'notes.json' not in files:return False
    import timesheet
    data=json.loads(files['notes.json'])
    if not isinstance(data,dict):raise ValueError('Dados locais de tarefas/horas inválidos.')
    timesheet.migrate(data)
    return any(sheet.get('timesheet_active') for sheet in data['timesheets'])


def _put(path,value):
    if path.resolve()!=path.absolute():raise ValueError('Destino vinculado recusado.')
    missing=[];parent=path.parent
    while not parent.exists():missing.append(parent);parent=parent.parent
    path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    for parent in missing:parent.chmod(0o700)
    fd,name=tempfile.mkstemp(prefix='.workspace-',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as stream:
            os.fchmod(stream.fileno(),0o600);stream.write(value);stream.flush();os.fsync(stream.fileno())
        os.replace(name,path)
        history._sync(path.parent)
    finally:Path(name).unlink(missing_ok=True)


def _validate(files):
    if _timer(files):raise ValueError('Encerre os cronômetros antes de criar ou restaurar este backup.')
    import store,invoice_profiles,invoice_signatures,invoice_payments
    with tempfile.TemporaryDirectory(prefix='orbitz-backup-check-') as temporary:
        stage=Path(temporary)
        for name,value in files.items():_put(stage/name,value)
        if 'notes.json' in files:store.read(stage/'notes.json')
        if 'invoice-profiles.json' in files:invoice_profiles.read(stage/'invoice-profiles.json')
        if 'planner-ui.json' in files and not isinstance(json.loads(files['planner-ui.json']),dict):raise ValueError('Estado de interface inválido.')
        invoices=stage/'invoices'
        if invoices.exists():
            for child in invoices.iterdir():
                original,_=history._get(invoices,child.name)
                if (child/'payment.json').exists():invoice_payments._read(invoices,child.name)
                versions=child/'versions'
                if versions.exists():
                    for version in versions.iterdir():invoice_signatures._get(versions,child.name,version.name,original['pdf_sha256'])


def _archive(files):
    manifest=dict(version=1,app='orbitz-workspace',created_at=datetime.now(timezone.utc).isoformat(),files={name:dict(size=len(value),sha256=hashlib.sha256(value).hexdigest()) for name,value in files.items()})
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w',compression=zipfile.ZIP_STORED) as archive:
        archive.writestr('manifest.json',json.dumps(manifest,ensure_ascii=False).encode('utf-8'))
        for name,value in files.items():
            info=zipfile.ZipInfo(name);info.external_attr=(stat.S_IFREG|0o600)<<16
            archive.writestr(info,value)
    return stream.getvalue()


def _read_archive(path):
    raw=history._read(Path(path),MAX_ARCHIVE)
    files={}
    end=raw.rfind(b'PK\x05\x06',max(0,len(raw)-65557))
    if end<0 or end+22>len(raw):raise ValueError('Arquivo de backup ZIP inválido.')
    entries=struct.unpack_from('<H',raw,end+10)[0]
    central_size=struct.unpack_from('<I',raw,end+12)[0]
    if entries>MAX_FILES+1 or central_size>(MAX_FILES+1)*1024:raise ValueError('Diretório ZIP excede os limites do backup.')
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        infos=archive.infolist()
        if len(infos)>MAX_FILES+1 or len({item.filename for item in infos})!=len(infos):raise ValueError('Quantidade ou nomes duplicados inválidos no backup.')
        if 'manifest.json' not in archive.namelist():raise ValueError('Manifesto de backup ausente.')
        total=0
        for item in infos:
            limit=history.MAX_METADATA if item.filename=='manifest.json' else _limit(item.filename)
            mode=item.external_attr>>16
            if item.is_dir() or item.flag_bits&1 or stat.S_ISLNK(mode) or (stat.S_IFMT(mode) not in (0,stat.S_IFREG)) or item.file_size>limit:
                raise ValueError('Entrada inválida no backup.')
            total+=item.file_size
            if total>MAX_TOTAL+history.MAX_METADATA or (item.file_size>1048576 and item.file_size>max(1,item.compress_size)*200):raise ValueError('Backup comprimido excede limites de segurança.')
            with archive.open(item) as source:value=source.read(limit+1)
            if len(value)!=item.file_size or len(value)>limit:raise ValueError('Tamanho de backup inválido.')
            if item.filename=='manifest.json':manifest=json.loads(value)
            else:files[item.filename]=value
    if not isinstance(manifest,dict) or manifest.get('app')!='orbitz-workspace' or type(manifest.get('version')) is not int or manifest['version']!=1 or not isinstance(manifest.get('files'),dict) or set(manifest['files'])!=set(files):raise ValueError('Manifesto de backup inválido.')
    for name,value in files.items():
        if manifest['files'][name]!=dict(size=len(value),sha256=hashlib.sha256(value).hexdigest()):raise ValueError('Hash/tamanho do backup não confere.')
    _validate(files)
    return files,hashlib.sha256(raw).hexdigest()


def _publish(value,target,overwrite=False):
    target=Path(target).expanduser().absolute()
    if target.suffix.lower()!='.zip' or type(overwrite) is not bool:raise ValueError('Escolha um arquivo .zip e confirmação válida.')
    before=None
    if os.path.lexists(target):
        if not overwrite:raise FileExistsError('Backup já existe; confirme a substituição.')
        before=history._stamp(target)
    fd,name=tempfile.mkstemp(prefix='.workspace-backup-',dir=target.parent)
    try:
        with os.fdopen(fd,'wb') as stream:
            os.fchmod(stream.fileno(),0o600);stream.write(value);stream.flush();os.fsync(stream.fileno())
        if before is None:os.link(name,target)
        else:
            if history._stamp(target)!=before:raise FileExistsError('Destino mudou; arquivo preservado.')
            os.replace(name,target)
        history._sync(target.parent)
    finally:Path(name).unlink(missing_ok=True)
    return target


def export_backup(path,*,overwrite=False,data_dir=None):
    directory=_directory(data_dir)
    if Path(path).expanduser().resolve().is_relative_to(directory):raise ValueError('Exporte o backup fora da pasta de dados do aplicativo.')
    with _locks(directory):
        files=_collect(directory);_validate(files)
        raw=_archive(files)
        if _collect(directory)!=files:raise ValueError('Dados mudaram durante o backup; exportação cancelada.')
        return _publish(raw,path,overwrite)


def inspect_backup(path,*,data_dir=None):
    files,digest=_read_archive(path)
    directory=_directory(data_dir)
    with _locks(directory):current=_collect(directory)
    return dict(token=_token(digest,current),sha256=digest,files=len(files),bytes=sum(map(len,files.values())),scope=list(SCOPE),current_active_timer=bool(_timer(current)))


def _apply(directory,before,after):
    for name in sorted(set(before)|set(after)):
        path=directory/name
        current=history._read(path,_limit(name)) if os.path.lexists(path) else None
        if current!=before.get(name):raise ValueError('Arquivo mudou durante restauração; edição posterior preservada.')
        if name in after:_put(path,after[name])
        elif path.exists():path.unlink();history._sync(path.parent)


def _recover(directory,before,after):
    pending=[]
    for name in sorted(set(before)|set(after)):
        try:
            path=directory/name
            current=history._read(path,_limit(name)) if os.path.lexists(path) else None
            if current not in (before.get(name),after.get(name)):raise ValueError('Edição posterior preservada.')
            if name in before:
                if current!=before[name]:_put(path,before[name])
            elif path.exists():path.unlink();history._sync(path.parent)
        except Exception:pending.append(name)
    return pending


def _clean_empty(directory,names):
    parents={parent for name in names for parent in (directory/name).parents if parent!=directory and directory in parent.parents and parent!=directory/'invoices'}
    for parent in sorted(parents,key=lambda path:len(path.parts),reverse=True):
        try:parent.rmdir()
        except OSError:pass


def restore_backup(path,*,confirmed=False,expected=None,quiescent=False,data_dir=None):
    if confirmed is not True or quiescent is not True:raise ValueError('Confirme a restauração com a interface encerrada e operações paradas.')
    after,digest=_read_archive(path)
    directory=_directory(data_dir)
    with _locks(directory):
        before=_collect(directory)
        if expected!=_token(digest,before):raise ValueError('Backup ou dados mudaram desde a prévia; revise novamente.')
        if _timer(before):raise ValueError('Encerre os cronômetros antes de restaurar.')
        _validate(before)
        recovery=directory/'workspace-backups'
        if recovery.is_symlink():raise ValueError('Diretório de recuperação vinculado recusado.')
        recovery.mkdir(mode=0o700,exist_ok=True);recovery.chmod(0o700)
        folder=Path(tempfile.mkdtemp(prefix=datetime.now().strftime('%Y%m%d-%H%M%S-'),dir=recovery))
        previous=_publish(_archive(before),folder/'before.zip')
        journal=dict(version=1,state='prepared',before={name:hashlib.sha256(value).hexdigest() for name,value in before.items()},after={name:hashlib.sha256(value).hexdigest() for name,value in after.items()})
        _put(folder/'recovery.json',json.dumps(journal).encode())
        try:
            if _collect(directory)!=before:raise ValueError('Dados mudaram durante preparação; restauração cancelada.')
            _apply(directory,before,after)
            if _collect(directory)!=after:raise ValueError('Verificação da restauração falhou.')
            _validate(after)
            _clean_empty(directory,set(before)-set(after))
            journal['state']='restored'
            _put(folder/'recovery.json',json.dumps(journal).encode())
        except Exception as error:
            pending=_recover(directory,before,after)
            try:
                recovered=_collect(directory)
                pending.extend(name for name in set(recovered)|set(before) if recovered.get(name)!=before.get(name) and name not in pending)
            except Exception:pending.append('verification')
            _clean_empty(directory,set(after)-set(before))
            journal.update(state='recovery-pending' if pending else 'rolled-back',pending=pending)
            _put(folder/'recovery.json',json.dumps(journal).encode())
            raise RuntimeError('Restauração não confirmada; rollback '+('com pendências' if pending else 'verificado')+'. Backup prévio: '+str(previous)) from error
        return dict(restored=True,previous_backup=str(previous))


def rollback_restore(recovery_folder,*,confirmed=False,quiescent=False,data_dir=None):
    """Resume recovery after an interrupted restore, without trusting partial pairs."""
    if confirmed is not True or quiescent is not True:raise ValueError('Confirme o rollback com a interface encerrada.')
    directory=_directory(data_dir)
    folder=Path(recovery_folder).absolute()
    if folder.resolve()!=folder or folder.parent!=directory/'workspace-backups':raise ValueError('Pasta de recuperação inválida.')
    before,_=_read_archive(folder/'before.zip')
    journal=json.loads(history._read(folder/'recovery.json',history.MAX_METADATA))
    before_hash={name:hashlib.sha256(value).hexdigest() for name,value in before.items()}
    if not isinstance(journal,dict) or type(journal.get('version')) is not int or journal['version']!=1 or journal.get('state') not in ('prepared','restored','rolled-back','recovery-pending') or journal.get('before')!=before_hash or not isinstance(journal.get('after'),dict):raise ValueError('Registro de recuperação inválido.')
    for name,value in journal['after'].items():
        _limit(name)
        if not isinstance(value,str) or not re.fullmatch('[0-9a-f]{64}',value):raise ValueError('Hash de recuperação inválido.')
    with _locks(directory):
        current=_collect(directory)
        if _timer(current):raise ValueError('Encerre os cronômetros antes de recuperar.')
        for name in set(current)|set(before_hash)|set(journal['after']):
            actual=hashlib.sha256(current[name]).hexdigest() if name in current else None
            if actual not in (before_hash.get(name),journal['after'].get(name)):
                # A missing file can also be the point of interruption between
                # unlink/replace. It is safe to restore the archived prior bytes.
                if actual is not None or journal['state'] not in ('prepared','recovery-pending'):raise ValueError('Dados mudaram após a restauração; rollback recusado para preservar edições posteriores.')
        try:
            _apply(directory,current,before)
            if _collect(directory)!=before:raise ValueError('Verificação do rollback falhou.')
            _validate(before)
            _clean_empty(directory,set(current)-set(before))
            journal.update(state='rolled-back',pending=[])
            _put(folder/'recovery.json',json.dumps(journal).encode())
        except Exception as error:
            pending=_recover(directory,current,before)
            journal.update(state='recovery-pending',pending=pending)
            _put(folder/'recovery.json',json.dumps(journal).encode())
            raise RuntimeError('Rollback não confirmado; backup prévio preservado.') from error
    return dict(restored=True,previous_backup=str(folder/'before.zip'))
