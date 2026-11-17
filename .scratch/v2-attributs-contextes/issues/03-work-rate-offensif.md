# 03: Work Rate offensif : soutien et repli après la perte

**Chantier :** `v2-attributs-contextes` (ADR 0002). **Priorité :** P2. **Catégorie :** attributs.

**Constat (audit du 17/11/2026) :** Work Rate n'est lu que par le pressing (`defense.press_intensity`, `press_rest_s`, `replacement_intensity`) ; le ticket `v2-realisme/12d` l'a écarté des appels (« seul Off the Ball »).

**What to build:** Work Rate entre dans deux contextes nouveaux : « soutien offensif » (volume des courses pour se proposer au porteur, avec Off the Ball pour le moment et le choix de l'espace) et « repli après la perte » (intensité et délai du retour derrière le ballon, avec Teamwork). L'intensité de l'appel lui-même reste à Off the Ball (pas de double comptage avec 12d).

**Attributs :** Work Rate, Off the Ball, Teamwork (poids à proposer).

**Blocked by:** 01, 02.

**Status:** à faire (contexte, poids et chiffres réels à proposer au propriétaire avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 35 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 35 min |
| Intégration et vérifications | 30 min |
| **Total (travail effectif)** | **2 h 30** |

Confiance : faible. Hypothèses : les rôles soutien et replacement du cerveau (`cerveau.py`) portent déjà une intensité. Au-dessus du seuil de 2 h : découpage à examiner (soutien, puis repli).
Temps machine, non compté : suite complète ; séries de 50 matchs avant et après ; banc de profils de l'attribut (`scripts/measure_v2.py --profil`).

## Acceptance criteria

- [ ] Contexte, poids et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Contexte déclaré dans le registre et documenté dans la carte ; entrée retirée de la liste de transition du test de rayon
- [ ] Scène reproductible : 99 contre 11 sur l'attribut, effet probabiliste, jamais binaire
- [ ] 50 matchs avant/après sur l'indicateur visé ; profils 99 / 11 dans le plafond d'écart de la carte ; pas de double comptage (R1)
- [ ] Déterminisme à graine fixée ; suite complète passée, compte comparé à l'attendu de `CLAUDE.md`
- [ ] Durée réelle relevée et comparée à l'estimation
