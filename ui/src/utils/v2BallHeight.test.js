// Tests de la hauteur du ballon à l'écran (ticket v2-hauteur-ballon/02b1) : `node --test src/utils/v2BallHeight.test.js`.
import assert from "node:assert/strict";
import test from "node:test";
import { BALL_R, ballRadius, ballShadow } from "./v2BallHeight.js";

const close = (a, b, tol = 1e-9) => Math.abs(a - b) <= tol;

test("le ballon grossit de 5 % par mètre, jusqu'à + 40 %", () => {
  assert.equal(BALL_R, 0.5);
  assert.ok(close(ballRadius(0), 0.5));
  assert.ok(close(ballRadius(2), 0.55));
  assert.ok(close(ballRadius(4), 0.6)); // l'ancien rayon fixe du ballon aérien (ticket 01)
  assert.ok(close(ballRadius(8), 0.7));
  assert.ok(close(ballRadius(25), 0.7));
});

test("hauteur absente, négative ou non finie : ballon au sol", () => {
  for (const z of [undefined, null, -1, NaN]) {
    assert.ok(close(ballRadius(z), 0.5));
    assert.equal(ballShadow(z), null);
  }
});

test("pas d'ombre au sol ; l'ombre rapetisse et pâlit en montant, bornée à 10 m", () => {
  assert.equal(ballShadow(0), null);
  const low = ballShadow(0.01);
  assert.ok(close(low.r, 0.5, 1e-3) && close(low.opacity, 0.3, 1e-3));
  const mid = ballShadow(5);
  assert.ok(close(mid.r, 0.375) && close(mid.opacity, 0.2));
  for (const z of [10, 30]) {
    const high = ballShadow(z);
    assert.ok(close(high.r, 0.25) && close(high.opacity, 0.1));
  }
});

test("l'ombre ne grandit jamais et ne fonce jamais quand le ballon monte", () => {
  let prev = ballShadow(0.01);
  for (let z = 0.1; z <= 20; z += 0.1) {
    const s = ballShadow(z);
    assert.ok(s.r <= prev.r + 1e-12 && s.opacity <= prev.opacity + 1e-12);
    prev = s;
  }
});
