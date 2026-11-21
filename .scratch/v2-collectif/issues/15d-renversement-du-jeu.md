# 15d: Renversement du jeu quand un côté est saturé

**Chantier :** `v2-collectif` (audit de réalisme du propriétaire du 21/11/2026, piste « switch of play »). **Priorité :** P1. **Catégorie :** décision.

**Constat vérifié (21/11/2026) :** le changement de jeu en diagonale est renvoyé au ticket 15 par `32-types-de-passes.md` (« Le changement de jeu en diagonale et le jeu long face au pressing restent au ticket 15 »), mais le 15 a été découpé en `15a` (court ou long selon le pressing, depuis la zone de construction) et `15b` (troisième homme, attirer le pressing), et aucun des deux ne le couvre ; `15c` ne traite que le jeu long des défenseurs. Aucune notion de côté saturé ni de côté opposé dans `v2engine/` (seul le latéral du côté opposé est cité comme appelant possible, `cerveau.CALLER_IF_FREE`).

**What to build:**
1. Lecture du côté saturé : sur le monde perçu du porteur (08d), adversaires et coéquipiers dans le couloir et le demi-espace du ballon (`09a`) contre ceux du côté opposé.
2. Valeur de la passe vers le côté opposé : quand le côté du ballon est saturé, la passe longue en diagonale (ou le relais en deux passes par l'axe, `v2-collectif/14`) vers un coéquipier libre du côté opposé prend la valeur de l'espace qu'il trouve (valeur future de la passe, `v2-collectif/13`) ; le risque reste celui du calcul de passe existant (passe longue, lobée au `32b`).
3. Côté opposé disponible : le joueur du côté faible (ailier ou latéral) tient la largeur (`09b`) pour être une solution.
4. Mesure : renversements par match (passe qui change de côté de plus de 30 m en largeur, ou deux passes en moins de 4 s), part réussie, gain de terrain après.

**Attributs :** Vision (voir le côté opposé, rayon existant), Passing / Long Passing selon la carte (exécution), Decisions (choisir) ; cumul à justifier dans `docs/CARTE_ATTRIBUTS_V2.md` (ADR 0002).

**Constantes à proposer avant le code :** seuil de saturation (le même que celui du `v2-realisme/30b`, chiffré au `30a` : une seule définition), distance minimale du changement de côté, poids dans la décision. Chiffre réel à sourcer : nombre de changements de jeu par match (non trouvé à ce jour).

**Blocked by:** `v2-realisme/30b` (voir le joueur libre : la portée de Vision actuelle, 30 m à la médiane, exclut le côté opposé), `v2-realisme/09a` (couloirs), `v2-realisme/09b` (occupation de la largeur), `v2-collectif/32b` (passe lobée), lui-même bloqué par `v2-hauteur-ballon/03` (portée selon la hauteur), qui attend `v2-hauteur-ballon/02a`.

**Bloque :** `v2-collectif/22b` (calibration tactique).

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications (50 matchs appariés) | 30 min |
| **Total (travail effectif)** | **2 h 15** |

Confiance : faible (dépend de la forme de la passe lobée du 32b ; découpage à examiner avant le code : lecture de la saturation et mesure, puis décision). Hypothèses : la décision du porteur reste dans `decision.py` ; la saturation lit le monde perçu sans nouveau mécanisme de perception.
Temps machine, non compté : suite complète ; série appariée de 50 matchs.

## Acceptance criteria

- [ ] Constantes et chiffre réel validés par le propriétaire avant le code ; découpage examiné
- [ ] Scène : côté du ballon saturé et coéquipier libre du côté opposé : le porteur renverse plus souvent qu'aujourd'hui ; côté non saturé : pas de renversement forcé
- [ ] Renversements par match mesurés, dans le repère réel retenu ; part réussie rapportée
- [ ] Pas de régression mesurée (50 matchs appariés) : passes, pertes, buts, tirs avec intervalle
- [ ] Déterminisme à graine fixée ; durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 %
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
