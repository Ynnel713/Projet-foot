// Ticket v2-ecran-match/10a. Usage : node em10a-mesure.cjs <dossier_captures> (Vite sur :5173, trace em10a)
const { chromium } = require("playwright");
const out = process.argv[2];
const SIZES = [[844, 390], [1024, 768], [1280, 720], [1366, 768], [1920, 1080]];
(async () => {
  const b = await chromium.launch();
  const res = {};
  for (const [w, h] of SIZES) {
    const p = await b.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 1 });
    await p.goto("http://localhost:5173/v2?fixture=em10a&t=30&paused=1");
    await p.waitForSelector("svg[viewBox]", { timeout: 120000 });
    await p.waitForTimeout(1500);
    res[`${w}x${h}`] = await p.evaluate(() => {
      const cols = {};
      for (const side of ["home", "away"]) {
        const col = document.querySelector(`[data-zone=composition-${side}]`);
        const r = col.getBoundingClientRect();
        if (!r.width) { cols[side] = "masquée"; continue; }
        const cards = [...col.querySelectorAll("[data-card]")];
        const visible = cards.filter((c) => { const q = c.getBoundingClientRect(); return q.top >= r.top - 0.5 && q.bottom <= r.bottom + 0.5; });
        const names = [...col.querySelectorAll("[data-name]")];
        const longest = names.reduce((a, n) => (n.textContent.length > a.textContent.length ? n : a));
        const li = cards[0];
        cols[side] = {
          box: `${Math.round(r.width)}x${Math.round(r.height)}`,
          scroll: col.scrollHeight - col.clientHeight, hScroll: col.scrollWidth - col.clientWidth,
          titulaires: cards.filter((c) => c.dataset.card === "titulaire").length,
          remplacants: cards.filter((c) => c.dataset.card === "remplacant").length,
          visibles: visible.length,
          hauteurs: [...new Set(cards.map((c) => `${c.dataset.card}:${c.getBoundingClientRect().height}`))],
          offsets: cards.map((c) => Math.round(c.getBoundingClientRect().top - r.top)),
          plusLong: { nom: longest.textContent, tronque: longest.scrollWidth > longest.clientWidth, title: longest.title === longest.textContent },
          liseré: getComputedStyle(li).borderLeftWidth + "/" + getComputedStyle(li).borderRightWidth,
          numeroX: Math.round(li.firstElementChild.getBoundingClientRect().left - r.left),
        };
      }
      return { cols, docScroll: document.documentElement.scrollHeight > innerHeight || document.documentElement.scrollWidth > innerWidth };
    });
    await p.screenshot({ path: `${out}/em10a-${w}x${h}.png` });
    await p.close();
  }
  console.log(JSON.stringify(res, null, 1));
  await b.close();
})();
