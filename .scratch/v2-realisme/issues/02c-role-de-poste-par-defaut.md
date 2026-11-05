# 02c: Rôle de poste par défaut, porté par le joueur et tracé

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (les placements et appels différenciés s'appuient sur un rôle). **Catégorie :** données.

**Constat vérifié :** aucun rôle de poste dans `v2engine/` : `PlayerState` porte seulement `poste` ; le bloc est une mise à l'échelle uniforme de la forme de départ (`bloc.py:178-199`).

**What to build:** Une table de rôles (par exemple latéral défensif ou offensif, milieu récupérateur, relayeur, meneur, ailier de couloir ou intérieur, avant-centre de profondeur ou pivot) et un rôle par défaut pour chaque poste ; le rôle est porté par l'état du joueur et écrit dans la trace. Aucun effet sur le jeu dans ce ticket (les effets arrivent en 02d, 02e et 09).

**Hors de ce ticket :** choix du rôle par le coach (13i).

**Attributs :** aucun

**Blocked by:** 02a (Côté gauche ou droit selon le poste, et non selon le nom).

**Bloque :** 02d, 02e, 09c, 13h.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 40** |

Confiance : élevée. Hypothèses : table de données, aucune décision.
Temps machine, non compté : suite complète (environ 40 min).

## Tests

- **Unitaires (scène contrôlée) :** chaque poste de la base a un rôle par défaut ; trace : le rôle figure dans les instantanés
- **Intégration :** trace identique à la version précédente hors nouveau champ

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Table des rôles documentée (rôle, intention footballistique)
- [ ] Rôle tracé ; aucun effet sur le jeu (mesures identiques à graine fixée)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
