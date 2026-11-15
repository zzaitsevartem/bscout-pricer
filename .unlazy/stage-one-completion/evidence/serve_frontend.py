import json
import os
import socket
import subprocess
from pathlib import Path
root=Path.cwd()
path=root/'.unlazy/stage-one-completion/evidence/runtime.json'
runtime=json.loads(path.read_text())
with socket.socket() as sock:
    sock.bind(('127.0.0.1', 0))
    port=sock.getsockname()[1]
runtime['frontend_port']=port
path.write_text(json.dumps(runtime))
env=os.environ.copy()
env['BACKEND_URL']=f"http://127.0.0.1:{runtime['backend_port']}"
raise SystemExit(subprocess.run(['npm','run','dev','--','--hostname','127.0.0.1','--port',str(port)],
                               cwd='/private/tmp/bscout-develop-one-frontend', env=env).returncode)
