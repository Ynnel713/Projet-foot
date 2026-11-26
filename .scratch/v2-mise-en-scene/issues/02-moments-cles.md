# 02: Moments clés (mode court, Tier 1)

**Chantier :** `v2-mise-en-scene` (réécrit le 26/11/2026, audit du mode « moments clés », décisions du propriétaire). **Catégorie :** mode de visionnage.

**What to build:** le mode court : **tous les moments Tier 1 et seulement eux** (01b) : buts, penalties, grosses occasions quelle que soit leur issue (but, arrêt, tir à côté ou contré, tacle ou interception salvateur, centre non repris, dégagement). Fenêtres, fusion et absorption du `01c` ; sélection du `01d` sans Tier 2.

- **Première version sans cartons rouges ni VAR** (décision du propriétaire, 26/11/2026 : absents du moteur V2). Ils entrent au Tier 1 à la livraison de `v2-attributs-restants/09a` (rouge) et `v2-realisme/21g`, `21h` (but annulé, penalty accordé ou retiré, rouge après révision), par ajout d'un type au `01b`, sans changer ce mode.
- **Ordre de grandeur** : environ 7,7 grosses occasions par match (28c, avant 01a) et les buts, dont une partie est absorbée par une occasion : environ 8 à 10 moments. Durée visée **5 à 7 minutes à ×1**, à confirmer par la mesure ; le budget n'écarte jamais un Tier 1 (01d).

**Attributs :** aucun.

**Constantes à proposer avant le code :** durée cible du mode (repère, pas un plafond : Tier 1 jamais coupé).

**Blocked by:** 01d (mode côté serveur), 01f (lecture).

**Bloque :** 03, 07a.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 10 min |
| Développement | 15 min |
| Tests unitaires et comportementaux | 20 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h** |

Confiance : moyenne. Hypothèses : le mécanisme (01b à 01f) porte tout le travail ; ce ticket règle le mode et ses scènes.
Temps machine, non compté : suite complète (environ 10 min) ; 50 matchs (environ 2 h 30, partagés avec `07a` si enchaînés).

## Tests

- **Scènes contrôlées** (critères d'origine conservés) : le centre qui traverse la surface et laisse un attaquant à deux doigts du but vide est un moment clé ; un face-à-face conclu par un tacle salvateur aussi ; un tir de loin sans danger ne l'est pas.
- Fusion : tir repoussé puis but : un seul moment.
- 50 matchs (graine d'audit) : nombre de moments et durée du mode par match, répartition par issue.

## Acceptance criteria

- [ ] Constantes validées par le propriétaire avant le code
- [ ] Les trois scènes contrôlées donnent le résultat attendu
- [ ] Tir repoussé puis but : un seul moment
- [ ] 100 % des buts, penalties et grosses occasions présents dans le mode (50 matchs)
- [ ] Nombre de moments, durée par match (médiane, 10e et 90e centiles) et répartition par issue rapportés
- [ ] Sans spoiler ; déterminisme à graine fixée
- [ ] `npm run build` et `npm run lint` OK
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Comments

- 10/11/2026 (audit de la roadmap, `docs/AUDIT_ROADMAP_V2.md`) : moments VAR ajoutés à la livraison de `v2-realisme/21g` et `21h`, sans bloquer ce ticket ; lus dans le journal (`v2-realisme/19b`).
- 26/11/2026 : réécrit. Les réserves A1 et A2 du 28c sont traitées par `01a` ; score d'intérêt et fusion sont communs aux modes (`01b`, `01c`) ; le nom « Moments clés » reste au mode court, le mode de 10 à 15 minutes est le Résumé (`03`).
