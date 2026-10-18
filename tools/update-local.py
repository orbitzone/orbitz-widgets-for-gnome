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
from datetime import datetime

REPO = Path(__file__).resolve().parents[1]
HOME = Path.home()
LEGACY_UUID = 'azclock@azclock.gitlab.com'
NEW_UUID = 'orbitz-widgets@orbitzone.github.io'
EXTENSIONS = HOME / '.local/share/gnome-shell/extensions'
EXT = EXTENSIONS / LEGACY_UUID
NOTES = HOME / '.local/share/orbitz-postits/app'
COLLECTORS = HOME / '.local/share/orbitz-widgets/collectors'
BACKUPS = HOME / 'Documents/Codex/work/orbitz-local-updates'
SCHEMA = 'org.gnome.shell.extensions.azclock'
OLD_DIRS = [HOME / 'Documents/Codex' / p for p in (
    '2026-10-08/quan/outputs', '2026-10-09/pngrub-ae-in-f14-1e100-net/outputs',
    '2026-10-11/https-rdap-org-ip-2a06-3a98c1/outputs')]


def select_identity():
    """Use the migrated installation when present; never overlay another UUID."""
    global EXT, SCHEMA
    source = json.loads((REPO / 'extension/metadata.json').read_text())
    installed = [EXTENSIONS / identity for identity in (NEW_UUID, LEGACY_UUID)
                 if (EXTENSIONS / identity).exists()]
    if not installed:
        raise RuntimeError('Nenhuma instalação Orbitz/azclock encontrada; prepare a migração de identidade primeiro.')
    EXT = installed[0]
    metadata = json.loads((EXT / 'metadata.json').read_text())
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
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
    return result


def atomic_copy(source, target):
    content = source.read_bytes()
    if target == EXT / 'metadata.json':
        metadata = json.loads(content)
        if metadata.get('uuid') != EXT.name or metadata.get('settings-schema') != SCHEMA:
            raise RuntimeError('Metadata fonte incompatível com UUID/schema do destino; cópia recusada.')
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.orbitz-update-', dir=target.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(content)
            os.fchmod(stream.fileno(), source.stat().st_mode & 0o777)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, target)
        fd = os.open(target.parent, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    finally:
        Path(name).unlink(missing_ok=True)


def preflight():
    # Rollback may target a previous identity recorded by its manifest.
    metadata = json.loads((EXT / 'metadata.json').read_text())
    if metadata.get('uuid') != EXT.name:
        raise RuntimeError('UUID instalado incompatível com diretório.')
    # Probe parent access before touching any installed code/configuration.
    for destination in (EXT, NOTES, COLLECTORS):
        parent = destination if destination.exists() else destination.parent
        if parent.is_symlink():
            raise RuntimeError('Diretório vinculado inesperado: ' + str(parent))
        while not parent.exists():
            parent = parent.parent
        fd, name = tempfile.mkstemp(prefix='.orbitz-preflight-', dir=parent)
        os.close(fd)
        Path(name).unlink()
    if settings('writable', 'widget-data') != 'true':
        raise RuntimeError('Configuração widget-data não pode ser gravada.')


def restore(folder, force=False):
    manifest = json.loads((folder / 'manifest.json').read_text())
    identity_from_manifest(manifest)
    for item in manifest['files']:
        if item['backup'] and digest(folder / item['backup']) != item['old_hash']:
            raise RuntimeError('Backup inválido; rollback não iniciado.')
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
                target.unlink(missing_ok=True)
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
        saved = json.loads((args.rollback.resolve() / 'manifest.json').read_text())
        identity_from_manifest(saved)
        preflight()
        restore(args.rollback.resolve(), args.force)
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
    BACKUPS.mkdir(parents=True, exist_ok=True, mode=0o700)
    folder = Path(tempfile.mkdtemp(prefix=datetime.now().strftime('%Y%m%d-%H%M%S-'), dir=BACKUPS))
    manifest = {'repo': str(REPO), 'extension': str(EXT), 'schema': SCHEMA, 'old_settings': old, 'new_settings': new, 'files': []}
    for index, (source, target) in enumerate(planned):
        old_hash = digest(target) if target.exists() else None
        backup = f'files/{index}' if target.exists() else None
        if backup:
            (folder / 'files').mkdir(exist_ok=True, mode=0o700)
            shutil.copy2(target, folder / backup)
            if digest(folder / backup) != old_hash:
                raise RuntimeError('Destino mudou durante o backup; instalação não iniciada.')
            with (folder / backup).open('rb') as stream:
                os.fsync(stream.fileno())
        manifest['files'].append({'target': str(target), 'source': str(source),
            'backup': backup, 'old_hash': old_hash,
            'new_hash': digest(source)})
    path = folder / 'manifest.json'
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    path.chmod(0o600)
    with path.open('rb') as stream:
        os.fsync(stream.fileno())
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
                    target.unlink(missing_ok=True)
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
