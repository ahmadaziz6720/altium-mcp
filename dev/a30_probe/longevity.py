"""python longevity.py <seconds>: the resident bridge over minutes: the
heartbeat's largest gap (from its file time only, never opening it), a call
every 10 s, and a launched script now and then beside it."""
import os
import sys
import time

import probe_lib as P
import bridge_res

secs = float(sys.argv[1])
hb = bridge_res.HB
t0 = time.time()
gap, last_m, last_t = 0.0, None, time.time()
lat, launches, next_call, next_launch = [], 0, t0 + 1, t0 + 30
m0 = P.private_bytes()
while time.time() - t0 < secs:
    try:
        m = os.stat(hb).st_mtime
    except OSError:
        m = None
    now = time.time()
    if m != last_m:
        last_m, last_t = m, now
    gap = max(gap, now - last_t)
    if now >= next_call:
        dt, s = bridge_res.call()
        lat.append(dt)
        if dt is None:
            print("call TIMEOUT at", round(now - t0), P.dialogs())
        next_call = time.time() + 10
        last_t = time.time()  # the call itself is not a gap of the timer
    if now >= next_launch:
        out = P.X / "triv.txt"
        out.unlink(missing_ok=True)
        P.launch(P.X / "triv.pas")
        print("a launched script beside it:", P.wait_file(out, 20), "at", round(now - t0), "s")
        launches += 1
        next_launch = time.time() + 60
        last_t = time.time()
    time.sleep(0.2)
ok = [x for x in lat if x is not None]
ok.sort()
print(f"{secs:.0f} s: {len(ok)}/{len(lat)} calls served, median {ok[len(ok)//2]*1000:.0f} ms, "
      f"max {ok[-1]*1000:.0f} ms; largest heartbeat gap {gap:.2f} s; {launches} launches beside it; "
      f"private {m0/2**20:.1f} -> {P.private_bytes()/2**20:.1f} MB")
