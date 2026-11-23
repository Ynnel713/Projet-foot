import { test } from "node:test";
import assert from "node:assert/strict";
import { ballScale, shadowOpacity, shadowScale } from "./v2BallHeight.js";

const close = (a, b) => assert.ok(Math.abs(a - b) < 1e-9, `${a} != ${b}`);

test("le ballon grossit de 5 % par mètre, plafonné à + 40 %", () => {
  close(ballScale(0), 1);
  close(ballScale(2), 1.1);
  close(ballScale(8), 1.4);
  close(ballScale(19), 1.4);
  close(ballScale(-1), 1); // jamais sous le sol
});

test("l'ombre rétrécit jusqu'à la moitié et pâlit de 0,30 à 0,10 à 10 m", () => {
  close(shadowScale(0), 1);
  close(shadowScale(4), 0.8);
  close(shadowScale(10), 0.5);
  close(shadowScale(15), 0.5);
  close(shadowOpacity(0), 0.3);
  close(shadowOpacity(5), 0.2);
  close(shadowOpacity(10), 0.1);
  close(shadowOpacity(18), 0.1);
});
