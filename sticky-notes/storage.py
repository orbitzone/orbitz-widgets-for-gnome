"""Transactional local notes. Legacy notes/tasks are imported without modification."""
from pathlib import Path
from datetime import date
import json
import os
import sqlite3
import uuid

COLORS=['#ffe293','#ffd6df','#d9edb5','#cce7ff','#e5d7fa','#ffdbb5']
DATA=Path(os.environ.get('XDG_DATA_HOME') or Path.home()/'.local/share')/'orbitz-postits'

class Store:
    def __init__(self, directory=DATA, legacy=None):
        self.directory=Path(directory);self.directory.mkdir(parents=True,exist_ok=True,mode=0o700)
        self.path=self.directory/'notes.sqlite3'
        self.db=sqlite3.connect(self.path,timeout=3)
        os.chmod(self.path,0o600)
        self.db.execute('PRAGMA journal_mode=WAL');self.db.execute('PRAGMA synchronous=FULL')
        self.db.row_factory=sqlite3.Row
        if self.db.execute('PRAGMA quick_check').fetchone()[0]!='ok':raise ValueError('Banco de notas inválido. Os arquivos foram preservados.')
        self.db.executescript('''
        CREATE TABLE IF NOT EXISTS notes(
          id TEXT PRIMARY KEY, text TEXT NOT NULL, color TEXT NOT NULL,
          x INTEGER NOT NULL DEFAULT 100, y INTEGER NOT NULL DEFAULT 100,
          width INTEGER NOT NULL DEFAULT 310, height INTEGER NOT NULL DEFAULT 300,
          above INTEGER NOT NULL DEFAULT 0, revision INTEGER NOT NULL DEFAULT 0,
          archived INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
        ''')
        if not self.db.execute("SELECT 1 FROM metadata WHERE key='imported'").fetchone():
            raw={'notes':'','note_color':COLORS[0]}
            if legacy and Path(legacy).exists():
                raw=json.loads(Path(legacy).read_text())
                if not isinstance(raw,dict) or not isinstance(raw.get('notes'),str):raise ValueError('Nota antiga inválida. O original foi preservado.')
            with self.db:
                self.db.execute('INSERT INTO notes(id,text,color) VALUES(?,?,?)',(str(uuid.uuid4()),raw['notes'],raw.get('note_color') if raw.get('note_color') in COLORS else COLORS[0]))
                self.db.execute("INSERT INTO metadata VALUES('imported','1')")
        self.backup()

    def backup(self):
        directory=self.directory/'backups';directory.mkdir(exist_ok=True,mode=0o700)
        path=directory/(date.today().isoformat()+'.sqlite3')
        if path.exists():return
        tmp=path.with_suffix('.tmp')
        try:
            with sqlite3.connect(tmp) as destination:self.db.backup(destination)
            os.chmod(tmp,0o600);tmp.replace(path)
        finally:
            if tmp.exists():tmp.unlink()
        for old in sorted(directory.glob('*.sqlite3'))[:-14]:old.unlink()

    def all(self,archived=False):
        return [dict(row) for row in self.db.execute('SELECT * FROM notes WHERE archived=? ORDER BY rowid',(int(archived),))]

    def get(self,identity):
        row=self.db.execute('SELECT * FROM notes WHERE id=?',(identity,)).fetchone()
        if row is None:raise ValueError('Nota não encontrada.')
        return dict(row)

    def create(self,x=100,y=100):
        identity=str(uuid.uuid4())
        with self.db:self.db.execute('INSERT INTO notes(id,text,color,x,y) VALUES(?,?,?,?,?)',(identity,'',COLORS[0],x,y))
        return self.get(identity)

    def text(self,identity,value,revision):
        if not isinstance(value,str) or len(value)>100000:raise ValueError('Limite de 100 mil caracteres por nota.')
        with self.db:
            cursor=self.db.execute('UPDATE notes SET text=?,revision=revision+1 WHERE id=? AND revision=?',(value,identity,revision))
            if cursor.rowcount!=1:raise ValueError('A nota foi alterada por outro processo. Copie o texto antes de recarregar.')
        return revision+1

    def properties(self,identity,**values):
        if not values or not set(values)<={'color','x','y','width','height','above','archived'}:raise ValueError('Propriedade inválida.')
        if 'color' in values and values['color'] not in COLORS:raise ValueError('Cor inválida.')
        for key,value in values.items():
            if key!='color' and (type(value) is not int or abs(value)>100000):raise ValueError('Dimensão inválida.')
        with self.db:self.db.execute('UPDATE notes SET '+','.join(key+'=?' for key in values)+' WHERE id=?',(*values.values(),identity))

    def close(self):self.db.close()
