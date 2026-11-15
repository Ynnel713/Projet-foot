# 11e: Validation des contacts physiques

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (contrôle de cohérence Strength / Balance / Agility). **Catégorie :** validation.

**Constat vérifié :** aucun indicateur de contact hors tacles et fautes.

**What to build:** Indicateurs : collisions par match, duels d'épaule gagnés par écart de Strength, actions poursuivies après contact par Balance (12c). Rapport sur 50 matchs.

**Attributs :** aucun

**Blocked by:** 11c (Duel épaule contre épaule à la course); 11d (Le tacle selon l'angle d'approche et la vitesse relative); 12c (Balance : rester debout et continuer après un contact).

**Bloque :** rien.

**Status:** livré (15/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 10 min |
| Développement | 35 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 25** |

Confiance : élevée. Hypothèses : lecture de la trace.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Statistiques (séries de matchs) :** 50 matchs : rapport publié

## Acceptance criteria

- [x] Indicateurs définis et ajoutés
- [x] Chaque attribut agit sur son seul effet (règle R1 vérifiée)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Comments

**15/11/2026, démarrage.** Blocage par 11d levé (11d livré, `9c59a2e`). Estimation annoncée : 1 h 35 (1 h 25 du ticket + 10 min pour les remarques facultatives A1 et A2 de l'expert sur le 11d et le statut du 11d). Critères chiffrés posés avant le code : part du contact du plus fort conforme à la courbe du 11b par écart de Strength ; duels d'épaule gagnés par le plus fort croissants avec l'écart ; R1 : à Strength quasi égale (moins de 5 points), part gagnée par le meilleur en Balance avec un IC contenant 50 % ; vitesse perdue et délai décroissants avec Balance ; part du porteur bousculé gardant le ballon 1 s après, rapportée par tranche ; tacles par angle : faute croissante de la face vers l'arrière ; indicateurs existants identiques à `11d-apres` (le banc n'observe que).

**15/11/2026, implémentation.** `scripts/v2_indicators.py` : tranches (`strength_gap_band`, `balance_band`, `approach_band`), `Collector.on_collision`, `on_shoulder_duel`, `on_unsettle` (porteur suivi 1 s, `_close_unsettled_carriers` au tick), `on_tackle_approach`. `scripts/measure_v2.py` : enveloppes de `match.contact_share`, `match._unsettle`, `match.resolve_shoulder_duel` (restaurées), angle au tacle, `contact_report`. Aucun fichier du moteur modifié. Tests : `tests/test_v2_indicators_contacts.py`.

**15/11/2026, mesure (50 matchs, `11e-serie.txt`, `docs/INDICATEURS_V2.md` section 44).** Indicateurs existants identiques à `11d-apres.txt`. Part du contact du plus fort 0,534 / 0,604 / 0,691 / 0,750 (écart de Strength 0-9 / 10-19 / 20-39 / 40+) ; duels d'épaule au plus fort 56 / 67 / 83 / 86 % ; R1 : 47 % au meilleur en Balance à Strength quasi égale (252 duels, IC ~41-53 %) ; vitesse perdue 33 / 23 / 15 / 7 % et délai 0,50 / 0,35 / 0,23 / 0,13 s (Balance < 50 / 50-64 / 65-79 / 80+) ; porteur bousculé gardant le ballon 1 s après : 95,6 / 95,6 / 96,2 / 94,8 % (plat) ; tacles de face / de côté / par derrière : 34 / 33 / 33 % des tentatives, fautes 38 / 48 / 65 %, gagnés 21 / 17 / 12 %. Constats hors périmètre : 997 contacts francs par match dont 337 entre coéquipiers (1 099 déséquilibres par match) ; un tiers des tacles par derrière (04j) ; Balance sans effet visible sur la conservation du ballon. `11e-det1` et `11e-det2` identiques hors temps de calcul.

**15/11/2026, suite complète.** 3 130 passés, 0 ignoré, 14 désélectionnés (3 105 + 25 ; `11e-suite.txt`) ; `CLAUDE.md` mis à jour. V1 inchangée (aucun fichier V1 touché).

**15/11/2026, durée.** Estimation annoncée 1 h 35 ; durée réelle environ 1 h 30 (analyse 15, développement 30, tests 15, intégration 30), − 5 % : collecte branchée sur les points d'entrée publics du moteur, sans le modifier ; ajout non prévu du décompte des contacts entre coéquipiers après le premier match d'essai. Durée estimée à l'horloge de la session hors attentes machine et échanges avec le propriétaire, non chronométrée. Temps machine hors total : série de 50 matchs (33 min), suite complète (11 min), déterminisme 2 x 2 matchs, deux matchs d'essai.

**15/11/2026, passage 1 de l'expert : APPROVED ; QC VALIDÉ ; clôture VALIDÉ** (journal, `v2-realisme/11e/cloture`). Remarques facultatives, non traitées : A1 porteurs bousculés en attente non purgés en fin de match (au plus un cas par match, impact négligeable) ; A2 « ballon encore à l'équipe 1 s après » peu sensible (base ~95 %, fautes subies et passes en vol comptées gardées) : la conclusion « Balance sans effet visible » vaut pour cet indicateur, un indicateur plus fin (perte sans faute en 2-3 s) est à envisager ; A3 aucun ticket ne traite les contacts francs entre coéquipiers (ticket d'évitement recommandé). À surveiller : ~1 000 contacts francs par match pèsent sur le rythme via les délais de Balance. Fiche du ticket et `docs/PLAN_V2.md` laissés hors des fichiers revus (suivi documentaire), pour un statut à jour dans le commit.

