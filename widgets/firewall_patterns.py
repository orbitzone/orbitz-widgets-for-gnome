"""Bounded UFW state validation, aggregation and presentation; no system I/O."""
from orbitz_i18n import t
import datetime
import ipaddress
import json
import math
import re
import time

WINDOW = 86400
MAX_SOURCES = 512
DISCOVERY = {'137', '138', '1900', '5353', '5355'}

def empty():
    return dict(version=2, cursor='', sources={}, totals={}, partial=False, limited_until=0, updated=0)

def valid_state(data):
    def number(value):return type(value) in (int,float) and math.isfinite(value) and value>=0
    def count(value):return type(value) is int and value>=0
    def bucket_key(value):return isinstance(value,str) and value.isdecimal() and len(value)<=12
    if not isinstance(data,dict) or data.get('version')!=2:return False
    if not isinstance(data.get('cursor'),str) or len(data['cursor'])>4096 or type(data.get('partial')) is not bool:return False
    if not all(number(data.get(k)) for k in ('updated','limited_until')):return False
    sources=data.get('sources');totals=data.get('totals')
    if not isinstance(sources,dict) or len(sources)>MAX_SOURCES or not isinstance(totals,dict) or len(totals)>300:return False
    for key,total in totals.items():
        if not bucket_key(key) or not isinstance(total,dict) or not count(total.get('count')) or not count(total.get('noise')) or total['noise']>total['count']:return False
    for source,group in sources.items():
        try:ipaddress.ip_address(source)
        except (ValueError,TypeError):return False
        if not isinstance(group,dict) or not number(group.get('last')):return False
        buckets=group.get('buckets');samples=group.get('samples')
        if not isinstance(buckets,dict) or not 1<=len(buckets)<=300 or not isinstance(samples,list) or len(samples)>5:return False
        for key,bucket in buckets.items():
            if not bucket_key(key) or not isinstance(bucket,dict) or not count(bucket.get('count')) or bucket['count']<1:return False
            if not number(bucket.get('first')) or not number(bucket.get('last')) or bucket['first']>bucket['last']:return False
            for field,limit,size in [('ports',64,8),('destinations',16,45),('protocols',8,16),('interfaces',4,32)]:
                values=bucket.get(field)
                if not isinstance(values,list) or len(values)>limit or any(not isinstance(x,str) or len(x)>size for x in values):return False
            if not bucket['destinations']:return False
        for sample in samples:
            if not isinstance(sample,dict) or not number(sample.get('time')) or not isinstance(sample.get('message'),str) or len(sample['message'])>1024:return False
    return True

def prune(data, now):
    cutoff=now-WINDOW
    for source in list(data['sources']):
        group=data['sources'][source]
        group['buckets']={k:v for k,v in group['buckets'].items() if v['last']>=cutoff}
        if not group['buckets']:del data['sources'][source]
    data['totals']={k:v for k,v in data['totals'].items() if int(k)*300+300>=cutoff}

def limited_add(values,value,limit):
    if value not in values and len(values)<limit: values.append(value)

def ingest(data, lines, now):
    prune(data,now)
    for line in lines:
        try:
            entry=json.loads(line)
            cursor=entry.get('__CURSOR')
            if isinstance(cursor,str) and len(cursor)<4096:data['cursor']=cursor
            msg=entry.get('MESSAGE','')
            if not isinstance(msg,str) or not re.search(r'\[UFW (?:BLOCK|REJECT)\]',msg):continue
            f=dict(re.findall(r'\b([A-Z]+)=([^\s]*)',msg))
            src=ipaddress.ip_address(f['SRC']);dst=ipaddress.ip_address(f['DST'])
            stamp=int(entry['__REALTIME_TIMESTAMP'])/1e6
            if not now-WINDOW<=stamp<=now+60:continue
            key=str(int(stamp)//300)
            total=data['totals'].setdefault(key,{'count':0,'noise':0})
            total['count']+=1
            proto={'2':'IGMP','1':'ICMP','58':'ICMPv6'}.get(f.get('PROTO','?'),f.get('PROTO','?'))[:16]
            port=f.get('DPT','—')
            if port!='—' and (not port.isdecimal() or not 1<=int(port)<=65535):continue
            noise=dst.is_multicast or str(dst)=='255.255.255.255' or (not src.is_global and proto=='UDP' and (port in DISCOVERY or f.get('SPT') in DISCOVERY)) or proto=='IGMP'
            if noise:total['noise']+=1;continue
            source=str(src)
            if source not in data['sources'] and len(data['sources'])>=MAX_SOURCES:
                victim=min(data['sources'],key=lambda s:data['sources'][s]['last'])
                del data['sources'][victim];data['limited_until']=now+WINDOW
            g=data['sources'].setdefault(source,{'buckets':{},'samples':[],'last':stamp})
            g['last']=max(g['last'],stamp)
            b=g['buckets'].setdefault(key,{'count':0,'first':stamp,'last':stamp,'ports':[],'destinations':[],'protocols':[],'interfaces':[]})
            b['count']+=1;b['first']=min(b['first'],stamp);b['last']=max(b['last'],stamp)
            for name,value,limit in [('ports',port,64),('destinations',str(dst),16),('protocols',proto,8),('interfaces',f.get('IN','')[:32],4)]:limited_add(b[name],value,limit)
            g['samples']=(g['samples']+[{'time':stamp,'message':msg[:1024]}])[-5:]
        except (ValueError,TypeError,KeyError,OverflowError,AttributeError):continue
    data['updated']=now

def date(stamp):
    return datetime.datetime.fromtimestamp(stamp).astimezone().strftime('%d/%m %H:%M:%S')

def summarize(source,g,now):
    buckets=list(g['buckets'].values())
    first=min(b['first'] for b in buckets);last=max(b['last'] for b in buckets)
    count=sum(b['count'] for b in buckets)
    def values(key):return sorted({x for b in buckets for x in b[key]})
    ports=values('ports');destinations=values('destinations');protocols=values('protocols')
    minutes=(last-first)/60;active=len(buckets)
    persistent=count>=12 and active>=3 and minutes>=10
    varied=len(ports)>=6 or len(destinations)>=3 or len(protocols)>=2
    burst=count>=30 and len(ports)>=12
    reason=[];priority=0
    if persistent and varied:
        priority=3;reason.append(t('widgets.firewall_patterns.persistence_with_varying_paths_ports_destinations_or_protocols'))
    elif persistent and count>=30:
        priority=2;reason.append(t('widgets.firewall_patterns.persistent_repetition_even_without_path_variation'))
    elif burst:
        priority=2;reason.append(t('widgets.firewall_patterns.many_ports_in_a_sequence_of_blocks_possible_scan'))
    if not priority:return None
    if not ipaddress.ip_address(source).is_global:
        reason.append(t('widgets.firewall_patterns.local_reserved_source_this_may_be_normal_device_communication_rev'))
        priority=min(priority,2)
    reason.append(t('widgets.firewall_patterns.value0_blocks_value1_active_5_minute_intervals_period_of_value2_0', value0=count, value1=active, value2=minutes, value3=len(ports), value4=len(destinations), value5=len(protocols)))
    if last<now-1800:reason.append(t('widgets.firewall_patterns.no_new_records_from_this_source_in_the_last_30_min'))
    else:reason.append(t('widgets.firewall_patterns.activity_recorded_in_the_last_30_min'))
    remote=ipaddress.ip_address(source).is_global
    return dict(source=source,source_remote=remote,destination=destinations[0],protocol=', '.join(protocols),ports=', '.join(ports[:24]),port_values=ports[:24],count=count,first=date(first),last=date(last),last_epoch=last,interface=', '.join(values('interfaces')),kind=(t('widgets.firewall_patterns.persistent_local_activity') if not remote else (t('widgets.firewall_patterns.persistence_with_variation') if priority==3 else t('widgets.firewall_patterns.pattern_to_review'))),priority=priority,reason='\n'.join(reason),local=not remote)

def payload(data,now=None):
    now=time.time() if now is None else now;prune(data,now)
    groups=[p for s,g in data['sources'].items() if (p:=summarize(s,g,now))]
    groups.sort(key=lambda g:(-g['priority'],-g['last_epoch'],-g['count']))
    count=sum(b['count'] for b in data['totals'].values());noise=sum(b['noise'] for b in data['totals'].values())
    scope=t('widgets.firewall_patterns.last_24_h_automatic_refresh_every_60_s_analysis_by_source_and_5_m')
    if data['partial']:scope+=t('widgets.firewall_patterns.collection_in_progress_the_next_batch_resumes_from_the_last_recor')
    if data.get('limited_until',0)>now:scope+=t('widgets.firewall_patterns.storage_limit_reached_some_older_sources_were_discarded_partial_c')
    scope+=t('widgets.firewall_patterns.value0_blocks_analyzed_value1_discovery_multicast_blocks_summariz', value0=count, value1=noise, value2=max(0, len(groups) - 30))
    label=t('widgets.firewall_patterns.pattern') if len(groups)==1 else t('widgets.firewall_patterns.patterns')
    return dict(text=t('widgets.firewall_patterns.summary', count=len(groups), label=label)+(t('widgets.firewall_patterns.partial') if data['partial'] or data.get('limited_until',0)>now else ''),count=count,groups=groups[:30],scope=scope,updated=date(data['updated']) if data['updated'] else t('widgets.firewall_patterns.query_pending'),pattern_mode=True)
