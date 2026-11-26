# 14b: Effet latéral du ballon (enroulé)

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P2 (centres et tirs enroulés n'existent pas sans courbure). **Catégorie :** physique.

**Constat vérifié :** aucune rotation ni courbure du ballon dans `v2engine/`.

**What to build:** Un ballon frappé avec effet garde une accélération latérale proportionnelle à sa vitesse, décroissante dans le temps ; la frappe choisit l'effet (tickets de geste : `v2-attributs-restants/10a`, `11`).

**Attributs :** aucun

**Blocked by:** 14a (Freinage du ballon au sol : roulement et air); `v2-hauteur-ballon/02a`.

**Bloque :** 14c, 14d, 16d, 16e.

**Status:** découpé (26/11/2026, audit Magnus `docs/AUDIT_MAGNUS_V2.md`, demande du propriétaire) en 14b1 (spin et force de Magnus dans le solveur), 14b2 (passes sur trajectoire courbe), 14b3 (tirs sur trajectoire courbe, visée inverse), 14b4 (qui met de l'effet : spin par type de frappe). Ticket chapeau : ne pas l'implémenter tel quel ; le texte ci-dessous reste la référence de détail. Une référence à ce ticket sans lettre vaut pour tous ses morceaux. Estimation d'origine (2 h) remplacée par 9 h 30 au total (14b1 2 h 25, 14b2 1 h 50, 14b3 2 h 40, 14b4 2 h 35 ; révisée le 26/11/2026 après les demandes du propriétaire) : elle ignorait les sites de décision qui supposent une ligne droite (audit, section 4).

**Note de réalisme (26/11/2026) :** tant que 14b n'est pas livré, coups francs, corners et centres enroulés sont des lignes droites. Trou assumé, documenté, pas caché : aucun but enroulé au-dessus du mur ni corner rentrant possible, aucun gardien trompé par une courbe. Gros levier de réalisme des coups de pied arrêtés (16d, 16e) et des centres (`v2-attributs-restants/11`).

**Périmètre :** D-V03 révisée le 26/11/2026 (`docs/TRD_V2.md`) : rotation du ballon et effet Magnus dans le périmètre, vent exclu.

**Ordre :** 14b1 → 14b2 et 14b3 en parallèle (vérifié dans le code : la visée des tirs n'utilise aucun site du 14b2) → 14b4.

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
