# 31a: Passe et va : le passeur repart dans l'espace libéré (une-deux)

**Chantier :** `v2-realisme` (audit des combinaisons du 26/11/2026, demande du propriétaire, ticket proposé « C1 »). **Priorité :** P1. **Catégorie :** décision.

**Constat vérifié (26/11/2026) :**
- La reconnaissance existe : plan de passe (`v2-collectif/14`, livré : le receveur peut rendre le ballon au passeur), jeu à une touche (`v2-collectif/31a`, livré : remise de première), indicateur 13 « retour au passeur et une-deux » (`docs/INDICATEURS_V2.md`).
- Le « va » manque. Après sa passe, le passeur redevient un coéquipier ordinaire : il n'appelle que s'il est devant le ballon (`cerveau._call_rank`, « devant le ballon ») et parmi les `CALLER_CAP` premiers ; après une passe vers l'avant il est derrière, donc il tient sa place (`_runs_or_holds` → `TENIR`). Aucune course ne part de la passe elle-même.
- Mesure : une-deux 1,59 → 1,58 par équipe et par match alors que les retours au passeur montent de 2,4 à 3,4 % (`v2-collectif/31a`, 50 matchs). Réserve A2 de l'expert au `v2-collectif/31a`, acceptée par le propriétaire et notée au `v2-collectif/22a` : « le passeur ne repart pas en course après sa passe ; ticket à créer ». C'est ce ticket.

**What to build:**
1. **Décider de repartir.** Au moment où il choisit une passe courte (longueur au plus une borne validée), le passeur décide aussi s'il enchaîne une course vers l'avant, dans l'espace qu'il vient de libérer ou derrière son vis-à-vis. La chance croît avec Off the Ball. Elle est plus forte quand son marqueur est attiré par le ballon ou par le receveur (perception du 08a et du 08b, pas de vue omnisciente). Pas de course si elle le met hors-jeu à coup sûr (respect de la ligne, `offside.py`, Off the Ball déjà lu).
2. **La course.** Le point visé est choisi en même temps que la passe ; le passeur part au tick qui suit, vers ce point choisi parmi les espaces candidats (`25a`), devant le ballon, d'où une passe du receveur réussit au moins à `OPEN_LANE_PROBABILITY` (0,7, ticket 06). Pendant la course, il compte comme appelant prioritaire, au même rang que la suite d'un plan de passe (`_call_rank`, rang 0). Il ne s'ajoute pas au plafond `CALLER_CAP` : il prend la place d'un appelant de plus bas rang. La course dure au plus une durée validée, puis il reprend sa place.
3. **Le retour.** Le porteur transmet au receveur un plan dont la suite est lui-même. **Ce n'est pas possible avec le plan du ticket 14 tel quel** (réserve A1 de l'expert, 26/11/2026) : les suites possibles sont prises parmi les coéquipiers vus, porteur exclu (`decision.py`, `mates` et `seen_full`) ; la valeur d'une suite se calcule sur la position actuelle du coéquipier (`danger(n.position, team)`), derrière le receveur pour le passeur, donc rarement meilleure que la position atteinte ; le plan est posé au départ de la passe depuis `action.follow` (`match.py`). Voie retenue (a) : quand le passeur décide de repartir, il s'ajoute lui-même aux suites possibles, valorisé au point de course choisi (et non à sa position), et la passe avec cette suite pose le plan comme aujourd'hui. Voie (b) écartée : un rang propre dans `_call_rank` sans plan, plus simple, mais le receveur ne saurait pas que la course est lancée pour lui. Le receveur décide comme aujourd'hui : remise de première (`v2-collectif/31a`) ou après contrôle, selon Decisions, la ligne ouverte et sa Vision. La réussite de l'une-deux sort des mécanismes existants : Passing des deux passes, First Touch et Technique de la remise, timing de la course.
4. **Le défenseur.** Le vis-à-vis du passeur suit la course selon le marquage existant (Marking, Positioning ; `v2-attributs-contextes/04b`) sur les positions perçues : une course dans le dos d'un défenseur qui regarde le ballon est vue en retard (`08e`). Rien de nouveau côté défense.

**Attributs :** Off the Ball (volonté et moment de repartir ; rayon existant : appels offensifs). Decisions du receveur, Passing, First Touch et Technique : rayons inchangés. Marking et Positioning du défenseur : rayons du `08e`. À vérifier dans `docs/CARTE_ATTRIBUTS_V2.md` (ADR 0002), sans double comptage : Work Rate reste aux efforts sans ballon défensifs (carte, ligne Work Rate), il n'entre pas ici.

**Constantes à proposer avant le code :** longueur maximale de la passe qui permet la course ; chance de repartir selon Off the Ball (11 / 55 / 99) ; majoration quand le marqueur est attiré ; durée maximale de la course ; distance minimale à gagner vers l'avant. Chiffres réels : fréquence des une-deux par équipe et par match (non trouvée au ticket 14 ; piste : données ouvertes StatsBomb, même méthode que le `v2-collectif/31a`, passe A → B puis B → A en moins de 3 s avec A avancé d'au moins 5 m).

**Lien avec l'existant :** ne recrée pas le plan de passe (14) ni la remise (`v2-collectif/31a`) ; ajoute la seule course du passeur. Distinct du dédoublement du latéral (`25i`, qui passe derrière le porteur) et du contre-appel (`25g`, qui se défait d'un marqueur sans passe préalable).

**Blocked by:** 25a (espaces candidats) ; `v2-collectif/14`, `v2-collectif/31a`, 02g, 08e (livrés).

**Bloque :** 31b ; `v2-collectif/22a` (réserve A2 du `v2-collectif/31a`).

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 1 h 20 |
| Tests unitaires et comportementaux | 40 min |
| Intégration et vérifications | 25 min |
| **Total (travail effectif)** | **2 h 45** |

Confiance : moyenne. Réestimé le 26/11/2026 de 2 h 15 à 2 h 45 (réserve A1 de l'expert : le passeur doit entrer dans les suites de `decision`, valorisé au point de course, décision de repartir prise au choix de la passe) ; au-delà de 2 h, à examiner pour découpage avant le code (par exemple : décision et course, puis retour par le plan). Hypothèses : pas de nouvel état du ballon (le plan du ticket 14 porte la suite une fois le passeur admis parmi les suites) ; rang 0 de `_call_rank` pendant la course ; le choix de l'espace réutilise `choose_space` sur les candidats du 25a ; recherche éventuelle du chiffre réel non comptée (environ 30 min si StatsBomb).
Temps machine, non compté : suite complète (environ 10 min) ; 50 matchs avant/après.

## Tests

- **Scènes :** passe courte, marqueur collé au receveur : le passeur repart plus souvent à Off the Ball 99 qu'à 11, jamais 0 ni 100 % ; passe longue au-delà de la borne : pas de course ; course qui le mettrait hors-jeu à coup sûr : pas de course ; pendant la course, le passeur est appelant au rang 0 et le nombre d'appelants ne dépasse pas `CALLER_CAP` ; après une passe courte suivie d'une course, `ball.plan[1]` désigne le passeur (test de la réserve A1).
- **Statistiques (50 matchs, mêmes graines) :** une-deux par équipe et par match, retours au passeur dans les 3 s, part des une-deux réussies, passes par match, réussite des passes, pertes de balle, temps de calcul ; trou laissé au milieu par le passeur parti : pertes suivies d'un tir adverse dans les 15 s (indicateurs de transition du `10n`).

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Scènes contrôlées : chance de repartir croissante avec Off the Ball, jamais 0 ni 100 % ; pas de course sur passe longue ni hors-jeu certain (tests)
- [ ] En match, plafond d'appelants respecté (test) et passeur au rang 0 pendant sa course
- [ ] Le passeur parti en course est une suite possible du plan, valorisée au point de course : `ball.plan[1]` le désigne dans la scène (réserve A1 de l'expert)
- [ ] En match (50 matchs, mêmes graines) : une-deux par équipe et par match en hausse nette par rapport à avant (1,58 au `v2-collectif/31a`, base à remesurer) ; écart au chiffre réel rapporté, sans réglage générique (calibration au `v2-collectif/22b`) ; passes par match et réussite rapportées (repère 890 à 940, déjà dépassé : à la `v2-collectif/22a`)
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Comments

**26/11/2026, clôture de l'audit `projet/audit-combinaisons`, passage 1 de l'expert : APPROVED_WITH_RESERVATIONS.** A1 (réserve) : retour au passeur impossible « sans nouveau mécanisme » (porteur exclu des suites, valeur sur la position actuelle, plan posé au départ de la passe) ; corrigé dans ce ticket avant clôture (voie (a), réestimation 2 h 15 → 2 h 45). A2 (facultatif) : « marqueur collé au ballon » reformulé. À surveiller : trou laissé au milieu, ajouté aux statistiques.
