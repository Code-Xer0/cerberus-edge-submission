"""Root-owned fixed context publisher; never accepts browser commands or credentials."""
import json,os,subprocess,urllib.request
from pathlib import Path
snapshot=json.loads(Path('/opt/cerberus-edge/edge-status.json').read_text())
result=subprocess.run(['/usr/bin/docker','exec','ragnar','cat','/opt/ragnar/web/cerberus-edge/reporting.v1.json'],capture_output=True,check=True,timeout=10)
report=json.loads(result.stdout);report['events']=report.get('events',[])[:50]
token=(Path(os.environ['CREDENTIALS_DIRECTORY'])/'edge-internal').read_text().strip()
request=urllib.request.Request('http://127.0.0.1:8766/api/internal/edge-context',data=json.dumps({'snapshot':snapshot,'report':report}).encode(),headers={'Content-Type':'application/json','X-Cerberus-Internal':token})
with urllib.request.urlopen(request,timeout=15) as response:print(json.dumps({'context':'accepted','status':response.status}))
