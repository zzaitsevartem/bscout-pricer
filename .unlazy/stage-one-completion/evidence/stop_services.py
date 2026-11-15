import json
import subprocess
from pathlib import Path

services = json.loads(Path("services.json").read_text())
for service in services:
    result = subprocess.run(
        ["docker", "rm", "-f", service["id"]], capture_output=True, text=True
    )
    print(f"{service['service']}: removed={result.returncode == 0}")
    if result.returncode:
        raise SystemExit(result.returncode)
