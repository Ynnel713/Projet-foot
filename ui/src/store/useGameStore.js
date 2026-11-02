// Zustand plutôt que Context API : l'écran de simulation change d'état
// souvent (score par score, barre de progression) -- Context re-rend TOUS
// les consommateurs à chaque changement sauf découpage soigneux ; Zustand
// donne des abonnements sélectifs nativement, ce qui compte sur mobile où
// chaque rendu superflu coûte plus cher.
import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";

// localStorage dont les échecs d'écriture (quota plein, navigation privée de
// certains navigateurs) sont ignorés : l'état reste alors en mémoire, sans
// faire échouer l'action qui l'a modifié.
const safeLocalStorage = {
  getItem: (key) => {
    try {
      return localStorage.getItem(key);
    } catch {
      return null;
    }
  },
  setItem: (key, value) => {
    try {
      localStorage.setItem(key, value);
    } catch {
      // stockage indisponible : mémoire seule
    }
  },
  removeItem: (key) => {
    try {
      localStorage.removeItem(key);
    } catch {
      // stockage indisponible : mémoire seule
    }
  },
};

// `persist` (localStorage) : la compétition en cours et le club suivi survivent
// au rechargement de la page -- carte « Reprendre » de l'accueil et nom de la
// compétition dans l'en-tête (refonte UI, lot 2). La compétition elle-même vit
// côté API, en mémoire : un 404 au retour l'efface (voir Home).
export const useGameStore = create(
  persist(
    (set) => ({
      activeCompetitionId: null,
      activeCompetitionLabel: null,
      followedClub: null, // mis en évidence dans classement/résultats
      setActiveCompetition: (id, label) => set({ activeCompetitionId: id, activeCompetitionLabel: label }),
      clearActiveCompetition: () => set({ activeCompetitionId: null, activeCompetitionLabel: null }),
      setFollowedClub: (name) => set({ followedClub: name }),
    }),
    { name: "simulafoot-game", storage: createJSONStorage(() => safeLocalStorage) },
  ),
);
