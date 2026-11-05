# 17a: Carte des attributs : état réel de branchement

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (la carte annonce branchés des attributs que le moteur ne lit pas). **Catégorie :** documentation.

**Constat vérifié :** `docs/CARTE_ATTRIBUTS_V2.md` donne Technique « branché ; à revoir », alors qu'aucun appel `player_attribute(..., "Technique")` n'existe dans `v2engine/` (seule mention : une docstring de `match.py`).

**What to build:** Relire la colonne « État » de la carte contre le code (recherche de chaque nom d'attribut) et la corriger : branché (avec le fichier), lu sans effet sur l'issue (cas de Dribbling avant 04a), à créer (avec le ticket qui le branche, dont ceux de ce chantier). Aucun code.

**Attributs :** aucun

**Blocked by:** None.

**Bloque :** 17d, 18a.

**Status:** à faire

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 30 min |
| Développement | 30 min |
| Tests unitaires et comportementaux | 0 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 15** |

Confiance : élevée. Hypothèses : documentation seulement.
Temps machine, non compté : suite complète (environ 40 min).

## Tests

- **Intégration :** liste des attributs lus par le code jointe au rapport

## Acceptance criteria

- [ ] Chaque ligne de la carte cohérente avec le code ou renvoyée à un ticket
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
