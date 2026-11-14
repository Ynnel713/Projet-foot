# 11b: Collision asymétrique : Strength

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (le plus fort pousse le plus faible). **Catégorie :** physique.

**Constat vérifié :** la poussée est partagée à moitié quel que soit le joueur (`match.py:130-132`) ; Strength n'est lue que dans le tacle.

**What to build:** Répartir la correction de position et de vitesse selon un poids de contact qui dépend de Strength (courbe partagée) ; le joueur le plus faible est plus déplacé.

**Attributs :** Strength (duel de contact)

**Blocked by:** 11a (Collision : la vitesse change aussi, pas seulement la position).

**Bloque :** 04i, 11c, 12c, 15b, 16c.

**Status:** implémenté (14/11/2026) — en attente de /valider-ticket-simulafoot

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 30 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 25** |

Confiance : élevée. Hypothèses : pas de masse corporelle dans la base : Strength seule.
Temps machine, non compté : suite complète (environ 40 min).

## Tests

- **Comportementaux (profils comparés) :** Strength 90 contre 40 : déplacement subi au moins deux fois plus faible pour le plus fort (valeur validée)

## Acceptance criteria

- [x] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code (délégation du 13/11/2026 : « je valide automatiquement toutes tes recommandations »)
- [x] Effet de Strength mesuré en scène A/B (Strength 90 contre 40, chevauchement de 0,2 m : 0,05 m contre 0,15 m, trois fois moins pour le plus fort)
- [x] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour (Strength lue dans `duel`, déjà dans son rayon ; Strength seule, Balance non mélangée ; test de rayon inchangé et vert)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions (`11b-det1`, `11b-det2`)
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md` (3 058 = 3 051 + 7 ; `11b-suite.txt`)

## Comments

**14/11/2026, constante proposée et validée par délégation du propriétaire** (« je valide automatiquement toutes tes recommandations », 13/11/2026). Part du contact gagnée par chacun, `duel.contact_share` : `duel_probability(Strength A, Strength B)` (courbe de duel partagée, demi-étendue 40 points, pente 1) avec amplitude 0,25, bornes 0,25 et 0,75. À égalité 50/50 ; 10 points d'écart 58/42 ; 20 points 65/35 ; 40 points ou plus 75/25 (le plus fort trois fois moins déplacé). Le joueur qui gagne la part `s` subit `1 - s` de la correction de position et du choc mou du 11a : rapport de masses `s / (1 - s)`, quantité de mouvement conservée à masses pondérées. Chiffre réel : non trouvé (masses de 65 à 95 kg en Ligue 1, rapport ~1,5 ; l'appui et le gainage, portés par Strength, au-delà). Strength seule (Balance joue après le contact, ticket 12c). Estimation annoncée au démarrage : 1 h 25 (celle du ticket).

**14/11/2026, implémentation.** `duel.contact_share` (Strength lue dans `duel`, son rayon) ; `match._resolve_player_collisions` : correction de position et impulsion le long de la normale réparties selon cette part (moitié chacun à égalité, comme au 11a). Tests : `tests/test_v2engine_collision_strength.py` (7 : égalité, symétrie et bornes, scène A/B 90 contre 40, part croissante avec l'écart, choc mou et quantité de mouvement à masses pondérées, coureur faible contre joueur fort arrêté, vitesse tangentielle gardée) ; les 7 tests du 11a (masses égales) passent sans changement.


**14/11/2026, garde des attributs.** `tests/test_v2engine_garde_attributs.py` (17d) échouait pour Stamina : aucune divergence entre 11 et 99 sur les graines 1 à 3 du mini-match de 60 s (avant le changement : graine 1, pas 344 ; après : graine 4, pas 245 ; aucune non plus sur les graines 1 à 3 en 120 s). Stamina n'agit que par l'énergie (sprint entamé, réserve) : le partage des collisions change les trajectoires, l'effet n'apparaît plus par hasard dans les trois premières graines ; le code de Stamina n'est pas touché. Correction du test (ni suppression ni désélection) : plan propre à Stamina, mini-match de 60 s sur 10 graines, comme les attributs à effet rare.

**14/11/2026, mesure, déterminisme.** Série appariée de 30 matchs (graines 50 à 79, `bench_series`, `.scratch/v2-realisme/mesures/11b-serie.txt`), contre l'état du ticket 24 rejoué depuis un worktree de HEAD (`11b-avant-serie.txt`, comparaison `11b-comparaison-24.txt`) : aucun écart significatif sur les indicateurs principaux (passes − 7, IC − 23,9 ; + 9,6 ; passes réussies − 0,4 point ; tacles − 1,5, IC − 3,0 ; + 0,0 ; pertes de balle au contact − 1,8 ; fautes − 0,8 ; buts − 0,4 ; km par joueur − 0,06 ; temps par possession + 0,01 s). 139 indicateurs significatifs sur 2 660 (5,2 %, 5 % attendus par le hasard) : effet global au niveau du bruit, attendu (Strength autour de 55 à 70 dans la base, la plupart des contacts restent proches de 50/50). `11b-det1` et `11b-det2` identiques hors temps de calcul. V1 inchangée.

**14/11/2026, durée.** Estimation 1 h 25 ; durée réelle environ 1 h 10 (analyse 15, développement 10, tests 15, intégration 30), − 18 % : partage en une fonction et quatre lignes ; intégration allongée par la garde Stamina et par la série de référence à reconstruire (aucune série enregistrée à l'état du ticket 24 ; un premier lancement via `uv run` dans le worktree avait réinstallé le paquet du venv sur le worktree, corrigé par `uv sync` avant toute mesure retenue). Durée estimée à l'horloge de la session hors attentes machine et échanges avec le propriétaire, non chronométrée. Temps machine hors total : deux séries de 30 matchs, suite complète deux fois, déterminisme 2 x 2 matchs.
