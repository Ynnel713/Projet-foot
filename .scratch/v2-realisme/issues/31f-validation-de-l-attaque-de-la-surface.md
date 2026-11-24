# 31f: Validation de l'attaque de la surface sur centre

**Chantier :** `v2-realisme` (demande du propriétaire du 24/11/2026 : « il n'y a pas beaucoup de centres pour le moment dans le moteur et j'aimerais corriger ça avant de continuer le chantier des têtes »). **Priorité :** P1. **Catégorie :** validation.

**What to build:** rapport sur 50 matchs (graines d'audit), avec le script du `31a` : entrées dans la zone de centre, coéquipiers dans la surface au moment d'un centre possible (avant le `31a` / après le `31e`), centres par équipe, centres réussis, zones occupées, premier contact (tête, pied, défenseur, gardien), tirs et buts sur centre, gestes de la tête (`15c1`), contres encaissés après un centre ; comparaison aux repères réels (sourcés ou « non trouvé »). Diagnostic de la valeur du centre (`LONG_BALL_WON`) : si les cibles existent mais que le centre reste rare parce que l'option est sous-valorisée, ticket à part proposé au propriétaire (pas de réglage ici).

**Attributs :** aucun.

**Blocked by:** `31a` à `31e`. **Bloque :** rien.

**Status:** à faire

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 20 min |
| Tests unitaires et comportementaux | 10 min |
| Intégration et vérifications | 30 min |
| **Total (travail effectif)** | **1 h 15** |

Confiance : moyenne. Temps machine, non compté : série de 50 matchs (environ 45 min).

## Acceptance criteria

- [ ] Rapport sur 50 matchs ; écarts aux repères réels expliqués, sans réglage
- [ ] Constats hors périmètre proposés au propriétaire en tickets séparés
- [ ] Durée réelle relevée

## Comments
