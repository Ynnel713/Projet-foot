// node run-bench.mjs <port> <trace> <log|fps> [secondes]
// Lance un Chrome headless non bridé, ouvre http://localhost:<port>/, charge /__fx/harness.js et exécute __bench.
import { spawn } from "node:child_process";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const [port, name, mode, secs = "20", cpu = "1"] = process.argv.slice(2);
const CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe";
const debugPort = 9300 + Math.floor(Math.random() * 600);
const profile = mkdtempSync(join(tmpdir(), "em01-"));
const chrome = spawn(CHROME, [
  "--headless=new", `--remote-debugging-port=${debugPort}`, `--user-data-dir=${profile}`,
  "--disable-background-timer-throttling", "--disable-renderer-backgrounding", "--disable-backgrounding-occluded-windows",
  "--no-first-run", "--window-size=1024,768", `http://localhost:${port}/`,
], { stdio: "ignore" });

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let ws;
try {
  let target;
  for (let i = 0; i < 50 && !target; i++) {
    await sleep(200);
    try {
      const list = await (await fetch(`http://127.0.0.1:${debugPort}/json`)).json();
      target = list.find((t) => t.type === "page" && t.url.startsWith(`http://localhost:${port}`));
    } catch { /* pas encore prêt */ }
  }
  ws = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((r) => ws.addEventListener("open", r));
  let id = 0;
  const pending = new Map();
  ws.addEventListener("message", (e) => {
    const m = JSON.parse(e.data);
    if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); }
  });
  const call = (method, params) => new Promise((r) => { const k = ++id; pending.set(k, r); ws.send(JSON.stringify({ id: k, method, params })); });
  await sleep(4000); // chargement de la page
  if (Number(cpu) > 1) await call("Emulation.setCPUThrottlingRate", { rate: Number(cpu) });
  const expr = `(async () => {
    await new Promise((r, j) => { const s = document.createElement("script"); s.src = "/__fx/harness.js?" + Date.now(); s.onload = r; s.onerror = j; document.head.appendChild(s); });
    const r = await __bench(${JSON.stringify(name)}, ${JSON.stringify(mode)}, ${Number(secs)});
    if (r && r.log) { const fnv = (h, s) => { for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619) >>> 0; } return h; }; r.logHash = fnv(2166136261, r.log.join("\\n")); }
    return r;
  })()`;
  const res = await call("Runtime.evaluate", { expression: expr, awaitPromise: true, returnByValue: true });
  if (mode === "fps") {
    // temps CPU du moteur de rendu par image affichée, lecture x8 déjà en cours (métriques CDP cumulées)
    await call("Performance.enable", {});
    const metrics = async () => Object.fromEntries((await call("Performance.getMetrics", {})).result.metrics.map((m) => [m.name, m.value]));
    const m0 = await metrics();
    const count = await call("Runtime.evaluate", { expression: `new Promise((done) => { let n = 0; const end = performance.now() + ${Number(secs)} * 1000; const f = (t) => { n++; if (t < end) requestAnimationFrame(f); else done(n); }; requestAnimationFrame(f); })`, awaitPromise: true, returnByValue: true });
    const m1 = await metrics();
    const n = count.result.result.value;
    const per = (k) => +(((m1[k] - m0[k]) * 1000) / n).toFixed(2);
    res.result.result.value.cpu = { frames: n, taskMsPerFrame: per("TaskDuration"), scriptMsPerFrame: per("ScriptDuration"), layoutMsPerFrame: per("LayoutDuration"), styleMsPerFrame: per("RecalcStyleDuration") };
  }
  if (mode === "shot") { const shot = await call("Page.captureScreenshot", { format: "png" }); writeFileSync(join(process.cwd(), `shot-${port}-${name}-${secs}.png`), Buffer.from(shot.result.data, "base64")); }
  const value = res.result?.result?.value; if (!value || typeof value !== "object") console.log(JSON.stringify(res).slice(0, 800));
  const out = join(process.cwd(), `res-${port}-${name}-${mode}-cpu${cpu}.json`);
  writeFileSync(out, JSON.stringify(value, null, 1));
  const { log, ...head } = value || {};
  console.log(JSON.stringify(head), log ? `log=${log.length}` : "");
} finally {
  ws?.close();
  chrome.kill();
}
