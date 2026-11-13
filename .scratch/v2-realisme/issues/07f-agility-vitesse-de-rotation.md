# 07f: Agility : vitesse de rotation du corps

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (avancé le 05/11/2026 sur décision du propriétaire : base du contrôle orienté et du jeu à une touche (`v2-collectif/31`)). **Catégorie :** physique.

**Constat vérifié :** Agility n'est lue nulle part dans `v2engine/` ; la carte des attributs lui donne « changer de direction, freiner, se retourner ».

**What to build:** La vitesse angulaire maximale du 07a dépend d'Agility (courbe partagée). Le freinage et les changements de trajectoire restent aux tickets 12a et 12b (même attribut, effets distincts, inscrits dans la carte).

**Attributs :** Agility (rotation du corps)

**Blocked by:** 07a (Orientation du corps : état propre et rotation bornée).

**Bloque :** 04h, 07g, `v2-collectif/31`.

**Status:** implémenté (13/11/2026) — en attente de /valider-ticket-simulafoot

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 30 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 25** |

Confiance : élevée. Hypothèses : courbe partagée de `attributes`.
Temps machine, non compté : suite complète (environ 40 min).

## Tests

- **Comportementaux (profils comparés) :** Agility 99 contre 11 : demi-tour plus rapide d'un rapport validé

## Acceptance criteria

- [x] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code (vitesse angulaire réelle : non trouvée ; valeurs recommandées, validées par délégation, voir Comments)
- [x] Effet d'Agility mesuré en scène A/B (demi-tour 0,40 s à 99 contre 0,68 s à 11 au pas de 0,02 s (0,67 s en continu), rapport 1,67 ; `tests/test_v2engine_agilite.py`)
- [x] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour (Agility lue dans `movement` seulement, par la façade)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`) : 1 h 10 contre 1 h 25, − 18 %
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions (`07f-det1`, `07f-det2`)
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md` (2 805 passés, 0 ignoré, 14 désélectionnés = 2 802 + 3 ; `07f-suite.txt`)

## Comments

**13/11/2026, lancement.** Validation du propriétaire : « Ok 07f ». Estimation annoncée : 1 h 25, confiance élevée. Délégation permanente du propriétaire pour les constantes recommandées (« Je valide automatiquement toutes tes recommandations et les conseils d'experts », 12/11/2026, reprise au 18j).

**13/11/2026, constantes.** Vitesse angulaire réelle du corps d'un footballeur : non trouvée (recherche du 13/11/2026 : études du demi-tour, Dos'Santos et al. 2021, *Sports*, Zago et al., donnent des temps de virage avec course et freinage, pas une vitesse de rotation sur place ; une étude de fiabilité, 2023, juge la vitesse angulaire de pic mesurée par centrale inertielle peu fiable). **Recommandation retenue (délégation)** : repères linéaires, même forme que Pace et Acceleration (`movement._lerp`) : 270°/s à 11, 360°/s à 55 (valeur du 07a, gardée pour le joueur moyen), 450°/s à 99 ; demi-tour 0,67 / 0,5 / 0,4 s, écart 99/11 de 1,67 (Acceleration : 1,5). Base réelle : Agility moyenne 62,4, médiane 65 (7 138 joueurs) : le joueur médian fait son demi-tour en 0,48 s.

**13/11/2026, code.** `movement.turn_rate_rad_s(agility)`, `movement._TURN_POINTS` ; `movement.step` lit Agility par la façade (`condition.effective_rating`), aucun champ ajouté à `PlayerState`. `TURN_RATE_RAD_S` gardé (valeur à 55). Freinage et virage non touchés (12a, 12b).

**13/11/2026, mesures (`.scratch/v2-realisme/mesures/07f-*`).**
- Aucun effet sur le jeu : `measure_v2 2` identique au 18k à graine fixée, 2 420 lignes sur 2 420 hors temps de calcul (`07f-det1.txt` contre `18k-det1.txt`). Le cap reste sans effet avant 07b, 07d et 07e.
- Déterminisme : deux exécutions identiques hors temps de calcul (`07f-det1`, `07f-det2`).
- Temps de calcul 75,5 s par match contre 70,1 au 18k : mesuré pendant la suite complète, sur la même machine, non comparable (charge).
- Tests : 3 ajoutés (`tests/test_v2engine_agilite.py` : repères et bornes, scène A/B du demi-tour, course identique et cap seul différent) ; `test_v2engine_orientation.py` et `test_v2engine_reception.py` lisent la vitesse du joueur par défaut des scènes (Agility 60, 370°/s) au lieu de `TURN_RATE_RAD_S` ; `test_v2engine_rayon_attributs.py` : Agility autorisée dans `movement`.
- Suite complète : 2 805 passés, 0 ignoré, 14 désélectionnés (2 802 + 3 ; `07f-suite.txt`) ; `CLAUDE.md` mis à jour. Aucun fichier d'interface touché (UI non reconstruite).

**Durée.** Estimée 1 h 25. Réelle environ 1 h 10, non chronométrée (analyse 20 min, développement 10 min, tests 15 min, intégration et vérifications 25 min) : − 18 %. Temps machine hors total : 2 x 2 matchs (`measure_v2 2`, environ 3 min), suite complète (8 min 34).
