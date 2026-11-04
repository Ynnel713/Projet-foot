# 09b: Blessures

**Découpé du ticket 09 le 04/11/2026** (audit de granularité). Détail : `09-discipline-fautes-cartons-blessures.md`.

**What to build:** une blessure rare sur un contact, plus probable pour un joueur qui va au contact dangereux (**Bravery**) et sur un tacle dur ; arrêt de jeu, soins, puis remplacement forcé (`v2-coach-et-gestion-de-match/05a`). La blessure ne change pas la réussite de l'action en cours.

**Attributs :** Bravery.

**Blocked by:** 07a (contacts du duel), 09a (gravité de la faute), `v2-coach-et-gestion-de-match/05a` (remplacement forcé) ; passe après `v2-collectif/22c`.

**Bloque :** `v2-coach-et-gestion-de-match/05b` (cas « blessure »).

**Status:** à faire (constantes à proposer avant le code)

## Acceptance criteria

- [ ] Blessures par match dans une fourchette réelle sourcée (ou « non trouvé »)
- [ ] Bravery élevée : plus de contacts dangereux engagés et plus de blessures, à situation égale
- [ ] Un joueur blessé est remplacé au prochain arrêt de jeu ; à défaut de remplaçant, l'équipe joue à 10 sans téléportation
- [ ] L'arrêt pour soins est compté dans le temps additionnel
- [ ] Constantes produit et critères chiffrés validés par le propriétaire avant le code
- [ ] Déterminisme à graine fixée ; suite V2 verte ; V1 inchangée
