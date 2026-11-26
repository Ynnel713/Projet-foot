# 31b: Validation des combinaisons : une-deux, triangles, remises, déviations et progression

**Chantier :** `v2-realisme` (audit des combinaisons du 26/11/2026, demande du propriétaire, ticket proposé « C5 »). **Priorité :** P1. **Catégorie :** validation.

**Constat vérifié (26/11/2026) :**
- Les mécanismes ont leur ticket : plan de passe, troisième homme et une-deux reconnus (`v2-collectif/14`, livré) ; jeu à une touche, remise et talonnade (`v2-collectif/31a`, `07e`, livrés) ; passe à une touche selon l'arrivée du ballon (`v2-collectif/36a`) ; soutien en angle et triangle (`v2-collectif/06` livré, `25c`) ; passe de la tête vers un coéquipier (`15c`) ; course du passeur (`31a`).
- Une partie des mesures existe au banc : retour au passeur et une-deux (indicateur 13), troisième homme (14), triangles (15), passes de première (24). `04q` mesure l'issue des réceptions dos au jeu sous contact (remise ou déviation comprise) ; `25h` reprend les triangles par phase.
- Aucun ticket ne rassemble les combinaisons. Trois mesures manquent : remises (passe de première rendue vers l'arrière ou le côté, au passeur ou à un soutien), déviations (passe de première qui prolonge le ballon dans sa direction, au pied ou de la tête), effet des combinaisons sur la progression du ballon.

**What to build:** banc seulement, moteur inchangé. Les nouvelles mesures sont définies dans `docs/INDICATEURS_V2.md` et ajoutées à `scripts/v2_indicators.py` :
1. **remises** par équipe et par match : passe de première dont le receveur visé est derrière ou à côté du remiseur (angle et distance à proposer), réussies et perdues ;
2. **déviations** par équipe et par match : passe de première, au pied ou de la tête, dont la direction s'écarte de moins d'un angle à proposer de celle du ballon reçu, réussies et perdues ;
3. **progression** : mètres gagnés vers le but adverse et lignes cassées dans les 5 s qui suivent une combinaison (une-deux, troisième homme, remise, déviation), comparés aux séquences de même départ sans combinaison ; part des possessions avec au moins une combinaison qui atteignent le dernier tiers.

Le rapport, sur 50 matchs, reprend aussi les indicateurs existants (13, 14, 15, 24) et les compare aux repères réels sourcés, ou « non trouvé ». Chaque écart au réel est renvoyé à un ticket, jamais réglé ici (calibration au `v2-collectif/22b`).

**Attributs :** aucun.

**Lien avec l'existant :** ne duplique pas `04q` (dos au jeu sous contact, profils, pièges) ni `25h` (jeu sans ballon) : les remises et déviations de `04q` en sont un sous-ensemble, rapporté à part. Repères réels : une-deux non trouvée (ticket 14) ; troisième homme, définition réelle plus étroite (ticket 14) ; passes de première 7,4 à 9,3 % (`v2-collectif/31a`, StatsBomb). Remises et déviations : à chercher dans les données ouvertes StatsBomb (passe de première dont l'angle avec le ballon reçu est mesurable), sinon « non trouvé ».

**Blocked by:** 31a, 25c, 15c, `v2-collectif/36a` ; 01e (livré : séries longues et intervalles).

**Bloque :** `v2-collectif/22b`. Alimente `v2-mise-en-scene/01b` et `03` (bonus « belle construction » du Tier 2, ajouté à sa livraison ; 26/11/2026) sans les bloquer.

**Status:** à faire (définitions et repères réels à proposer au propriétaire avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et rapport | 25 min |
| **Total (travail effectif)** | **1 h 45** |

Confiance : moyenne. Hypothèses : passes de première déjà tracées (`DecisionRecord.one_touch`, `v2-collectif/31a`), têtes tracées par le `15c` ; lignes cassées déjà calculées au banc (`v2-collectif/14`, indicateur 12 C2) ; recherche StatsBomb non comptée (environ 30 min).
Temps machine, non compté : suite complète (environ 10 min) ; 50 matchs.

## Tests

- **Unitaires (journaux connus) :** une passe de première rendue à 3 m derrière le remiseur compte une remise ; une passe de première qui prolonge le ballon à moins de l'angle validé compte une déviation ; une une-deux suivie d'un gain de 12 m en 4 s rapporte 12 m de progression.
- **Statistiques (50 matchs) :** rapport publié dans `docs/INDICATEURS_V2.md`, avec intervalles de confiance (01e).

## Acceptance criteria

- [ ] Définitions des trois nouvelles mesures (angles, distances, fenêtre de 5 s) et repères réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Indicateurs reproductibles à graine fixée, testés sur des journaux connus
- [ ] Rapport sur 50 matchs : une-deux, troisième homme, triangles, passes de première, remises, déviations, progression après combinaison contre sans ; intervalles de confiance ; chaque écart au réel renvoyé à un ticket, jamais réglé ici
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
