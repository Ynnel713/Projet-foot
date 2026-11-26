# 05a: Mécanique du remplacement en V2

**Découpé du ticket 05 le 04/11/2026** (audit de granularité). Détail et points de vigilance (D-V02, D-V07, joueur expulsé jamais remplacé) : `05-remplacements-v2.md`.

**What to build:** un banc et jusqu'à 5 remplacements en 3 fenêtres (la mi-temps ne compte pas comme fenêtre). Dans ce ticket, le coach remplace **poste pour poste**, sur la fatigue : le joueur le plus épuisé à son poste (réserve d'énergie de `v2-collectif/12`) sort en priorité.
- **Exécution physique** : le changement n'a lieu que sur un arrêt de jeu (ballon sorti, faute, but) ou à la mi-temps (ticket 07) ; le sortant quitte le terrain, l'entrant entre par la ligne médiane puis rejoint sa position, sans téléportation. Un entrant hors de son poste naturel subit la pénalité du ticket `v2-attributs-restants/04b`.
- **Trace** : minute, sortant, entrant ; le remplacement nourrit le temps additionnel (ticket 03) ; affiché à l'écran.

**Attributs :** Stamina (via la fatigue) ; attributs seuls (table poste/attributs, D-V07) pour l'entrant ; Postes naturels (via 04b).

**Blocked by:** 07 (livré), 03 ; `v2-collectif/12` ; `v2-attributs-restants/02a`, `02b` (arrêts de jeu, dépendance d'origine, sans doute levable : les tickets `v2-collectif/29` et `30` les fournissent) et `04b` ; `v2-realisme/12e`, `20c` (ajouté le 10/11/2026, audit de la roadmap).

**Bloque :** 05b ; `v2-attributs-restants/09b` (remplacement forcé) ; 05c, 05d (ajoutés le 26/11/2026, audit des remplacements).

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

## Complément de l'audit des remplacements (26/11/2026)

Audit des remplacements contre cinq tickets proposés par le propriétaire (S1 à S5). Constat vérifié : aucun banc ni remplacement dans `v2engine/` ; le fond de 2e période de `added_time.BACKGROUND_S` compte encore les remplacements. Deux points manquaient à ce ticket :

- **Règle (« S1 »).** Le « What to build » pose 5 remplacements en 3 fenêtres, mais aucun critère ne teste la règle. Loi 3 (IFAB) : plusieurs changements faits au même arrêt de jeu comptent pour une seule fenêtre ; ceux faits à la mi-temps n'en consomment pas. La prolongation (sixième remplacement, fenêtre supplémentaire) n'existe pas en V2 : hors de ce ticket.
- **Entrée en jeu (« S4 »).** La fraîcheur est couverte (réserve pleine, ci-dessus). Rien ne modélise aujourd'hui un temps d'adaptation de l'entrant : la mémoire de perception (`v2-realisme/08b`) initialise un joueur jamais vu à sa position réelle dès sa première apparition (`perception_memory.update`), donc l'entrant voit et est vu exactement, et elle ne porte que 2 s, pas des minutes. Proposition : un **malus de cohésion temporaire**, seulement s'il est validé par le propriétaire, porté par la façade des notes (`v2-realisme/19a`, `condition.effective_rating`, état `PlayerCondition`) : baisse de Teamwork et de Decisions de l'entrant, décroissante jusqu'à zéro en quelques minutes, bornée. Un seul calcul, dans la façade, aucun mécanisme parallèle. Constantes à proposer : ampleur (points de note), durée, forme de la décroissance. Chiffre réel d'un temps d'adaptation des entrants : non trouvé à ce jour, recherche à faire avant la proposition (rendement des remplaçants dans leurs premières minutes) ; sans chiffre, le propriétaire choisit entre un malus non sourcé, borné, et aucun malus.

Critères ajoutés :

- [ ] Règle testée : jamais plus de 5 remplacements ni plus de 3 fenêtres hors mi-temps par équipe ; deux changements au même arrêt de jeu comptent pour une fenêtre ; changements de la mi-temps hors fenêtres ; le moteur refuse un sixième remplacement et une quatrième fenêtre ; fenêtres utilisées tracées (`5 remplacements, 3 fenêtres` : Loi 3, IFAB 2022-23)
- [ ] Malus de cohésion : décision du propriétaire avant le code (constantes, ou aucun malus) ; s'il est retenu, il passe par `condition.effective_rating` seul, décroît jusqu'à zéro dans la durée validée et ne dépasse jamais l'ampleur validée (tests) ; l'entrant n'hérite d'aucun plan de passe ni appel du sortant (test)
- [ ] Effet de l'entrant borné : actions réussies de l'entrant dans ses 5 premières minutes comparées à ses minutes suivantes, rapportées (indicateur), sans réglage

Réestimation demandée au lancement : la règle testée et, si le malus est retenu, son passage par la façade ajoutent environ 30 min (ticket d'origine sans estimation chiffrée).

