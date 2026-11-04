"""Authenticated, fixed-target Pi-hole plugin. No credential or general proxy is exposed."""
import asyncio,hashlib,ipaddress,json,os,secrets,time
from urllib.parse import urlsplit,urlunsplit,urlencode
from aiohttp import web,ClientTimeout
from pihole_policy import validate_action

async def remote(request,credential,path,*,data=None):
 configured=os.environ.get('CERBERUS_PIHOLE_BROKER_URL','');token=credential('pihole-broker')
 if not configured or not token:raise web.HTTPServiceUnavailable(text='Pi-hole broker is not configured on this node')
 parsed=urlsplit(configured)
 if parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.password or parsed.path not in ('','/') or parsed.query or parsed.fragment:raise web.HTTPServiceUnavailable(text='Pi-hole broker transport requires a fixed HTTPS origin')
 headers={'Authorization':'Bearer '+token,'Accept-Encoding':'identity'};kwargs={};netloc=parsed.netloc
 pinned=os.environ.get('CERBERUS_PIHOLE_BROKER_IP','')
 if pinned:
  try:address=ipaddress.ip_address(pinned)
  except ValueError:raise web.HTTPServiceUnavailable(text='Pi-hole pinned transport address is invalid')
  netloc=('['+str(address)+']' if address.version==6 else str(address))+(':'+str(parsed.port) if parsed.port else '')
  headers['Host']=parsed.netloc;kwargs['server_hostname']=parsed.hostname
 url=urlunsplit(('https',netloc,path,'',''))
 # The path is one of three internal constants, never supplied by the browser.
 async with request.app['client'].request('POST' if data is not None else 'GET',url,headers=headers,json=data,allow_redirects=False,timeout=ClientTimeout(total=22 if data else 12),**kwargs) as response:
  if response.status in (400,409):raise web.HTTPConflict(text='Pi-hole rejected the action or its reviewed state changed; inspect policy before preparing another action')
  if response.status!=200:raise web.HTTPBadGateway(text='Pi-hole broker returned HTTP '+str(response.status)+'; no verified result is available')
  raw=await response.content.read(262145)
  if len(raw)>262144:raise web.HTTPBadGateway(text='Pi-hole broker response exceeded its bound')
  try:value=json.loads(raw)
  except ValueError:raise web.HTTPBadGateway(text='Pi-hole broker returned invalid JSON')
  if not isinstance(value,dict):raise web.HTTPBadGateway(text='Pi-hole broker response has invalid shape')
  return value

def store(db):
 with db() as c:c.execute('CREATE TABLE IF NOT EXISTS dns_plans(id TEXT PRIMARY KEY,actor TEXT,at REAL,payload TEXT,state TEXT,result TEXT)')

def identity(status):return hashlib.sha256(json.dumps({'provider':status.get('provider'),'blocking':status.get('blocking')},sort_keys=True).encode()).hexdigest()

async def handle(request,actor,path,body,db,audit,credential):
 configured=bool(os.environ.get('CERBERUS_PIHOLE_BROKER_URL') and credential('pihole-broker'))
 if request.method=='GET' and path=='status':
  if not configured:return web.json_response({'schema':'cerberus.pihole/1','state':'unconfigured','detail':'Pi-hole control broker has not been connected. The existing DNS path is unchanged.','capabilities':{'status':False,'domains':False,'enable':False,'pause':False,'exact_policy':False}})
  value=await remote(request,credential,'/v1/status');return web.json_response(dict(value,state='available'))
 if request.method=='GET' and path=='domains':return web.json_response(await remote(request,credential,'/v1/domains'))
 if request.method=='POST' and path=='review':
  try:action=validate_action(await body(request))
  except ValueError as error:raise web.HTTPBadRequest(text=str(error))
  current=await remote(request,credential,'/v1/status?fresh=1')
  if action['action']=='pause' and current.get('blocking') is not True:raise web.HTTPConflict(text='Blocking is not currently enabled; an existing pause will not be extended')
  policy=await remote(request,credential,'/v1/domain?'+urlencode({'name':action['domain']})) if 'domain' in action else None
  if policy:action['expected_policy']={k:policy.get(k) for k in ('allow','deny','allow_enabled','deny_enabled')}
  plan={'id':secrets.token_hex(16),'action':action,'before':identity(current),'target':action.get('domain','Pi-hole filtering'),'scope':'All clients using this Pi-hole resolver; exact policies use the default Pi-hole group.','effect':{'enable':'Enable DNS filtering.','pause':'Temporarily pause DNS filtering; the native Pi-hole timer must restore it.','allow':'Store an exact allow exception.','deny':'Store an exact deny entry; conflicting allow exceptions must be removed explicitly.','remove_allow':'Remove this exact allow exception.','remove_deny':'Remove this exact deny entry.'}[action['action']],'recovery':'A pause is bounded to 30, 60 or 300 seconds by the native Pi-hole timer. Domain policy changes require an explicit inverse operation. WAN, DHCP and resolver forwarding are unchanged.','expires_at':time.time()+120}
  store(db)
  with db() as c:c.execute('INSERT INTO dns_plans VALUES(?,?,?,?,?,NULL)',(plan['id'],actor,time.time(),json.dumps(plan),'prepared'))
  return web.json_response(plan)
 if request.method=='POST' and path=='apply':
  data=await body(request);pid=str(data.get('plan_id',''));store(db)
  with db() as c:
   c.execute('BEGIN IMMEDIATE');row=c.execute('SELECT * FROM dns_plans WHERE id=? AND actor=?',(pid,actor)).fetchone()
   if not row:raise web.HTTPNotFound(text='DNS review plan not found')
   if row['result']:
    saved=json.loads(row['result']);return web.json_response(saved,status=200 if saved.get('state')=='verified' else 409 if saved.get('state')=='rejected' else 503)
   if row['state']!='prepared':raise web.HTTPConflict(text='Previous DNS request has uncertain completion; check current state before preparing another action')
   plan=json.loads(row['payload'])
   if plan['expires_at']<time.time():raise web.HTTPGone(text='DNS review has expired')
   c.execute('UPDATE dns_plans SET state=? WHERE id=?',('checking',pid))
  try:
   current=await remote(request,credential,'/v1/status?fresh=1')
   if identity(current)!=plan['before']:raise web.HTTPConflict(text='Pi-hole state changed after review. Prepare a new review.')
   audit(actor,'dns_pending',{'plan_id':pid,'operation':plan['action']['action'],'target':plan['target'],'completion':'pending'})
   result=await remote(request,credential,'/v1/actions',data=plan['action'])
   result.update(plan_id=pid,scope=plan['scope']);status_code=200
  except web.HTTPConflict as error:
   result={'plan_id':pid,'operation':plan['action']['action'],'target':plan['target'],'state':'rejected','action_executed':False,'error':error.text};status_code=409
  except (web.HTTPException,asyncio.TimeoutError,OSError,ValueError):
   result={'plan_id':pid,'operation':plan['action']['action'],'target':plan['target'],'state':'unknown','completion':'unknown','error':'DNS response could not be verified. Inspect current filtering and policy before retrying.'};status_code=503
  result['receipt_id']=audit(actor,'dns',result)
  with db() as c:c.execute('UPDATE dns_plans SET state=?,result=? WHERE id=?',(result.get('state','unknown'),json.dumps(result),pid))
  return web.json_response(result,status=status_code)
 raise web.HTTPNotFound(text='This Pi-hole capability is not connected')
