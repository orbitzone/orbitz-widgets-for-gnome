"""Private immutable invoice copies; no index and no access to prior user PDFs."""
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import tempfile
import uuid
import invoice

ROOT = Path(os.environ.get('XDG_DATA_HOME') or Path.home()/'.local/share')/'orbitz-widgets/invoices'
MAX_PDF = 128 * 1024 * 1024
MAX_METADATA = 4 * 1024 * 1024


def _id(value):
    if not isinstance(value,str) or not re.fullmatch('[0-9a-f]{32}',value):
        raise ValueError('Identidade do registro de fatura inválida.')
    return value


def _root(root):
    path = Path(root) if root is not None else ROOT
    path = path.absolute()
    if path.resolve() != path:
        raise ValueError('Histórico de faturas não aceita caminho vinculado.')
    return path


def _sync(directory):
    fd = os.open(directory,os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:os.fsync(fd)
    finally:os.close(fd)


@contextmanager
def _locked(root,create=False):
    root = _root(root)
    if create:
        root.mkdir(parents=True,exist_ok=True,mode=0o700)
        root.chmod(0o700)
    if not root.exists():
        yield None
        return
    if not root.is_dir():
        raise ValueError('Armazenamento de faturas inválido.')
    try:
        fd = os.open(root/'.lock',os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK | (os.O_CREAT if create else 0),0o600)
    except FileNotFoundError:
        if any(root.iterdir()):
            raise ValueError('Lock do histórico indisponível; registros preservados.') from None
        yield root
        return
    with os.fdopen(fd,'r+') as lock:
        if not stat.S_ISREG(os.fstat(lock.fileno()).st_mode):
            raise ValueError('Lock do histórico inválido.')
        if create:os.fchmod(lock.fileno(),0o600)
        fcntl.flock(lock,fcntl.LOCK_EX)
        yield root


def _read(path,limit):
    fd = os.open(path,os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd,'rb') as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_size > limit:
            raise ValueError('Arquivo da fatura inválido ou acima do limite.')
        value = stream.read(limit+1)
        after = os.fstat(stream.fileno())
    if len(value)>limit or (before.st_ino,before.st_size,before.st_mtime_ns)!=(after.st_ino,after.st_size,after.st_mtime_ns) or len(value)!=after.st_size:
        raise ValueError('Arquivo da fatura mudou durante leitura.')
    return value


def _write(path,value):
    fd = os.open(path,os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb') as stream:
        os.fchmod(stream.fileno(),0o600)
        stream.write(value)
        stream.flush()
        os.fsync(stream.fileno())


def _validated_snapshot(value):
    # Metadata is an untrusted JSON boundary. The timesheet validator expects
    # mappings; reject malformed activities here rather than masking arbitrary
    # programming errors from the domain with a broad exception handler.
    if not isinstance(value,dict) or not isinstance(value.get('entries'),list) or any(not isinstance(entry,dict) for entry in value['entries']):
        raise ValueError('Estrutura das atividades da fatura inválida.')
    return invoice.validate_snapshot(value)


def _metadata(identity,snapshot,pdf,created_at):
    canonical_id = re.sub('[^A-Z0-9]','',snapshot['client']['tax_id'].upper())
    client_key = hashlib.sha256(canonical_id.encode('ascii')).hexdigest()
    issued_on = snapshot['issued_on']
    return dict(version=1,id=identity,created_at=created_at,snapshot=snapshot,
                client_key=client_key,client_id=client_key,client_name=snapshot['client']['name'],
                **{key:snapshot[key] for key in ('sheet_id','sheet_name','issued_on','reference','period','hours','minutes','rate','total','currency','language')},
                issued_year=int(issued_on[:4]),issued_month=int(issued_on[5:7]),
                pdf_sha256=hashlib.sha256(pdf).hexdigest(),pdf_size=len(pdf))


def _get(root,identity,verify_pdf=True):
    identity = _id(identity)
    if root is None:
        raise FileNotFoundError('Registro de fatura não encontrado.')
    directory = root/identity
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError('Diretório do registro de fatura inválido.')
    names = {path.name for path in directory.iterdir()}
    if not {'metadata.json','invoice.pdf'} <= names or names - {'metadata.json','invoice.pdf','versions','payment.json'}:
        raise ValueError('Conteúdo inesperado no registro; arquivos preservados.')
    data = json.loads(_read(directory/'metadata.json',MAX_METADATA))
    if not isinstance(data,dict) or data.get('id')!=identity or type(data.get('version')) is not int or data['version']!=1:
        raise ValueError('Metadados da fatura inválidos.')
    timestamp = datetime.fromisoformat(data['created_at'])
    if timestamp.tzinfo is None:
        raise ValueError('Data do registro inválida.')
    snapshot = _validated_snapshot(data['snapshot'])
    if type(data.get('pdf_size')) is not int or not 0 < data['pdf_size'] <= MAX_PDF or not isinstance(data.get('pdf_sha256'),str) or not re.fullmatch('[0-9a-f]{64}',data['pdf_sha256']):
        raise ValueError('Metadados do PDF inválidos.')
    if verify_pdf:
        pdf = _read(directory/'invoice.pdf',MAX_PDF)
        expected = _metadata(identity,snapshot,pdf,data['created_at'])
        if not pdf.startswith(b'%PDF-'):
            raise ValueError('Integridade do registro da fatura inválida.')
    else:
        # Browsing does not load/hash the entire archive. Full verification is
        # reserved for get/open/export/delete; obvious size/type damage is flagged.
        info = (directory/'invoice.pdf').lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_size != data['pdf_size']:
            raise ValueError('Arquivo do PDF inválido.')
        pdf = None
        expected = _metadata(identity,snapshot,b'',data['created_at'])
        expected.update(pdf_sha256=data['pdf_sha256'],pdf_size=data['pdf_size'])
    if data != expected:
        raise ValueError('Integridade do registro da fatura inválida.')
    return data,pdf


def record(snapshot,pdf_path,*,root=None):
    snapshot = _validated_snapshot(snapshot)
    pdf = _read(Path(pdf_path),MAX_PDF)
    if not pdf.startswith(b'%PDF-'):
        raise ValueError('O arquivo exportado não contém um PDF válido.')
    with _locked(root,create=True) as folder:
        for _ in range(8):
            identity = uuid.uuid4().hex
            if not os.path.lexists(folder/identity):break
        else:
            raise RuntimeError('Não foi possível criar identidade exclusiva para fatura.')
        data = _metadata(identity,snapshot,pdf,datetime.now(timezone.utc).isoformat())
        raw = json.dumps(data,ensure_ascii=False,indent=2).encode('utf-8')
        if len(raw)>MAX_METADATA:
            raise ValueError('Metadados da fatura excedem o limite do histórico.')
        with tempfile.TemporaryDirectory(prefix='.record-',dir=folder) as temporary:
            stage = Path(temporary)/identity
            stage.mkdir(mode=0o700)
            _write(stage/'invoice.pdf',pdf)
            _write(stage/'metadata.json',raw)
            _sync(stage)
            if os.path.lexists(folder/identity):
                raise FileExistsError('Identidade de fatura já existe; registro anterior preservado.')
            os.rename(stage,folder/identity)
            _sync(folder)
        return data


def get(identity,*,root=None):
    _id(identity)
    with _locked(root) as folder:
        return _get(folder,identity)[0]


def resolve_pdf(identity,*,root=None):
    _id(identity)
    with _locked(root) as folder:
        _get(folder,identity)
        return folder/identity/'invoice.pdf'


get_path = resolve_pdf


def list_records(*,root=None):
    records,errors = [],[]
    with _locked(root) as folder:
        if folder is None:return dict(records=[],errors=[])
        for directory in sorted(folder.iterdir()):
            if directory.name=='.lock':continue
            if directory.name.startswith(('.record-','.deleted-')):
                errors.append(dict(id='',message='Operação interrompida no histórico; arquivos preservados.'))
                continue
            try:
                _id(directory.name)
                records.append(_get(folder,directory.name,verify_pdf=False)[0])
            except (ValueError,KeyError,TypeError,OSError,UnicodeError):
                errors.append(dict(id=directory.name if re.fullmatch('[0-9a-f]{32}',directory.name) else '',message='Registro inválido ou indisponível; arquivos preservados.'))
    records.sort(key=lambda record:(record['issued_on'],record['created_at'],record['id']),reverse=True)
    return dict(records=records,errors=errors)


def _stamp(path):
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode):
        raise ValueError('Destino da cópia deve ser arquivo regular, sem link simbólico.')
    return info.st_dev,info.st_ino,info.st_size,info.st_mtime_ns


def _export_bytes(pdf,target,*,overwrite=False,root=None):
    if type(overwrite) is not bool:
        raise ValueError('Confirmação de substituição inválida.')
    target = Path(target).expanduser().absolute()
    if target.suffix.lower()!='.pdf':
        raise ValueError('Escolha um arquivo com extensão .pdf.')
    if target.resolve().is_relative_to(_root(root)):
        raise ValueError('A cópia deve ficar fora do armazenamento gerenciado.')
    previous = None
    if target.exists() or target.is_symlink():
        if not overwrite:raise FileExistsError('A cópia já existe; confirme a substituição na interface.')
        previous = _stamp(target)
    fd,name = tempfile.mkstemp(prefix='.invoice-copy-',suffix='.pdf',dir=target.parent)
    try:
        with os.fdopen(fd,'wb') as stream:
            os.fchmod(stream.fileno(),0o600)
            stream.write(pdf);stream.flush();os.fsync(stream.fileno())
        if previous is None:
            os.link(name,target)
        else:
            if _stamp(target)!=previous:
                raise FileExistsError('O destino mudou durante a cópia; existente preservado.')
            os.replace(name,target)
        _sync(target.parent)
    finally:Path(name).unlink(missing_ok=True)
    return target


def export_copy(identity,target,*,overwrite=False,root=None):
    _id(identity)
    with _locked(root) as folder:
        data,pdf = _get(folder,identity)
        return _export_bytes(pdf,target,overwrite=overwrite,root=root)


def _check_versions_delete(directory):
    versions = directory/'versions'
    if not os.path.lexists(versions):return
    if versions.is_symlink() or not versions.is_dir():
        raise ValueError('Pasta de versões inválida; original preservado.')
    for child in versions.iterdir():
        identity = child.name.removeprefix('.deleted-')
        _id(identity)
        if child.is_symlink() or not child.is_dir():
            raise ValueError('Pasta de versão inválida; original preservado.')
        for item in child.iterdir():
            if item.name not in ('metadata.json','invoice.pdf') or not stat.S_ISREG(item.lstat().st_mode):
                raise ValueError('Conteúdo inesperado nas versões; original preservado.')


def delete(identity,*,root=None):
    _id(identity)
    with _locked(root) as folder:
        if folder is None:raise FileNotFoundError('Registro de fatura não encontrado.')
        deleted = folder/('.deleted-'+identity)
        if deleted.exists() or deleted.is_symlink():
            raise ValueError('Exclusão anterior pendente; arquivos preservados para recuperação.')
        _get(folder,identity)
        _check_versions_delete(folder/identity)
        payment=folder/identity/'payment.json'
        if os.path.lexists(payment) and not stat.S_ISREG(payment.lstat().st_mode):raise ValueError('Estado de pagamento inválido; registro preservado.')
        os.rename(folder/identity,deleted)
        _sync(folder)
        try:
            shutil.rmtree(deleted)
            _sync(folder)
        except OSError:
            raise OSError('Registro retirado da lista; limpeza privada pendente. O PDF externo foi preservado.') from None


def get_payment(identity,*,root=None):
    import invoice_payments
    return invoice_payments.get(identity,root=root)


def set_payment(identity,state,*,root=None):
    if state not in ('not_reported','reported_paid'):raise ValueError('Estado manual de pagamento inválido.')
    import invoice_payments
    return invoice_payments.set_paid(identity,state=='reported_paid',root=root)


def possible_duplicates(snapshot,*,root=None):
    import invoice_duplicates
    return invoice_duplicates.check(snapshot,root=root)
