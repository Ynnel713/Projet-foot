# 27b: Distributions de référence tirées des données de suivi

**Chantier :** `v2-realisme` (suggestions du propriétaire du 14/11/2026, axe « validation sur données réelles de trajectoires » : sans elle, le moteur peut être cohérent mais faux). **Priorité :** P1. **Catégorie :** mesure.

**Constat vérifié (14/11/2026) :** les repères du banc sont des moyennes (01c) ; une moyenne juste peut cacher une distribution fausse (un bloc toujours à 40 m de large au lieu d'un bloc qui respire entre 30 et 55 m).

**What to build:** sur les données du 27a, calculer des distributions (pas seulement des moyennes), par phase de possession quand le jeu de données le permet : largeur et profondeur de chaque équipe, écarts défense-milieu et milieu-attaque, hauteur de la ligne défensive, distance au plus proche adversaire du receveur à la réception, distance du soutien le plus proche du porteur, vitesse des joueurs par poste (part au-dessus de 19,8 et 25 km/h), distance entre le presseur et le porteur. Mêmes définitions que les indicateurs du moteur (`scripts/v2_indicators.py`), écarts de définition notés. Résultat publié dans `docs/INDICATEURS_V2.md` (section nouvelle), avec la taille de l'échantillon.

**Attributs :** aucun.

**Blocked by:** 27a.

**Bloque :** 27c.

**Status:** implémenté (14/11/2026) — en attente de /valider-ticket-simulafoot

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

- [x] Chaque distribution publiée avec médiane, quartiles et taille d'échantillon
- [x] Mêmes fonctions de calcul pour le réel et pour le moteur (aucune réécriture parallèle)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme : sortie identique sur deux lectures des mêmes données
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md` (2 982 passés, 0 ignoré, 14 désélectionnés : 2 971 + 11 tests du 27b, en 10 min 37 ; attendu de `CLAUDE.md` mis à jour)

## Implémentation (14/11/2026)

**Décisions du propriétaire (14/11/2026, « OK avec tes propositions ») :** vitesse sur fenêtre centrée de ±0,2 s, joueur détecté sur toute la fenêtre, au-dessus de 12 m/s écarté ; familles de postes (défenseur central, latéral, milieu, ailier, attaquant ; LM et RM : milieux ; remplaçants `SUB` exclus ; Metrica sans postes, gardien par position médiane) ; réception = changement de porteur dans la même équipe, adversaire le plus proche gardien compris ; presseur = adversaire de champ le plus proche ; soutien = coéquipier le plus proche, gardien compris ; découpage avec / sans ballon puis phases SkillCorner. Estimation revue annoncée avant le code : 2 h 05 (20/60/25/20), le porteur (`Frame.holder`) et le gardien Metrica en plus. Le ticket 24, en cours dans une autre session, ne touche pas ces fichiers de code (conflits possibles seulement dans la documentation, au merge).

**Critères chiffrés posés avant le code :** n, Q1, médiane, Q3 pour chaque distribution ; un test vérifie que le script du réel appelle les fonctions de `v2_indicators` (identité des objets) ; chaque indicateur testé sur une scène synthétique à valeur connue (forme dont hauteur sur un terrain de 106 m, réception, soutien, presseur, vitesse à vitesse constante) ; deux exécutions à même sha256 ; suite complète comparée à l'attendu.

**Code :** `scripts/v2_indicators.py` (fonctions partagées `nearest_distance`, `speed_shares`, `quartiles`, table `POSTE_FAMILY`) ; `scripts/suivi_reel.py` (`Frame.holder`, joueur en possession SkillCorner) ; `scripts/suivi_distributions.py` (calcul et rapport JSON) ; tests `tests/test_suivi_distributions.py` (11) et `tests/test_suivi_reel.py` (porteur lu).

**Mesures :** `docs/INDICATEURS_V2.md`, section 39. Constats : la variante « équipe détectée » est biaisée par sa sélection (bloc resserré quand la caméra voit tout le monde : longueur 28,0 / 22,5 m contre 33,9 / 29,1 m en toutes positions, 31,9 m chez Metrica) : repère de forme pour le 27c = « toutes positions » ; vitesses SkillCorner (joueurs détectés, près du ballon) au-dessus de Metrica (2,0 % du temps au-dessus de 19,8 km/h) : repère de vitesse globale = Metrica, SkillCorner pour l'ordre entre postes. Deux exécutions : sha256 `95a8e952…` identique, 1 min 10 s chacune sur 4 processus.

**Durée :** estimée 2 h 05 (20/60/25/20 ; 1 h 50 au ticket), réelle environ 1 h 35 (20/35/20/20), − 24 %, sous 30 % ; durée estimée à l'horloge de la session hors attentes machine, non chronométrée ; les fonctions de forme du moteur s'appliquaient telles quelles à des `Vec2`, d'où un développement plus court. Temps machine, hors total : deux calculs complets (1 min 10 s chacun), suite complète (10 min 37).
