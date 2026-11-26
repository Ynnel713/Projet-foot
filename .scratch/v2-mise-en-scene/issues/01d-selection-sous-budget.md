# 01d: Sélection sous budget et modes côté serveur

**Chantier :** `v2-mise-en-scene` (audit du mode « moments clés », 26/11/2026). **Catégorie :** lecture de la trace (moteur inchangé).

**What to build:** dans le module du `01b`, une fonction par mode qui choisit les moments (01c) à montrer, dans l'ordre chronologique :
1. **Tier 1 toujours** : tous les moments Tier 1 sont gardés, même si leur durée dépasse le budget du mode (un match à huit buts dépasse le budget, il n'est jamais amputé d'un but).
2. **Tier 2 ensuite**, par score d'intérêt décroissant, tant que la durée cumulée (fenêtres + carton de contexte du `01f`) reste sous le budget du mode.
3. **Plafond par type** : au plus N moments d'un même type et d'une même issue dans le mode (évite dix arrêts identiques).
4. **Modes** : Buts (moments de type but), Moments clés (Tier 1 seulement, `02`), Résumé (Tier 1 + Tier 2 sous budget, `03`). Les budgets et règles propres à chaque mode sont fixés dans `02` et `03` ; ce ticket fournit le mécanisme et le mode Buts.

**Attributs :** aucun.

**Constantes à proposer avant le code :** durée du carton de contexte comptée dans le budget (fixée au `01f`, provisoire ici) ; plafonds par type.

**Blocked by:** 01c.

**Bloque :** 01e, 02, 03.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 10 min |
| Développement | 30 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 10 min |
| **Total (travail effectif)** | **1 h 15** |

Confiance : élevée. Hypothèses : sélection gloutonne par score suffisante (pas d'optimisation de remplissage).
Temps machine, non compté : suite complète (environ 10 min).

## Tests

- Trace construite à 8 buts et budget court : les 8 buts sont gardés.
- Budget atteint : le Tier 2 au plus faible score est écarté le premier ; ordre de sortie chronologique.
- Plafond par type respecté.
- Mode Buts sur une trace 0-0 : liste vide.

## Acceptance criteria

- [ ] Constantes validées par le propriétaire avant le code
- [ ] Tier 1 jamais écarté (test à 8 buts) ; Tier 2 écarté par score croissant (test)
- [ ] Sortie chronologique, plafond par type respecté
- [ ] Mode Buts : uniquement les buts, liste vide pour un 0-0
- [ ] Fonction pure, sortie identique sur deux exécutions
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
