// Raccourcis clavier de la lecture (ticket v2-ecran-match/09, validés par le propriétaire le 19/11/2026) : barre
// d'espace = lecture/pause, touches 1 à 5 = les vitesses dans l'ordre. Fonction pure, testée sous node. Les chiffres
// sont lus par la position de la touche (`code` : rangée du haut ou pavé numérique) : sur un clavier AZERTY, la rangée
// du haut sans Maj donne « & é " ' ( » (réserve A1 de l'expert, 19/11/2026).

const EDITABLE = new Set(["INPUT", "TEXTAREA", "SELECT"]);

const DIGIT = /^(?:Digit|Numpad)([1-9])$/;

// Action à mener pour une touche, ou null. `event` : { key, code, repeat, target, ctrlKey, metaKey, altKey }.
export function playbackKey(event, speeds) {
  if (event.ctrlKey || event.metaKey || event.altKey) return null; // raccourcis du navigateur
  if (event.repeat) return null; // touche maintenue : une seule commande (réserve A3 de l'expert)
  const target = event.target;
  if (target && (EDITABLE.has(target.tagName) || target.isContentEditable)) return null; // saisie en cours
  if (event.key === " ") return { type: "toggle" };
  const digit = DIGIT.exec(event.code || "")?.[1] ?? (/^[1-9]$/.test(event.key) ? event.key : null);
  const index = digit == null ? -1 : Number(digit) - 1;
  if (index >= 0 && index < speeds.length) return { type: "speed", speed: speeds[index] };
  return null;
}

// Libellé d'une vitesse : « ×1 », « ×1,5 » (virgule décimale).
export const speedLabel = (s) => `×${String(s).replace(".", ",")}`;
