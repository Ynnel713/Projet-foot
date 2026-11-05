# 14b: Effet latéral du ballon (enroulé)

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P2 (centres et tirs enroulés n'existent pas sans courbure). **Catégorie :** physique.

**Constat vérifié :** aucune rotation ni courbure du ballon dans `v2engine/`.

**What to build:** Un ballon frappé avec effet garde une accélération latérale proportionnelle à sa vitesse, décroissante dans le temps ; la frappe choisit l'effet (tickets de geste : `v2-attributs-restants/10a`, `11`).

**Attributs :** aucun

**Blocked by:** 14a (Freinage du ballon au sol : roulement et air); `v2-hauteur-ballon/02a`.

**Bloque :** 14c, 14d, 16d, 16e.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h** |

Confiance : faible. Hypothèses : modèle simplifié de Magnus, coefficients à sourcer.
Temps machine, non compté : suite complète (environ 40 min).

## Tests

- **Unitaires (scène contrôlée) :** ballon frappé à 25 m/s avec effet : écart latéral sur 20 m dans la fourchette sourcée

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Trajectoire courbe mesurée en scène
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
