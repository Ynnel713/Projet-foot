# 10b3: Sauts de la place de référence d'un défenseur central d'un tick à l'autre

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P2 (stabilité des décisions défensives). **Catégorie :** mesure, puis placement.

**Origine :** réserve A1 de l'expert au ticket 10b2 (passage 2, 19/11/2026), acceptée par le propriétaire (« Je valide automatiquement toutes tes recommandations et celles de l'expert », 19/11/2026).

**Constat (hypothèse à vérifier) :** au 10b2, la décision de couverture d'un central change encore en 1 s ou moins plus souvent qu'au 10b (allers-retours 5,25 → 13,8 par match, reprises par le même central 2,5 → 8,1 ; 20 matchs, script `verif10b2.py` du dossier de clôture). Le diagnostic sur 4 matchs (`flip10b2.py`) montre des reprises en un tick (0,1 s) où la distance du point de couverture à la place de référence passe de 10,3 à 2,8 m ou de 10,7 à 6,4 m. Le point de couverture est continu (6 m derrière le porteur) : le saut viendrait de la place de référence (`Bloc.reference`, `v2engine/bloc.py`), par exemple de la hauteur de ligne `_line_for` qui évoluerait par paliers. Non vérifié.

**What to build:**
1. Mesure : histogramme des écarts de `Bloc.reference` d'un central d'un tick à l'autre, porteur inchangé, ballon porté ; part des sauts de plus de 2 m ; cause (hauteur de ligne, écarts entre lignes, forme).
2. Si le saut est confirmé : lisser la place de référence utilisée pour les décisions défensives (proposition au propriétaire avant le code, sans constante nouvelle si possible).
3. Relancer `verif10b2.py` : les allers-retours de la couverture ne dépassent pas 13,8 par match (repère du 10b2) et baissent si le lissage est retenu.

**Attributs :** aucun

**Lien avec l'existant :** prolonge le 10b2 ; la règle de couverture et son hystérésis ne changent pas.

**Blocked by:** 10b2 (Le défenseur central ne prend la couverture que si sa place reste tenue).

**Bloque :** 10j (mesure de stabilité à refaire au 10j de toute façon).

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement (mesure, puis lissage éventuel) | 40 min |
| Tests unitaires et comportementaux | 20 min |
| Intégration et vérifications | 30 min |
| **Total (travail effectif)** | **1 h 50** |

Confiance : faible (la cause n'est pas établie). Hypothèses : le saut vient de `Bloc.reference` ; un lissage local suffit.
Temps machine, non compté : mesure de stabilité sur 20 matchs (environ 25 min) ; 100 matchs appariés si le comportement change (environ 1 h) ; suite complète (environ 20 min).

## Tests

- **Unitaires (scène contrôlée) :** porteur immobile, ballon porté : la place de référence d'un central ne varie pas de plus de la valeur validée d'un tick à l'autre
- **Statistiques (séries de matchs) :** 20 matchs : histogramme des sauts, allers-retours de la couverture

## Acceptance criteria

- [ ] Cause des sauts mesurée et rapportée (ou hypothèse écartée)
- [ ] Constantes produit éventuelles validées par le propriétaire avant le code
- [ ] Allers-retours de la couverture rapportés (repère 10b2 : 13,8 par match)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
