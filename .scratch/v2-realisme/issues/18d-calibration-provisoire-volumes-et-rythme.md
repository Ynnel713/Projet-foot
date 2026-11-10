# 18d: Calibration provisoire 1 : volumes de course et rythme après les fondations P0

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (garder des matchs regardables et mesurables pendant les développements P1, sans figer de valeur). **Catégorie :** validation.

**Constat vérifié :** le point d'étape 18a rapporte les écarts sans régler ; sans calibration intermédiaire, les tickets P1 se mesureraient sur des volumes éloignés du réel (dernières mesures publiées : 20,7 km par joueur, 37 % du temps au-dessus de 19,8 km/h, 10,3 passes par minute).

**What to build:** Régler provisoirement, sur 500 matchs (01e), les constantes de course, d'intensité par rôle (12d si livré, sinon celles du 02f), de réception et de rythme de décision, pour ramener km, haute intensité, appels et passes par minute dans l'ordre de grandeur des repères du 01c. Règles d'une calibration provisoire (décision du propriétaire du 05/11/2026) : seules les constantes des mécanismes concernés bougent, dans leurs fourchettes validées ; chaque valeur est marquée « provisoire » dans le code et dans `docs/INDICATEURS_V2.md` avec la date et la mesure ; aucun réglage ne masque une lacune de mécanisme (un écart dû à un mécanisme absent devient un ticket) ; la calibration finale (`v2-collectif/22a` à `22c`) repart de ces valeurs et peut toutes les revoir.

**Hors de ce ticket :** tirs, buts et gardien (18e) ; calibration finale (`v2-collectif/22a`).

**Attributs :** aucun

**Blocked by:** 18a (Point d'étape après les fondations P0); 01e (Banc : séries de 500 à 2 000 matchs, parallélisées, avec intervalles de confiance); 12d (Intensité de course selon le rôle); 12e (Réserve d'énergie) (ajouté le 10/11/2026, audit de la roadmap).

**Bloque :** 18e, `v2-collectif/22a`.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 20 min |
| Intégration et vérifications | 30 min |
| **Total (travail effectif)** | **1 h 50** |

Confiance : moyenne. Hypothèses : leviers existants seulement ; temps machine important.
Temps machine, non compté : suite complète (environ 40 min) ; séries de 500 matchs.

## Tests

- **Statistiques (séries de matchs) :** 500 matchs avant / après, intervalles de confiance ; profils A/B inchangés en sens (Work Rate, Off the Ball, Stamina)

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Chaque constante modifiée marquée « provisoire », avec date et mesure
- [ ] Écarts restants attribués (mécanisme ou calibration finale)
- [ ] Aucun effet d'attribut inversé ni annulé (scènes A/B rejouées)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Complément de l'audit de la roadmap (10/11/2026)

Source : `docs/AUDIT_ROADMAP_V2.md`. 12d et 12e passent avant ce ticket : calibrer les volumes de course alors que toutes les intentions visent la vitesse maximale (`cerveau.Intention.intensity`) et que la fatigue ne dépend que de la minute reviendrait à masquer deux mécanismes absents, ce que la règle des calibrations provisoires interdit. La mention « 12d si livré » du « What to build » devient « 12d et 12e livrés ».
