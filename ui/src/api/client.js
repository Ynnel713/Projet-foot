// VITE_API_URL doit pointer vers l'IP locale du PC (pas localhost) pour être
// joignable depuis le téléphone -- voir ui/.env.local.
const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API ${path} -> ${res.status} : ${body}`);
  }
  return res.json();
}

export const getLeagues = () => request("/api/leagues");
export const getPersoClubs = () => request("/api/clubs");
export const getNations = () => request("/api/nations");

export const createCompetition = (body) =>
  request("/api/competitions", { method: "POST", body: JSON.stringify(body) });

export const getCompetition = (id) => request(`/api/competitions/${id}`);
// Bouton unique qui alterne : simule la journée courante SANS avancer, puis
// avance à la suivante SANS simuler (voir Simulation.jsx) -- même logique
// que le bouton alternant de l'écran Streamlit d'origine.
export const simulateCurrent = (id) => request(`/api/competitions/${id}/simulate-current`, { method: "POST" });
export const advanceJournee = (id) => request(`/api/competitions/${id}/advance`, { method: "POST" });
export const simulateAll = (id) => request(`/api/competitions/${id}/simulate-all`, { method: "POST" });
export const getStandings = (id) => request(`/api/competitions/${id}/standings`);
export const getLeaderboards = (id) => request(`/api/competitions/${id}/leaderboards`);
export const getMatches = (id, journee) =>
  request(`/api/competitions/${id}/matches${journee ? `?journee=${journee}` : ""}`);
// `params` : { home, away, journee } (championnat), { home, away, group,
// matchday } (poules), ou { home, away, round_number, leg } (tableau,
// leg 0=aller/1=retour) -- un seul groupe pertinent à la fois, voir
// api.routers.competitions.get_pitch_view.
export const getPitchView = (id, params) => {
  const clean = Object.fromEntries(Object.entries(params).filter(([, v]) => v !== undefined && v !== null));
  return request(`/api/competitions/${id}/pitch?${new URLSearchParams(clean)}`);
};

// Ligue des Champions / Coupe du Monde (format HYBRID : poules puis
// élimination directe -- mêmes écrans Groups.jsx/Bracket.jsx pour les deux).
export const createChampionsLeague = () => request("/api/competitions/champions-league", { method: "POST" });
export const createWorldCup = () => request("/api/competitions/world-cup", { method: "POST" });
export const getGroups = (id) => request(`/api/competitions/${id}/groups`);
export const simulateGroupsMatchday = (id) =>
  request(`/api/competitions/${id}/groups/simulate-matchday`, { method: "POST" });
export const startKnockout = (id) => request(`/api/competitions/${id}/knockout/start`, { method: "POST" });
export const getBracket = (id) => request(`/api/competitions/${id}/bracket`);
export const simulateBracketRound = (id) =>
  request(`/api/competitions/${id}/bracket/simulate-round`, { method: "POST" });
export const advanceBracketRound = (id) => request(`/api/competitions/${id}/bracket/advance`, { method: "POST" });
