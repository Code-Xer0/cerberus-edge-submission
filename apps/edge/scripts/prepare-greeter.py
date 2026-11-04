#!/usr/bin/env python3
"""Apply branding to a captured Ragnar login page without changing its scripts."""
import hashlib
import re
import sys
from pathlib import Path

source = Path(sys.argv[1]).read_text(encoding="utf-8")
dest = Path(sys.argv[2])
scripts = re.findall(r"<script\b[^>]*>.*?</script>", source, flags=re.S | re.I)
changes = {
    "<title>Ragnar - Login</title>": "<title>Cerberus Edge — Sign in</title>",
    '<link rel="icon" href="/images/ragnar.ico" type="image/x-icon">':
        '<link rel="icon" href="/images/cerberus-edge-icon.png" type="image/png">\n    <link rel="apple-touch-icon" href="/images/cerberus-edge-icon.png">\n    <meta name="theme-color" content="#080b11">',
    "</head>": '    <link rel="stylesheet" href="/css/cerberus-login.css">\n</head>',
    'src="/images/ragnar.png" alt="Ragnar"': 'src="/images/cerberus-mark.png" alt="Cerberus three-headed hound"',
    '<h1 class="text-3xl font-bold text-white">Ragnar</h1>': '<h1 class="text-3xl font-bold text-white">Cerberus Edge</h1>',
    'Cyberviking Security Scanner': 'Hyperion Security · Secure Access',
    'This Ragnar instance is bound to different hardware': 'This Cerberus Edge instance is bound to different hardware',
    'Ragnar Cyberviking &mdash; Hardware-bound authentication': 'Cerberus Edge &mdash; Hardware-bound authentication',
}
result = source
for before, after in changes.items():
    if result.count(before) != 1:
        raise SystemExit("login template changed; refusing to generate: " + before[:50])
    result = result.replace(before, after, 1)
if re.findall(r"<script\b[^>]*>.*?</script>", result, flags=re.S | re.I) != scripts:
    raise SystemExit("authentication scripts changed unexpectedly")
dest.parent.mkdir(parents=True, exist_ok=True)
dest.write_text(result, encoding="utf-8")
print("source_sha256=" + hashlib.sha256(source.encode()).hexdigest())
print("greeter_sha256=" + hashlib.sha256(result.encode()).hexdigest())
print("authentication_scripts_unchanged=" + str(len(scripts)))
