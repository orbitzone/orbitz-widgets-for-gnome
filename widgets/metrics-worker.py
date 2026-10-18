#!/usr/bin/env python3
"""One persistent process for sampled CPU, process and traffic widgets."""
import contextlib,io,json,sys,time
from pathlib import Path
SCRIPTS={'cpu':'cpu-ram-widget.py','processes':'processos-widget.py','network':'rede-widget.py'}

def main():
    jobs={}
    for argument in sys.argv[1:]:
        mode,interval=argument.split(':',1)
        if mode not in SCRIPTS or not 2<=float(interval)<=3600:raise ValueError('Amostragem inválida')
        path=Path(__file__).parent/SCRIPTS[mode]
        jobs[mode]={'interval':float(interval),'next':0,'path':str(path),'code':compile(path.read_text(),str(path),'exec')}
    heartbeat=time.monotonic()
    while jobs:
        if time.monotonic()-heartbeat >= 10:
            print(json.dumps({"mode":"heartbeat","text":""}),flush=True)
            heartbeat=time.monotonic()
        for mode,job in jobs.items():
            now=time.monotonic()
            if now<job['next']:continue
            output=io.StringIO()
            cpu_start=time.process_time()
            try:
                with contextlib.redirect_stdout(output):
                    namespace = {'__name__':'__main__','__file__':job['path']}
                    exec(job['code'], namespace)
                text=output.getvalue().strip()
                if len(text.encode())>8192:raise ValueError('Saída excedida')
            except Exception:
                text='Leitura indisponível'
                namespace={}
            print(json.dumps({'mode':mode,'text':text,'devices':namespace.get('EXTERNAL_DEVICES',[]),'cpu_seconds':round(time.process_time()-cpu_start,6)},ensure_ascii=False),flush=True)
            job['next']=now+job['interval']
        delay=min(job['next'] for job in jobs.values())-time.monotonic()
        time.sleep(max(.05,min(1,delay)))

if __name__=='__main__':main()
