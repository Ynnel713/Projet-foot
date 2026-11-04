# 04b: Postes naturels

**Découpé du ticket 04 le 04/11/2026** (audit de granularité). Détail : `04-pied-fort-pied-faible-postes.md`.

**What to build:** **Postes FM naturels** : un joueur aligné hors de ses postes naturels subit une pénalité sur Positioning, Decisions et Marking (carte des attributs), graduée selon la distance entre le poste joué et le poste naturel.

**Attributs :** Postes naturels.

**Blocked by:** `v2-collectif/19` ; passe après `v2-collectif/22c` (contrôle de non-régression).

**Bloque :** `v2-coach-et-gestion-de-match/05a` (entrant hors de son poste naturel).

**Status:** à faire (constantes à proposer avant le code)

## Acceptance criteria

- [ ] Joueur hors poste : erreurs de placement et de marquage mesurablement plus fréquentes, proportionnées à l'écart de poste
- [ ] Données manquantes : comportement neutre, jamais d'erreur
- [ ] Constantes produit et critères chiffrés validés par le propriétaire avant le code
- [ ] Suite V2 verte ; V1 inchangée
