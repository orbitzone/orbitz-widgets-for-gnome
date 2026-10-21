"""Resolve explicit note links without executing text or opening local files."""
from pathlib import Path
import re
from urllib.parse import urlsplit, unquote, quote

EMAIL=r'[A-Za-z0-9.!#$%&\x27*+/=?^_`{|}~-]+@[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?\.[A-Za-z]{2,63}'
LINKS=re.compile(r'https?://[^\s<>"\x27]+|www\.[^\s<>"\x27]+|mailto:'+EMAIL+'|'+EMAIL,re.IGNORECASE)
PATHS=re.compile(r'"([^"\n]+)"|\x27([^\x27\n]+)\x27|(?:file://|~/|/)[^\s<>"\x27]+')


def directory_uri(value):
    if value.startswith('file://'):
        parsed=urlsplit(value)
        if parsed.netloc not in ('','localhost') or parsed.query or parsed.fragment:return None
        value=unquote(parsed.path)
    if not value.startswith(('/','~/')):return None
    try:
        path=Path(value).expanduser()
        if path.is_dir():return path.resolve().as_uri()
        if path.is_file():return path.resolve().parent.as_uri()
    except (OSError,ValueError,RuntimeError):pass
    return None


def link_at(text, offset):
    if not 0<=offset<len(text):return None
    start=text.rfind('\n',0,offset)+1;end=text.find('\n',offset)
    if end<0:end=len(text)
    line=text[start:end];point=offset-start
    # A logical line may contain a path with spaces; visual wrapping is irrelevant.
    stripped=line.strip();left=len(line)-len(line.lstrip())
    if left<=point<left+len(stripped):
        uri=directory_uri(stripped)
        if uri:return (start+left,start+left+len(stripped),uri)
    for match in PATHS.finditer(line):
        group=1 if match.group(1) is not None else 2 if match.group(2) is not None else 0
        value=match.group(group)
        if match.start(group)<=point<match.end(group):
            uri=directory_uri(value) or directory_uri(value.rstrip('.,;:!?)'))
            if uri:return (start+match.start(group),start+match.end(group),uri)
    for match in LINKS.finditer(line):
        value=match.group().rstrip('.,;:!?')
        while value.endswith(')') and value.count(')')>value.count('('):value=value[:-1]
        if not match.start()<=point<match.start()+len(value):continue
        span=(start+match.start(),start+match.start()+len(value))
        if re.fullmatch(EMAIL,value):return (*span,'mailto:'+quote(value,safe='@'))
        if value.lower().startswith('mailto:'):return (*span,'mailto:'+quote(value[7:],safe='@'))
        url='https://'+value if value.lower().startswith('www.') else value
        try:
            parts=urlsplit(url)
            if parts.scheme.lower() in ('http','https') and parts.hostname and not parts.username and not parts.password:
                return (*span,url)
        except ValueError:pass
    return None


def target_at(text, offset):
    link=link_at(text,offset)
    return link[2] if link else None
