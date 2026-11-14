# 12c: Balance : rester debout et continuer après un contact

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (Balance joue après le contact, Strength pendant). **Catégorie :** physique.

**Constat vérifié :** Balance n'entre que dans la résistance au tacle (moyenne avec Strength, `duel.py:58-64`) ; la carte la définit comme « continuer l'action APRÈS un contact ».

**What to build:** Après un contact perdu (collision 11b, duel d'épaule 11c, tacle sans perte), le joueur subit une perte de vitesse et un court délai avant d'agir, réduits par Balance. Balance est retirée de la résistance au tacle pour respecter son rayon (à valider : changement d'un mécanisme livré, nouveau comportement ici).

**Attributs :** Balance (après le contact)

**Lien avec l'existant :** découpe (validée le 05/11/2026) de `v2-attributs-restants/07b` : Balance, levée de la dérogation A3.

**Blocked by:** 11b (Collision asymétrique : Strength).

**Bloque :** 11e, 12g.

**Status:** livré (14/11/2026), validé expert + QC

**Point de vigilance :** retirer Balance du tacle change le ticket livré `v2-socle/03` : décision explicite du propriétaire avant le code.

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 55** |

Confiance : moyenne. Hypothèses : décision du propriétaire sur le tacle.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Comportementaux (profils comparés) :** Balance 99 contre 11 après le même contact : délai plus court et moins de vitesse perdue

## Acceptance criteria

- [x] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code (14/11/2026 : « Ok avec tes recommandations mais un seul ticket »)
- [x] Effet de Balance mesuré en scène A/B (même contact, Strength 40 contre 90 : Balance 99, délai 0,1 s et 5 % de vitesse perdue ; Balance 11, 0,6 s et 40 %)
- [x] Décision sur le tacle consignée (Balance retirée du tacle, Strength seule ; décision du propriétaire du 14/11/2026)
- [x] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour (Balance lue dans `duel` seule ; dérogation A3 levée et retirée de `TOLERATED_MIXES`)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions (`12c-det1`, `12c-det2`)
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md` (3 073 = 3 058 + 15 ; `12c-suite.txt`)

## Comments

**14/11/2026, décisions du propriétaire avant le code** (« Ok avec tes recommandations mais un seul ticket ») :
- **Tacle** : Balance retirée de la résistance du porteur, Strength seule (`duel.tackle_success_probability`) ; dérogation A3 levée. Change le mécanisme livré `v2-socle/03`.
- **Contact perdu** : collision dont le joueur reçoit la plus petite part (`duel.contact_share` ≤ 0,5 ; à égalité, les deux) à plus de 2 m/s de vitesse de rapprochement (`duel.CONTACT_MIN_CLOSING_MPS`, en dessous : frôlements au pas) ; ou tacle subi sans perdre le ballon, faute exclue.
- **Effet, réduit par Balance (courbe partagée, centre 62)** : vitesse perdue 99 → 5 %, 62 → 20 %, 11 → 40 % ; délai avant d'agir 99 → 0,1 s, 62 → 0,3 s, 11 → 0,6 s. Porteur : prochaine décision repoussée ; sans ballon : ni tacle ni contrôle pendant le délai ; délais non cumulés. Chiffre réel : non trouvé (un joueur bousculé met quelques dixièmes de seconde à se rééquilibrer, ordre de grandeur).
- **Découpage** proposé (12c-a après le contact, 12c-b tacle) refusé : un seul ticket. Estimation réannoncée au démarrage : 2 h 20 (au lieu de 1 h 55 : seuil de contact franc et double cas porteur / sans ballon).

**14/11/2026, implémentation.** `duel.after_contact_speed_loss` et `duel.after_contact_delay_s` (Balance lue dans `duel`, son rayon ; forme en S partagée, repères asymétriques de part et d'autre de la médiane) ; `match._resolve_player_collisions` rend les perdants d'un contact franc ; `match._unsettle` applique perte de vitesse et délai ; appelé après les collisions de chaque pas et après un tacle subi sans perte ni faute. `tests/scenes.py` (boucle recopiée du match) aligné. Tests : `tests/test_v2engine_balance_apres_contact.py` (13 : repères des courbes, décroissance, Balance hors du tacle, perdant du contact, égalité, frôlement, sans ballon, porteur et non-cumul, scène A/B 99 contre 11, tacle subi, faute exclue) ; `test_v2engine_rayon_attributs.py` : A3 retirée des mélanges tolérés ; commentaire de `test_v2engine_conduite.py` mis à jour.

**14/11/2026, test des scans.** `tests/test_v2engine_scan.py::test_a_simulated_match_traces_scans_and_the_memory_they_refresh_feeds_the_decision` échouait : sur la seule graine du test (20260923, 10 minutes), l'âge moyen de la mémoire du porteur était de 1,93 s avec scans contre 1,90 s sans (assertion : plus vieux sans scan). Sur 6 graines (20260923, 1 à 5) : 1,47 s avec contre 1,95 s sans, 5 graines sur 6 dans le bon sens ; avant le 12c, 1,27 s contre 1,90 s, 6 sur 6. Le porteur bousculé décide plus tard (délai de Balance), sa mémoire a vieilli d'autant : effet attendu, petit. Correction du test (ni suppression ni désélection, assertion inchangée) : quatre graines (20260923, 1, 2, 3) mises en commun ; durée du fichier 86 s.

**14/11/2026, mesure, suite et déterminisme.** Série appariée de 30 matchs (graines 50 à 79, `bench_series`, `12c-serie.txt`) contre l'état du 11b (`12c-comparaison-11b.txt`) : aucun écart significatif sur les indicateurs principaux (passes − 6,9, IC − 28,8 ; + 15,1 ; passes réussies + 0,2 point ; tacles + 0,2 ; pertes au tacle + 1,3, IC − 0,03 ; + 2,6, à la limite : le porteur résiste par Strength seule ; pertes au contact + 1,6 ; fautes + 0,2 ; buts + 0,8 ; xG neutre − 0,07 ; km + 0,03 ; temps par possession + 0,01 s). 179 indicateurs significatifs sur 2 653 (6,7 %, 5 % attendus par le hasard), surtout des tranches de 15 min à petits effectifs : effet global petit. Suite complète : 3 071 passés, 0 ignoré, 14 désélectionnés (3 058 + 13 ; `12c-suite.txt`) ; `CLAUDE.md` mis à jour (avec le compte du 11b, resté en attente). `12c-det1` et `12c-det2` identiques hors temps de calcul. V1 inchangée.

**14/11/2026, durée.** Estimation réannoncée 2 h 20 (ticket : 1 h 55) ; durée réelle environ 1 h 35 (analyse 20, développement 25, tests 25, intégration 25), − 32 % : deux fonctions de courbe et un point d'application (`_unsettle`) réutilisé par la collision et le tacle ; intégration allongée par le test des scans (série de graines avant / après) ; durée estimée à l'horloge de la session hors attentes machine et échanges avec le propriétaire, non chronométrée. Temps machine hors total : série de 30 matchs, suite complète deux fois, 12 matchs de 10 minutes (graines du test des scans), déterminisme 2 x 2 matchs.

**14/11/2026, clôture (passage 1) : expert REJECTED** (empreinte 2210b80e), QC non lancé. A1 [BLOQUANT] : le délai sans ballon écrivait `control_ban_until_s`, que `defense._watch_triggers` lit comme un contrôle raté ; toute bousculade perdue loin du ballon lançait 5 s de pressing d'équipe adverse (pressings d'équipe déclenchés + 120 par match, IC + 89 ; + 152, + 11,5 % ; écart ligne-ballon, porteur pressé − 0,32 m). A2 [RÉSERVE] : bilan de mesure à relister (pressing et bloc). A3 [FACULTATIF] : gardien privé de contrôle après un contact perdu, à surveiller. **Correction** : champ propre `BallState.unsettled_until_s`, écrit par `_unsettle`, lu au contact du ballon et dans le choix du tacleur ; `control_ban_until_s` et `tackle_ban_until_s` ne sont plus touchés. Tests ajoutés : pas de pressing d'équipe après un contact perdu ; ballon qui échappe au joueur déséquilibré pendant le délai, joué après (15 tests dans le fichier).

**14/11/2026, mesure après correction (A1, A2).** Série appariée de 30 matchs relancée (graines 50 à 79, `12c-serie.txt`, comparaison `12c-comparaison-11b.txt`, remplace la précédente) : pressings d'équipe déclenchés + 8,6 par match (IC − 7,4 ; + 24,6, non significatif, au lieu de + 120) ; pressings + 6,5 (non significatif) ; écart ligne-ballon sans ballon, porteur pressé − 0,06 m (IC − 0,26 ; + 0,14, non significatif). Indicateurs principaux sans écart significatif : passes + 9,8, passes réussies + 0,1 point, tacles − 0,1, pertes au tacle + 1,5 (IC − 0,07 ; + 3,0, à la limite : le porteur résiste par Strength seule), pertes au contact + 0,2, fautes + 0,2, buts + 0,1, xG neutre − 0,33, km par joueur + 0,11 (IC − 0,004 ; + 0,23, à la limite), temps par possession + 0,01 s. Pressing et bloc (A2) : seuls écarts significatifs, plans abandonnés pour ligne fermée + 1,1 point et passes abandonnées après rotation pour ligne fermée − 2,1 par match, petits. 202 indicateurs significatifs sur 2 657 (7,6 %, 5 % attendus par le hasard), dont 126 parmi les 1 668 indicateurs par tranche de 15 minutes à petits effectifs (7,6 %, 5,9 % au 11b) : effet global petit. Suite complète : 3 073 passés, 0 ignoré, 14 désélectionnés (3 058 + 15). `12c-det1` et `12c-det2` identiques hors temps de calcul. V1 inchangée.

**14/11/2026, durée révisée.** Correction du rejet comprise : environ 2 h 05 (analyse 20, développement 35, tests 35, intégration 35), − 11 % sur l'estimation réannoncée de 2 h 20. Temps machine hors total : deux séries de 30 matchs, suite complète trois fois, 12 matchs de 10 minutes, déterminisme 2 x 2 x 2 matchs.

**14/11/2026, clôture (passage 2).** Expert : APPROVED (empreinte 3884c91e). QC : VALIDÉ. Clôture journalisée : VALIDÉ. Facultatifs de l'expert, non traités (toucher au code rouvrirait la revue) : A1, un joueur qui perd deux contacts francs dans le même pas subit deux fois la perte de vitesse (mêlée à trois, dédoublonner les perdants) ; A2, le porteur bousculé qui perd ensuite le ballon peut tacler ou contrôler aussitôt (écrire aussi `unsettled_until_s` pour le porteur) ; A3, double commentaire dans le filtre des tacleurs (`match.py`). À surveiller : pertes au tacle (+ 1,5) et distance par joueur (+ 0,11 km), à la limite, aux tickets 11c et 11e ; à l'écran, un joueur bousculé ne doit pas paraître figé plus de quelques dixièmes de seconde.
