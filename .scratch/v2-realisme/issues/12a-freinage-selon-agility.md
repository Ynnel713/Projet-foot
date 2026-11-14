# 12a: Freinage individualisé : Agility

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (un joueur agile s'arrête plus court). **Catégorie :** physique.

**Constat vérifié :** `DECEL_MAX_MPS2 = 7.0` (`movement.py:27`) est commun à tous « en attendant Agility ».

**What to build:** Le freinage maximal dépend d'Agility (courbe partagée, bornes sourcées ou validées).

**Attributs :** Agility (freinage)

**Lien avec l'existant :** découpe (validée le 05/11/2026) de `v2-attributs-restants/07b` : freinage.

**Blocked by:** 01f (Fabrique de scènes de test partagée).

**Bloque :** 12b, 12g.

**Status:** implémenté (14/11/2026) — en attente de /valider-ticket-simulafoot

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 30 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 25** |

Confiance : élevée. Hypothèses : seule la constante devient une courbe.
Temps machine, non compté : suite complète (environ 40 min).

## Tests

- **Comportementaux (profils comparés) :** Agility 99 contre 11 : distance d'arrêt depuis 7 m/s plus courte

## Acceptance criteria

- [x] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code (délégation du 14/11/2026 : « je valide automatiquement toutes tes recommandations »)
- [x] Effet d'Agility mesuré en scène A/B (arrêt depuis 7 m/s : 4,09 m à 11, 3,50 m à 55, 3,07 m à 99, pas de 0,1 s ; mêmes valeurs à 0,05 et 0,15 s à 3 cm près)
- [x] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour (Agility déjà permise dans `movement`, prévue pour 12a ; carte mise à jour)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions (`12a-det1`, `12a-det2`)
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md` (2 938 = 2 933 + 5)

## Comments

**14/11/2026, constantes proposées et validées par délégation du propriétaire** (« je valide automatiquement toutes tes recommandations », message du 13/11/2026). Freinage maximal selon Agility, linéaire : 6 m/s² à 11, 7 à 55 (la valeur commune d'avant : rythme de la base inchangé), 8 à 99. Écart 99/11 de 1,33, sous ceux d'Acceleration (1,5) et de la rotation (1,67) : le freinage dépend aussi de la force des jambes, hors Agility. Chiffres réels par niveau : non trouvés (Harper, Carling et Kiely 2019 : les freinages au-dessus de 3,5 m/s² sont fréquents en match, valeur maximale non donnée). Estimation annoncée au démarrage : 1 h 25 (celle du ticket).

**14/11/2026, implémentation.** `movement.decel_max_mps2(Agility)` (`_DECEL_POINTS`), lu une fois par pas dans `movement.step` par la façade `effective_rating` ; remplace `DECEL_MAX_MPS2` dans la loi d'arrivée et le freinage (constante gardée comme valeur à 55). Agility lue une seule fois pour le freinage et la rotation du corps (07f), même valeur. Tests : `tests/test_v2engine_freinage_agility.py` (courbe, arrêt plus court à 99 qu'à 11 à trois pas de calcul, freinage mesuré borné par la courbe, loi d'arrivée) ; `test_v2engine_cinematique.py` : la borne de freinage lit la courbe à l'Agility par défaut (60, 7,11 m/s²).

**14/11/2026, mesure, suite et déterminisme.** Série appariée de 30 matchs (graines 50 à 79, `bench_series`, `.scratch/v2-realisme/mesures/12a-serie.txt`), comparée à l'état du 07g (`12a-comparaison-07g.txt`) : aucun écart global significatif (buts − 0,30, IC − 1,53 ; + 0,93 ; xG − 0,32, IC − 0,83 ; + 0,19 ; km par joueur − 0,05 ; course au-dessus de 19,8 km/h + 0,1 point ; sprints par joueur + 0,3), attendu : la courbe garde 7 m/s² à 55 et la base est autour de 55 à 65. Deux écarts de sprints par poste (MDC + 1,7, RB − 1,3) sur une quarantaine d'indicateurs : au niveau du hasard. Suite complète : 2 938 passés, 0 ignoré, 14 désélectionnés (2 933 + 5 ; `12a-suite.txt`) ; `CLAUDE.md` mis à jour. `12a-det1` et `12a-det2` identiques hors temps de calcul. V1 inchangée.

**14/11/2026, durée.** Estimation 1 h 25 ; durée réelle environ 1 h 05 (analyse 10, développement 15, tests 15, intégration 25), − 24 %, sous 30 %. Durée estimée à l'horloge de la session hors attentes machine, non chronométrée. Temps machine hors total : série de 30 matchs (environ 30 min), suite complète, déterminisme 2 x 2 matchs.

