# 07d: Temps de contrôle et enchaînement selon l'orientation

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (dos au jeu, il faut se retourner avant d'attaquer). **Catégorie :** exécution.

**Constat vérifié :** `possession.reception_delay_s` (`possession.py:170`) ne dépend que de First Touch et de la pression.

**What to build:** Le temps avant la première décision augmente pour une réception dos au jeu (rotation nécessaire) et baisse de profil ; dos au jeu, les options vers l'avant ne sont accessibles qu'après la rotation (le porteur peut jouer en remise avant).

**Attributs :** aucun

**Lien avec l'existant :** à coordonner avec `v2-collectif/31` (contrôle orienté, à faire) : 31 règle la durée par First Touch et Technique, ce ticket ajoute l'orientation, sans toucher à 31.

**Blocked by:** 07c (Réception de face, de profil ou dos au jeu); `v2-collectif/31`.

**Bloque :** 07g.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 55** |

Confiance : moyenne. Hypothèses : 31 livré avant ; sinon dépendance à rediscuter.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** même joueur, même ballon : dos au jeu plus lent que de profil
- **Statistiques (séries de matchs) :** 50 matchs : temps de possession individuelle par type de réception

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Effet de l'orientation mesuré en scène
- [ ] Temps de possession individuelle rapporté (repère 2-3 s)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Comments

**12/11/2026, repris du 07c (réserves acceptées par délégation du propriétaire).**
- A1 (condition) : avant de lire le type de réception, le combiner avec la direction d'arrivée du ballon (`ReceptionEvent.ball_facing_deg`, `match._ball_facing_deg`) : un ballon qui arrive à plus de 90° du cap est un contrôle à l'aveugle ou dos au jeu, pas « de face ». Test : cap vers le but, ballon de derrière, joueur non visé, type ou pénalité attendus explicitement.
- A2 : angle d'arrivée d'un ballon arrêté (0° aujourd'hui) : prendre l'angle entre le cap et la position du ballon.
- A3 : hystérésis autour de `movement.FACING_RUN_SPEED_MPS` (réserve A1 du 07a), à faire dès que le cap agit sur le jeu.
- Mesure : la part de dos au jeu de l'avant-centre (0,4 % au 07c) reste irréaliste tant que le marqueur collé n'empêche pas de se tourner (04i, 08c).


**13/11/2026, repris du `v2-collectif/31` (31a à 31c livrés).** Le temps de réception vaut désormais 2,3 s x 0,6 (contrôle orienté) ou x 1,4 (non orienté), la chance d'orienter dépendant de First Touch, de la vitesse du ballon et de Technique (`possession.oriented_control_probability`, `reception_delay_s(..., oriented=)`) ; le contrôle orienté tourne aussitôt le corps vers le jeu (`match._orient`). Ici : ajouter l'effet de l'orientation du corps au moment du contrôle sans repasser par Technique ni par la vitesse du ballon (remarque de l'expert au 31c), et recontrôler les buts par match (3,48 après le 31c, environ 0,9 erreur type au-dessus du 31b).
