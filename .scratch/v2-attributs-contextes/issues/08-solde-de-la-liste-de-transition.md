# 08: Solde de la liste de transition : deux contextes pour chaque attribut encore cloisonné

**Chantier :** `v2-attributs-contextes` (ADR 0002, point 1). **Priorité :** P2. **Catégorie :** branchement d'attributs.

**Origine :** ticket 02 (17/11/2026). Choix du propriétaire : pour la règle « chaque attribut non spécialiste figure dans au moins deux contextes », seuls les contextes du registre `v2engine/contextes.py` comptent ; une lecture directe d'un seul attribut par la façade n'en est pas un. Les attributs sans ticket de branchement sont rattachés ici dans la liste de transition (`TRANSITION`, `tests/test_v2engine_rayon_attributs.py`).

**What to build:** faire entrer dans au moins deux contextes du registre chaque attribut que la liste de transition rattache à ce ticket, et l'en retirer : Pace, Acceleration, Stamina, Agility, Strength, Aggression, Tackling, Marking, Teamwork, Off the Ball, Composure, Passing, Dribbling, First Touch ; Vision et Anticipation pour leur second contexte (le premier, « lecture du pressing », vient du ticket `v2-collectif/15b1`). Pour chacun : choisir les situations de jeu (en priorité celles déjà prévues par les tickets que le ticket 07 met aux normes, pour ne pas les compter deux fois), proposer contextes et poids au propriétaire, migrer ou brancher, mesurer.

**Hors de ce ticket :** les attributs déjà rattachés à un autre ticket (Work Rate `03`, Decisions `04a`, Positioning `04b`, Flair `05`, Balance `06`, gardien `v2-attributs-restants/03b`) ; les spécialités.

**Attributs :** les 16 ci-dessus ; contextes et poids à proposer au propriétaire, attribut par attribut (constantes produit).

**Blocked by:** 02 ; `v2-collectif/15b1` (premier contexte de Vision et Anticipation) ; ticket 07 (pour repérer les contextes déjà prévus ailleurs).

**Status:** à faire — à découper en lots avant le code

## Estimation

| Poste | Durée |
|---|---|
| Analyse et choix des contextes (16 attributs) | 1 h 30 |
| Développement | 2 h 30 |
| Tests et mesures avant/après (50 matchs, banc de profils) | 1 h 30 |
| Intégration et vérifications | 1 h |
| **Total (travail effectif)** | **6 h 30** |

Confiance : faible. Hypothèses : une partie des attributs reçoit son second contexte par les tickets mis aux normes au 07, avant ce ticket ; chaque branchement change le jeu (mesure avant/après obligatoire). Au-delà du seuil de 2 h : à découper en lots (par exemple physique, duel et défense, passe et réception) avant tout code.
Temps machine, non compté : séries de 50 matchs avant/après par lot ; suite complète.

## Acceptance criteria

- [ ] Découpage en lots validé par le propriétaire, chaque lot avec sa propre estimation
- [ ] Contextes et poids validés par le propriétaire avant le code, documentés dans la section « Contextes » de la carte
- [ ] Attributs concernés retirés de `TRANSITION` (garde de rayon verte)
- [ ] Mesure avant/après sur 50 matchs et banc de profils (`scripts/measure_v2.py --profil`), plafond d'écart 99 / 11 respecté
- [ ] Suite complète passée, compte comparé à l'attendu de `CLAUDE.md`
