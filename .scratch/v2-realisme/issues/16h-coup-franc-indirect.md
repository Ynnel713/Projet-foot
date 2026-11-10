# 16h: Coup franc indirect : distinguer direct et indirect (loi 13)

**Chantier :** `v2-realisme` (audit de la roadmap du 10/11/2026, complément hors-jeu et coups de pied arrêtés, `docs/AUDIT_ROADMAP_V2.md` §12). **Priorité :** P2 (règle de base, et le hors-jeu redevient une vraie remise en jeu). **Catégorie :** arbitrage.

**Constat vérifié :** le moteur ne connaît qu'un « coup franc » (`restart.FREE_KICK`), toujours direct : le preneur décide comme dans le jeu, tir compris (`match._play_restart`, ticket 30). Le hors-jeu sifflé ne donne pas de vraie remise en jeu : `match._award_offside_free_kick` (« coup franc indirect simplifié ») rend le ballon en jeu au défenseur de champ le plus proche du lieu de la faute, sans ballon mort, sans placement ni distance réglementaire. Aucune faute actuelle ne donne de coup franc indirect (recherche du 10/11/2026) ; un but direct sur un hors-jeu est en pratique impossible (lieu de la faute dans le camp de l'équipe qui défend).

**What to build:** Le type du coup franc (direct ou indirect) est porté par la remise en jeu, selon la faute : hors-jeu, passe en retrait prise à la main (21e), jeu dangereux sans contact, obstruction : indirect ; fautes de contact : direct. Le hors-jeu devient une vraie remise en jeu (`restart.FREE_KICK` indirect au lieu de la faute : ballon mort, placement, 9,15 m), avec une mesure avant/après du temps de jeu effectif et des hors-jeu par match (le temps mort d'un coup franc est de 33 s, `restart.DEAD_S`). Sur un indirect, le preneur ne tire pas directement : il passe ; un tir après la touche d'un coéquipier reste permis (loi 13). Un indirect dans la surface : mur sur la ligne de but si le ballon est à moins de 9,15 m d'elle. Un but marqué directement sur un indirect est impossible par construction.

**Hors de ce ticket :** mur et coup franc direct frappé (16e) ; placement sur coup franc centré (16i).

**Attributs :** aucun

**Blocked by:** `v2-collectif/30` (livré).

**Bloque :** 21e, 21i ; 16i.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 55 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h 10** |

Confiance : moyenne. Hypothèses : le hors-jeu passe par la remise en jeu existante (`restart.foul_restart`), avec un type ; le surcroît de temps mort change le temps de jeu effectif, mesuré et non réglé ici.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** coup franc indirect construit à la main à 20 m face au but : jamais de tir direct, passe à un coéquipier, tir possible après sa touche ; direct au même endroit : tir possible ; hors-jeu sifflé : ballon mort, adversaires à 9,15 m
- **Statistiques (séries de matchs) :** 50 matchs avant/après : temps de jeu effectif, hors-jeu par match, coups francs par type ; aucun tir direct sur un indirect

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Type de coup franc tracé ; le hors-jeu donne une vraie remise en jeu indirecte
- [ ] Temps de jeu effectif et hors-jeu par match mesurés avant/après, écarts expliqués
- [ ] Aucun tir direct sur un indirect (scène et 50 matchs)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
