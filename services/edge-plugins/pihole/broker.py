"""Narrow Pi-hole v6 control broker. Install inside the existing Pi-hole container."""
import datetime,hashlib,hmac,ipaddress,json,os,re,subprocess,threading,time
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse,parse_qs,quote
from pihole_policy import domain_name,validate_action
CLI='/usr/local/bin/pihole'
TOKEN=Path(os.environ.get('CREDENTIALS_DIRECTORY','/etc/cerberus-dns'))/'broker-token'
LOCK=threading.Lock();CACHE={};MAX_BODY=4096
class SourceError(Exception):pass


def command(*args):
 result=subprocess.run([CLI,*args],stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10,text=True,env=dict(os.environ,PATH='/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'))
 if result.returncode:raise SourceError('Pi-hole command did not complete')
 if len(result.stdout)>2097152:raise SourceError('Pi-hole response exceeded the broker limit')
 return result.stdout

def api(path):
 text=command('api',path)
 try:value=json.JSONDecoder().raw_decode(text[text.index('{'):])[0]
 except (ValueError,TypeError):raise SourceError('Pi-hole returned invalid JSON')
 if not isinstance(value,dict) or value.get('error'):raise SourceError('Pi-hole API did not return a successful result')
 return value

def number(value):return value if isinstance(value,(float,int)) and not isinstance(value,bool) and 0<=value<10**16 else None

def policy():
 result=[]
 for kind in ('allow','deny'):
  for row in api('domains/'+kind+'/exact').get('domains',[])[:200]:
   if isinstance(row,dict) and isinstance(row.get('domain'),str):result.append({'domain':row['domain'],'type':kind,'kind':'exact','enabled':row.get('enabled') is True})
 return result

def domain_state(name):
 name=domain_name(name);result={'domain':name}
 for kind in ('allow','deny'):
  rows=api('domains/'+kind+'/exact/'+quote(name,safe='')).get('domains',[])
  matching=[r for r in rows if isinstance(r,dict) and r.get('domain')==name]
  result[kind]=bool(matching);result[kind+'_enabled']=any(r.get('enabled') is True for r in matching)
 return result

def status(fresh=False):
 if not fresh and CACHE.get('at',0)>time.monotonic()-10:return CACHE['value']
 summary=api('stats/summary');blocking=api('dns/blocking');q=summary.get('queries',{});clients=summary.get('clients',{});gravity=summary.get('gravity',{})
 state=blocking.get('blocking');value={'schema':'cerberus.pihole/1','generated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'provider':'Pi-hole v6','blocking':True if state in (True,'enabled') else False if state in (False,'disabled') else None,'timer_seconds':number(blocking.get('timer')),'queries':{k:number(q.get(k)) for k in ('total','blocked','percent_blocked','unique_domains','forwarded','cached')},'clients':{k:number(clients.get(k)) for k in ('active','total')},'gravity_domains':number(gravity.get('domains_being_blocked')),'attribution':'Current DNS hairpin may aggregate client identities; provider clients are not verified AP device counts.','capabilities':{'status':True,'domains':True,'enable':True,'pause':True,'exact_policy':True}}
 CACHE.update(at=time.monotonic(),value=value);return value


def apply(data):
 action=validate_action(data);before=status(True);operation=action['action']
 if operation=='pause' and before['blocking'] is not True:raise ValueError('Blocking is not currently enabled; an existing pause cannot be extended by this action')
 if operation=='enable':command('enable')
 elif operation=='pause':command('disable',str(action['seconds'])+'s')
 else:
  kind='allow' if operation in ('allow','remove_allow') else 'deny';current=domain_state(action['domain']);expected=data.get('expected_policy')
  if not isinstance(expected,dict) or any(type(expected.get(k)) is not bool or expected[k]!=current[k] for k in ('allow','deny','allow_enabled','deny_enabled')):raise ValueError('Domain policy changed after review')
  if operation=='deny' and current['allow']:raise ValueError('Remove the existing exact allow exception explicitly before adding a deny entry')
  command(kind,*(['remove'] if operation.startswith('remove_') else []),action['domain'])
 CACHE.clear();after=status(True)
 if operation=='enable':verified=after['blocking'] is True
 elif operation=='pause':verified=after['blocking'] is False and after['timer_seconds'] is not None and 0<after['timer_seconds']<=action['seconds']+1
 else:
  entries=domain_state(action['domain']);present=entries[kind];verified=(not present) if operation.startswith('remove_') else present and entries.get(kind+'_enabled') is True
 return {'state':'verified' if verified else 'unverified','operation':operation,'target':action.get('domain','Pi-hole filtering'),'accepted':True,'blocking':after['blocking'],'timer_seconds':after['timer_seconds'],'at':time.time()}

class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def respond(self,code,value):
  data=json.dumps(value).encode();self.send_response(code);self.send_header('Content-Type','application/json');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
 def authorized(self):
  try:expected=TOKEN.read_text().strip()
  except OSError:return False
  return bool(expected) and hmac.compare_digest(self.headers.get('Authorization',''),'Bearer '+expected)
 def route(self):
  if not self.authorized():return self.respond(401,{'error':'Broker authentication required'})
  parsed=urlparse(self.path)
  try:
   with LOCK:
    if self.command=='GET' and parsed.path=='/v1/status':return self.respond(200,status(parsed.query=='fresh=1'))
    if self.command=='GET' and parsed.path=='/v1/domain':return self.respond(200,domain_state(parse_qs(parsed.query).get('name',[''])[0]))
    if self.command=='GET' and parsed.path=='/v1/domains':return self.respond(200,{'domains':policy(),'limit_per_type':200})
    if self.command=='POST' and parsed.path=='/v1/actions':
     length=int(self.headers.get('Content-Length','0'))
     if not 0<length<=MAX_BODY:raise ValueError('Invalid request size')
     data=json.loads(self.rfile.read(length))
     if not isinstance(data,dict):raise ValueError('JSON object required')
     return self.respond(200,apply(data))
    return self.respond(404,{'error':'Broker route not allowed'})
  except (ValueError,TypeError):return self.respond(400,{'error':'Invalid action or conflicting policy; inspect the current state before retrying'})
  except (SourceError,subprocess.TimeoutExpired,OSError):return self.respond(503,{'error':'Pi-hole result could not be verified','completion':'unknown' if self.command=='POST' else 'unavailable'})
 do_GET=route
 do_POST=route
if __name__=='__main__':ThreadingHTTPServer((os.environ.get('CERBERUS_DNS_BIND','127.0.0.1'),8768),Handler).serve_forever()
