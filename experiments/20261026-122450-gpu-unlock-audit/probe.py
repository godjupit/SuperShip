"""Read-only PCI applicability probe against a pinned gpu-unlock checkout."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

root = Path(sys.argv[1]).resolve()
source = root / "kernel/gpu_unlock/main.c"
raw = source.read_bytes()
match = re.search(r"supported_ids\[\]\s*=\s*\{(.*?)\};", raw.decode(), re.S)
if match is None:
    raise SystemExit("Cannot find upstream supported_ids; refusing to infer support")
body = re.sub(r"/\*.*?\*/", "", match.group(1), flags=re.S)
supported = {int(value, 16) for value in re.findall(r"0x[0-9a-fA-F]+", body)}
devices = []
for device in sorted(Path("/sys/bus/pci/devices").iterdir()):
    if int((device / "vendor").read_text(), 16) != 0x10de:
        continue
    device_id = int((device / "device").read_text(), 16)
    driver = device / "driver"
    devices.append({"bdf": device.name, "device_id": f"0x{device_id:04x}",
                    "class": (device / "class").read_text().strip(),
                    "supported": device_id in supported,
                    "driver": driver.resolve().name if driver.exists() else None})
print(json.dumps({"upstream_sha": subprocess.check_output(
    ["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip(),
    "source_sha256": hashlib.sha256(raw).hexdigest(),
    "rtx3090_2204_listed": 0x2204 in supported,
    "rtx4090_2684_listed": 0x2684 in supported,
    "devices": devices, "applicable_device_count": sum(d["supported"] for d in devices)},
    indent=2))
