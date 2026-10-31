# 01: Base joueurs FM26 à jour, doublons supprimés, Moyenne FM qui fait foi en V1

**What to build:** Mettre à jour `data/joueurs.xlsx` depuis fminside (FM26) pour les 3 000 premiers joueurs : attributs, postes naturels, taille, pied faible et preferred moves. Supprimer les doublons dont on est certain. Créer une « Moyenne FM » qui fait foi pour la V1 (moteur Poisson), sans toucher à « Moyenne joueur », et régénérer les onglets de sélections nationales.

**Status:** livré (31/10/2026), validé expert + QC

**Décisions du propriétaire (30-31/10/2026)**
- Source : fminside.net (preferred moves lus avec sa session connectée) ; doutes d'identité levés via Transfermarkt.
- « Moyenne FM » fait foi en V1 ; « Moyenne joueur » reste intacte. En V2 (moteur graphique), aucune moyenne : seuls les attributs s'expriment.
- Moyenne pondérée, remise sur l'échelle actuelle (celle de Moyenne joueur).
- Pondération par poste sur 4 niveaux d'importance (essentiel, important, utile, secondaire) : « pour un attaquant, finition devrait plus compter que marquage ».
- Colonne « Moyenne FM » juste après le nom du joueur.
- Doublons : supprimer seulement ceux dont on est certain.
- Table des niveaux (`players._FM_LEVELS`, poids 8/4/2/1) proposée par Claude, acceptée par le propriétaire le 31/10/2026 (« tout est bon »).
- `PLACEHOLDER_BELOW = 30` (notes par défaut 19-22 exclues de l'échelle de référence) et remise à l'échelle par rangs, au sein de chaque famille de table : confirmés par le propriétaire le 31/10/2026 (« I confirm both », réserve A2 de l'expert).
- Recalage par famille de table plutôt que par groupe de poste : demandé par le propriétaire le 31/10/2026 (« Yes, fix it », réserve A1 de l'expert).

## Critères d'acceptation

- [x] « Moyenne joueur » identique avant/après sur toutes les lignes conservées (0 écart sur 7 473)
- [x] « Moyenne FM » renseignée pour 7 473/7 473 joueurs, sur l'échelle de Moyenne joueur (19 à 91), placée juste après « Nom » ; le moteur la lit (`clubs.NOTE_COLUMN`)
- [x] Pour un BU la finition pèse plus que le marquage, pour un DC l'inverse (test `test_finishing_outweighs_marking_for_a_striker_not_for_a_defender`)
- [x] 90 doublons supprimés, chacun avec exactement un jumeau conservé ; aucun club disparu ni effectif sous 11 dans les 9 championnats jouables
- [x] Preferred moves : 2 992 lignes du top 3 000 renseignées depuis fminside (« (aucun) » quand FM n'en donne pas)
- [x] Sélections régénérées (129 pays, 91 complètes) ; comptes de l'onglet Ligue des Champions justes
- [x] Aucun fichier interdit par CLAUDE.md touché ; pas de nouvel import privé
- [x] Suite complète verte : 2 121 passés, 4 ignorés (Node absent, `test_canvas_html.py:463`), 13 désélectionnés, 0 échec (31/10/2026, après correction A1)

## Comments

**31/10/2026 — passage 1 de /valider-ticket-simulafoot**
- QC (`donnees-moyenne-fm/01`) : REFUSÉ — le fichier de ticket revu (doublon `01-maj-base-joueurs-moyenne-fm.md`, supprimé depuis) décrivait `_GK_IMPORTANCE` au lieu de `_FM_LEVELS` ; 2 tests passés puis ignorés non expliqués (expliqué depuis : 4 tests de `test_canvas_html.py` ignorés quand Node est absent du PATH).
- Expert : APPROVED_WITH_RESERVATIONS.
  - A1 [réserve] : recalage par rangs sur le groupe DEF entier alors que DC et Latéral ont des tables différentes → latéraux ~3,7 points sous les DC, 4,11 DC par sélection, 5 sélections sans latéral.
  - A2 [réserve] : pas d'accord écrit du propriétaire sur `PLACEHOLDER_BELOW = 30` ni sur la méthode par rangs.
- Décision du propriétaire sur A1 : « Yes, fix it » (31/10/2026) → recalage par famille de table (`players.fm_table_family` : DC, Latéral, MDC, MC, MOC, Ailier, BU, GK) au lieu du groupe de poste.
- Décision du propriétaire sur A2 : « I confirm both » (31/10/2026).
- Mesure après correction (`verif_expert.py`, même script) : écart Moyenne FM − Moyenne joueur DC +0,47, LB +0,60, RB +0,26 (tous postes entre −0,1 et +0,8 hors GK +1,8) ; top 100 DEF : DC 66 → 66 %, RB 21 → 14 %, LB 13 → 20 % ; DC par sélection 3,50 → 3,55 ; 91 sélections complètes.

**31/10/2026 — passage 2 de /valider-ticket-simulafoot** (empreinte b2e2e235…)
- Expert : APPROVED (A1 corrigée, A2 levée par l'accord écrit). Facultatif : commentaire « à valider » de `_FM_LEVELS` périmé ; garde sur référence vide dans `rank_rescale` ; `simulafoot_nlg` lit encore « Moyenne joueur ».
- QC : VALIDÉ. Non bloquant : même commentaire périmé ; docstring « ~35-91 » au lieu de 19-91 ; 13 désélectionnés contre 12 de référence (hors diff).
- Clôture : VALIDÉ (cloture.py decision, journal `donnees-moyenne-fm/01/cloture`).
