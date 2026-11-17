# 04a: Decisions en défense : presser ou temporiser, tacler ou attendre

**Chantier :** `v2-attributs-contextes` (ADR 0002). **Priorité :** P2. **Catégorie :** attributs.

**Constat (audit du 17/11/2026) :** Decisions est lu par le choix du porteur (`decision.py`), des remises (`restart.py`) et, depuis le ticket `v2-realisme/11h` (livré le 16/11/2026, fusionné le 17/11/2026), par le renoncement au tacle hors urgence selon l'angle d'approche (`duel.tackle_attempt_factor`). Le choix du presseur (engager ou attendre le soutien) et le tacle de face (tacler ou temporiser) n'en dépendent pas.

**What to build:** contexte « choix défensif » : le défenseur au contact choisit entre tacler et temporiser, et le presseur entre engager et attendre le soutien, selon Decisions (bon choix plus probable), avec Aggression qui garde la fréquence de base des tentatives (pas de double comptage). Le facteur du 11h (tacle par derrière ou de côté hors urgence) reste tel quel ; ce ticket l'étend au tacle de face et au presseur dans le même contexte « choix défensif », sans compter deux fois le renoncement du 11h. À articuler avec `21c` (faute tactique, découpé en 21c1 à 21c7).

**Attributs :** Decisions, Aggression (fréquence, inchangée), Anticipation (poids à proposer).

**Blocked by:** 01, 02.

**Status:** à faire (contexte, poids et chiffres réels à proposer au propriétaire avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 30 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 35 min |
| Intégration et vérifications | 25 min |
| **Total (travail effectif)** | **2 h 15** |

Confiance : faible. Hypothèses : le déclenchement du tacle (`match.should_attempt_tackle`) et le presseur (`defense.py`) acceptent une probabilité de plus sans refonte. Au-dessus du seuil de 2 h de peu : découpage examiné avant le code.
Temps machine, non compté : suite complète ; séries de 50 matchs avant et après ; banc de profils de l'attribut (`scripts/measure_v2.py --profil`).

## Acceptance criteria

- [ ] Contexte, poids et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Contexte déclaré dans le registre et documenté dans la carte ; entrée retirée de la liste de transition du test de rayon
- [ ] Scène reproductible : 99 contre 11 sur l'attribut, effet probabiliste, jamais binaire
- [ ] 50 matchs avant/après sur l'indicateur visé ; profils 99 / 11 dans le plafond d'écart de la carte ; pas de double comptage (R1)
- [ ] Déterminisme à graine fixée ; suite complète passée, compte comparé à l'attendu de `CLAUDE.md`
- [ ] Durée réelle relevée et comparée à l'estimation
