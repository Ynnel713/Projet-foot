# 25e: Fixer un défenseur pour libérer un coéquipier (appel leurre)

**Chantier :** `v2-realisme` (demande du propriétaire du 14/11/2026 : jeu sans ballon et placement dynamique comme cœur du jeu ; audit de la roadmap du même jour). **Priorité :** P1. **Catégorie :** décision.

**Constat vérifié (14/11/2026) :** le descriptif du `v2-collectif/16` (livré) annonce des appels leurres, des décrochages pour libérer une zone et des permutations ; ses critères cochés ne portent que sur les appels non redondants et l'appel dans le dos, et aucune trace de leurre ou de permutation n'existe dans `v2engine/`. Un appel est toujours évalué sur l'espace que le coureur obtient pour lui, jamais sur l'espace qu'il crée pour un autre.

**What to build:** un appel peut viser à attirer un défenseur perçu (son marqueur, ou le défenseur qui couvre la zone d'un coéquipier) : sa valeur est le gain de solution ou d'espace pour le coéquipier libéré, estimé sur la réaction probable du défenseur (il suit son homme ou tient sa zone, selon ce que le coureur perçoit de son rôle). Le coureur ne demande pas le ballon ; s'il est libre quand même, il reste une solution. Aucun script : le défenseur décide avec ses propres règles (`defense.py`), le leurre peut échouer.

**Attributs :** Off the Ball (voir l'occasion, rayon existant), Teamwork (accepter de courir pour un autre). Cumul à justifier dans la carte (règle R2 révisée).

**Blocked by:** 25a, `v2-collectif/16` (livré).

**Bloque :** 25h, `v2-collectif/17` (surcharges).

**Ticket 24 en cours :** toute courbe d'attribut de ce ticket passe par `success_probability` / `duel_probability`, dont la forme change au 24 ; les constantes de niveau sont proposées après la livraison du 24.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **2 h** |

Confiance : faible. Hypothèses : estimation de la réaction du défenseur par une règle simple (marqueur attitré suit, défenseur de zone tient) ; au plus un leurre par possession.
Temps machine, non compté : suite complète ; mesure 50 matchs.

## Tests

- **Scènes :** avant-centre marqué devant un milieu offensif : l'avant-centre décroche, son marqueur suit, l'espace entre les lignes s'ouvre ; marqueur qui tient sa zone : l'avant-centre devient une solution libre.
- **Statistiques (50 matchs) :** leurres par match, passes reçues par le coéquipier libéré dans les 3 s.

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Leurre visible dans la trace (intention, coéquipier visé, défenseur attiré ou non)
- [ ] Après un leurre réussi (défenseur attiré), le coéquipier visé reçoit plus souvent qu'à situation égale sans leurre
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
