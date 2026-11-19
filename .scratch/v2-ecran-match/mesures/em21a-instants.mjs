import fs from "node:fs";
import { ballMotion, trailLength } from "../../../ui/src/utils/v2BallLook.js";
const t = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const half = t.second_half_start_minute ?? 45; const tr = t.ball_track;
let fast = null, slow = null;
for (let m = 20; m < 40 && !(fast && slow); m += 0.01 / 60 * 5) {
  const mo = ballMotion(tr, m, half); if (!mo) continue;
  if (!fast && mo.speed > 24 && trailLength(mo) >= 2.2) fast = { m, speed: mo.speed, trail: trailLength(mo), dir: mo.dir };
  if (!slow && mo.speed > 5 && mo.speed < 8 && mo.distance > 3) slow = { m, speed: mo.speed, dir: mo.dir };
}
console.log(JSON.stringify({ fast, slow }));
