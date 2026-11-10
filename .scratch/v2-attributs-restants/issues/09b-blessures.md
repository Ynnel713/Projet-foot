# 09b: Blessures

**Découpé du ticket 09 le 04/11/2026** (audit de granularité). Détail : `09-discipline-fautes-cartons-blessures.md`.

**What to build:** une blessure rare sur un contact, plus probable pour un joueur qui va au contact dangereux (**Bravery**) et sur un tacle dur ; arrêt de jeu, soins, puis remplacement forcé (`v2-coach-et-gestion-de-match/05a`). La blessure ne change pas la réussite de l'action en cours.

**Attributs :** Bravery.

**Blocked by:** 07a (contacts du duel), 09a (gravité de la faute), `v2-coach-et-gestion-de-match/05a` (remplacement forcé) ; passe après `v2-collectif/22c`.

**Bloque :** `v2-coach-et-gestion-de-match/05b` (cas « blessure ») ; `v2-realisme/20g` (blessures sans contact et crampes) (ajouté le 10/11/2026, audit de la roadmap).

**Status:** à faire (constantes à proposer avant le code)

## Acceptance criteria

- [ ] Blessures par match dans une fourchette réelle sourcée (ou « non trouvé »)
- [ ] Bravery élevée : plus de contacts dangereux engagés et plus de blessures, à situation égale
- [ ] Un joueur blessé est remplacé au prochain arrêt de jeu ; à défaut de remplaçant, l'équipe joue à 10 sans téléportation
- [ ] L'arrêt pour soins est compté dans le temps additionnel
- [ ] Constantes produit et critères chiffrés validés par le propriétaire avant le code
- [ ] Déterminisme à graine fixée ; suite V2 verte ; V1 inchangée

## Complément de l'audit de la roadmap (10/11/2026)

Source : `docs/AUDIT_ROADMAP_V2.md`. Ce ticket garde la blessure sur contact. La blessure sans contact selon la charge, le joueur touché qui continue diminué et les crampes vont au `v2-realisme/20g`. La capacité réduite d'un blessé passe par la façade de la condition (`v2-realisme/19a`). Un joueur frais peut se blesser, un joueur fatigué peut finir sans blessure : la fatigue augmente le risque, elle ne le déclenche pas.
