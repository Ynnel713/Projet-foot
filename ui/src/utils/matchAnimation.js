// Protocole parent <-> iframe `render/canvas.html` (docs/canvas_integration_state.md §2.11, version 1) et
// adaptation de la réponse API en payload `init`.
//
// Les clips sont calculés côté Python (moteur de rendu, inchangé) À PARTIR de la composition persistée dans
// le Match (LineupSnapshot) : ce module ne recalcule JAMAIS une composition, n'appelle jamais rien qui
// ressemble à pick_best_formation, ne reconstruit rien depuis PlayerMatchStat. Il valide la réponse de
// l'API et signale l'indisponibilité au lieu de produire un payload partiel.

export const PROTOCOL_VERSION = 1;
export const HOST_SOURCE = "simulafoot-host"; // parent -> iframe
export const CANVAS_SOURCE = "simulafoot-canvas"; // iframe -> parent

// Messages de la section 2.10 (match sans compo persistée) et assimilés. Jamais de payload partiel.
export const UNAVAILABLE_MESSAGES = {
  lineup_not_persisted: "Animation indisponible : la composition de ce match n'a pas été enregistrée.",
  no_highlights: "Aucun temps fort à animer pour ce match.",
  not_played: "Ce match n'a pas encore été joué.",
  protocol_version_mismatch: "Animation indisponible : version du protocole incompatible avec le serveur.",
  invalid_payload: "Animation indisponible : réponse du serveur invalide.",
  load_error: "Animation indisponible : erreur de chargement.",
  no_handshake: "Animation indisponible : le lecteur n'a pas répondu.",
};

export function unavailableMessage(reason) {
  return UNAVAILABLE_MESSAGES[reason] ?? UNAVAILABLE_MESSAGES.load_error;
}

// Réponse de GET /api/competitions/{id}/animation -> { available: true, payload } | { available: false, reason }.
// `payload` est exactement le contenu du message `init` : { match: {home, away, home_goals, away_goals}, clips: [...] }.
export function buildAnimationPayload(response) {
  if (!response || typeof response !== "object") return { available: false, reason: "invalid_payload" };
  if (response.version !== PROTOCOL_VERSION) return { available: false, reason: "protocol_version_mismatch" };
  if (response.available !== true) {
    return { available: false, reason: typeof response.reason === "string" ? response.reason : "invalid_payload" };
  }
  const { match, clips } = response;
  const clipsOk = Array.isArray(clips) && clips.length > 0 && clips.every((c) => c?.metadata && Array.isArray(c.frames));
  if (!match || !clipsOk) return { available: false, reason: "invalid_payload" };
  return { available: true, payload: { match, clips } };
}

export function initMessage(payload) {
  return { source: HOST_SOURCE, version: PROTOCOL_VERSION, type: "init", payload };
}

// URL de l'iframe : `parent_origin` est l'origine de la PWA, utilisée par l'iframe comme seule cible/seule
// source acceptée des messages (jamais de "*").
export function canvasSrc(baseUrl, parentOrigin) {
  return `${baseUrl}/render/canvas.html?embed=1&parent_origin=${encodeURIComponent(parentOrigin)}`;
}
