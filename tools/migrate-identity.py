#!/usr/bin/python3
"""Plan/prepare a reversible Orbitz identity migration; never switches GNOME UUIDs."""
import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

REPO = Path(__file__).resolve().parents[1]
LEGACY_UUID = 'azclock@azclock.gitlab.com'
NEW_UUID = 'orbitz-widgets@orbitzone.github.io'
LEGACY_SCHEMA = 'org.gnome.shell.extensions.azclock'
NEW_SCHEMA = 'org.gnome.shell.extensions.orbitz-widgets'
EXTENSIONS = Path.home()/'.local/share/gnome-shell/extensions'
BACKUPS = Path(os.environ.get('XDG_STATE_HOME') or Path.home()/'.local/state')/'orbitz-widgets/identity-backups'


def checked_path(path):
    path = Path(path).absolute()
    if path.resolve() != path:
        raise RuntimeError('Caminho vinculado recusado: ' + str(path))
    return path


def tree_hashes(root):
    result = {}
    for path in sorted(root.rglob('*')):
        if path.is_symlink():
            raise RuntimeError('Link simbólico recusado: ' + str(path))
        if path.is_file():
            result[str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).hexdigest()
        elif not path.is_dir():
            raise RuntimeError('Arquivo especial recusado: ' + str(path))
    return result


def private_json(path, data):
    fd, temporary = tempfile.mkstemp(prefix='.identity-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            os.fchmod(stream.fileno(), 0o600)
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    finally:
        Path(temporary).unlink(missing_ok=True)


def compile_schemas(directory):
    subprocess.run(['glib-compile-schemas', '--strict', str(directory)],
                   check=True, capture_output=True, text=True)


class DesktopSettings:
    """Real backend instantiated only by explicit CLI, never during import/tests."""
    def __init__(self, old_directory, source_directory):
        from gi.repository import Gio
        self.Gio = Gio
        self.settings = {}
        for identity, directory in [(LEGACY_SCHEMA, old_directory/'schemas'),
                                    (NEW_SCHEMA, source_directory/'schemas')]:
            # Compile copies; do not require or mutate an installed compiled file.
            with tempfile.TemporaryDirectory(prefix='orbitz-schema-') as temporary:
                stage = Path(temporary)
                for xml in directory.glob('*.xml'):
                    if xml.is_symlink():
                        raise RuntimeError('Schema vinculado recusado.')
                    shutil.copy2(xml, stage/xml.name)
                compile_schemas(stage)
                source = Gio.SettingsSchemaSource.new_from_directory(str(stage), Gio.SettingsSchemaSource.get_default(), False)
                schema = source.lookup(identity, False)
                expected_path = '/org/gnome/shell/extensions/' + ('azclock/' if identity == LEGACY_SCHEMA else 'orbitz-widgets/')
                if schema is None or schema.get_path() != expected_path:
                    raise RuntimeError('Schema/path esperado ausente: ' + identity)
                self.settings[identity] = Gio.Settings.new_full(schema, None, None)
        self.shell = Gio.Settings.new('org.gnome.shell')

    def snapshot(self, identity):
        settings = self.settings[identity]
        schema = settings.props.settings_schema
        result = {}
        for key in sorted(schema.list_keys()):
            value = settings.get_value(key)
            user = settings.get_user_value(key)
            result[key] = dict(type=value.get_type_string(), value=value.print_(True),
                               user=None if user is None else user.print_(True))
        return result

    def activation(self):
        return {key: self.shell.get_value(key).print_(True) for key in
                ('enabled-extensions', 'disabled-extensions', 'disable-user-extensions')}

    def write(self, identity, key, value):
        from gi.repository import GLib
        settings = self.settings[identity]
        if value is None:
            settings.reset(key)
        else:
            variant = GLib.Variant.parse(settings.get_value(key).get_type(), value, None, None)
            if not settings.set_value(key, variant):
                raise RuntimeError('GSettings recusou gravação: ' + key)
        self.Gio.Settings.sync()


def enabled(activation):
    from gi.repository import GLib
    return GLib.Variant.parse(GLib.VariantType.new('as'), activation['enabled-extensions'], None, None).unpack()


def guard_activation(settings):
    activation = settings.activation()
    # Conservative: refuse even if a globally-disabled extension remains selected.
    if NEW_UUID in enabled(activation):
        raise RuntimeError('UUID novo consta em enabled-extensions; desative-o manualmente antes de preparar/restaurar.')
    return activation


def check_contract(old, target):
    from gi.repository import GLib
    if set(old) != set(target):
        raise RuntimeError('Chaves de schema divergentes; migração recusada.')
    required = {'widget-data': 'aaa{ss}', 'changed-data': 'a{ss}'}
    for key, item in old.items():
        if item['type'] != target[key]['type'] or (key in required and item['type'] != required[key]):
            raise RuntimeError('Tipo de schema divergente: ' + key)
        for snapshot in (item, target[key]):
            kind = GLib.VariantType.new(item['type'])
            GLib.Variant.parse(kind, snapshot['value'], None, None)
            if snapshot['user'] is not None:
                GLib.Variant.parse(kind, snapshot['user'], None, None)
        if target[key]['user'] is not None and target[key]['value'] != item['value']:
            raise RuntimeError('Configuração nova divergente; sem sobrescrita automática: ' + key)
    if not set(required) <= set(old):
        raise RuntimeError('Chaves obrigatórias ausentes.')


def validate_layout(old_directory, new_directory, source, backups):
    for path in (old_directory, new_directory, source, backups):
        checked_path(path)
    if old_directory.name != LEGACY_UUID or new_directory.name != NEW_UUID or old_directory.parent != new_directory.parent:
        raise RuntimeError('Diretórios de identidade inválidos.')
    if backups.is_relative_to(REPO) or backups.is_relative_to(source) or backups.is_relative_to(old_directory) or backups.is_relative_to(new_directory):
        raise RuntimeError('Backup privado precisa ficar fora do repositório e instalações.')
    if new_directory.exists():
        raise RuntimeError('Destino novo já existe; use o manifesto de preparo/rollback, sem mesclar instalações.')
    old_metadata = json.loads((old_directory/'metadata.json').read_text())
    new_metadata = json.loads((source/'metadata.json').read_text())
    for metadata, uuid, schema in [(old_metadata, LEGACY_UUID, LEGACY_SCHEMA), (new_metadata, NEW_UUID, NEW_SCHEMA)]:
        if metadata.get('uuid') != uuid or metadata.get('settings-schema') != schema:
            raise RuntimeError('Manifesto UUID/schema incompatível com destino.')


def restore_config(settings, before, expected):
    # Retry a partial rollback only where current values still match our states.
    current = settings.snapshot(NEW_SCHEMA)
    if set(current) != set(before) or any(current[k] not in (before[k], expected[k]) for k in before):
        raise RuntimeError('Configuração nova mudou; rollback recusado sem sobrescrever alterações posteriores.')
    pending = []
    for key in before:
        try:
            guard_activation(settings)
            item = settings.snapshot(NEW_SCHEMA)[key]
            if item not in (before[key], expected[key]):
                raise RuntimeError('Edição posterior preservada.')
            if item != before[key]:
                settings.write(NEW_SCHEMA, key, before[key]['user'])
        except Exception as error:
            pending.append(key + ': ' + str(error))
    if pending or settings.snapshot(NEW_SCHEMA) != before:
        raise RuntimeError('Recuperação de configuração pendente: ' + '; '.join(pending))


def prepare(old_directory, new_directory, source, backups, settings, apply=False):
    old_directory, new_directory, source, backups = map(checked_path, (old_directory,new_directory,source,backups))
    validate_layout(old_directory, new_directory, source, backups)
    old_hashes, source_hashes = tree_hashes(old_directory), tree_hashes(source)
    activation = guard_activation(settings)
    old, target = settings.snapshot(LEGACY_SCHEMA), settings.snapshot(NEW_SCHEMA)
    check_contract(old, target)
    if not apply:
        return dict(state='plan', legacy_files=len(old_hashes), source_files=len(source_hashes), keys=len(old))
    backups.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(backups, 0o700)
    folder = Path(tempfile.mkdtemp(prefix=datetime.now().strftime('%Y%m%d-%H%M%S-'), dir=backups))
    manifest = dict(version=1, state='backed-up', legacy=str(old_directory), destination=str(new_directory),
                    source=str(source), old=old, target_before=target, activation=activation,
                    legacy_hashes=old_hashes,
                    target_after={k:dict(v,user=v['value']) for k,v in old.items()})
    private_json(folder/'manifest.json', manifest)
    attempted = []
    published = False
    try:
        # Stage next to destination for atomic directory publication. Old tree stays intact.
        with tempfile.TemporaryDirectory(prefix='.orbitz-identity-', dir=new_directory.parent) as temporary:
            stage = Path(temporary)/NEW_UUID
            shutil.copytree(old_directory, stage)
            for relative in source_hashes:
                path = Path(relative)
                if '__pycache__' in path.parts or path.name in ('gschemas.compiled', 'speedtest'):
                    continue
                target_path = stage/path
                target_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source/path, target_path)
            compile_schemas(stage/'schemas')
            manifest['prepared_hashes'] = tree_hashes(stage)
            # Recheck all inputs, activation and both configs before publication/config writes.
            if tree_hashes(old_directory) != old_hashes or tree_hashes(source) != source_hashes:
                raise RuntimeError('Fonte/instalação mudou durante preparo.')
            if settings.snapshot(LEGACY_SCHEMA) != old or settings.snapshot(NEW_SCHEMA) != target or guard_activation(settings) != activation:
                raise RuntimeError('Configuração/ativação mudou durante preparo.')
            if new_directory.exists():
                raise RuntimeError('Destino apareceu durante preparo.')
            manifest['state'] = 'staged'
            private_json(folder/'manifest.json', manifest)
            os.rename(stage, new_directory)
            published = True
            for key, item in old.items():
                if settings.snapshot(LEGACY_SCHEMA) != old or guard_activation(settings) != activation:
                    raise RuntimeError('Origem/ativação mudou durante migração de configuração.')
                current = settings.snapshot(NEW_SCHEMA)
                expected = {k: (dict(v, user=v['value']) if k in attempted else target[k]) for k,v in old.items()}
                if current != expected:
                    raise RuntimeError('Configuração nova mudou durante migração.')
                attempted.append(key)
                settings.write(NEW_SCHEMA, key, item['value'])
            expected = {k:dict(v,user=v['value']) for k,v in old.items()}
            if (settings.snapshot(NEW_SCHEMA) != expected or tree_hashes(new_directory) != manifest['prepared_hashes']
                    or settings.snapshot(LEGACY_SCHEMA) != old or guard_activation(settings) != activation):
                raise RuntimeError('Verificação de preparo falhou.')
            manifest['target_after'] = expected
            manifest['state'] = 'prepared'
            private_json(folder/'manifest.json', manifest)
    except Exception:
        pending = []
        for key in reversed(attempted):
            try:
                guard_activation(settings)
                current = settings.snapshot(NEW_SCHEMA)[key]
                if current['user'] not in (old[key]['value'], target[key]['user']):
                    raise RuntimeError('Edição posterior preservada.')
                settings.write(NEW_SCHEMA, key, target[key]['user'])
            except Exception as error:
                pending.append(key + ': ' + str(error))
        if published:
            try:
                guard_activation(settings)
                if tree_hashes(new_directory) != manifest['prepared_hashes']:
                    raise RuntimeError('Arquivos posteriores preservados.')
                manifest['removal_started'] = True
                manifest['state'] = 'recovery-pending'
                private_json(folder/'manifest.json', manifest)
                shutil.rmtree(new_directory)
            except Exception as error:
                pending.append('installation: ' + str(error))
        manifest['state'] = 'recovery-pending' if pending else 'recovered'
        manifest['recovery_pending'] = pending
        private_json(folder/'manifest.json', manifest)
        raise
    return dict(state='prepared', backup=str(folder), destination=str(new_directory))


def verify_removal_tree(directory, manifest):
    if not directory.exists():
        return
    actual = tree_hashes(directory)
    expected = manifest.get('prepared_hashes', {})
    if manifest.get('removal_started') is True:
        valid = all(name in expected and value == expected[name] for name, value in actual.items())
    else:
        valid = actual == expected
    if not valid:
        raise RuntimeError('Instalação nova mudou; rollback recusado.')


def rollback(folder, old_directory, new_directory, settings):
    folder, old_directory, new_directory = map(checked_path, (folder, old_directory, new_directory))
    manifest = json.loads((folder/'manifest.json').read_text())
    if manifest.get('version') != 1 or manifest.get('state') not in ('prepared', 'staged', 'rollback-pending', 'recovery-pending') or manifest.get('legacy') != str(old_directory) or manifest.get('destination') != str(new_directory):
        raise RuntimeError('Manifesto de preparo inválido para estes destinos.')
    guard_activation(settings)
    verify_removal_tree(new_directory, manifest)
    try:
        restore_config(settings, manifest['target_before'], manifest['target_after'])
        guard_activation(settings)
        verify_removal_tree(new_directory, manifest)
        # Neither the legacy installation nor its config was modified.
        if new_directory.exists():
            manifest['removal_started'] = True
            manifest['state'] = 'rollback-pending'
            private_json(folder/'manifest.json', manifest)
            shutil.rmtree(new_directory)
    except Exception as error:
        manifest['state'] = 'rollback-pending'
        manifest['rollback_pending'] = str(error)
        private_json(folder/'manifest.json', manifest)
        raise
    manifest['state'] = 'rolled-back'
    private_json(folder/'manifest.json', manifest)
    return dict(state='rolled-back', backup=str(folder))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--prepare', action='store_true', help='Prepara instalação/config; não ativa UUID novo.')
    mode.add_argument('--rollback', type=Path, help='Restaura somente o preparo, com UUID novo já desativado.')
    parser.add_argument('--extensions-dir', type=Path, default=EXTENSIONS)
    parser.add_argument('--backup-dir', type=Path, default=BACKUPS)
    args = parser.parse_args()
    old, new = args.extensions_dir/LEGACY_UUID, args.extensions_dir/NEW_UUID
    backend = DesktopSettings(old, REPO/'extension')
    if args.rollback:
        result = rollback(args.rollback, old, new, backend)
    else:
        result = prepare(old, new, REPO/'extension', args.backup_dir, backend, args.prepare)
    print(json.dumps(result, ensure_ascii=False))
    print('Nenhuma ativação GNOME alterada. Troca/retorno de UUID exigem ação manual explícita e verificação de apenas um ativo.')


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        raise SystemExit('MIGRACAO_NAO_CONFIRMADA: ' + str(error))
