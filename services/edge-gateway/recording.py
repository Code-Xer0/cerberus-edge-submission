"""Fixed presentation-only recording ingress. Authentication remains with Ragnar."""
from pathlib import Path
from aiohttp import web,ClientTimeout
ASSETS=Path(__file__).parent/'recording-assets'
ALLOWED={'login.css':'text/css','login.js':'application/javascript','login.ogg':'audio/ogg'}
def decorate_login(html):
 return html.replace('type="text" id="username"','type="password" id="username"',1).replace('</head>','<link rel="stylesheet" href="/recording-assets/login.css"><script src="/recording-assets/login.js" defer></script></head>',1)
async def entry(request):
 response=web.HTTPFound('/login?recording=1&operator=1');response.set_cookie('cerberus_recording','operator',path='/',secure=True,httponly=True,samesite='Lax');response.headers['Cache-Control']='no-store';return response
async def asset(request):
 name=request.match_info['name']
 if name not in ALLOWED:raise web.HTTPNotFound()
 return web.FileResponse(ASSETS/name,headers={'Content-Type':ALLOWED[name],'X-Content-Type-Options':'nosniff','Cache-Control':'no-store'})
async def intercept(request,ragnar):
 mode=request.cookies.get('cerberus_recording');operator=mode=='operator' or request.query.get('operator')=='1';enabled=mode in ('1','operator')
 if request.method=='GET' and request.path=='/' and enabled:raise web.HTTPFound('/web/cerberus-edge-v3/index.html?operator=1#home' if operator else '/web/cerberus-edge-v3/index.html#recording/overview')
 if request.method=='GET' and request.path=='/login' and (enabled or request.query.get('recording')=='1'):
  async with request.app['client'].get(ragnar+'/login',headers={'Cookie':request.headers.get('Cookie',''),'Accept-Encoding':'identity'},allow_redirects=False,timeout=ClientTimeout(total=15)) as source:
   if source.status!=200:return None
   raw=await source.read()
   if len(raw)>300000:raise web.HTTPBadGateway(text='Login presentation unavailable')
   response=web.Response(text=decorate_login(raw.decode('utf-8')),content_type='text/html',headers={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'})
   for name in ('Content-Security-Policy','X-Frame-Options','Referrer-Policy','Permissions-Policy'):
    if name in source.headers:response.headers[name]=source.headers[name]
   for value in source.headers.getall('Set-Cookie',[]):response.headers.add('Set-Cookie',value)
   response.set_cookie('cerberus_recording','operator' if operator else '1',path='/',secure=True,httponly=True,samesite='Lax');return response
 return None
