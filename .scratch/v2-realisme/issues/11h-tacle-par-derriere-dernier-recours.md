# 11h: Le tacle par derrière en dernier recours (risque contre bénéfice)

**Chantier :** `v2-realisme` (constat du ticket 11e, 15/11/2026 ; piste du propriétaire du 15/11/2026). **Priorité :** P1. **Catégorie :** décision.

**Constat vérifié (11e, 50 matchs) :** les tentatives de tacle se répartissent à parts égales : de face 34 %, de côté 33 %, **par derrière 33 %**, alors que le tacle par derrière ne gagne que 12 % des ballons et fait faute 65 % du temps (11d). La décision de tenter (`duel.should_attempt_tackle`, `match.py:662`) ne lit qu'Aggression et la portée : le défenseur ne pèse jamais l'angle.

**What to build:** Le défenseur évalue le risque et le bénéfice avant de tacler. Par derrière, le tacle devient un **dernier recours** : hors urgence, il suit et contient au lieu de tacler ; en **urgence défensive** (« désespoir »), il le tente. Urgence (définition à valider) : le porteur menace directement le but, soit à moins de 20 m du but adverse avec un angle de tir, soit lancé vers le but sans coéquipier du défenseur entre lui et le but (dernier rempart). Loin du but (par exemple à 30 m et plus, couverture en place), un tacle par derrière est « suicidaire » : il n'est presque jamais tenté. De côté : réduction plus faible.

**Attributs :** Aggression garde la fréquence de base (inchangée). Piste à trancher par le propriétaire (règle R1) : **Decisions** règle le discernement (le bon défenseur renonce hors urgence, le mauvais tacle quand même), conforme à la carte (« choisir... tacler, attendre ») ; ou aucun attribut (facteurs de situation seuls).

**Constantes à proposer avant le code (valeurs indicatives, non validées) :** taux de tentative multiplié par 1,0 de face, 0,6 de côté, 0,15 par derrière hors urgence ; 1,0 dans tous les cas en urgence ; urgence : porteur à moins de 20 m du but, ou dernier rempart. Chiffre réel : non trouvé (qualitatif : loi 12, le tacle par derrière dangereux est une faute grossière, donc évité par les défenseurs).

**Lien avec l'existant :** complète le 11d (issue selon l'angle) par la décision ; distinct du 04j (tacle glissé, un autre geste, que ce ticket ne remplace pas) ; la gravité selon l'angle reste au 21b (cartons).

**Blocked by:** aucun (11d livré).

**Bloque :** rien.

**Status:** livré (16/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 25 min |
| **Total (travail effectif)** | **1 h 55** |

Confiance : moyenne. Hypothèses : urgence calculée depuis l'état (distance au but, défenseurs entre porteur et but) sans nouveau module ; si Decisions est retenu, une courbe de plus (réestimer).
Temps machine, non compté : suite complète (environ 12 min) ; série appariée de 50 matchs.

Réestimations annoncées (16/11/2026) : 1 h 55 → **2 h 25** (Decisions retenu : courbe de discernement) → **3 h 05** (prudence dans sa surface ajoutée par le propriétaire).

**Durée réelle : 3 h 55** (analyse 30, développement 60, tests 40, intégration 105 min) : + 27 % sur la dernière annonce (3 h 05), + 104 % sur l'estimation initiale. Causes : périmètre élargi deux fois par le propriétaire (Decisions, prudence de surface) et rédaction des tickets 11o, 11p et du complément du 21c ; défaut du banc (contexte du tirage effacé avant la résolution, renoncement mal défini) corrigé après la première série ; série « avant » tuée deux fois (mémoire, limite de durée) ; trois arbitrages de mesure soumis au propriétaire. Durée estimée à l'horloge de la session hors attentes machine, non chronométrée.

## Tests

- **Unitaires (scène contrôlée) :** même défenseur derrière le porteur, à 35 m du but avec couverture : tentatives rares ; à 15 m, dernier rempart : tentatives au taux de base ; de face : inchangé.
- **Statistiques (séries de matchs) :** 50 matchs appariés : part des tacles par derrière, fautes, tacles gagnés, buts encaissés après renoncement

## Décisions du propriétaire (16/11/2026)

- Facteurs à Decisions 55 : 1,0 de face, 0,6 de côté, 0,15 par derrière, interpolés sur l'angle d'approche (0°, 90°, 180°).
- Discernement par Decisions (notes 11, 55, 99) : par derrière 0,40, 0,15, 0,05 ; de côté, même coefficient (0,72, 0,6, 0,55) ; de face 1,0.
- Urgence (facteur 1,0) : porteur à moins de 20 m du but défendu avec un angle de tir de moins de 45° par rapport à l'axe, **ou dernier rempart** (aucun coéquipier de champ du défenseur plus près du but que le porteur, gardien exclu). « Il est hors de question de retirer le "dernier rempart" de l'urgence. »
- Dans sa surface : pas d'urgence, même pour le dernier rempart (confirmé), et prudence de surface multipliée au facteur hors urgence (Decisions 99 : 0,35 ; 55 : 0,5 ; 11 : 0,75).
- Prudence liée aux cartons : ticket `11o`, bloqué par `v2-attributs-restants/09a`. Fautes hors tacle et prudence de surface pour ces fautes : complément du ticket `21c`.
- Fautes par match en baisse (19,8 → 10,9) : acceptées, le `21c` compense (critère chiffré ajouté au 21c). Part des tacles par derrière hors urgence à 15 % au lieu de 10 % : acceptée.

## Résultat (50 matchs appariés, 16/11/2026)

`docs/INDICATEURS_V2.md` section 49. Tacles par match 37,3 → 22,1 ; fautes 19,8 → 10,9 (écart significatif) ; buts + 0,52 ± 0,93 et tirs par équipe + 0,26 ± 1,1 (non significatifs) ; penalties − 0,04 ± 0,12. Part des tacles par derrière hors urgence : 31 % → 15 % des tacles hors urgence (cible indicative 10 % : le facteur décroît de 0,6 à 90° à 0,15 à 180°, un tacle à 135°, déjà « par derrière », garde environ 0,38). Tacles évités par le 11h : 16,7 par match, dont 8,4 par derrière ; buts encaissés dans les 15 s qui suivent : 0,28 par match. Tacles dans sa surface : 0,54 → 0,18 par match (penalties qui en découlent 0,28 → 0,10). Tacles par match sous le repère réel 30-40 : réserve A1 de l'expert, acceptée par le propriétaire (« Accepter + nouveau ticket »), ticket `11p` tacleur le mieux placé.

## Acceptance criteria

- [x] Constantes produit, définition de l'urgence, choix de l'attribut (Decisions ou aucun) et chiffres réels validés par le propriétaire avant le code
- [x] Part des tacles tentés par derrière : de 33 % à **10 % au plus** hors urgence (cible indicative à confirmer) — 15 %, accepté par le propriétaire le 16/11/2026
- [x] Fautes par match rapportées (attendu : en baisse ; repère réel 21-26)
- [x] Buts et tirs sans régression significative ; buts encaissés après un renoncement rapportés
- [x] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Comments

- 16/11/2026, passage 1 : expert APPROVED_WITH_RESERVATIONS. A1 réserve : tacles par match 37,3 → 22,1, sous le repère réel 30-40, amplifié par la règle du seul adversaire le plus proche. A2 facultatif : série « avant » non reproductible depuis le dépôt. A3 facultatif : ligne en double dans un test (corrigée). A4 : durée réelle à relever (faite).
- 16/11/2026, passage 2 (après corrections A3, A4) : expert APPROVED_WITH_RESERVATIONS, A1 seule. Passage 3 (empreinte restreinte aux fichiers de code, contenu identique) : APPROVED_WITH_RESERVATIONS.
- Réserve A1 acceptée par le propriétaire : « Accepter + nouveau ticket (Recommandé) » → ticket `11p` tacleur le mieux placé.
- QC : VALIDÉ. Clôture journalisée : VALIDÉ (expert avec réserves acceptées, QC VALIDÉ).
