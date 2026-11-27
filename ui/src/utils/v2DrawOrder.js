// Ordre de dessin du ballon et des joueurs par rapport aux buts (ticket v2-hauteur-ballon/02b2). La caméra ne tourne
// qu'autour de l'axe x (`utils/v2Projection.js`) : la profondeur de la scène se lit dans la largeur y (le côté y = W est
// le plus proche de la caméra) et la hauteur z ; la longueur x ne cache rien. Un élément du but ne couvre un objet que
// s'il est entre lui et la caméra. Fonctions pures, testées par `node --test` (v2DrawOrder.test.js).
import { COS, SIN } from "./v2Projection.js";

const TAN = SIN / COS; // un point à la hauteur h au-dessus d'un objet le couvre à l'écran s'il est h·tan α plus près (en y)

// Derrière la ligne de but `goalX` (`out` : -1 côté x = 0, 1 côté x = L), dans le filet ou au-delà ; `onLine` : la
// ligne elle-même compte (ballon d'un but, posé sur la ligne par `v2GoalBall.js`).
export const behindGoalLine = (x, goalX, out, onLine = false) => (onLine ? (x - goalX) * out >= 0 : (x - goalX) * out > 0);

// Joueur dessiné sous les buts : entré dans un filet (derrière une ligne), sans être sorti du côté de la caméra
// (au-delà du poteau proche, où le filet latéral de devant est derrière lui).
export const playerUnderGoal = (p, goalX, out, posts) => behindGoalLine(p.x, goalX, out) && p.y <= posts[1];

// Parties du but `goalX` dessinées par-dessus le ballon. `ball` : { x, y, z } (z : bas du ballon, m) ; `posts` : [y du
// poteau lointain, y du poteau proche] ; `crossbar` : hauteur de la barre et du toit du filet. Ballon devant la ligne ou
// au-dessus du toit : rien (il passe devant le but). Ballon sur ou derrière la ligne et sous le toit : le cadre (poteaux
// et barre sur la ligne) ; le toit si son point qui se projette sur le ballon (y + (barre − z)·tan α) est entre les
// poteaux ; le filet latéral de devant si le ballon est derrière lui (y < poteau proche), celui du fond s'il est au-delà.
export function goalPartsOverBall(ball, goalX, out, posts, crossbar) {
  const none = { far: false, roof: false, near: false, frame: false };
  const z = ball?.z ?? 0;
  if (!ball || !behindGoalLine(ball.x, goalX, out, true) || z >= crossbar) return none;
  const [far, near] = posts;
  const roofY = ball.y + (crossbar - z) * TAN;
  return { far: ball.y < far, roof: roofY >= far && roofY <= near, near: ball.y < near, frame: true };
}

// Le ballon est dessiné avec les buts (entre leurs parties du fond et celles de devant) si un but le couvre en partie.
export const ballInsideGoal = (...parts) => parts.some((p) => p.far || p.roof || p.near || p.frame);
