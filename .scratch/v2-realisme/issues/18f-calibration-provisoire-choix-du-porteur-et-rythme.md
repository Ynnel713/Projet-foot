# 18f: Calibration provisoire 1 bis : choix du porteur et rythme de décision

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0. **Catégorie :** validation.

**Origine :** découpé du 18d le 11/11/2026 (estimation du 18d au-delà de 2 h). Le 18d règle la course et les appels ; ce ticket reprend le volet « choix du porteur et rythme de décision » que le point d'étape 18a avait ajouté au 18d (`docs/INDICATEURS_V2.md` section 25).

**Constat vérifié (12e, 50 matchs) :** le porteur choisit la conduite dans 72 % des décisions (passe 27 %, tir 1,3 %) ; 2,55 passes par possession (cible 3 à 5) ; 21,4 tirs tracés par équipe (R1 : 8 à 15), dont la plupart dans les 15 s d'une récupération haute ; passes 911 par match (R7 : 890 à 940, déjà dans la fourchette), 12,5 par minute de jeu effectif (cible 15 à 17, l'écart tient surtout au temps de jeu effectif, 70 %, sans remplacements ni assez de fautes). Une part des décisions n'est pas comparable à une donnée réelle : le porteur réévalue toutes les 0,5 s (`decision.DECISION_INTERVAL_S`), chaque intervalle de conduite compte pour une décision.

**What to build:** D'abord diagnostiquer pourquoi la conduite l'emporte (valeur de la conduite contre celle de la passe dans la monnaie commune du ticket 33 : chance de garder le ballon, `FREE_TOUCH_SHARE`, `PRESSURE_KEEP_SHARE`, portée de l'espace libre ; rythme de décision), en séparant mécanisme et constante. Puis régler provisoirement, sur 50 matchs puis 500, les seules constantes en cause, dans leurs fourchettes validées, pour rapprocher passes par possession (3 à 5) et volume de tirs (R1), sans faire sortir les passes par match de 890 à 940. Mêmes règles de calibration provisoire que le 18d. Relire après réglage : tacles (47), fautes (15), possession d'équipe (17,6 s), passes visées vers les DC (environ 12 par match ; si l'écart reste, ticket de relance à créer).

**Hors de ce ticket :** volumes de course et appels (18d) ; tir et gardien (18e) ; passes longues et en profondeur (`v2-collectif/32a`, 32b).

**Attributs :** aucun

**Blocked by:** 18d (Calibration provisoire 1 : volumes de course et rythme).

**Bloque :** 18e, `v2-collectif/22a`.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 30 min |
| Développement | 30 min |
| Tests unitaires et comportementaux | 20 min |
| Intégration et vérifications | 30 min |
| **Total (travail effectif)** | **1 h 50** |

Confiance : faible (la cause de la part des conduites n'est pas encore établie). Hypothèses : leviers existants seulement ; si la cause est un mécanisme, ticket neuf.
Temps machine, non compté : séries de 50 matchs (environ 70 min chacune), série de 500 matchs (environ 4 h), suite complète (environ 40 min).

## Tests

- **Statistiques (séries de matchs) :** 50 puis 500 matchs avant / après, intervalles de confiance ; profils A/B inchangés en sens (Dribbling, Decisions, Passing, Vision)

## Acceptance criteria

- [ ] Cause de la part des conduites établie (mécanisme ou constante) avant tout réglage
- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Passes par possession rapprochées de 3 à 5 ; passes par match toujours dans 890 à 940
- [ ] Chaque constante modifiée marquée « provisoire », avec date et mesure
- [ ] Écarts restants attribués (mécanisme ou calibration finale)
- [ ] Aucun effet d'attribut inversé ni annulé (scènes A/B rejouées)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
