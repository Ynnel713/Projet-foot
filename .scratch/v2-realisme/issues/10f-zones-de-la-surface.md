# 10f: Défense de la surface : premier poteau, second poteau, point de penalty, retrait

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (les buts se marquent surtout dans ces quatre zones). **Catégorie :** placement.

**Constat vérifié :** dans les 25 m, le défenseur libre le plus proche marque un attaquant côté but (`defense.py:341-350`) ; aucune zone de surface n'est tenue.

**What to build:** Quand le ballon est dans un couloir extérieur du dernier tiers défensif, attribuer des zones de surface (premier poteau, second poteau, point de penalty, zone de retrait) aux défenseurs libres après le presseur et la couverture, selon une priorité validée.

**Attributs :** aucun

**Blocked by:** 02e (Place de référence sans ballon selon le rôle).

**Bloque :** 10g, 10h, 16b.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : valable sur passes au sol en attendant les centres (`v2-attributs-restants/01`).
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** ballon sur l'aile à 10 m de la ligne de but : quatre zones tenues si quatre défenseurs libres

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Zones attribuées et tracées
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
