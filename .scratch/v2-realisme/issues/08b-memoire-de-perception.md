# 08b: Mémoire de perception : positions vues, datées et vieillissantes

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (avancé le 05/11/2026 sur décision du propriétaire : base du contrôle orienté et du jeu à une touche (`v2-collectif/31`)). **Catégorie :** perception.

**Constat vérifié :** aucune mémoire : la perception est recalculée sur les positions réelles à chaque pas (`cerveau.perceive`).

**What to build:** Chaque joueur garde la dernière position et vitesse vues de chaque autre joueur, avec l'instant ; la position perçue est extrapolée et son erreur croît avec l'âge de l'observation. Anticipation règle seulement la qualité de l'extrapolation (déjà son rayon : lire l'action), sans nouvel effet.

**Attributs :** Anticipation (extrapolation, rayon existant)

**Blocked by:** 08a (Champ de vision : ce qui est dans le dos n'est pas vu).

**Bloque :** 08c, 08d, 08e, `v2-collectif/31`.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : erreur linéaire avec le temps : forme simple à valider.
Temps machine, non compté : suite complète (environ 40 min).

## Tests

- **Unitaires (scène contrôlée) :** adversaire vu puis caché 2 s : position perçue extrapolée, erreur bornée

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Mémoire tracée pour le porteur et les receveurs
- [ ] Aucun effet sur le jeu dans ce ticket
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
