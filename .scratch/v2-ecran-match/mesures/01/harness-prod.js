// Banc EM-01 sur build de production : sert la trace enregistrée (/__fx/<nom>.json) à la place de l'API par
// interception de fetch, ouvre /v2, lance le match.
//   mode "log" : horloge synthétique (pas de 50 ms), journal des changements visibles + empreinte cumulée du DOM ;
//   mode "fps" : horloge réelle, x8, durées entre images pendant `seconds` secondes.
async function __bench(name, mode, seconds = 20) {
  const fx = await (await fetch(`/__fx/${name}.json`)).json();
  const { lineups, ...live } = fx;
  const realFetch = window.__realFetch || (window.__realFetch = window.fetch);
  const json = (o) => new Response(JSON.stringify(o), { status: 200, headers: { "Content-Type": "application/json" } });
  window.fetch = async (url, opts) => {
    const u = String(url);
    if (u.includes("/api/perso/clubs") || u.includes("/clubs")) return json([{ name: live.home }, { name: live.away }]);
    if (u.includes("/api/v2/matches/start")) return json({ id: "fx" });
    if (u.includes("/api/v2/lineup")) return json(decodeURIComponent(u.split("club=")[1]) === live.home ? lineups.home : lineups.away);
    if (u.includes("/api/v2/matches/fx")) return json(live);
    return realFetch(url, opts);
  };
  history.pushState({}, "", "/v2");
  dispatchEvent(new PopStateEvent("popstate"));
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const root = document.getElementById("root");
  for (let i = 0; i < 50 && ![...root.querySelectorAll("button")].some((b) => b.innerText.includes("Lancer")); i++) await sleep(100);
  for (let i = 0; i < 50 && root.querySelectorAll("select").length < 2; i++) await sleep(100);
  const launch = [...root.querySelectorAll("button")].find((b) => b.innerText.includes("Lancer"));
  if (!launch || launch.disabled) return "pas de bouton Lancer";

  if (mode === "fps") {
    launch.click();
    for (let i = 0; i < 100 && !root.querySelector("button.rounded-full"); i++) await sleep(100);
    [...root.querySelectorAll("button")].find((b) => b.innerText.trim() === "x8").click();
    await sleep(1000);
    const gaps = [];
    let prev = performance.now();
    const until = prev + seconds * 1000;
    await new Promise((done) => {
      const f = (now) => { gaps.push(now - prev); prev = now; if (now < until) requestAnimationFrame(f); else done(); };
      requestAnimationFrame(f);
    });
    gaps.sort((a, b) => a - b);
    const q = (p) => +gaps[Math.floor(p * (gaps.length - 1))].toFixed(2);
    return { frames: gaps.length, median: q(0.5), p95: q(0.95), max: q(1), nodes: root.querySelectorAll("svg *").length };
  }

  // mode "log" (ou "shot" : arrêt après `seconds` images, pour une capture)
  const DT = 50;
  let T = 1000;
  let nextId = 1;
  const queue = new Map();
  window.requestAnimationFrame = (cb) => { const id = nextId++; queue.set(id, cb); return id; };
  window.cancelAnimationFrame = (id) => { queue.delete(id); };
  performance.now = () => T;
  const flush = () => new Promise((r) => { const ch = new MessageChannel(); ch.port1.onmessage = () => r(); ch.port2.postMessage(0); });
  const fnv = (h, s) => { for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619) >>> 0; } return h; };
  const summary = () => {
    const score = root.querySelector(".font-bold.text-white.tabular-nums");
    const clock = score?.nextElementSibling;
    const txt = root.innerText;
    return [score?.innerText, clock?.innerText, txt.includes("RALENTI") ? "RALENTI" : "", txt.includes("MI-TEMPS") ? "MI-TEMPS" : "",
      (txt.match(/Match terminé[^\n]*/) || [""])[0], (txt.match(/⚑ Hors-jeu[^\n]*/) || [""])[0]].join(" | ");
  };
  launch.click();
  for (let i = 0; i < 100 && !root.querySelector("button.rounded-full"); i++) await sleep(100);
  [...root.querySelectorAll("button")].find((b) => b.innerText.trim() === "x8").click();
  await flush(); await flush();
  const res = { name, frames: 0, log: [], hash: 2166136261, t0: Date.now() };
  window.__res = res;
  let last = "";
  for (let f = 0; f < (mode === "shot" ? seconds : 80000); f++) {
    if (queue.size === 0) break;
    T += DT;
    const cbs = [...queue.values()];
    queue.clear();
    for (const cb of cbs) cb(T);
    await flush(); await flush();
    const s = summary();
    if (s !== last) { res.log.push(`${f}|${s}`); last = s; }
    res.hash = fnv(res.hash, root.innerHTML);
    res.frames = f + 1;
  }
  res.ms = Date.now() - res.t0;
  res.done = true;
  return res;
}
