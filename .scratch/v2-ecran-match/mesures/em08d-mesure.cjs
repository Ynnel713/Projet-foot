const { chromium } = require("playwright");
(async () => {
  const b = await chromium.launch(); const res = {};
  for (const [fx, w, h] of [["em11-om-ol", 1366, 768], ["em11-om-ol", 1024, 768], ["em11-om-ol", 1920, 1080], ["em11-psg-havre", 1024, 768], ["em11-psg-havre", 1366, 768]]) {
    const p = await b.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 1 });
    await p.goto(`http://localhost:5173/v2?fixture=${fx}&t=104&paused=1`);
    await p.waitForSelector("[data-scorers]", { timeout: 120000 }); await p.waitForTimeout(1000);
    res[`${fx} ${w}x${h}`] = await p.evaluate(() => [...document.querySelectorAll("[data-scorers] li")].filter((li) => li.children.length === 2).map((li) => {
      const [n, m] = li.children; const range = document.createRange(); range.selectNodeContents(n);
      const textW = range.getBoundingClientRect().width;
      return `${n.innerText}|écart ${(m.getBoundingClientRect().left - n.getBoundingClientRect().right).toFixed(1)}|blanc ${(n.getBoundingClientRect().width - Math.min(textW, n.scrollWidth)).toFixed(1)}|nom ${n.getBoundingClientRect().width.toFixed(1)}${n.scrollWidth > n.clientWidth ? "|tronqué" : ""}${m.scrollWidth > m.clientWidth ? "|minutes tronquées" : ""}`;
    }));
    await p.close();
  }
  console.log(JSON.stringify(res, null, 1)); await b.close();
})();
