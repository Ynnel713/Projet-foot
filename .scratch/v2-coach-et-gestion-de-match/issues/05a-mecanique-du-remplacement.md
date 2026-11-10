# 05a: Mécanique du remplacement en V2

**Découpé du ticket 05 le 04/11/2026** (audit de granularité). Détail et points de vigilance (D-V02, D-V07, joueur expulsé jamais remplacé) : `05-remplacements-v2.md`.

**What to build:** un banc et jusqu'à 5 remplacements en 3 fenêtres (la mi-temps ne compte pas comme fenêtre). Dans ce ticket, le coach remplace **poste pour poste**, sur la fatigue : le joueur le plus épuisé à son poste (réserve d'énergie de `v2-collectif/12`) sort en priorité.
- **Exécution physique** : le changement n'a lieu que sur un arrêt de jeu (ballon sorti, faute, but) ou à la mi-temps (ticket 07) ; le sortant quitte le terrain, l'entrant entre par la ligne médiane puis rejoint sa position, sans téléportation. Un entrant hors de son poste naturel subit la pénalité du ticket `v2-attributs-restants/04b`.
- **Trace** : minute, sortant, entrant ; le remplacement nourrit le temps additionnel (ticket 03) ; affiché à l'écran.

**Attributs :** Stamina (via la fatigue) ; attributs seuls (table poste/attributs, D-V07) pour l'entrant ; Postes naturels (via 04b).

**Blocked by:** 07 (livré), 03 ; `v2-collectif/12` ; `v2-attributs-restants/02a`, `02b` (arrêts de jeu, dépendance d'origine, sans doute levable : les tickets `v2-collectif/29` et `30` les fournissent) et `04b` ; `v2-realisme/12e`, `20c` (ajouté le 10/11/2026, audit de la roadmap).

**Bloque :** 05b ; `v2-attributs-restants/09b` (remplacement forcé).

**Status:** à faire (constantes à proposer avant le code)

**Lien avec le temps additionnel (ticket 03, 04/11/2026) :** le fond de 2e période de `v2engine/added_time.BACKGROUND_S` (180 à 330 s) inclut aujourd'hui les remplacements. Quand ils sont joués ici, compter le temps perdu par remplacement dans `added_minutes` et retirer leur part du fond, pour ne pas les compter deux fois.

## Acceptance criteria

- [ ] Nombre de remplacements et minutes dans des fourchettes réelles sourcées (ou « non trouvé ») ; aucun avant la mi-temps (le remplacement sur blessure arrive avec `v2-attributs-restants/09b`)
- [ ] Aucun remplacement pendant que le ballon est en jeu
- [ ] Les sortants sont en moyenne plus fatigués que les joueurs restés sur le terrain au même poste
- [ ] Un entrant frais court mesurablement plus que le sortant
- [ ] Remplacements visibles dans la trace et l'UI V2
- [ ] Déterministe pour une graine donnée ; suite V2 verte ; V1 inchangée

## Complément de l'audit de la roadmap (10/11/2026)

Source : `docs/AUDIT_ROADMAP_V2.md`. La fatigue dont dépend le choix du sortant est la réserve d'énergie `v2-realisme/12e` (le chapeau `v2-collectif/12`). L'entrant commence avec une réserve pleine (échauffement : à proposer, sinon neutre). Critères ajoutés :

- [ ] Titulaire fatigué contre remplaçant frais moins bien noté : l'entrant gagne plus souvent le duel de vitesse face au titulaire fatigué que face au même titulaire frais (mesurable avec la réserve de `v2-realisme/12e`) ; le volet « sans devenir meilleur sur les gestes techniques » est vérifié au `v2-realisme/20d`, après `20a`
- [ ] Dynamique mesurée : occasions créées par l'équipe dans les 15 minutes qui suivent ses remplacements, comparées aux 15 minutes précédentes
