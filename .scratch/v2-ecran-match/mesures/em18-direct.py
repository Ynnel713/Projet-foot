import json, time, urllib.request
B = "http://localhost:8000/api/v2"
req = urllib.request.Request(f"{B}/matches/start", data=json.dumps({"home": "RC Lens", "away": "Stade Brestois 29"}).encode(), headers={"Content-Type": "application/json"})
mid = json.load(urllib.request.urlopen(req))["id"]
ticks = ball = 0; events = []; t0 = time.time(); log = []
while time.time() - t0 < 40:
    r = json.load(urllib.request.urlopen(f"{B}/matches/{mid}?from_tick={ticks}&from_ball={ball}&from_event={len(events)}"))
    assert r["first_event"] == len(events)
    ticks += len(r["ticks"]); ball += len(r["ball_track"]); events += r["events"]
    log.append((round(time.time() - t0, 1), r["done"], ticks, len(events)))
    if r["done"]: break
    time.sleep(1)
ids = [e["id"] for e in events]
print("relevés (s, fini, images, événements):", log[:3], "...", log[-2:])
print("événements reçus avant la fin du calcul:", len(events), "| ids contigus:", ids == list(range(len(ids))),
      "| minute max:", round(max(e["minute"] for e in events), 2) if events else None,
      "| types:", sorted({e["kind"] for e in events}))
