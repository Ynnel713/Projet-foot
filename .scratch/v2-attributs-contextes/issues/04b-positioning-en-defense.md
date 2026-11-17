# 04b: Positioning en défense : couverture de la profondeur et placement sur les lignes de passe

**Chantier :** `v2-attributs-contextes` (ADR 0002). **Priorité :** P2. **Catégorie :** attributs.

**Constat (audit du 17/11/2026) :** Positioning n'est lu que par l'erreur de placement dans le bloc (`bloc.positioning_error_m`).

**What to build:** Positioning entre dans les contextes « couverture de la profondeur » (le dernier défenseur se place à la bonne distance derrière sa ligne) et « placement sur une ligne de passe » (défenseur sans ballon qui se met entre le porteur et un receveur), avec Anticipation pour la lecture de la passe (rayon existant, sans double comptage avec `anticipation.pass_readers`). À articuler avec `v2-realisme/10c` (couverture de la profondeur) et `10b`.

**Attributs :** Positioning, Anticipation, Concentration (à venir, ticket v2-collectif/21) (poids à proposer).

**Blocked by:** 01, 02.

**Status:** à faire (contexte, poids et chiffres réels à proposer au propriétaire avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 35 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 35 min |
| Intégration et vérifications | 25 min |
| **Total (travail effectif)** | **2 h 20** |

Confiance : faible. Hypothèses : la place de référence du bloc reçoit une correction de plus sans toucher à la tolérance Teamwork. Au-dessus du seuil de 2 h : découpage examiné avant le code (profondeur, puis lignes de passe).
Temps machine, non compté : suite complète ; séries de 50 matchs avant et après ; banc de profils de l'attribut (`scripts/measure_v2.py --profil`).

## Acceptance criteria

- [ ] Contexte, poids et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Contexte déclaré dans le registre et documenté dans la carte ; entrée retirée de la liste de transition du test de rayon
- [ ] Scène reproductible : 99 contre 11 sur l'attribut, effet probabiliste, jamais binaire
- [ ] 50 matchs avant/après sur l'indicateur visé ; profils 99 / 11 dans le plafond d'écart de la carte ; pas de double comptage (R1)
- [ ] Déterminisme à graine fixée ; suite complète passée, compte comparé à l'attendu de `CLAUDE.md`
- [ ] Durée réelle relevée et comparée à l'estimation
