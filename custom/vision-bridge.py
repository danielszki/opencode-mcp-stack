#!/usr/bin/env python3
"""Ponte de framing para o servidor opencode-vision.

O opencode fala JSON-RPC newline-delimited por stdio; o servidor opencode-vision
usa framing Content-Length. Este processo encaminha newline -> CL na entrada e
CL -> newline na saida, para que ambos se entendam.
"""
import json
import subprocess
import sys

CHILD = [
    "/home/mint/.local/share/venv-mcp/bin/python",
    "/home/mint/.config/opencode/vision-launcher.py",
]

child = subprocess.Popen(CHILD, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=open("/home/mint/opencode/.vision-child.log", "ab"), bufsize=0)
out = child.stdout


def write_cl(obj):
    data = json.dumps(obj).encode("utf-8")
    child.stdin.write(b"Content-Length: %d\r\n\r\n" % len(data) + data)
    child.stdin.flush()


def read_cl():
    headers = b""
    while b"\r\n\r\n" not in headers:
        b = out.read(1)
        if not b:
            raise EOFError
        headers += b
    n = 0
    for line in headers.split(b"\r\n"):
        if line.lower().startswith(b"content-length"):
            n = int(line.split(b":")[1])
    body = b""
    while len(body) < n:
        chunk = out.read(n - len(body))
        if not chunk:
            raise EOFError
        body += chunk
    return json.loads(body)


while True:
    line = sys.stdin.buffer.readline()
    if not line:
        break
    line = line.strip()
    if not line:
        continue
    obj = json.loads(line)
    write_cl(obj)
    if obj.get("id") is not None:
        try:
            resp = read_cl()
        except (EOFError, json.JSONDecodeError):
            break
        if obj.get("method") == "initialize":
            req_ver = obj.get("params", {}).get("protocolVersion")
            if req_ver:
                resp.setdefault("result", {})["protocolVersion"] = req_ver
        sys.stdout.buffer.write(json.dumps(resp).encode("utf-8") + b"\n")
        sys.stdout.buffer.flush()

child.terminate()