// Zustand plutôt que Context API : l'écran de simulation change d'état
// souvent (score par score, barre de progression) -- Context re-rend TOUS
// les consommateurs à chaque changement sauf découpage soigneux ; Zustand
// donne des abonnements sélectifs nativement, ce qui compte sur mobile où
// chaque rendu superflu coûte plus cher.
import { create } from "zustand";

export const useGameStore = create((set) => ({
  activeCompetitionId: null,
  activeCompetitionLabel: null,
  followedClub: null, // mis en évidence dans classement/résultats
  setActiveCompetition: (id, label) => set({ activeCompetitionId: id, activeCompetitionLabel: label }),
  setFollowedClub: (name) => set({ followedClub: name }),
}));
