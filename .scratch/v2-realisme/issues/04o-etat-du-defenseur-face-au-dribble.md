# 04o: Le défenseur face au dribble : élan, appuis, distance et temps de réajustement

**Chantier :** `v2-realisme` (demande du propriétaire du 24/11/2026, éléments sur la technique, point 3 « distance et équilibre de l'adversaire » et point 6 « réaction des défenseurs »). **Priorité :** P1. **Catégorie :** exécution.

**Constat vérifié (24/11/2026) :** le presseur se présente à une distance d'arrêt réglée par Aggression (`defense.press_point`, `stop_distance_m`) ; sa physique a de l'inertie (freinage selon Agility `12a`, perte de vitesse en virage `12b`, rotation bornée `07a` / `07f`). Mais aucun geste de dribble n'existe encore, et les tickets de gestes (`04g` « éliminé pour un temps », `04h` « écart temporaire », `04k` « se fige ou se décale », `04m` « décalage latéral temporaire ») prévoient chacun leur propre état du défenseur battu, sans règle commune ni lecture de son élan au moment du geste.

**What to build:** une seule lecture, et un seul état, partagés par tous les gestes du duel :
- **vulnérabilité du défenseur au moment du geste** : distance au porteur (trop près : il se fait passer ; bonne distance : il voit venir), vitesse et direction de son élan par rapport à la direction du geste (lancé à pleine vitesse, ou ses appuis portés du mauvais côté, il est plus exposé au crochet et au changement de rythme ; campé à bonne distance, il l'est moins), orientation du corps (`07a`). Cette vulnérabilité entre dans la chance de réussite de chaque geste (`04g` à `04m`) et dans sa valeur au choix (`04n`), lue sur ce que le porteur perçoit (`08b`) ;
- **défenseur battu** : un état unique « déséquilibré » (durée, direction) qui coupe un instant sa capacité de tacler et de repartir ; la suite **vient de la physique existante** (freinage, virage, rotation selon Agility), pas d'un délai fixe : un défenseur lancé met plus de temps à revenir qu'un défenseur arrêté. Les gestes ne fixent que le déséquilibre initial ; aucun pivot instantané.

**Attributs (ADR 0002, poids à proposer) :** la distance du défenseur au porteur reste celle d'Aggression (`defense.stop_distance_m`, existant), sans second attribut ; la vulnérabilité se lit sur l'état physique réel (distance, élan, orientation), pas sur une note. Lecture du geste : **un seul contexte** « lire le geste du porteur » (Anticipation, Decisions, Concentration quand livrée), déclaré une fois au registre et partagé avec le `04k` (« ne pas mordre ») et les autres gestes, jamais recompté. Agility seulement par la physique (`12a`, `12b`, `07f`), sans bonus. Pas de nouvel effet de Dribbling (il reste dans chaque geste, R1). Positioning : non (son rayon est le placement de zone, carte).

**Lien avec l'existant :** remplace les états « éliminé », « écart temporaire », « figé » prévus séparément aux `04g`, `04h`, `04k`, `04m` ; `04g` pose le premier geste avec une version simple de cet état, ce ticket la généralise avant les autres gestes.

**Blocked by:** `04g` (premier geste), `12a`, `12b`, `07f` (livrés) ; `v2-attributs-contextes/01` et `02` (livrés).

**Bloque :** `04h`, `04k`, `04l`, `04m`, `04n`, `39`, `v2-collectif/22a`.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : `04g` livré avec un état « éliminé » simple ; la vulnérabilité est une seule fonction lue par les gestes. Temps machine, non compté : série de 50 matchs (environ 40 min), suite complète (environ 20 min).

## Tests

- **Scènes :** même porteur, même geste : défenseur lancé à pleine vitesse battu plus souvent qu'un défenseur campé à 2 m ; défenseur trop près (moins de 1 m) plus exposé au contournement ; défenseur battu : temps pour revenir à moins de 1,5 m du porteur plus long s'il était lancé, et plus court à Agility 99 qu'à 11 (physique seule).
- **Statistiques (50 matchs) :** durée moyenne du déséquilibre, part des gestes réussis selon l'élan du défenseur.

## Acceptance criteria

- [ ] Constantes produit (poids de la distance, de l'élan, de l'orientation ; déséquilibre initial) et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Un seul état « défenseur déséquilibré », tracé, lu par `04g` et par les gestes suivants
- [ ] Scènes ci-dessus ; aucun défenseur ne repart dans le sens opposé sans passer par la physique
- [ ] Effets des attributs probabilistes, jamais binaires ; contextes déclarés et documentés ; pas de double comptage (R1)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Comments
