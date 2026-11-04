#!/usr/bin/env python3
"""Create a private source-only review candidate. Never publishes or copies assets/secrets."""
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
root=Path(__file__).resolve().parents[1]
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
target=root.parents[2]/'staging'/('cerberus-edge-source-candidate-'+stamp)
target.mkdir(parents=True,exist_ok=False)
paths=['src/app','src/components','src/features','src/lib','src/screens','src/edge-v3.tsx','src/edge-v3.css','tests','scripts/test-contracts.mjs','scripts/cerberus-edge-refresh.py','electron','package.json','package-lock.json','tsconfig.json','vite.config.ts','index.html']
for name in paths:
 source=root/name
 if source.is_dir():shutil.copytree(source,target/name,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
 else:(target/name).parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target/name)
(target/'public-v3/notices').mkdir(parents=True)
shutil.copy2(root/'public-v3/notices/RAGNAR-LICENSE.txt',target/'public-v3/notices/RAGNAR-LICENSE.txt')
shutil.copy2(root/'public-v3/manifest.webmanifest',target/'public-v3/manifest.webmanifest')
(target/'.gitignore').write_text('node_modules/\ndist/\nrelease/\n.cache/\npublic/assets/\npublic-v3/assets/\nbuild/icons/\n.env*\n')
(target/'README.md').write_text('''# Cerberus Edge — private source review candidate

Not published. Existing proprietary Cerberus application source is excluded. This candidate contains the new React Edge implementation and its read-only host snapshot producer. Ragnar remains a separately installed, attributed upstream runtime; its installed license is retained in notices. No distribution permission or contest eligibility is asserted.

## Reproduce

Use the locked npm dependencies (`npm ci`), then `npm run test:contracts` and `npm run build`. The visual build requires an independently approved asset overlay, intentionally excluded from this candidate:

- `public/assets/{rajdhani-regular.ttf,rajdhani-semibold.ttf,orbitron.ttf}`
- `public-v3/assets/{cerberus-mark.png,cerberus-edge-icon.png,land-110m.json}`
- `public-v3/assets/pack/{argus.svg,vesper.svg,bastion.svg}`
- `public-v3/notices/ragnar-viking.png`
- Electron packaging additionally needs the approved `build/icons/` overlay.

Without that overlay, this is an incomplete visual build input and must not be represented as a reproducible public release. The original private workspace has the overlay and has passed its build. Resolve asset rights and upstream terms before publication. Choose an explicit license for new Edge code before any public release; no license is invented here.

The adapter and Meta provider belong to the Muse team and are not included. Runtime URLs and capability gaps are documented in the main private handoff. No API keys, private deployment state, raw telemetry, mockup archive, or existing Cerberus source is copied.
''')
enforcer=root.parents[1]/'services/edge-enforcer'
(target/'host-enforcer').mkdir()
for name in ['enforcer.py','config.example.json','cerberus-enforcer.service','README.md','test_enforcer.py','test_netns.py']:
 shutil.copy2(enforcer/name,target/'host-enforcer'/name)
shutil.copytree(root.parents[1]/'services/edge-state',target/'state-contract',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
shutil.copytree(root.parents[1]/'schemas',target/'schemas')
manifest={str(p.relative_to(target)):hashlib.sha256(p.read_bytes()).hexdigest() for p in target.rglob('*') if p.is_file()}
(target/'SOURCE-MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
subprocess.run(['git','init','-q',str(target)],check=True)
print(target)
print('Files:',len(manifest),'Asset publication and source licensing gates remain open. No remote configured.')
