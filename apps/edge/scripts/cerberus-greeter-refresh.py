#!/usr/bin/env python3
"""Restore known Cerberus greeter assets without overwriting an unknown login."""
import hashlib
import subprocess
from pathlib import Path

ROOT = Path("/opt/cerberus-edge/login-brand-20261103")
TARGET = "/opt/ragnar/web"
ORIGINAL = "f8c5a65486b1a8631ccd850d9818deacd4a04d3f612ea41ace3318f0536bed7b"
FILES = ("css/cerberus-login.css", "images/cerberus-mark.png",
         "images/cerberus-edge-icon.png", "fonts/cerberus-rajdhani.ttf",
         "fonts/cerberus-orbitron.ttf")


def run(*args):
    return subprocess.run(args, capture_output=True, text=True, timeout=15, check=True)


def remote_hash(path):
    try:
        return run("docker", "exec", "ragnar", "sha256sum", path).stdout.split()[0]
    except subprocess.CalledProcessError:
        return None


def local_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    login = ROOT / "login.html"
    desired = local_hash(login)
    current = remote_hash(TARGET + "/login.html")
    if current not in (ORIGINAL, desired):
        raise SystemExit("login template differs from known versions; refusing to overwrite")
    run("docker", "exec", "ragnar", "mkdir", "-p", TARGET+"/css", TARGET+"/images", TARGET+"/fonts")
    if current == ORIGINAL:
        backup = TARGET + "/login.pre-cerberus-20261103.html"
        if remote_hash(backup) is None:
            run("docker", "exec", "ragnar", "cp", TARGET+"/login.html", backup)
    for relative in FILES:
        source = ROOT / relative
        if remote_hash(TARGET+"/"+relative) != local_hash(source):
            run("docker", "cp", str(source), "ragnar:"+TARGET+"/"+relative)
    if current != desired:
        run("docker", "cp", str(login), "ragnar:"+TARGET+"/login.html")


if __name__ == "__main__":
    main()
