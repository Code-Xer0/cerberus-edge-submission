import importlib.util,os,tempfile,unittest
from unittest.mock import patch
from pathlib import Path
from aiohttp import web
from aiohttp.test_utils import TestServer,TestClient
import gateway
class GatewayTests(unittest.IsolatedAsyncioTestCase):
 async def asyncSetUp(self):
  self.tmp=tempfile.TemporaryDirectory();gateway.ROOT=Path(self.tmp.name);gateway.ORIGIN='https://edge.invalid';gateway.COOKIE_NAME='session';self.calls=[]
  async def source(request):
   if request.path=='/login':return web.Response(text='<html><head></head><body><script>originalAuth();</script><form id="login-form"></form></body></html>',content_type='text/html')
   if request.path=='/redirect':raise web.HTTPFound('/login')
   if request.path=='/cookies':
    response=web.Response(text='ok');response.set_cookie('one','a');response.set_cookie('two','b');return response
   if request.path=='/api/auth/status':return web.json_response({'configured':True,'authenticated':request.headers.get('Cookie')==gateway.COOKIE_NAME+'=valid'})
   return web.json_response({'upstream':request.path})
  app=web.Application();app.router.add_route('*','/{path:.*}',source);self.source=TestServer(app);await self.source.start_server();gateway.RAGNAR=str(self.source.make_url('')).rstrip('/');self.client=TestClient(TestServer(gateway.create_app()));await self.client.start_server()
  async def agent(request):
   if request.path=='/api/insights':return web.json_response({'context_available':True,'insights':[{'id':'a'*32,'title':'Observed endpoint 192.0.2.1','facts':['192.0.2.1 changed'], 'hypotheses':[], 'observed_at':'2026-11-04T00:00:00Z'}]})
   self.calls.append(await request.json());return web.json_response({'id':'thread-test','messages':[]})
  backend=web.Application();backend.router.add_route('*','/{path:.*}',agent);self.backend=TestServer(backend);await self.backend.start_server();gateway.AGENT=str(self.backend.make_url('')).rstrip('/')
  self.credentials=tempfile.TemporaryDirectory();self.previous=os.environ.get('CREDENTIALS_DIRECTORY');os.environ['CREDENTIALS_DIRECTORY']=self.credentials.name
 async def asyncTearDown(self):
  await self.client.close();await self.source.close();await self.backend.close();self.tmp.cleanup();self.credentials.cleanup()
  if self.previous is None:os.environ.pop('CREDENTIALS_DIRECTORY',None)
  else:os.environ['CREDENTIALS_DIRECTORY']=self.previous
 async def test_recording_ingress_is_opt_in_and_preserves_auth_script(self):
  response=await self.client.get('/recording',allow_redirects=False);self.assertEqual(response.status,302);self.assertEqual(response.headers['Location'],'/login?recording=1&operator=1');self.assertIn('cerberus_recording=operator',response.headers['Set-Cookie'])
  response=await self.client.get('/',headers={'Cookie':'cerberus_recording=1'},allow_redirects=False);self.assertEqual(response.status,302);self.assertEqual(response.headers['Location'],'/web/cerberus-edge-v3/index.html#recording/overview')
  response=await self.client.get('/',headers={'Cookie':'cerberus_recording=operator'},allow_redirects=False);self.assertEqual(response.headers['Location'],'/web/cerberus-edge-v3/index.html?operator=1#home')
  response=await self.client.get('/');self.assertEqual(response.status,200);self.assertEqual((await response.json())['upstream'],'/')
  response=await self.client.get('/login?recording=1');text=await response.text();self.assertIn('<script>originalAuth();</script>',text);self.assertIn('/recording-assets/login.js',text)
  response=await self.client.get('/recording-assets/login.js');self.assertEqual(response.status,200)
  response=await self.client.get('/recording-assets/gateway.py');self.assertEqual(response.status,404)
 async def test_refreshed_cookie_keeps_review_but_a_new_login_does_not(self):
  import base64,json
  original=gateway.upstream
  async def validated(app,path,**kwargs):
   if path=='/api/auth/status':return {'configured':True,'authenticated':True}
   return await original(app,path,**kwargs)
  def cookie(stamp,login=123):
   payload=base64.urlsafe_b64encode(json.dumps({'username':'operator','authenticated':True,'login_time':login,'last_activity':stamp}).encode()).decode().rstrip('=');return 'session='+payload+'.'+stamp+'.signature'
  with patch.object(gateway,'upstream',side_effect=validated):
   session=await (await self.client.get('/api/edge/session',headers={'Cookie':cookie('old')})).json()
   headers={'Cookie':cookie('refreshed'),'Origin':gateway.ORIGIN,'X-Cerberus-CSRF':session['csrf']}
   response=await self.client.post('/api/edge/session/end',headers=headers,json={});self.assertEqual(response.status,200)
   headers['Cookie']=cookie('other',login=456)
   self.assertEqual((await self.client.post('/api/edge/session/end',headers=headers,json={})).status,403)
 async def test_session_end_requires_authentication_and_csrf(self):
  self.assertEqual((await self.client.post('/api/edge/session/end',json={})).status,401)
  self.assertEqual((await self.client.post('/api/edge/session/end',headers={'Cookie':'session=valid'},json={})).status,403)
 async def test_terminal_history_pagination_params_reach_agent(self):
  self.seen_paths=[]
  async def spy(request):
   self.seen_paths.append(request.rel_url.raw_path_qs)
   return web.json_response({'thread_id':'thread-x','messages':[],'has_more':False,'limit':3})
  spy_app=web.Application();spy_app.router.add_route('*','/{path:.*}',spy)
  spy_server=TestServer(spy_app);await spy_server.start_server()
  previous=gateway.AGENT;gateway.AGENT=str(spy_server.make_url('')).rstrip('/')
  try:
   headers=await self.headers()
   response=await self.client.get('/api/edge/terminal/threads/thread-abc?before=42&limit=3',headers=headers)
   self.assertEqual(response.status,200)
   self.assertTrue(any('before=42' in p and 'limit=3' in p for p in self.seen_paths),self.seen_paths)
  finally:gateway.AGENT=previous;await spy_server.close()
 async def test_session_end_clears_gateway_csrf_and_audits_without_touching_ragnar(self):
  headers=await self.headers()
  first=await self.client.get('/api/edge/session',headers={'Cookie':'session=valid'});token=(await first.json())['csrf']
  self.assertTrue(any(entry[0]==token for entry in self.client.server.app['csrf'].values()))
  response=await self.client.post('/api/edge/session/end',headers=headers,json={})
  self.assertEqual(response.status,200);payload=await response.json()
  self.assertIn('Max-Age=0',response.headers['Set-Cookie']);self.assertIn('session=',response.headers['Set-Cookie']);self.assertIn('HttpOnly',response.headers['Set-Cookie']);self.assertTrue(payload.get('session_ended'));self.assertEqual(payload.get('ragnar_logout'),False)
  self.assertEqual(self.client.server.app['csrf'],{})
  with gateway.db() as c:row=c.execute("SELECT * FROM audit WHERE kind='session_end'").fetchone()
  self.assertIsNotNone(row)
  gateway.COOKIE_NAME='ragnar_session_testnode';response=await self.client.get('/api/edge/session',headers={'Cookie':'ragnar_session_testnode=valid'});self.assertEqual(response.status,200)
 async def test_unknown_and_unauthorized_routes_are_not_general_endpoint_proxy(self):
  self.assertEqual((await self.client.get('/api/edge/session')).status,401)
  self.assertEqual((await self.client.get('/api/edge/settings',headers={'Cookie':'session=valid'})).status,404)
 async def test_mutations_require_same_origin_and_session_bound_token(self):
  result=await self.client.get('/api/edge/session',headers={'Cookie':'session=valid'});session=await result.json();headers={'Cookie':'session=valid','X-Cerberus-CSRF':session['csrf'],'Origin':'https://wrong.invalid'}
  self.assertEqual((await self.client.post('/api/edge/terminal/messages',headers=headers,json={'body':'hi'})).status,403)
  headers['Origin']=gateway.ORIGIN;headers['Cookie']='session=invalid';self.assertEqual((await self.client.post('/api/edge/terminal/messages',headers=headers,json={'body':'hi'})).status,401)
 async def test_proxy_preserves_redirect_and_multiple_cookies(self):
  response=await self.client.get('/redirect',allow_redirects=False);self.assertEqual(response.status,302);self.assertEqual(response.headers['Location'],'/login');cookies=await self.client.get('/cookies');self.assertEqual(len(cookies.headers.getall('Set-Cookie')),2)
 async def headers(self):
  session=await (await self.client.get('/api/edge/session',headers={'Cookie':'session=valid'})).json();return {'Cookie':'session=valid','Origin':gateway.ORIGIN,'X-Cerberus-CSRF':session['csrf']}
 async def test_actor_is_derived_and_cannot_be_supplied_by_browser(self):
  headers=await self.headers();response=await self.client.post('/api/edge/terminal/messages',headers=headers,json={'body':'hello','author':'forged-admin'});self.assertEqual(response.status,200);self.assertTrue(self.calls[-1]['author'].startswith('session:'));self.assertNotEqual(self.calls[-1]['author'],'forged-admin')
 async def test_model_missing_key_never_calls_provider(self):
  headers=await self.headers();preview=await (await self.client.post('/api/edge/insights/explain/preview',headers=headers,json={'provider':'meta'})).json();self.assertNotIn('192.0.2.1',preview['evidence']);self.assertFalse(preview['configured']);response=await self.client.post('/api/edge/insights/explain',headers=headers,json={'preview_id':preview['preview_id']});self.assertEqual(response.status,503)
 async def test_completed_model_call_replays_receipt_without_second_charge(self):
  Path(self.credentials.name,'meta-key').write_text('unit-test-only')
  headers=await self.headers();preview=await (await self.client.post('/api/edge/insights/explain/preview',headers=headers,json={'provider':'meta'})).json()
  class Response:
   status=200
   async def __aenter__(self):return self
   async def __aexit__(self,*args):pass
   async def json(self):return {'status':'completed','id':'test-response','output':[{'type':'message','content':[{'type':'output_text','text':'An observed change needs verification.'}]}],'usage':{'input_tokens':10,'output_tokens':10}}
  with patch.object(self.client.server.app['client'],'post',return_value=Response()) as call:
   first=await self.client.post('/api/edge/insights/explain',headers=headers,json={'preview_id':preview['preview_id']});second=await self.client.post('/api/edge/insights/explain',headers=headers,json={'preview_id':preview['preview_id']});self.assertEqual(first.status,200);self.assertEqual((await first.json())['receipt_id'],(await second.json())['receipt_id']);self.assertEqual(call.call_count,1)
 async def test_failed_provider_is_recorded_and_not_retried_or_substituted(self):
  Path(self.credentials.name,'meta-key').write_text('unit-test-only')
  headers=await self.headers();preview=await (await self.client.post('/api/edge/insights/explain/preview',headers=headers,json={'provider':'meta'})).json()
  class Response:
   status=402
   async def __aenter__(self):return self
   async def __aexit__(self,*args):pass
  with patch.object(self.client.server.app['client'],'post',return_value=Response()) as call:
   first=await self.client.post('/api/edge/insights/explain',headers=headers,json={'preview_id':preview['preview_id']});result=await first.json()
   second=await self.client.post('/api/edge/insights/explain',headers=headers,json={'preview_id':preview['preview_id']})
   self.assertEqual(first.status,502);self.assertEqual(second.status,502);self.assertEqual(result['provider'],'meta');self.assertEqual(result['status'],'failed');self.assertIn('402',result['error']);self.assertEqual(call.call_count,1)
   receipt=await self.client.get('/api/edge/receipts/'+str(result['receipt_id']),headers=headers);self.assertEqual(receipt.status,200);self.assertEqual((await receipt.json())['payload']['status'],'failed');self.assertEqual(receipt.headers['Cache-Control'],'no-store')
 async def test_incomplete_model_output_does_not_become_a_success(self):
  Path(self.credentials.name,'meta-key').write_text('unit-test-only');headers=await self.headers();preview=await (await self.client.post('/api/edge/insights/explain/preview',headers=headers,json={'provider':'meta'})).json()
  class Response:
   status=200
   async def __aenter__(self):return self
   async def __aexit__(self,*args):pass
   async def json(self):return {'status':'incomplete','output':[{'type':'message','content':[{'type':'output_text','text':'Partial answer'}]}]}
  with patch.object(self.client.server.app['client'],'post',return_value=Response()):
   response=await self.client.post('/api/edge/insights/explain',headers=headers,json={'preview_id':preview['preview_id']});result=await response.json();self.assertEqual(response.status,502);self.assertNotIn('explanation',result);self.assertIn('incomplete',result['error'])
 async def test_receipts_are_account_scoped(self):
  gateway.audit('other-account','explanation',{'explanation':'Private text'})
  headers=await self.headers();self.assertEqual((await self.client.get('/api/edge/receipts/1',headers=headers)).status,404)
 async def test_lost_capture_response_is_persisted_as_unknown_and_never_retried(self):
  headers=await self.headers();original=gateway.upstream;writes=[]
  async def capture_source(app,path,**kwargs):
   if path=='/api/traffic/status':return {'summary':{'status':'running','interface':'ap-test'}}
   if path=='/api/traffic/stop':writes.append(path);raise TimeoutError()
   return await original(app,path,**kwargs)
  with patch.object(gateway,'upstream',side_effect=capture_source):
   response=await self.client.post('/api/edge/capture/stop',headers=headers,json={});result=await response.json()
  self.assertEqual(response.status,503);self.assertEqual(result['state'],'unknown');self.assertEqual(writes,['/api/traffic/stop'])
  saved=await (await self.client.get('/api/edge/receipts/'+str(result['receipt_id']),headers=headers)).json();self.assertEqual(saved['payload']['target'],'ap-test');self.assertEqual(saved['payload']['completion'],'unknown')
 async def test_pihole_read_is_authenticated_and_unconfigured_is_explicit(self):
  self.assertEqual((await self.client.get('/api/edge/plugins/pihole/status')).status,401)
  response=await self.client.get('/api/edge/plugins/pihole/status',headers=await self.headers());value=await response.json();self.assertEqual(value['state'],'unconfigured');self.assertFalse(value['capabilities']['pause'])
 async def test_dns_apply_replays_a_durable_receipt_without_repeating_the_command(self):
  import pihole_plugin
  headers=await self.headers();calls=[]
  async def source(request,credential,path,**kwargs):
   calls.append(path)
   if path=='/v1/actions':return {'state':'verified','operation':'pause','target':'Pi-hole filtering','blocking':False,'timer_seconds':60}
   return {'provider':'Pi-hole v6','blocking':True}
  with patch.object(pihole_plugin,'remote',side_effect=source):
   review=await self.client.post('/api/edge/plugins/pihole/review',headers=headers,json={'action':'pause','seconds':60});plan=await review.json();self.assertEqual(review.status,200)
   first=await self.client.post('/api/edge/plugins/pihole/apply',headers=headers,json={'plan_id':plan['id']});second=await self.client.post('/api/edge/plugins/pihole/apply',headers=headers,json={'plan_id':plan['id']});a=await first.json();b=await second.json();self.assertEqual(first.status,200);self.assertEqual(a['receipt_id'],b['receipt_id']);self.assertEqual(calls.count('/v1/actions'),1)
 async def test_dns_unknown_completion_is_recorded_and_not_retried(self):
  import pihole_plugin
  headers=await self.headers();calls=[]
  async def source(request,credential,path,**kwargs):
   if path=='/v1/actions':calls.append(path);raise TimeoutError()
   return {'provider':'Pi-hole v6','blocking':True}
  with patch.object(pihole_plugin,'remote',side_effect=source):
   plan=await (await self.client.post('/api/edge/plugins/pihole/review',headers=headers,json={'action':'pause','seconds':60})).json();first=await self.client.post('/api/edge/plugins/pihole/apply',headers=headers,json={'plan_id':plan['id']});value=await first.json();self.assertEqual(first.status,503);self.assertEqual(value['state'],'unknown');await self.client.post('/api/edge/plugins/pihole/apply',headers=headers,json={'plan_id':plan['id']});self.assertEqual(len(calls),1)
 def test_redaction_removes_addresses_and_secrets(self):
  text=gateway.redact({'fact':'host 192.168.0.2 at 02:aa:bb:cc:dd:ee token=secret-value'});self.assertNotIn('192.168.0.2',text);self.assertNotIn('02:aa',text);self.assertNotIn('secret-value',text)
 async def test_radio_proxies_voiced_feed_events(self):
  async def radio_backend(request):
   if request.path=='/api/pack/radio':return web.json_response({'events':[{'hk':'vesper','tag':'HIGH · SOURCE LABEL','txt':'Sign: test device.','t':'2026-11-04T00:00:00Z'}],'count':1})
   if request.path=='/api/auth/status':return web.json_response({'configured':True,'authenticated':True})
   return web.json_response({'upstream':request.path})
  radio_app=web.Application();radio_app.router.add_route('*','/{path:.*}',radio_backend)
  radio_server=TestServer(radio_app);await radio_server.start_server()
  previous=gateway.AGENT;gateway.AGENT=str(radio_server.make_url('')).rstrip('/')
  try:
   headers=await self.headers()
   response=await self.client.get('/api/edge/radio',headers=headers)
   self.assertEqual(response.status,200);body=await response.json()
   self.assertEqual(len(body['events']),1);self.assertEqual(body['events'][0]['hk'],'vesper')
  finally:gateway.AGENT=previous;await radio_server.close()
 async def test_radio_refresh_is_a_reviewed_post_not_a_get(self):
  async def radio_backend(request):
   if request.path=='/api/pack/radio/refresh' and request.method=='POST':return web.json_response({'events':[{'hk':'argus','txt':'Live line.'}],'count':1,'voiced':'model'})
   if request.path=='/api/auth/status':return web.json_response({'configured':True,'authenticated':True})
   return web.json_response({'upstream':request.path})
  radio_app=web.Application();radio_app.router.add_route('*','/{path:.*}',radio_backend)
  radio_server=TestServer(radio_app);await radio_server.start_server()
  previous=gateway.AGENT;gateway.AGENT=str(radio_server.make_url('')).rstrip('/')
  try:
   headers=await self.headers()
   get_response=await self.client.get('/api/edge/radio/refresh',headers=headers)
   self.assertEqual(get_response.status,404)
   post_response=await self.client.post('/api/edge/radio/refresh',headers=headers,json={})
   self.assertEqual(post_response.status,200);body=await post_response.json()
   self.assertEqual(body.get('voiced'),'model')
  finally:gateway.AGENT=previous;await radio_server.close()
if __name__=='__main__':unittest.main()
