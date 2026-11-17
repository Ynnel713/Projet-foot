# 06: Balance après contact : conduite, contrôle et frappe en déséquilibre

**Chantier :** `v2-attributs-contextes` (ADR 0002). **Priorité :** P2. **Catégorie :** attributs.

**Constat (audit du 17/11/2026) :** Balance n'est lu que par le duel au contact (`duel._balance_curve`).

**What to build:** Balance entre dans les contextes « garder le ballon après un contact » (risque de perte en conduite juste après un duel d'épaule ou une charge, avec Dribbling) et « geste en déséquilibre » (contrôle et frappe pendant ou juste après un contact, avec Technique). Le contact perdu du ticket `12c` reste l'effet de Balance sur le déplacement (pas de double comptage).

**Attributs :** Balance, Dribbling, Technique (poids à proposer).

**Blocked by:** 01, 02.

**Status:** à faire (contexte, poids et chiffres réels à proposer au propriétaire avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 30 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 25 min |
| **Total (travail effectif)** | **2 h 05** |

Confiance : faible. Hypothèses : un état « juste après contact » existe ou se dérive du contact perdu (`unsettle`, 12c) ; au seuil de 2 h : découpage examiné (conduite, puis gestes).
Temps machine, non compté : suite complète ; séries de 50 matchs avant et après ; banc de profils de l'attribut (`scripts/measure_v2.py --profil`).

## Acceptance criteria

- [ ] Contexte, poids et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Contexte déclaré dans le registre et documenté dans la carte ; entrée retirée de la liste de transition du test de rayon
- [ ] Scène reproductible : 99 contre 11 sur l'attribut, effet probabiliste, jamais binaire
- [ ] 50 matchs avant/après sur l'indicateur visé ; profils 99 / 11 dans le plafond d'écart de la carte ; pas de double comptage (R1)
- [ ] Déterminisme à graine fixée ; suite complète passée, compte comparé à l'attendu de `CLAUDE.md`
- [ ] Durée réelle relevée et comparée à l'estimation
