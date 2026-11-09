// node dev-check.mjs <url> : ouvre l'URL dans un Chrome headless et attend le bandeau MI-TEMPS (ou 20 s).
import { spawn } from "node:child_process";
import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
const url = process.argv[2];
const debugPort = 9300 + Math.floor(Math.random() * 600);
const chrome = spawn("C:/Program Files/Google/Chrome/Application/chrome.exe", ["--headless=new", `--remote-debugging-port=${debugPort}`, `--user-data-dir=${mkdtempSync(join(tmpdir(), "em01d-"))}`, "--no-first-run", "--window-size=1024,768", "about:blank"], { stdio: "ignore" });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let ws;
try {
  let target;
  for (let i = 0; i < 50 && !target; i++) { await sleep(200); try { target = (await (await fetch(`http://127.0.0.1:${debugPort}/json`)).json()).find((t) => t.type === "page"); } catch {} }
  ws = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((r) => ws.addEventListener("open", r));
  let id = 0; const pending = new Map();
  ws.addEventListener("message", (e) => { const m = JSON.parse(e.data); if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); } });
  const call = (method, params) => new Promise((r) => { const k = ++id; pending.set(k, r); ws.send(JSON.stringify({ id: k, method, params })); });
  await call("Page.enable", {});
  const t0 = Date.now();
  await call("Page.navigate", { url });
  const read = `(() => { const s = document.querySelector("#root .font-bold.text-white.tabular-nums"); return { score: s?.innerText, clock: s?.nextElementSibling?.innerText, speed: document.querySelector("button.bg-accent.text-data")?.innerText, half: document.body.innerText.includes("MI-TEMPS") }; })()`;
  let first = null, state;
  for (let i = 0; i < 100; i++) {
    await sleep(200);
    state = (await call("Runtime.evaluate", { expression: read, returnByValue: true })).result.result.value;
    if (state.score && !first) first = { ms: Date.now() - t0, ...state };
    if (state.half) break;
  }
  console.log(JSON.stringify({ first, last: state, ms: Date.now() - t0 }));
} finally { ws?.close(); chrome.kill(); }
