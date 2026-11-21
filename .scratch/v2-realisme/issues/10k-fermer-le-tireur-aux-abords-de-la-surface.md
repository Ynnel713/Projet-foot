# 10k: Fermer le tireur aux abords de la surface

**Chantier :** `v2-realisme` (suite du `18m` et du `10f`, décision du propriétaire du 21/11/2026 : garder la baisse des buts pour un ticket dédié). **Priorité :** P1 (excès de buts). **Catégorie :** placement.

**Constat vérifié (`docs/INDICATEURS_V2.md` sections 57 et 58, 50 matchs appariés) :** après la sélection des frappes de loin (`18m`), 4,59 tirs hors surface par équipe (réel environ 4,1) mais convertis à 13,3 % (réel 4,2 %) ; 4,86 buts par match (réel environ 2,7) ; conversion dans la surface 16,1 % (réel 14,7 %). Les frappes gardées partent ligne de tir libre, tireur peu gêné entre 16 et 25 m dans l'axe. Les zones de la surface (`10f`) ne jouent que ballon sur l'aile (3 % du temps de possession) et ne changent pas les buts.

**What to build:** À diagnostiquer d'abord (situation des tirs à 16-25 m : distance du plus proche défenseur, ligne de tir couverte ou non, presseur présent, défenseurs entre le tireur et le but), puis proposer la correction au propriétaire : par exemple, porteur dans l'axe à 25 m ou moins, le défenseur libre le plus proche se place sur la ligne de tir (contre), ou le presseur ferme d'abord le tir. Aucune constante sans accord.

**Attributs :** à vérifier sur la carte (`docs/CARTE_ATTRIBUTS_V2.md`) avant tout effet nouveau (Positioning, Anticipation, Bravery pour le contre).

**Blocked by:** aucun (`10f` livré ; à coordonner avec `10g`, marquage dans la surface).

**Bloque :** `v2-collectif/22c` (calibration des tirs et des buts).

**Status:** à faire (diagnostic, puis constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et diagnostic (situations de tir) | 30 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications (50 matchs appariés) | 30 min |
| **Total (travail effectif)** | **2 h 15** |

Confiance : faible (cause à confirmer par le diagnostic). Temps machine, non compté : diagnostic de 10 matchs, série appariée de 50 matchs, suite complète. Au-delà de 2 h : à examiner pour découpage après le diagnostic (diagnostic seul, puis correction).

## Acceptance criteria

- [ ] Diagnostic des tirs à 16-25 m chiffré, correction proposée et validée par le propriétaire avant le code
- [ ] Conversion hors surface et buts par match rapportés avant et après (50 matchs appariés, intervalles), cible indicative à fixer avec le propriétaire
- [ ] Déterminisme à graine fixée ; durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 %
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
