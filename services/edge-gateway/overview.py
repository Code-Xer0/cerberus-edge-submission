"""Read-only operator projections. Models never run from these reads."""
import asyncio,datetime,hashlib,json,time
from functools import lru_cache
from pathlib import Path

def freshness(value):
 try:
  stamp=value.get('generated_at') or value.get('snapshot_observed_at');age=time.time()-datetime.datetime.fromisoformat(str(stamp).replace('Z','+00:00')).timestamp()
  return 'current' if 0<=age<=90 and value.get('stale') is not True else 'stale'
 except (ValueError,TypeError,AttributeError):return 'unknown'

async def overview(app,cookie,actor,upstream,db):
 async def read(path,agent=False):
  try:
   value=await upstream(app,path,cookie=cookie,agent=agent);return {'data':value,'freshness':freshness(value)}
  except Exception:return {'freshness':'unavailable','detail':'Source did not supply a reliable response'}
 host,insights,report=await asyncio.gather(read('/web/cerberus-edge/edge-status.json'),read('/api/insights',True),read('/web/cerberus-edge/reporting.v1.json'))
 with db() as c:
  row=c.execute("SELECT seq,at,payload FROM audit WHERE actor=? AND kind='explanation' AND json_extract(payload,'$.status')='completed' ORDER BY seq DESC LIMIT 1",(actor,)).fetchone()
  recent=[dict(r) for r in c.execute('SELECT seq,kind,at FROM audit WHERE actor=? ORDER BY seq DESC LIMIT 8',(actor,))]
 saved=None
 if row:
  payload=json.loads(row['payload']);saved={**payload,'receipt_id':row['seq'],'at':row['at'],'relationship':'historical; current evidence equivalence is not established'}
 h=host.get('data',{});services=h.get('services',[]);cards=insights.get('data',{}).get('insights',[])
 facts=[]
 if host['freshness']=='current':facts.append({'text':str(sum(s.get('state')=='online' for s in services))+' of '+str(len(services))+' host services report active.','source':'host','kind':'observation'})
 if insights['freshness']=='current':facts.append({'text':str(len(cards))+' current source-backed insights are available for review.','source':'insights','kind':'deterministic'})
 gaps=[k+' observations are '+v['freshness'] for k,v in [('host',host),('insights',insights),('archive',report)] if v['freshness']!='current']
 return {'schema':'cerberus.overview/1','generated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sources':{'host':host,'insights':insights,'archive':{'freshness':report['freshness'],'total_events':report.get('data',{}).get('archive',{}).get('total_events')}},'brief':facts,'gaps':gaps,'insights':cards,'latest_explanation':saved,'recent_actions':recent,'action_executed':False}

@lru_cache(maxsize=2)
def vendor_index(path,mtime):
 result={}
 try:
  for line in Path(path).read_text(errors='replace').splitlines():
   if '(base 16)' in line:result[line.split()[0].upper()]=line.split('(base 16)',1)[1].strip()
 except OSError:pass
 return result

def vendor(mac,path='/usr/share/hwdata/oui.txt'):
 try:
  parts=mac.split(':')
  if len(parts)!=6 or int(parts[0],16)&3:return None
  return vendor_index(path,Path(path).stat().st_mtime_ns).get(''.join(parts[:3]).upper())
 except (OSError,ValueError):return None

async def topology(app,cookie,upstream):
 inventory,connections,capture=await asyncio.gather(upstream(app,'/api/network/stable',cookie=cookie),upstream(app,'/api/traffic/connections?limit=60',cookie=cookie),upstream(app,'/api/traffic/status',cookie=cookie))
 nodes=[];known=set()
 from core.composer import _is_synthetic_mac
 for h in inventory.get('hosts',[])[:1000]:
  if _is_synthetic_mac(str(h.get('mac','')),str(h.get('ip',''))):continue
  ip=str(h.get('ip',''));mac=str(h.get('mac',''));os=h.get('os');known.add(ip)
  nodes.append({'id':ip,'name':h.get('hostname') if h.get('hostname') not in ('Unknown','',None) else ip,'mac':mac,'manufacturer':vendor(mac),'os':os if os not in ('Unknown','',None) else None,'os_source':'retained sensor report','seen':h.get('last_scan'),'status':'reported-up' if h.get('status')=='up' else 'unverified','source':'ragnar-stable-cache'})
 edges=[]
 for c in connections.get('connections',[])[:60]:
  a=c.get('src_ip');b=c.get('dst_ip')
  if not a or not b or a==b:continue
  for ip in (a,b):
   if ip not in known:nodes.append({'id':ip,'name':ip,'source':'retained connection','status':'observed-endpoint'});known.add(ip)
  edges.append({'id':hashlib.sha256(json.dumps([a,b,c.get('src_port'),c.get('dst_port'),c.get('protocol')]).encode()).hexdigest()[:24],'source':a,'target':b,'protocol':c.get('protocol'),'last_seen':c.get('last_seen'),'direction_verified':type(c.get('bytes_sent')) is int and c['bytes_sent']>=0,'bytes_source_to_target':c.get('bytes_sent')})
 return {'schema':'cerberus.topology/1','generated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'nodes':nodes,'edges':edges,'coverage':'Bounded retained inventory and 60 connections. Attachment and counter direction are not yet independently verified.','attachment_verified':False,'capture':capture.get('summary',{})}
