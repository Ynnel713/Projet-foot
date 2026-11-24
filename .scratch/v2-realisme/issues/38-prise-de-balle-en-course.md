# 38: Prise de balle en course : contrôler sans casser son élan

**Chantier :** `v2-realisme` (demande du propriétaire du 24/11/2026, éléments sur la technique, point 1 « enchaînement / première intention » : contrôler en mouvement et déclencher aussitôt une accélération). **Priorité :** P1. **Catégorie :** exécution.

**Constat vérifié (24/11/2026) :** pendant la réception, tout porteur avance au pas de contrôle (`RECEPTION_SPEED_FACTOR`) vers le but adverse (`cerveau.py`, rôle porteur, `ball.receiving`), qu'il arrive lancé ou arrêté ; le délai avant sa première décision (`possession.reception_delay_s`) ne lit pas sa vitesse. Un joueur lancé dans l'espace freine donc pour contrôler, puis repart. Le jeu à une touche (`v2-collectif/31a`) ne couvre que la passe sans contrôle.

**What to build:** un receveur lancé (au-delà d'un seuil de vitesse, le même que le `07a` si possible) qui oriente son contrôle dans le sens de sa course (`36`) **garde une part de sa vitesse** : la touche pousse le ballon devant lui (`04e`) et il enchaîne en conduite, sans phase au pas. La course est un **terme de la difficulté du `26a`** (écart entre la vitesse du ballon et celle du receveur), pas un tirage distinct : l'issue reste continue, la touche trop longue étant la queue de la distribution (ballon libre, `04f`). Technique compense cette difficulté une seule fois par réception, dans le calcul du `26a`. La part de vitesse gardée découle de la distance de la touche obtenue (touche courte devant lui : il garde son élan ; touche longue : il doit la rattraper), sans courbe d'attribut propre. Un receveur arrêté ou dont la course ne va pas vers la direction choisie : inchangé.

**Hors de ce ticket :** passe en course (`v2-collectif/36b`) ; tir de première (`34a`).

**Attributs (ADR 0002) :** aucun effet nouveau : Technique (« contrôle en pleine course », carte) agit par le calcul du `26a`, une fois par réception ; First Touch inchangé (chance d'orienter, `31b`) ; Acceleration et Pace par la physique (R5), sans bonus.

**Blocked by:** `36` (direction du contrôle), `04e`, `04f`, `26a`.

**Bloque :** `39`, `v2-collectif/22a`.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 50** |

Confiance : moyenne. Hypothèses : la touche devant le porteur (`04e`) et la direction du contrôle (`36`) existent ; la part de vitesse gardée découle de la distance de touche du `26a`. Temps machine, non compté : série de 50 matchs (environ 40 min), suite complète (environ 20 min).

## Tests

- **Scènes :** receveur lancé à 7 m/s, passe dans sa course : vitesse 1 s après le contrôle plus haute à Technique 99 qu'à 11, et plus haute qu'aujourd'hui ; receveur arrêté : inchangé ; ballon plus rapide que la course : plus de touches trop longues.
- **Statistiques (50 matchs, avant / après) :** vitesse du porteur 1 s après une réception lancée, contre-attaques menées à terme (`v2-collectif/11`), pertes dans les 3 s, buts (dans le bruit).

## Acceptance criteria

- [ ] Constantes produit (seuil de course, poids de la course dans la difficulté du `26a`) et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Prise de balle en course tracée (vitesse avant et après)
- [ ] Scènes ci-dessus
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Comments
