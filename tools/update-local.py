#!/usr/bin/python3
"""Prepare/apply a reversible local RF-01 update; never reloads GNOME."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import secrets
import stat
import copy
import re
import xml.etree.ElementTree as ET
from datetime import datetime

REPO = Path(__file__).resolve().parents[1]
HOME = Path.home()
LEGACY_UUID = 'azclock@azclock.gitlab.com'
NEW_UUID = 'orbitz-widgets@orbitzone.github.io'
EXTENSIONS = HOME / '.local/share/gnome-shell/extensions'
EXT = EXTENSIONS / LEGACY_UUID
NOTES = HOME / '.local/share/orbitz-postits/app'
COLLECTORS = HOME / '.local/share/orbitz-widgets/collectors'
I18N = HOME / '.local/share/orbitz-widgets/i18n'
_schema_stage = None
BACKUPS = HOME / 'Documents/Codex/work/orbitz-local-updates'
SCHEMA = 'org.gnome.shell.extensions.azclock'
OLD_DIRS = [HOME / 'Documents/Codex' / p for p in (
    '2026-10-08/quan/outputs', '2026-10-09/pngrub-ae-in-f14-1e100-net/outputs',
    '2026-10-11/https-rdap-org-ip-2a06-3a98c1/outputs')]


def select_identity():
    """Use the migrated installation when present; never overlay another UUID."""
    global EXT, SCHEMA
    source = json.loads(secure_read(REPO / 'extension/metadata.json')[0])
    installed = [EXTENSIONS / identity for identity in (NEW_UUID, LEGACY_UUID)
                 if (EXTENSIONS / identity).exists()]
    if not installed:
        raise RuntimeError('Nenhuma instalação Orbitz/azclock encontrada; prepare a migração de identidade primeiro.')
    EXT = installed[0]
    metadata = json.loads(secure_read(EXT / 'metadata.json')[0])
    if metadata.get('uuid') != EXT.name:
        raise RuntimeError('UUID do manifesto instalado difere do diretório; atualização recusada.')
    if source.get('uuid') != EXT.name:
        raise RuntimeError('A fonte usa outra identidade; execute migrate-identity.py antes de atualizar.')
    expected_schema = {LEGACY_UUID: 'org.gnome.shell.extensions.azclock',
                       NEW_UUID: 'org.gnome.shell.extensions.orbitz-widgets'}[EXT.name]
    if metadata.get('settings-schema') != expected_schema:
        raise RuntimeError('Schema instalado incompatível com identidade; atualização recusada.')
    if source.get('settings-schema') != expected_schema:
        raise RuntimeError('Schema da fonte incompatível com identidade; atualização recusada.')
    SCHEMA = expected_schema
    return EXT


def identity_from_manifest(manifest):
    """DEP01 backups without identity fields always belong to azclock."""
    global EXT, SCHEMA
    legacy_schema = 'org.gnome.shell.extensions.azclock'
    new_schema = 'org.gnome.shell.extensions.orbitz-widgets'
    candidate = Path(manifest.get('extension', str(EXTENSIONS / LEGACY_UUID)))
    expected = {LEGACY_UUID: legacy_schema, NEW_UUID: new_schema}
    schema = manifest.get('schema', legacy_schema)
    if candidate.parent != EXTENSIONS or candidate.name not in expected or schema != expected[candidate.name]:
        raise RuntimeError('Identidade/schema de rollback incompatíveis; nenhuma configuração alterada.')
    EXT, SCHEMA = candidate, schema


def digest(path):
    content, _mode = secure_read(path)
    return hashlib.sha256(content).hexdigest()


def open_directory(path, *, create=False, allow_missing=False):
    """Walk from / with directory descriptors; never follow any symlink."""
    path = Path(path)
    if '..' in path.parts:
        raise RuntimeError('Componente de caminho inválido.')
    path = path.absolute()
    fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
    try:
        for component in path.parts[1:]:
            try:
                following = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            except FileNotFoundError:
                if create:
                    try:
                        os.mkdir(component, mode=0o700, dir_fd=fd)
                    except FileExistsError:
                        pass
                    following = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                elif allow_missing:
                    return fd
                else:
                    raise
            os.close(fd)
            fd = following
        return fd
    except BaseException:
        os.close(fd)
        raise


def validate_path(path):
    path = Path(path)
    try:
        parent = open_directory(path.parent)
    except FileNotFoundError:
        return
    try:
        try:
            info = os.stat(path.name, dir_fd=parent, follow_symlinks=False)
        except FileNotFoundError:
            return
        if stat.S_ISLNK(info.st_mode):
            raise RuntimeError('Link simbólico inesperado: ' + str(path))
    finally:
        os.close(parent)


def secure_read(path):
    path = Path(path)
    parent = open_directory(path.parent)
    try:
        fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        with os.fdopen(fd, 'rb') as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode):
                raise RuntimeError('Arquivo regular esperado: ' + str(path))
            return stream.read(), info.st_mode & 0o777
    finally:
        os.close(parent)


def settings(action, *args):
    result = subprocess.run(['gsettings', '--schemadir', str(EXT / 'schemas'),
                             action, SCHEMA, *args], capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError('GSettings indisponível: ' + result.stderr.strip())
    return result.stdout.strip()


def migrate(value):
    from gi.repository import GLib
    original = GLib.Variant.parse(None, value, None, None)
    data = original.unpack()
    count = 0
    for widget in data:
        for element in widget:
            command = element.get('Text_Command', '')
            updated = command
            for directory in OLD_DIRS:
                for script in sorted((REPO / 'widgets').glob('*.py')):
                    old = str(directory / script.name)
                    # Replace only an exact script token/path, never a prefix of another path.
                    import re
                    updated = re.sub(r'(?<![^\s\x22\x27])' + re.escape(old) + r'(?=$|[\s\x22\x27])',
                                     lambda _: str(COLLECTORS / script.name), updated)
            if updated != command:
                element['Text_Command'] = updated
                count += 1
    return GLib.Variant('aaa{ss}', data).print_(True), count


def files():
    select_identity()
    result = []
    for source_root, destination in [(REPO / 'extension', EXT),
                                      (REPO / 'sticky-notes', NOTES),
                                      (REPO / 'widgets', COLLECTORS)]:
        for source in sorted(source_root.rglob('*')):
            relative = source.relative_to(source_root)
            if 'vendor' in relative.parts or '__pycache__' in relative.parts:
                continue
            brand_asset = source_root == REPO / 'extension' and relative in (
                Path('metadata.json'), Path('media/orbitz-logo.svg'))
            if (source.suffix not in ('.py', '.js', '.html') and not brand_asset) or not source.is_file():
                continue
            target = destination / relative
            if source.is_symlink() or target.is_symlink():
                raise RuntimeError('Link simbólico inesperado: ' + str(target))
            if not target.exists() or digest(source) != digest(target):
                result.append((source, target))
    catalog_root = REPO / 'i18n'
    if catalog_root.exists():
        catalogs = []
        for language in ('pt-BR', 'en-US'):
            source = catalog_root / (language + '.json')
            if source.is_symlink() or not source.is_file() or source.stat().st_size > 2 * 1024 * 1024:
                raise RuntimeError('Catálogo de idioma ausente, vinculado ou excedido.')
            data = json.loads(secure_read(source)[0])
            if not isinstance(data, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in data.items()):
                raise RuntimeError('Catálogo de idioma inválido.')
            catalogs.append(set(data))
        if catalogs[0] != catalogs[1]:
            raise RuntimeError('Catálogos de idioma possuem IDs diferentes.')
        if I18N.is_symlink():
            raise RuntimeError('Diretório de idioma vinculado inesperado.')
        for name in ('pt-BR.json', 'en-US.json', 'ui_i18n.py'):
            source, target = catalog_root / name, I18N / name
            if source.is_symlink() or target.is_symlink():
                raise RuntimeError('Link simbólico inesperado: ' + str(target))
            if not source.is_file():
                raise RuntimeError('Recurso de idioma ausente: ' + name)
            if not target.exists() or digest(source) != digest(target):
                result.append((source, target))
    result.extend(language_schema_files())
    return result


def validate_language_schema(directory):
    from gi.repository import Gio
    source = Gio.SettingsSchemaSource.new_from_directory(str(directory), Gio.SettingsSchemaSource.get_default(), False)
    schema = source.lookup(SCHEMA, False)
    if schema is None or not schema.has_key('ui-language'):
        raise RuntimeError('Schema compilado sem ui-language.')
    key = schema.get_key('ui-language')
    if key.get_value_type().dup_string() != 's' or key.get_default_value().unpack() != 'pt-BR':
        raise RuntimeError('Tipo ou padrão ui-language inválido.')
    if key.get_range().unpack() != ('enum', ['pt-BR', 'en-US']):
        raise RuntimeError('Opções ui-language inválidas.')


def language_schema_files():
    """Stage only the new key in the active schema, preserving installed keys.

    Compile the installed schema bundle in a private temporary directory. Both
    XML and compiled output then use the ordinary manifest/atomic-copy rollback.
    The inactive schema XML and all settings values remain unchanged.
    """
    global _schema_stage
    source = REPO / 'extension/schemas' / (SCHEMA + '.gschema.xml')
    if not source.exists():
        return []
    schema = ET.fromstring(secure_read(source)[0]).find(f"schema[@id='{SCHEMA}']")
    key = schema.find("key[@name='ui-language']") if schema is not None else None
    if key is None:
        return []
    directory = EXT / 'schemas'
    target = directory / source.name
    if directory.is_symlink() or target.is_symlink() or not target.is_file():
        raise RuntimeError('Schema ativo ausente ou vinculado; migração recusada.')
    raw = secure_read(target)[0]
    installed = ET.fromstring(raw)
    schemas = installed.findall('schema')
    if len(schemas) != 1 or schemas[0].get('id') != SCHEMA:
        raise RuntimeError('Arquivo do schema ativo incompatível.')
    existing = schemas[0].find("key[@name='ui-language']")
    if existing is None:
        if raw.count(b'</schema>') != 1:
            raise RuntimeError('Fechamento do schema ativo inválido.')
        raw = raw.replace(b'</schema>', ET.tostring(copy.deepcopy(key), encoding='utf-8') + b'\n</schema>')
    else:
        def contract(item):
            return (item.get('type'), item.findtext('default', '').strip(),
                    [c.get('value') for c in item.findall('choices/choice')])
        if contract(existing) != contract(key):
            raise RuntimeError('Chave ui-language instalada incompatível; preservada.')
    if _schema_stage is not None:
        _schema_stage.cleanup()
    _schema_stage = tempfile.TemporaryDirectory(prefix='orbitz-schema-')
    staged = Path(_schema_stage.name)
    for path in directory.iterdir():
        if path.name.endswith(('.gschema.xml', '.gschema.override')):
            if path.is_symlink() or not path.is_file():
                raise RuntimeError('Recurso de schema vinculado inesperado.')
            atomic_copy(path, staged / path.name)
    atomic_write(raw, staged / target.name)
    compiled = subprocess.run(['glib-compile-schemas', '--strict', str(staged)], capture_output=True, text=True, timeout=10)
    if compiled.returncode:
        raise RuntimeError('Compilação temporária do schema de idioma falhou.')
    validate_language_schema(staged)
    result = []
    for name in (target.name, 'gschemas.compiled'):
        generated, destination = staged / name, directory / name
        if destination.is_symlink():
            raise RuntimeError('Schema vinculado inesperado.')
        if not destination.exists() or digest(generated) != digest(destination):
            result.append((generated, destination))
    return result


def atomic_copy(source, target):
    content, mode = secure_read(source)
    if target == EXT / 'metadata.json':
        metadata = json.loads(content)
        if metadata.get('uuid') != EXT.name or metadata.get('settings-schema') != SCHEMA:
            raise RuntimeError('Metadata fonte incompatível com UUID/schema do destino; cópia recusada.')
    atomic_write(content, target, mode)


def atomic_write(content, target, mode=0o600):
    target = Path(target)
    parent = open_directory(target.parent, create=True)
    name = '.orbitz-update-' + secrets.token_hex(16)
    try:
        try:
            info = os.stat(target.name, dir_fd=parent, follow_symlinks=False)
            if stat.S_ISLNK(info.st_mode):
                raise RuntimeError('Link simbólico inesperado: ' + str(target))
        except FileNotFoundError:
            pass
        fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=parent)
        with os.fdopen(fd, 'wb') as stream:
            stream.write(content)
            os.fchmod(stream.fileno(), mode)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, target.name, src_dir_fd=parent, dst_dir_fd=parent)
        os.fsync(parent)
    finally:
        try:
            os.unlink(name, dir_fd=parent)
        except FileNotFoundError:
            pass
        os.close(parent)


def secure_unlink(path):
    path = Path(path)
    try:
        parent = open_directory(path.parent)
    except FileNotFoundError:
        return
    try:
        try:
            info = os.stat(path.name, dir_fd=parent, follow_symlinks=False)
            if stat.S_ISLNK(info.st_mode):
                raise RuntimeError('Link simbólico inesperado: ' + str(path))
            os.unlink(path.name, dir_fd=parent)
            os.fsync(parent)
        except FileNotFoundError:
            pass
    finally:
        os.close(parent)


def preflight():
    # Rollback may target a previous identity recorded by its manifest.
    metadata = json.loads(secure_read(EXT / 'metadata.json')[0])
    if metadata.get('uuid') != EXT.name:
        raise RuntimeError('UUID instalado incompatível com diretório.')
    # Probe parent access before touching any installed code/configuration.
    for destination in (EXT, NOTES, COLLECTORS, I18N):
        parent = open_directory(destination, allow_missing=True)
        name = '.orbitz-preflight-' + secrets.token_hex(16)
        try:
            fd = os.open(name, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600, dir_fd=parent)
            os.close(fd)
            os.unlink(name, dir_fd=parent)
        finally:
            os.close(parent)
    if settings('writable', 'widget-data') != 'true':
        raise RuntimeError('Configuração widget-data não pode ser gravada.')


def rollback_path(value, *, relative=False):
    if not isinstance(value, str) or not value or '\x00' in value:
        raise RuntimeError('Caminho inválido no manifesto de rollback.')
    path = Path(value)
    if path.is_absolute() == relative or '..' in path.parts or str(path) != value or path == Path('.'):
        raise RuntimeError('Caminho inválido no manifesto de rollback.')
    return path


def rollback_source(target):
    """Expected source for an installable target; never trust manifest roots."""
    for root, source_root in ((EXT, REPO/'extension'), (NOTES, REPO/'sticky-notes'), (COLLECTORS, REPO/'widgets')):
        if not target.is_relative_to(root):
            continue
        relative = target.relative_to(root)
        if 'vendor' in relative.parts or '__pycache__' in relative.parts:
            break
        brand = root == EXT and relative in (Path('metadata.json'), Path('media/orbitz-logo.svg'))
        schema = root == EXT and relative in (Path('schemas')/(SCHEMA+'.gschema.xml'), Path('schemas/gschemas.compiled'))
        if relative.suffix in ('.py', '.js', '.html') or brand or schema:
            return source_root/relative, schema
        break
    if target.parent == I18N and target.name in ('pt-BR.json', 'en-US.json', 'ui_i18n.py'):
        return REPO/'i18n'/target.name, False
    raise RuntimeError('Destino fora da lista permitida para rollback: ' + str(target))


def validate_rollback_manifest(manifest, folder):
    """Validate all entries and backups before any installed/settings mutation."""
    if not isinstance(manifest, dict) or not {'files','old_settings','new_settings'} <= manifest.keys():
        raise RuntimeError('Formato inválido do manifesto de rollback.')
    if any(not isinstance(manifest[key], str) for key in ('old_settings','new_settings')):
        raise RuntimeError('Configuração inválida no manifesto de rollback.')
    if 'repo' in manifest and rollback_path(manifest['repo']) != REPO:
        raise RuntimeError('Fonte do manifesto de rollback incompatível.')
    if 'extension' in manifest:
        rollback_path(manifest['extension'])
    identity_from_manifest(manifest)
    if not isinstance(manifest['files'], list):
        raise RuntimeError('Lista de arquivos inválida no manifesto de rollback.')
    seen = set()
    # Check the entire structure/allowlist before accessing entry paths.
    for item in manifest['files']:
        if not isinstance(item, dict) or not {'target','source','backup','old_hash','new_hash'} <= item.keys():
            raise RuntimeError('Entrada inválida no manifesto de rollback.')
        target, source = rollback_path(item['target']), rollback_path(item['source'])
        expected, schema = rollback_source(target)
        staged_schema = (schema and source.parent.parent == Path(tempfile.gettempdir()) and
                         re.fullmatch(r'orbitz-schema-[A-Za-z0-9_-]+', source.parent.name) and source.name == target.name)
        if source != expected and not staged_schema:
            raise RuntimeError('Fonte fora da lista permitida para rollback: ' + str(source))
        if target in seen:
            raise RuntimeError('Destino duplicado no manifesto de rollback.')
        seen.add(target)
        for key in ('old_hash', 'new_hash'):
            value = item[key]
            if not (key == 'old_hash' and value is None) and (not isinstance(value, str) or not re.fullmatch('[0-9a-f]{64}', value)):
                raise RuntimeError('Hash inválido no manifesto de rollback.')
        if (item['backup'] is None) != (item['old_hash'] is None):
            raise RuntimeError('Backup/hash incompatíveis no manifesto de rollback.')
        if item['backup'] is not None:
            backup = rollback_path(item['backup'], relative=True)
            if not (folder/backup).is_relative_to(folder):
                raise RuntimeError('Backup fora da pasta de rollback.')
    for item in manifest['files']:
        validate_path(Path(item['target']))
        validate_path(Path(item['source']))
        if item['backup'] and digest(folder / item['backup']) != item['old_hash']:
            raise RuntimeError('Backup inválido; rollback não iniciado.')


def restore(folder, force=False, *, preflight_check=False):
    folder = Path(folder).absolute()
    manifest = json.loads(secure_read(folder / 'manifest.json')[0])
    validate_rollback_manifest(manifest, folder)
    if preflight_check:
        preflight()
    # Refuse to overwrite subsequent changes unless the user explicitly forces it.
    for item in manifest['files']:
        target = Path(item['target'])
        if (not force and target.exists() and
                digest(target) not in (item['new_hash'], item['old_hash'])):
            raise RuntimeError('Rollback recusado: arquivo mudou após atualização: ' + str(target))
    current = settings('get', 'widget-data')
    if not force and current not in (manifest['old_settings'], manifest['new_settings']):
        raise RuntimeError('Rollback recusado: configuração mudou após atualização.')
    settings('set', 'widget-data', manifest['old_settings'])
    if settings('get', 'widget-data') != manifest['old_settings']:
        raise RuntimeError('Falha verificando restauração GSettings.')
    pending = []
    for item in reversed(manifest['files']):
        target = Path(item['target'])
        try:
            if item['backup']:
                atomic_copy(folder / item['backup'], target)
            else:
                secure_unlink(target)
            actual = digest(target) if target.exists() else None
            if actual != item['old_hash']:
                raise RuntimeError('Hash restaurado divergente.')
        except Exception as recovery_error:
            pending.append(str(target))
            print('RECUPERACAO_CODIGO_PENDENTE:', target, recovery_error)
    if pending:
        raise RuntimeError('Rollback incompleto; arquivos pendentes: ' + str(len(pending)))
    print('ROLLBACK_OK — saia e entre na sessão para carregar os arquivos restaurados.')


def main():
    global EXT, SCHEMA
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--rollback', type=Path)
    parser.add_argument('--force', action='store_true', help='Permite rollback sobre mudanças posteriores.')
    args = parser.parse_args()
    if args.rollback:
        restore(args.rollback.absolute(), args.force, preflight_check=True)
        return
    if args.force:
        parser.error('--force só se aplica a --rollback')
    planned = files()
    old = settings('get', 'widget-data')
    new, changes = migrate(old)
    print('Arquivos a atualizar:', len(planned), '| comandos a migrar:', changes)
    if not args.apply:
        print('PLANO_OK — nenhuma instalação/configuração alterada.')
        return
    preflight()
    if not planned and not changes:
        print('INSTALACAO_JA_ATUAL — nenhuma alteração necessária.')
        return
    parent = open_directory(BACKUPS, create=True)
    name = datetime.now().strftime('%Y%m%d-%H%M%S-') + secrets.token_hex(12)
    try:
        os.mkdir(name, mode=0o700, dir_fd=parent)
    finally:
        os.close(parent)
    folder = BACKUPS / name
    manifest = {'repo': str(REPO), 'extension': str(EXT), 'schema': SCHEMA, 'old_settings': old, 'new_settings': new, 'files': []}
    for index, (source, target) in enumerate(planned):
        old_hash = digest(target) if target.exists() else None
        backup = f'files/{index}' if target.exists() else None
        if backup:
            atomic_copy(target, folder / backup)
            if digest(folder / backup) != old_hash:
                raise RuntimeError('Destino mudou durante o backup; instalação não iniciada.')
        manifest['files'].append({'target': str(target), 'source': str(source),
            'backup': backup, 'old_hash': old_hash,
            'new_hash': digest(source)})
    path = folder / 'manifest.json'
    atomic_write(json.dumps(manifest, ensure_ascii=False, indent=2).encode(), path)
    print('Backup privado:', folder)
    attempted = []
    try:
        # Abort before mutation if a source changed while the backup was made.
        for item in manifest['files']:
            if digest(Path(item['source'])) != item['new_hash']:
                raise RuntimeError('Fonte mudou durante preparação.')
        if settings('get', 'widget-data') != old:
            raise RuntimeError('Configuração mudou durante a preparação.')
        for item in manifest['files']:
            source, target = Path(item['source']), Path(item['target'])
            current_hash = digest(target) if target.exists() else None
            if current_hash != item['old_hash']:
                raise RuntimeError('Destino mudou durante preparação: ' + str(target))
            attempted.append(item)
            atomic_copy(source, target)
        if settings('get', 'widget-data') != old:
            raise RuntimeError('Configuração mudou durante a preparação.')
        settings('set', 'widget-data', new)
        if settings('get', 'widget-data') != new:
            raise RuntimeError('Falha verificando configuração gravada.')
        for item in manifest['files']:
            if digest(Path(item['target'])) != item['new_hash']:
                raise RuntimeError('Hash instalado divergente: ' + item['target'])
        if any(Path(item['target']) == EXT / 'schemas/gschemas.compiled' for item in manifest['files']):
            validate_language_schema(EXT / 'schemas')
    except Exception:
        # Keep unrelated settings changes intact; always restore code we attempted.
        try:
            current = settings('get', 'widget-data')
            if current == new:
                settings('set', 'widget-data', old)
                if settings('get', 'widget-data') != old:
                    raise RuntimeError('Configuração não foi restaurada.')
        except Exception as recovery_error:
            print('RECUPERACAO_CONFIG_PENDENTE:', recovery_error)
        for item in reversed(attempted):
            target = Path(item['target'])
            try:
                if target.exists() and digest(target) not in (item['old_hash'], item['new_hash']):
                    raise RuntimeError('Arquivo posterior preservado.')
                if item['backup']:
                    if digest(folder / item['backup']) != item['old_hash']:
                        raise RuntimeError('Backup inválido.')
                    atomic_copy(folder / item['backup'], target)
                else:
                    secure_unlink(target)
                actual = digest(target) if target.exists() else None
                if actual != item['old_hash']:
                    raise RuntimeError('Hash restaurado divergente.')
            except Exception as recovery_error:
                print('RECUPERACAO_CODIGO_PENDENTE:', target, recovery_error)
        raise
    print('ATUALIZACAO_OK — hashes e configuração conferidos; pronto para sair e entrar na sessão.')
    print('Não foram alterados notas, tarefas, horas, credenciais ou pastas históricas.')
    print('Rollback: /usr/bin/python3', Path(__file__).resolve(), '--rollback', folder)


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        raise SystemExit('ATUALIZACAO_NAO_CONFIRMADA: ' + str(error))
