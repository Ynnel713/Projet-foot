# 11a: Collision : la vitesse change aussi, pas seulement la position

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (deux joueurs qui se heurtent doivent ralentir). **Catégorie :** physique.

**Constat vérifié :** `match._resolve_player_collisions` (`match.py:114`) corrige les positions à moitié chacun, sans toucher les vitesses.

**What to build:** Lors d'un chevauchement, retirer aux deux joueurs la composante de vitesse dirigée l'un vers l'autre (choc mou), en plus de la correction de position.

**Attributs :** aucun

**Blocked by:** 01f (Fabrique de scènes de test partagée).

**Bloque :** 11b.

**Status:** livré (14/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 35 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 35** |

Confiance : élevée. Hypothèses : pas encore de masse (11b).
Temps machine, non compté : suite complète (environ 40 min) ; mesure 20 matchs.

## Tests

- **Unitaires (scène contrôlée) :** deux joueurs face à face à 5 m/s : vitesses de rapprochement nulles après contact

## Acceptance criteria

- [x] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code (délégation du 13/11/2026 : « je valide automatiquement toutes tes recommandations »)
- [x] Vitesse de rapprochement annulée au contact (scène : face à face à 5 m/s chacun, vitesses le long de l'axe nulles après le contact ; coureur à 6 m/s contre joueur arrêté, 3 m/s chacun ; vitesse tangentielle gardée ; quantité de mouvement conservée)
- [x] Aucune régression des duels (suite V2 : tous les tests de duels passent ; en match, tacles + 1,7, pertes de balle − 1,8, fautes − 0,2, pertes en conduite + 3,3 : non significatifs)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions (`11a-det1`, `11a-det2`)
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md` (2 962 = 2 955 + 7)

## Comments

**14/11/2026, constante proposée et validée par délégation du propriétaire** (« je valide automatiquement toutes tes recommandations », 13/11/2026). Choc mou : coefficient de restitution nul (`match.COLLISION_RESTITUTION = 0.0`), masses égales en attendant Strength (11b) : au contact, la composante de vitesse qui rapproche les deux joueurs le long de la normale est retirée, moitié chacun ; la composante tangentielle et celle qui les éloigne sont gardées. Chiffre réel : non trouvé (un contact d'épaule n'est ni un rebond ni un placage : choc mou, ordre de grandeur). Estimation annoncée au démarrage : 1 h 35 (celle du ticket).

**14/11/2026, implémentation.** `match._resolve_player_collisions` : après la correction de position (moitié chacun, inchangée), impulsion le long de la normale de contact quand la vitesse relative les rapproche (`closing > 0`). Tests : `tests/test_v2engine_collision_vitesse.py` (7 : restitution nulle, face à face à 5 m/s, coureur contre joueur arrêté, vitesse tangentielle gardée, joueurs qui s'éloignent, sans contact, quantité de mouvement conservée).

**14/11/2026, mesure, suite et déterminisme.** Série appariée de 30 matchs (graines 50 à 79, `bench_series`, `.scratch/v2-realisme/mesures/11a-serie.txt`) contre l'état du 12f (`11a-comparaison-12f.txt`) : passes − 13 par match (− 25,9 ; − 0,9), passes réussies + 0,5 point (0,0 ; + 1,1), temps par possession + 0,03 s (+ 0,01 ; + 0,05) : un presseur qui heurte le porteur ne le traverse plus et garde moins sa vitesse, le porteur garde un peu plus le ballon ; tacles, pertes de balle, fautes, buts (− 0,3), xG (+ 0,28), tirs, km : non significatifs. 210 indicateurs significatifs sur 2 649 (7,9 %, 5 % attendus par le hasard) : effet réel mais petit. Suite complète : 2 962 passés, 0 ignoré, 14 désélectionnés (2 955 + 7 ; `11a-suite.txt`) ; `CLAUDE.md` mis à jour. `11a-det1` et `11a-det2` identiques hors temps de calcul. V1 inchangée.

**14/11/2026, durée.** Estimation 1 h 35 ; durée réelle environ 55 min (analyse 10, développement 10, tests 15, intégration 20), − 42 % : impulsion le long de la normale en une dizaine de lignes, sans masse (11b), code et tests écrits pendant les attentes machine du 07g ; durée estimée à l'horloge de la session hors attentes machine, non chronométrée. Temps machine hors total : série de 30 matchs, suite complète, déterminisme 2 x 2 matchs.

**14/11/2026, clôture (passage 1).** Expert : APPROVED (empreinte 7e7aea25). QC : VALIDÉ. Clôture journalisée : VALIDÉ. Facultatifs de l'expert : A1, résolution en une passe séquentielle par paire (dans un groupe de trois joueurs ou plus, une vitesse de rapprochement résiduelle peut rester ; 2 ou 3 itérations avec le 11b) ; A2, reconstruction de la position du défenseur au contre (match.py:435) avec la vitesse d'après le choc, écart de quelques centimètres, déjà présent avant. À surveiller au 11b : conservation de la quantité de mouvement pondérée par les masses, volume de passes et de tacles.

