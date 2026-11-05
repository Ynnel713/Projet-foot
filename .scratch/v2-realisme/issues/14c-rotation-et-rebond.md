# 14c: Rotation et rebond

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P2 (un ballon rétro ou lifté ne rebondit pas pareil). **Catégorie :** physique.

**Constat vérifié :** aucune rotation ; le rebond arrive avec `v2-hauteur-ballon/02a` (à faire).

**What to build:** La rotation (avant ou arrière) modifie la vitesse horizontale au rebond (gain ou perte bornés).

**Attributs :** aucun

**Blocked by:** 14b (Effet latéral du ballon (enroulé)).

**Bloque :** 14d.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 45** |

Confiance : faible. Hypothèses : valeurs à sourcer.
Temps machine, non compté : suite complète (environ 40 min).

## Tests

- **Unitaires (scène contrôlée) :** même ballon avec rétro et avec lift : distance après rebond différente dans le sens attendu

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Effet de la rotation au rebond mesuré en scène
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
