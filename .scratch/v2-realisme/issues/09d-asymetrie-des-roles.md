# 09d: Formations asymétriques

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (beaucoup d'équipes jouent avec un côté offensif et un côté prudent). **Catégorie :** placement.

**Constat vérifié :** les rôles par défaut (02c) sont symétriques ; aucune donnée ne permet un côté différent de l'autre.

**What to build:** Permettre deux rôles différents au même poste de part et d'autre (par exemple latéral gauche offensif, droit défensif), lus depuis la composition (repli : rôle par défaut). Positions moyennes asymétriques en conséquence.

**Attributs :** aucun

**Blocked by:** 02d (Place de référence avec ballon selon le rôle); 02e (Place de référence sans ballon selon le rôle).

**Bloque :** 09h.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 35 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 30** |

Confiance : élevée. Hypothèses : source des rôles par côté : composition ou consignes (13i).
Temps machine, non compté : suite complète (environ 40 min) ; mesure 20 matchs.

## Tests

- **Unitaires (scène contrôlée) :** latéral gauche offensif et droit défensif : hauteurs moyennes différentes

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Asymétrie mesurée en scène et sur 20 matchs
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
