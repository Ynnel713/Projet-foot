# 15a: Qui attaque la trajectoire aérienne

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P2 (seuls les joueurs capables d'arriver au point de chute disputent le ballon). **Catégorie :** décision.

**Constat vérifié :** un ballon aérien ne peut être touché qu'à son point de chute (`ball.aerial_left_m`, ticket 29) ; aucune sélection des joueurs qui l'attaquent.

**What to build:** Pour un ballon aérien, chaque équipe désigne au plus deux joueurs qui vont au point de contact (temps d'arrivée et hauteur atteignable, `v2-hauteur-ballon/03`) ; les autres se placent pour le second ballon.

**Attributs :** aucun

**Lien avec l'existant :** découpe (validée le 05/11/2026) de `v2-attributs-restants/01` : sélection.

**Blocked by:** `v2-hauteur-ballon/03`.

**Bloque :** 15b, 15e, 16a, 16f.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : hauteur du ballon disponible.
Temps machine, non compté : suite complète (environ 40 min).

## Tests

- **Unitaires (scène contrôlée) :** dégagement long : les deux plus aptes de chaque équipe attaquent le ballon, les autres non

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Sélection tracée
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
