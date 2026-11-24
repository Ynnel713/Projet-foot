# 04l: Duel un contre un : le changement de rythme (démarrage-arrêt)

**Chantier :** `v2-realisme` (complément de l'audit du dribble, 17/11/2026, demande du propriétaire). **Priorité :** P2. **Catégorie :** exécution.

**Constat vérifié (17/11/2026) :** la conduite garde une vitesse réglée par Dribbling et la pression (`04d`) ; le porteur ne ralentit jamais volontairement pour repartir. Le freinage selon Agility (`12a`) est une capacité physique, pas un geste de dribble.

**What to build:** face à un défenseur qui l'accompagne de côté ou de face, le porteur peut freiner presque à l'arrêt puis repartir aussitôt. Le défenseur, lancé, freine plus tard ou repart moins vite : l'écart obtenu dépend du freinage et de la relance des deux joueurs (capacités physiques réelles, R5) et de la lecture du défenseur. Variante : le porteur s'arrête et repart dans une autre direction (lien avec 04h, sans recompter le crochet). Geste tracé et affiché.

**Attributs (ADR 0002, poids à proposer) :**
- porteur, contexte « changement de rythme » (exécution) : Dribbling (garder le ballon pendant l'arrêt), Agility (freinage, via `12a`), Acceleration (relance, capacité R5) ;
- défenseur, contexte « suivre le rythme » : Positioning (rester à distance), Anticipation (lire l'arrêt) ; Agility et Acceleration par la physique, sans bonus de plus.

**Lien avec l'existant :** complète le découpage de `v2-attributs-restants/07a`.

**Blocked by:** 04g (contournement), 04o (état du défenseur, ajouté le 24/11/2026), `12a` (freinage selon Agility), `v2-attributs-contextes/01` et `02`.

**Bloque :** 04n.

**Status:** à faire (constantes et chiffres réels à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 25 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : le freinage et la relance passent par `movement.step` (12a) ; le geste est une cible de conduite et une intensité, pas un nouveau moteur de déplacement.
Temps machine, non compté : suite complète ; mesure 50 matchs.

## Tests

- **Scènes :** défenseur qui accompagne à 1,5 m à pleine vitesse : écart après l'arrêt-départ plus grand pour un porteur à Agility et Acceleration hautes ; défenseur à Anticipation 99 garde un écart plus faible qu'à 11.
- **Statistiques (50 matchs) :** changements de rythme par match, écart moyen obtenu, part qui mène à une élimination.

## Acceptance criteria

- [ ] Constantes produit, poids des contextes et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Geste tracé et affiché
- [ ] Effets des attributs probabilistes, jamais binaires ; physique réelle (R5) ; contextes déclarés et documentés ; pas de double comptage avec 12a et 04h
- [ ] Scènes et mesure 50 matchs ci-dessus
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
