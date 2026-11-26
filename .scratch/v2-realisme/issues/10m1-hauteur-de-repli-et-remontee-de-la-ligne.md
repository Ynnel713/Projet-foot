# 10m1: Repli en hauteur à la perte, et remontée de la ligne dès que le ballon est contenu

**Chantier :** `v2-realisme` (découpé de 10m le 26/11/2026, demande du propriétaire). **Priorité :** P1. **Catégorie :** placement.

**Constat vérifié :** voir 10m. À la perte, la place de référence du bloc monte avec le ballon. Le centre de l'équipe avance au lieu de reculer : −0,25 m/s à la dernière mesure du banc, où une valeur positive signifie « vers son but ». Piège connu (ticket `v2-collectif/10`, 03/11/2026) : interdire la montée fait reculer l'équipe, mais le hors-jeu tombe de 2,0 à 0,69 par match.

**What to build:**
1. **Cible de repli en hauteur.** À la perte, la place de référence du bloc vise une hauteur en retrait du ballon, d'une profondeur à proposer, au lieu de suivre le ballon vers l'avant.
2. **Ballon contenu** (définition validée par le propriétaire le 26/11/2026), lue sur le monde perçu. Le porteur est le porteur adverse, celui qui a récupéré le ballon. Le ballon est contenu quand l'adversaire cède du terrain ou ne progresse pas :
   - un des déclencheurs du pressing d'équipe de `v2engine/defense.py`, réutilisés tels quels (une seule définition partagée) : passe de l'adversaire vers son propre but, receveur au moins 3 m plus près de son but (`BACKWARD_PASS_M`), ou porteur adverse qui reçoit en reculant vers son but (`BACKWARD_MPS`) ;
   - ou porteur adverse pressé (presseur à `PRESSED_M` = 3 m ou moins) depuis au moins `MAX_REACTION_S` = 1,0 s sans avoir progressé ni passé.
   
   **Ancrage de la durée :** `MAX_REACTION_S` est le délai de réaction le plus long du moteur (`v2engine/anticipation.py`, 0,4 s à la note 99, 1,0 s à la note 11, validé le 26/10/2026 ; référence 0,7 s par défaut, modèle de pression d'Unravel Sports sur données de suivi). Au bout de 1 s de pression, même le porteur le plus lent a eu le temps de réagir ; s'il n'a ni progressé ni passé, il est contenu. Constante existante, pas une nouvelle.
3. **Remontée.** Dès que le ballon est contenu, la ligne remonte progressivement vers sa hauteur de défense placée, avec sa règle de hors-jeu inchangée. Le repli ne bloque jamais la ligne en bas.

La profondeur de repli est un paramètre d'équipe, lisible plus tard par le style (13c, 13j), le score (`v2-collectif/21`) et la fatigue (20e), sans seconde mécanique.

**Point de vigilance :** le contre-pressing du ticket 10 place très tôt un presseur à moins de 3 m du porteur. La durée de pression d'au moins 1 s évite que le repli s'annule à chaque perte ; les critères de recul et de hors-jeu détectent un conflit restant.

**Prérequis bloquant (propriétaire, 26/11/2026) :** avant tout code, mesurer sur 20 matchs le temps entre l'arrivée du presseur à 3 m ou moins du porteur adverse et l'issue du duel (récupération, passe, élimination du presseur), et rapporter sa médiane et sa distribution. La durée de 1 s est alors confirmée, ou ajustée avec l'accord du propriétaire. 10m1 ne passe pas en code tant que cette mesure n'est pas faite et la constante confirmée ou ajustée.

**Ordre (propriétaire, 26/11/2026) :** 10m1 vient après 13a et 09f ; ensuite 13j et 09g, puis 13b à 13f. Cette contrainte d'ordre n'est pas une dépendance technique.

**Attributs :** aucun nouveau. Work Rate garde l'intensité du repli (ticket 10) ; Teamwork garde l'écart toléré à sa place.

**Lien avec l'existant :** premier morceau de 10m. Le resserrement en largeur est au 10m2.

**Blocked by:** 01f (livré) ; 13a et 09f (ordre décidé par le propriétaire le 26/11/2026, pas une dépendance technique) ; mesure préalable sur 20 matchs (voir Prérequis bloquant).

**Bloque :** 10m2, 10n, `v2-collectif/22b`.

**Dépendance non réciproque :** 01f (livré) n'est pas modifié ; sa ligne « Bloque » ne cite pas 10m1.

**Status:** à faire (bloqué par la mesure préalable sur 20 matchs ; constantes restantes à proposer avant le code : profondeur de repli, vitesse de remontée)

## Estimation

| Poste | Durée |
|---|---|
| Mesure préalable (prérequis bloquant, 20 matchs) | 20 min |
| Analyse et compréhension du code | 25 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **2 h 05** |

Confiance : moyenne. Hypothèses : la place de référence (`bloc.py`) accepte une cible de transition ; la notion de porteur pressé existe déjà (`PRESSED_M`).
Temps machine, non compté : 20 matchs de la mesure préalable ; suite complète (environ 10 min en session cloud) ; 50 matchs avant/après.
Au-delà de 2 h de 5 min, à cause du prérequis ajouté le 26/11/2026 : pas de nouveau découpage, la mesure préalable est déjà une étape séparée qui précède le code.

## Tests

- **Unitaires (scène contrôlée) :**
  - perte au milieu de terrain, porteur adverse libre : 3 s après, centre de l'équipe plus bas qu'à la perte ;
  - même perte, passe adverse en retrait d'au moins 3 m, ou porteur adverse pressé depuis au moins la durée validée sans avoir progressé ni passé : la ligne remonte à la vitesse de remontée validée ;
  - porteur adverse pressé depuis moins de la durée validée : la ligne ne remonte pas encore.
- **Statistiques (séries de matchs) :** 50 matchs avant/après, mêmes graines : vitesse de recul, latence, bloc reformé, hors-jeu par match, tirs de contre après récupération, part des buts issus d'une récupération.

## Acceptance criteria

- [ ] Mesure préalable faite sur 20 matchs (durée du duel presseur-porteur adverse) et durée de 1 s confirmée ou ajustée par le propriétaire, avant tout code
- [ ] Profondeur de repli et vitesse de remontée proposées et validées par le propriétaire avant le code ; hors-jeu actuel relevé avant le code
- [ ] Vitesse de recul du centre de l'équipe (positive = vers son but) positive, ou nettement plus élevée qu'avant, et bloc reformé plus vite ; seuils chiffrés proposés avant la mesure
- [ ] **Hors-jeu au moins 1,5 par match** (seuil du propriétaire, 26/11/2026) : estimation ponctuelle sur 50 matchs au moins 1,5, intervalle de confiance rapporté ; si sa borne basse descend sous 1,2, série portée à 200 matchs
- [ ] Tirs de contre après récupération et part des buts issus d'un ballon gagné à l'adversaire (catégories « récupération » et « erreur adverse » du 19e, rapportées séparément) en baisse ou stables (sens mesuré)
- [ ] Profondeur de repli exposée comme paramètre d'équipe
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
