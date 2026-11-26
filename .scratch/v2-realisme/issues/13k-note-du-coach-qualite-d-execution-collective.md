# 13k: Note du coach : qualité d'exécution collective du plan

**Chantier :** `v2-realisme` (audit des styles du coach du 26/11/2026, demande du propriétaire). **Priorité :** P1 (deux coachs aux mêmes styles jouent aujourd'hui exactement pareil). **Catégorie :** décision.

**Constat vérifié :** la colonne `Note /100` n'est lue que par la V1 (`simulation.py`, `COACH_INFLUENCE`, ±3 % sur les lambdas) ; aucun ticket V2 ne la prévoit (13a lit les styles seuls, `v2engine/` ne lit pas les coachs). Exemple de la base : Luis Enrique (91) et Enzo Maresca (76), mêmes styles Pressing + Offensif + Possession.

**What to build:** Le style fixe l'intention ; la note règle la synchronisation collective de son exécution, à intention égale :
- pressing (13b) : déclencheurs mieux coordonnés (délai plus court entre le premier presseur et ceux qui suivent, moins d'espace entre les lignes pendant le pressing) ;
- possession (13f) : circuits de soutien mieux placés autour du porteur ;
- transitions (13e, 13c) : bascule plus rapide de toute l'équipe après la récupération ou la perte ;
- gestion de l'effort (20e) : le coach mieux noté dose l'intensité en fin de match (presse moins souvent mais mieux) plutôt que de laisser l'équipe s'épuiser.
Effet borné selon le principe d'amplitude ci-dessous, centré sur la moyenne des notes connues (`coaches.average_note`, même référence que la V1), neutre sans coach.

**Principe d'amplitude (propriétaire, 26/11/2026) :** l'impact des styles et de la note du coach reste modéré et réaliste. Un bon coach compense un peu un effectif moyen sans faire de miracle ; un coach moyen n'effondre pas une grande équipe. Le niveau de l'effectif reste le premier déterminant du résultat.

**Attributs :** aucun nouveau. **Règle anti double comptage** (`docs/CARTE_ATTRIBUTS_V2.md`, `v2-collectif/18`) : Teamwork reste la discipline individuelle (suivre ou non le pressing, tenir sa place) ; la note n'agit que sur des paramètres d'équipe (délais de coordination, écarts tolérés entre lignes), jamais sur la décision d'un joueur. La rédaction exacte du rayon de la note est ajoutée à la carte avant le code.

**Lien avec l'existant :** lit `coaches.coach_note` (lecture seule, D-V02) ; module les leviers des tickets 13b à 13f et 20e, sans mécanique parallèle.

**Blocked by:** 13j ; 13b, 13c, 13e, 13f (leviers à moduler) ; 20e (intensité selon la capacité restante).

**Dépendance non réciproque :** 20e n'est pas modifié par l'audit des styles du 26/11/2026 (ticket déjà couvert, laissé intact) ; sa ligne « Bloque » est à compléter de 13k et 13l à sa prochaine mise à jour.

**Bloque :** 13i, 13l ; `v2-coach-et-gestion-de-match/10` (ajouté le 26/11/2026, audit de la gestion de match).

**Status:** à faire (constantes à proposer avant le code ; estimation au-delà de 2 h : à examiner pour découpage avant le code, par exemple coordination d'un côté, gestion de l'effort de l'autre)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 30 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h 05** |

Confiance : faible. Hypothèses : les leviers de 13b à 13f exposent des paramètres de coordination modulables ; aucune donnée réelle chiffrée attendue sur l'effet d'un coach (« non trouvé » probable, validation du propriétaire).
Temps machine, non compté : suite complète (environ 40 min) ; mesure 200 matchs appariés.

## Tests

- **Comportementaux (profils comparés) :** même équipe, mêmes styles, note haute contre note basse, même adversaire : délai de coordination du pressing plus court, distance entre lignes plus faible pendant le pressing, temps de bascule après récupération plus court ; en fin de match, réserve d'énergie moyenne plus haute à intensité de pressing comparable
- **Statistiques (séries de matchs) :** 200 matchs appariés : écart de différence de buts avec intervalle de confiance, borné (la note ne doit pas peser plus que la qualité de l'effectif)

## Acceptance criteria

- [ ] Rayon de la note ajouté à `docs/CARTE_ATTRIBUTS_V2.md` ; bornes et constantes produit validées par le propriétaire avant le code
- [ ] Écarts de coordination mesurés dans le sens attendu (200 matchs appariés, intervalle de confiance)
- [ ] Effet sur le résultat borné et inférieur à celui d'un écart de niveau d'effectif équivalent (seuil à proposer)
- [ ] Sans coach ou note inconnue : indicateurs identiques à la version précédente
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
