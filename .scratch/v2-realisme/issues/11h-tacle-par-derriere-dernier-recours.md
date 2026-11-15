# 11h: Le tacle par derrière en dernier recours (risque contre bénéfice)

**Chantier :** `v2-realisme` (constat du ticket 11e, 15/11/2026 ; piste du propriétaire du 15/11/2026). **Priorité :** P1. **Catégorie :** décision.

**Constat vérifié (11e, 50 matchs) :** les tentatives de tacle se répartissent à parts égales : de face 34 %, de côté 33 %, **par derrière 33 %**, alors que le tacle par derrière ne gagne que 12 % des ballons et fait faute 65 % du temps (11d). La décision de tenter (`duel.should_attempt_tackle`, `match.py:662`) ne lit qu'Aggression et la portée : le défenseur ne pèse jamais l'angle.

**What to build:** Le défenseur évalue le risque et le bénéfice avant de tacler. Par derrière, le tacle devient un **dernier recours** : hors urgence, il suit et contient au lieu de tacler ; en **urgence défensive** (« désespoir »), il le tente. Urgence (définition à valider) : le porteur menace directement le but, soit à moins de 20 m du but adverse avec un angle de tir, soit lancé vers le but sans coéquipier du défenseur entre lui et le but (dernier rempart). Loin du but (par exemple à 30 m et plus, couverture en place), un tacle par derrière est « suicidaire » : il n'est presque jamais tenté. De côté : réduction plus faible.

**Attributs :** Aggression garde la fréquence de base (inchangée). Piste à trancher par le propriétaire (règle R1) : **Decisions** règle le discernement (le bon défenseur renonce hors urgence, le mauvais tacle quand même), conforme à la carte (« choisir... tacler, attendre ») ; ou aucun attribut (facteurs de situation seuls).

**Constantes à proposer avant le code (valeurs indicatives, non validées) :** taux de tentative multiplié par 1,0 de face, 0,6 de côté, 0,15 par derrière hors urgence ; 1,0 dans tous les cas en urgence ; urgence : porteur à moins de 20 m du but, ou dernier rempart. Chiffre réel : non trouvé (qualitatif : loi 12, le tacle par derrière dangereux est une faute grossière, donc évité par les défenseurs).

**Lien avec l'existant :** complète le 11d (issue selon l'angle) par la décision ; distinct du 04j (tacle glissé, un autre geste, que ce ticket ne remplace pas) ; la gravité selon l'angle reste au 21b (cartons).

**Blocked by:** aucun (11d livré).

**Bloque :** rien.

**Status:** à faire (constantes à proposer avant le code)

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

## Tests

- **Unitaires (scène contrôlée) :** même défenseur derrière le porteur, à 35 m du but avec couverture : tentatives rares ; à 15 m, dernier rempart : tentatives au taux de base ; de face : inchangé.
- **Statistiques (séries de matchs) :** 50 matchs appariés : part des tacles par derrière, fautes, tacles gagnés, buts encaissés après renoncement

## Acceptance criteria

- [ ] Constantes produit, définition de l'urgence, choix de l'attribut (Decisions ou aucun) et chiffres réels validés par le propriétaire avant le code
- [ ] Part des tacles tentés par derrière : de 33 % à **10 % au plus** hors urgence (cible indicative à confirmer)
- [ ] Fautes par match rapportées (attendu : en baisse ; repère réel 21-26)
- [ ] Buts et tirs sans régression significative ; buts encaissés après un renoncement rapportés
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
