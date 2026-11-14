# 27b: Distributions de référence tirées des données de suivi

**Chantier :** `v2-realisme` (suggestions du propriétaire du 14/11/2026, axe « validation sur données réelles de trajectoires » : sans elle, le moteur peut être cohérent mais faux). **Priorité :** P1. **Catégorie :** mesure.

**Constat vérifié (14/11/2026) :** les repères du banc sont des moyennes (01c) ; une moyenne juste peut cacher une distribution fausse (un bloc toujours à 40 m de large au lieu d'un bloc qui respire entre 30 et 55 m).

**What to build:** sur les données du 27a, calculer des distributions (pas seulement des moyennes), par phase de possession quand le jeu de données le permet : largeur et profondeur de chaque équipe, écarts défense-milieu et milieu-attaque, hauteur de la ligne défensive, distance au plus proche adversaire du receveur à la réception, distance du soutien le plus proche du porteur, vitesse des joueurs par poste (part au-dessus de 19,8 et 25 km/h), distance entre le presseur et le porteur. Mêmes définitions que les indicateurs du moteur (`scripts/v2_indicators.py`), écarts de définition notés. Résultat publié dans `docs/INDICATEURS_V2.md` (section nouvelle), avec la taille de l'échantillon.

**Attributs :** aucun.

**Blocked by:** 27a.

**Bloque :** 27c.

**Status:** à faire

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 50** |

Confiance : moyenne. Hypothèses : les fonctions de `v2_indicators.py` s'appliquent à une image de positions réelles sans adaptation lourde ; données de diffusion (joueurs hors champ de caméra) traitées comme absentes, pas comme nulles.
Temps machine, non compté : calcul sur l'ensemble des matchs du jeu de données.

## Tests

- **Unitaires :** chaque indicateur sur une scène synthétique dont la valeur est connue, avec les mêmes fonctions que pour le moteur.

## Acceptance criteria

- [ ] Chaque distribution publiée avec médiane, quartiles et taille d'échantillon
- [ ] Mêmes fonctions de calcul pour le réel et pour le moteur (aucune réécriture parallèle)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme : sortie identique sur deux lectures des mêmes données
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
