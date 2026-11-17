# 05: Flair : goût du risque dans la décision du porteur

**Chantier :** `v2-attributs-contextes` (ADR 0002). **Priorité :** P2. **Catégorie :** attributs.

**Constat (audit du 17/11/2026) :** Flair n'est lu que par l'idée de talonnade (`decision.backheel_idea_probability`).

**What to build:** contexte « goût du risque » : Flair majore la valeur perçue des options risquées à fort gain (passe clé, dribble tenté face à un adversaire, frappe lointaine) dans la perception du porteur, sans toucher la valeur factuelle ni l'erreur de perception de Decisions (temps du cerveau distincts, ADR 0001). À articuler avec `v2-collectif/19` (profils et tendances) et `v2-realisme/25f` (dézonage).

**Attributs :** Flair, Decisions (inchangé : ampleur de l'erreur) (poids à proposer).

**Blocked by:** 01, 02.

**Status:** à faire (contexte, poids et chiffres réels à proposer au propriétaire avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 35 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 25 min |
| **Total (travail effectif)** | **1 h 55** |

Confiance : faible. Hypothèses : la perception du porteur (`decision.choose_action`) accepte un biais par type d'option sans refonte ; le taux de meilleur choix suivi (`scripts/measure_v2_meilleur_choix.py`) est remesuré.
Temps machine, non compté : suite complète ; séries de 50 matchs avant et après ; banc de profils de l'attribut (`scripts/measure_v2.py --profil`).

## Acceptance criteria

- [ ] Contexte, poids et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Contexte déclaré dans le registre et documenté dans la carte ; entrée retirée de la liste de transition du test de rayon
- [ ] Scène reproductible : 99 contre 11 sur l'attribut, effet probabiliste, jamais binaire
- [ ] 50 matchs avant/après sur l'indicateur visé ; profils 99 / 11 dans le plafond d'écart de la carte ; pas de double comptage (R1)
- [ ] Déterminisme à graine fixée ; suite complète passée, compte comparé à l'attendu de `CLAUDE.md`
- [ ] Durée réelle relevée et comparée à l'estimation
