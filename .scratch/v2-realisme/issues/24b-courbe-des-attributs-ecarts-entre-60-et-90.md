# 24b: Courbe des attributs : de vrais écarts entre 60 et 90

**Chantier :** `v2-realisme` (demande du propriétaire du 14/11/2026). **Priorité :** P1, avant la calibration finale (`v2-collectif/22a` à `22c`), qui repartira des nouvelles courbes. **Catégorie :** moteur.

**Constat vérifié :** voir le 24a (table des courbes). La courbe partagée `attributes._cubic_curve` (t³, centre 55, demi-étendue 44) écrase la zone 60 à 80 où se trouvent presque tous les joueurs : 10 points d'écart entre 60 et 70 valent moins d'un point de chance de réussite ; entre 70 et 80, environ 5 points. Les courbes linéaires (Pace, Acceleration, Agility, Stamina, First Touch pour le contrôle orienté, Technique) ont une pente constante d'environ 4 à 10 % pour 10 points.

**Exigence du propriétaire (14/11/2026) :** une vraie différence entre 70 et 80, quelle que soit la caractéristique ; les différences doivent se concentrer entre 60 et 90, où sont les joueurs.

**What to build:** Remplacer la forme de la courbe partagée (une seule fonction, `_cubic_curve`, qui sert à `success_probability` et `duel_probability`), en comparant **deux variantes**, puis garder la meilleure :
- **Variante A, cubique recentrée et adoucie :** centre sur la médiane réelle des notes (environ 62, mesurée sur la base au moment du ticket), exposant 1,5 au lieu de 3 (signe gardé : `sign(t)·|t|^1,5`), mêmes bornes. Changement minimal de forme.
- **Variante B, logistique :** `baseline + amplitude · tanh(k · t)` (forme en S), pente maximale au centre, centre sur la médiane réelle ; `k` choisi pour que l'écart 70 → 80 soit au moins celui visé ci-dessous.
- **Objectif chiffré (à valider par le propriétaire avant le code) :** pour chaque mécanisme probabiliste, l'écart de 70 à 80 vaut au moins le tiers de l'écart de 50 à 99, et l'écart de 60 à 70 au moins le quart ; en duel, 10 points d'écart entre les deux joueurs donnent au moins 58 / 42 (contre 50,6 / 49,4 aujourd'hui).
- Les courbes linéaires des attributs physiques sont relues : elles restent ancrées sur des valeurs réelles mesurables (vitesse de pointe, temps d'accélération) ; on ne les rend plus raides entre 60 et 90 que si une source réelle le justifie (sinon : « non trouvé », et on garde).
- Les `baseline` et `amplitude` de chaque action ne bougent pas dans ce ticket : seule la forme change ; le recalage des niveaux (passes réussies, conversion, tacles…) revient à la calibration finale, qui repart de ces courbes.
- Choix entre A et B : sur la table des courbes du 24a (avant / après) et sur le banc du 24a (70 contre 80 en match, attribut par attribut), en retenant la variante qui fait le plus d'attributs significatifs entre 70 et 80 sans faire sortir les indicateurs globaux de leur repère (buts, passes réussies, tirs). Le propriétaire tranche s'ils sont proches.

**Attributs :** tous ceux qui passent par `success_probability` ou `duel_probability` (Passing, First Touch au contrôle, Tackling, Strength, Balance, Dribbling, Finishing, Long Shots, Decisions, Vision, Composure, Anticipation, Positioning, Marking, Teamwork, Off the Ball, Flair, Aggression, attributs du gardien…) ; aucun rayon ne change (`docs/CARTE_ATTRIBUTS_V2.md`).

**Blocked by:** 24a (banc et mesure de référence).

**Bloque :** `v2-collectif/22a`, `22b`, `22c` (calibration finale : elle doit partir des nouvelles courbes).

**Status:** à faire (constantes à proposer avant le code : centre, exposant ou pente, objectif chiffré)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 40 min (les deux variantes derrière un choix unique, puis la retenue seule) |
| Tests unitaires et comportementaux | 35 min |
| Intégration et vérifications | 40 min (deux séries, choix, documentation) |
| **Total (travail effectif)** | **2 h 15** |

Confiance : moyenne. Hypothèses : une seule fonction de forme à changer ; beaucoup de tests existants fixent des valeurs de probabilité calculées avec la courbe actuelle et devront être recalculés (sans être supprimés ni affaiblis) : c'est le principal risque de dépassement. Au-delà de 2 h par la règle de `CLAUDE.md` : découpage examiné ; il est gardé en un ticket car la forme et son choix sont indissociables (les deux variantes sont jugées sur la même mesure) ; à redécouper si la mise à jour des tests dépasse 30 min.
Temps machine, non compté : banc du 24a deux fois (A et B) sur les attributs retenus ; série appariée de 50 matchs pour les indicateurs globaux ; suite complète.

## Tests

- **Unitaires (courbe) :** variante retenue : écart 70 → 80 au moins le tiers de 50 → 99 ; 60 → 70 au moins le quart ; duel à 10 points d'écart au moins 58 % ; bornes jamais dépassées (jamais 0 ni 1) ; monotone ; symétrique en duel (p(a, b) + p(b, a) = 1).
- **Comportementaux (profils comparés, banc du 24a) :** 70 contre 80, attribut par attribut : plus d'attributs avec un écart significatif qu'avant (référence du 24a).
- **Statistiques (séries de matchs) :** 50 matchs appariés avant / après : indicateurs globaux (buts, xG, tirs, passes réussies, tacles, pertes) rapportés, écarts expliqués.

## Acceptance criteria

- [ ] Constantes produit (centre, exposant ou pente, objectif chiffré) et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Variantes A et B mesurées sur la table des courbes et sur le banc 70 contre 80 ; choix argumenté (propriétaire s'ils sont proches)
- [ ] Variante retenue seule dans le code, objectif chiffré tenu (tests de courbe)
- [ ] Écart 70 / 80 significatif en match pour plus d'attributs qu'au 24a, rapporté attribut par attribut
- [ ] Indicateurs globaux mesurés avant / après (50 matchs appariés) ; écarts transmis à la calibration finale, aucun recalage de niveau ici
- [ ] Tests existants recalculés sur la nouvelle courbe, aucun supprimé ni désélectionné
- [ ] Rayon des attributs inchangé (`docs/CARTE_ATTRIBUTS_V2.md`), test de rayon vert
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
