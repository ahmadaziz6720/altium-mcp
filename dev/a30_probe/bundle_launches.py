"""python bundle_launches.py <n>: n launches of the bridge's own bundle (built
from this checkout into the probe folder), each with a request of an unknown
command, as a call reaches Altium now: private bytes, handles, time per call."""
import json
import sys
import time
import uuid

import probe_lib as P
import script_bundle

n = int(sys.argv[1])
EX = P.Path(r"C:\Users\Public\altium_mcp")
REQ, RESP = EX / "request.json", EX / "response.json"
bundle = script_bundle.ensure_bundle(P.SERVER / "AltiumScript" / "Altium_API.PrjScr",
                                     P.X / "bundle", keep=1)
print("bundle:", bundle, bundle.stat().st_size)
time.sleep(2)
m0, h0 = P.private_bytes(), P.handles()
times, started = [], []
for i in range(n):
    RESP.unlink(missing_ok=True)
    rid = uuid.uuid4().hex[:12]
    REQ.write_text(json.dumps({"command": "a30_noop", "request_id": rid}, indent=2))
    t = P.launch(bundle)
    while REQ.exists() and time.perf_counter() - t < 20:
        time.sleep(0.01)
    started.append(time.perf_counter() - t)
    if not P.wait_file(RESP, 20):
        print("call", i, "TIMEOUT", [(d.cls, d.title, d.text[:60]) for d in P.dialogs()])
        break
    times.append(time.perf_counter() - t)
    if i == 0:
        print("reply:", P.read(RESP)[:160])
    if i in (9, 19):
        print(f"after {i + 1}: private {P.private_bytes() / 2**20:.1f} MB, GDI/USER {P.handles()}")
time.sleep(3)
m1, h1 = P.private_bytes(), P.handles()
times.sort(); started.sort()
print(f"{len(times)} calls: request taken after median {started[len(started)//2]:.2f} s, "
      f"reply after median {times[len(times)//2]:.2f} s, max {times[-1]:.2f} s")
print(f"private bytes {m0/2**20:.1f} -> {m1/2**20:.1f} MB "
      f"({(m1 - m0) / 2**20 / max(1, len(times)):.2f} MB per call); GDI/USER {h0} -> {h1}")
RESP.unlink(missing_ok=True)
