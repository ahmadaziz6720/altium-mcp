"""python bridge_res.py start | calls <n> | stop

The bridge's own units (from this checkout) plus a form unit whose timer runs
the bridge's Run whenever request.json is there, as one script project,
launched once with ScriptingSystem:RunScript."""
import json
import shutil
import subprocess
import sys
import time
import uuid

import probe_lib as P

EX = P.Path(r"C:\Users\Public\altium_mcp")
REQ, RESP = EX / "request.json", EX / "response.json"
HB = P.X / "bridge_hb.txt"
SRC = P.SERVER / "AltiumScript"


def hb():
    return P.read(HB).strip() if HB.exists() else ""


def start():
    for f in (P.X / "stop.txt", HB):
        f.unlink(missing_ok=True)
    folder = P.X / f"bridge_{int(time.time() * 1000) % 10**8}"
    folder.mkdir()
    units = [p.name for p in sorted(SRC.glob("*.pas"))]
    for u in units:
        shutil.copy(SRC / u, folder / u)
    for ext in (".pas", ".dfm"):
        (folder / ("A30Bridge" + ext)).write_text((P.HERE / ("A30Bridge" + ext)).read_text(),
                                                  encoding="latin-1", newline="\r\n")
    docs = units + ["A30Bridge.pas"]
    text = "[Design]\nVersion=1.0\n\n" + "".join(
        f"[Document{i + 1}]\nDocumentPath={d}\n\n" for i, d in enumerate(docs))
    prj = folder / "A30Bridge.PrjScr"
    prj.write_text(text, encoding="latin-1", newline="\r\n")
    m0, h0 = P.private_bytes(), P.handles()
    t = time.perf_counter()
    subprocess.Popen(f'"{P.ALTIUM}" -RScriptingSystem:RunScript(ProjectName="{prj}"^|'
                     f'ProcName="A30Bridge>StartResident")', shell=True)
    ok = P.wait_file(HB, 60)
    took = time.perf_counter() - t
    time.sleep(2)
    m1, h1 = P.private_bytes(), P.handles()
    print("started" if ok else "NOT STARTED", f"{took:.2f} s", hb(), P.dialogs())
    print(f"the launch: private {m0/2**20:.1f} -> {m1/2**20:.1f} MB, GDI/USER {h0} -> {h1}")


def call(command="a30_noop", timeout=20.0, **params):
    RESP.unlink(missing_ok=True)
    rid = uuid.uuid4().hex[:12]
    t = time.perf_counter()
    REQ.write_text(json.dumps({"command": command, "request_id": rid, **params}, indent=2))
    while time.perf_counter() - t < timeout:
        if RESP.exists():
            s = P.read(RESP)
            try:
                if json.loads(s, strict=False).get("request_id") == rid:
                    return time.perf_counter() - t, s
            except ValueError:
                pass
        time.sleep(0.005)
    return None, None


if __name__ == "__main__":
    what = sys.argv[1]
    if what == "start":
        start()
    elif what == "stop":
        (P.X / "stop.txt").write_text("x")
        time.sleep(1.5)
        print(hb())
    elif what == "calls":
        n = int(sys.argv[2])
        command = sys.argv[3] if len(sys.argv) > 3 else "a30_noop"
        time.sleep(1)
        m0, h0 = P.private_bytes(), P.handles()
        lat = []
        for i in range(n):
            dt, s = call(command)
            if dt is None:
                print("call", i, "TIMEOUT", P.dialogs(), hb())
                break
            lat.append(dt)
            if i == 0:
                print("reply:", " ".join(s.split())[:200])
        time.sleep(3)
        m1, h1 = P.private_bytes(), P.handles()
        lat.sort()
        if lat:
            print(f"{len(lat)} calls: median {lat[len(lat)//2]*1000:.0f} ms, max {lat[-1]*1000:.0f} ms")
        print(f"private {m0/2**20:.1f} -> {m1/2**20:.1f} MB "
              f"({(m1 - m0) / 2**20 / max(1, len(lat)):.2f} MB per call); GDI/USER {h0} -> {h1}")
        print("heartbeat:", hb())
