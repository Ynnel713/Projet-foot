// Tests de l'ordre de dessin (ticket v2-hauteur-ballon/02b2) : `node --test src/utils/v2DrawOrder.test.js`.
import assert from "node:assert/strict";
import test from "node:test";
import { ballInsideGoal, behindGoalLine, goalPartsOverBall, playerUnderGoal } from "./v2DrawOrder.js";

const POSTS = [30.34, 37.66]; // poteaux d'un but de 7,32 m centré sur 34 m
const BAR = 2.44;

test("derrière la ligne : selon le côté du but ; la ligne elle-même seulement si demandé", () => {
  assert.equal(behindGoalLine(0, 0, -1), false);
  assert.equal(behindGoalLine(0, 0, -1, true), true);
  assert.equal(behindGoalLine(105, 105, 1, true), true);
  assert.equal(behindGoalLine(-0.5, 0, -1), true);
  assert.equal(behindGoalLine(0.5, 0, -1), false);
  assert.equal(behindGoalLine(105.5, 105, 1), true);
  assert.equal(behindGoalLine(104.9, 105, 1), false);
});

test("ballon devant la ligne ou au-dessus du toit : il passe devant tout le but", () => {
  const none = { far: false, roof: false, near: false, frame: false };
  assert.deepEqual(goalPartsOverBall({ x: 1, y: 34, z: 0 }, 0, -1, POSTS, BAR), none);
  assert.deepEqual(goalPartsOverBall({ x: -1, y: 34, z: 2.44 }, 0, -1, POSTS, BAR), none);
  assert.deepEqual(goalPartsOverBall({ x: -1, y: 34, z: 8 }, 0, -1, POSTS, BAR), none);
  assert.deepEqual(goalPartsOverBall(null, 0, -1, POSTS, BAR), none);
});

test("ballon dans le filet : cadre, toit et filet de devant par-dessus, filet du fond dessous", () => {
  const parts = goalPartsOverBall({ x: 106, y: 34, z: 0.5 }, 105, 1, POSTS, BAR);
  assert.deepEqual(parts, { far: false, roof: true, near: true, frame: true });
  assert.equal(ballInsideGoal(parts), true);
});

test("ballon derrière la ligne à côté du but : seul le filet latéral qui est entre lui et la caméra le couvre", () => {
  assert.deepEqual(goalPartsOverBall({ x: -1, y: 20, z: 0 }, 0, -1, POSTS, BAR), { far: true, roof: false, near: true, frame: true });
  assert.deepEqual(goalPartsOverBall({ x: -1, y: 50, z: 0 }, 0, -1, POSTS, BAR), { far: false, roof: false, near: false, frame: true });
});

test("aucun but ne couvre le ballon : il est dessiné après les joueurs", () => {
  const none = goalPartsOverBall({ x: 50, y: 34, z: 3 }, 0, -1, POSTS, BAR);
  assert.equal(ballInsideGoal(none, goalPartsOverBall({ x: 50, y: 34, z: 3 }, 105, 1, POSTS, BAR)), false);
});

test("ballon d'un but, posé sur la ligne : la barre, le toit et le filet de devant passent devant lui (A1 de l'expert)", () => {
  assert.deepEqual(goalPartsOverBall({ x: 105, y: 34, z: 0.5 }, 105, 1, POSTS, BAR), { far: false, roof: true, near: true, frame: true });
  assert.deepEqual(goalPartsOverBall({ x: 0, y: 34, z: 0 }, 0, -1, POSTS, BAR), { far: false, roof: true, near: true, frame: true });
  assert.equal(ballInsideGoal(goalPartsOverBall({ x: 0, y: 34, z: 3 }, 0, -1, POSTS, BAR)), false); // au-dessus : devant
});

test("toit : il couvre le ballon si son point projeté sur lui (y + (barre − z)·tan 35°) est entre les poteaux (A2)", () => {
  // juste au-delà du poteau lointain, au sol : point du toit en y ≈ 29,5 + 1,71 = 31,2, entre les poteaux
  assert.equal(goalPartsOverBall({ x: -1, y: 29.5, z: 0 }, 0, -1, POSTS, BAR).roof, true);
  // près du poteau proche, au sol : point du toit au-delà du poteau proche, seul le filet de devant le couvre
  const near = goalPartsOverBall({ x: -1, y: 37.5, z: 0 }, 0, -1, POSTS, BAR);
  assert.equal(near.roof, false);
  assert.equal(near.near, true);
});

test("joueurs : sous les buts s'ils sont entrés dans un filet, par-dessus sur la ligne ou au-delà du poteau proche (A3)", () => {
  assert.equal(playerUnderGoal({ x: -0.5, y: 34 }, 0, -1, POSTS), true);
  assert.equal(playerUnderGoal({ x: 0, y: 34 }, 0, -1, POSTS), false); // gardien sur sa ligne
  assert.equal(playerUnderGoal({ x: 0.4, y: 34 }, 0, -1, POSTS), false);
  assert.equal(playerUnderGoal({ x: -0.5, y: 39 }, 0, -1, POSTS), false); // sorti côté caméra
  assert.equal(playerUnderGoal({ x: 106, y: 20 }, 105, 1, POSTS), true); // derrière, côté du fond
});
