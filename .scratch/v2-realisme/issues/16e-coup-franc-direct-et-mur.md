# 16e: Coup franc direct et mur

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P2 (le coup franc direct est un tir à part entière). **Catégorie :** exécution.

**Constat vérifié :** un coup franc est aujourd'hui frappé ou passé par le preneur le plus proche, sans mur (ticket 30) ; Free Kick Taking n'est lu nulle part.

**What to build:** Sur un coup franc à portée, un mur de N joueurs (selon la distance) à 9,15 m, le gardien sur le côté opposé ; le tireur (meilleur Free Kick Taking) frappe par-dessus ou à côté du mur, avec effet ; résolution physique du tir (05a, 05b).

**Attributs :** Free Kick Taking

**Lien avec l'existant :** découpe (validée le 05/11/2026) de `v2-attributs-restants/02b` : coup franc direct.

**Blocked by:** 05b (Arrêt : le gardien atteint ou non le ballon); 14b (Effet latéral du ballon (enroulé)); `v2-collectif/35a`.

**Bloque :** 16g.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h 05** |

Confiance : faible. Hypothèses : hauteur et effet disponibles.
Temps machine, non compté : suite complète (environ 40 min).

## Tests

- **Unitaires (scène contrôlée) :** coup franc à 20 m : mur placé, gardien côté opposé
- **Comportementaux (profils comparés) :** Free Kick Taking 99 contre 11 : plus de tirs cadrés

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Mur et tir tracés
- [ ] Effet de l'attribut mesuré
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
