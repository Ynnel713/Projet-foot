# 09k: Montée de la ligne au bon moment : le piège du hors-jeu joué avec discernement

**Chantier :** `v2-realisme` (demande du propriétaire du 24/11/2026, éléments sur la défense, point 4 « gestion du hors-jeu »). **Priorité :** P2. **Catégorie :** décision collective.

**Constat vérifié (24/11/2026) :** la hauteur de la dernière ligne glisse en continu : + 5 m si le porteur adverse est pressé, − 5 m s'il est libre, au plus 5 m au-dessus de l'attaquant le plus avancé, rabaissée si la ligne est plus lente que lui (`bloc.py`, tickets `v2-collectif/05` et `23`, `PRESSURE_STEP_M`, `CUSHION_RUN_M` ; `offside.TRAP_DEPTH_M`) ; chaque défenseur suit avec un retard réglé par Teamwork (`line_lag_s`, 0 à 1,5 s). La ligne ne réagit à aucun **signal** du jeu : elle ne monte pas d'un coup sur une passe en retrait ou un porteur qui se retourne, et ne se fige pas quand le passeur, libre et face au jeu, a un attaquant lancé devant lui (seule la distance du presseur compte).

**What to build:**
- **Signaux de montée** : ballon joué en retrait, porteur dos au but ou pressé au point de ne pas pouvoir jouer long : la ligne monte d'un pas (montée franche, pas un glissement), avant le départ de la passe suivante.
- **Signaux d'arrêt** : passeur libre, face au jeu, avec un attaquant lancé ou un appel en cours : la ligne ne monte plus, voire recule (le `CUSHION_RUN_M` existant pour la vitesse) ; monter alors est l'erreur « suicidaire » du réel.
- **Après le départ du ballon** : plus de montée (le hors-jeu se juge au départ) ; un défenseur qui monte encore ou traîne derrière est mesuré (« couvre l'attaquant »).
- Discipline : le retard de chacun reste celui de Teamwork (existant) ; les signaux sont lus sur ce que perçoivent les défenseurs (`08e`), la posture du `08g` aide à voir l'appel.

**Attributs (ADR 0002) :** aucun nouveau : Teamwork (retard, existant). Un contexte « jouer le piège » (Decisions du défenseur qui donne le signal) seulement si la mesure montre une ligne trop uniforme entre équipes, à proposer alors au propriétaire.

**Blocked by:** `09j`, `v2-collectif/23`, `08e` (livrés) ; `08g` (posture, pour la lecture de l'appel).

**Bloque :** `10j`, `40`, `41`, `v2-collectif/22a`.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 25 min |
| **Total (travail effectif)** | **2 h 05** |

Confiance : moyenne. Hypothèses : les signaux sont lus dans `Bloc` comme la pression aujourd'hui ; le pas de montée réutilise `PRESSURE_STEP_M` ou une valeur proposée. Au-dessus de 2 h de peu : découpage à examiner au lancement (signaux de montée / signaux d'arrêt). Temps machine, non compté : série de 50 matchs (environ 40 min), suite complète (environ 20 min).

## Tests

- **Scènes :** passe en retrait du porteur adverse : la ligne monte avant la passe suivante ; passeur libre face au jeu avec un attaquant lancé : la ligne ne monte pas ; défenseur à Teamwork 11 : il reste en retard et remet l'attaquant en jeu plus souvent qu'à 99.
- **Statistiques (50 matchs, avant / après) :** hors-jeux sifflés par équipe et par match (repère réel à sourcer, sinon « non trouvé »), passes en profondeur réussies dans le dos d'une ligne qui montait, défenseur « qui couvre » l'attaquant, buts (dans le bruit).

## Acceptance criteria

- [ ] Constantes produit (signaux, pas de montée) et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Montées et arrêts tracés avec leur signal
- [ ] Scènes ci-dessus ; hors-jeux par match dans la fourchette validée
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Comments
