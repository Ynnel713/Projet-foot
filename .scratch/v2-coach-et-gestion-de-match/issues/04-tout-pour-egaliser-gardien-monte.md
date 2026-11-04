# 04: Tout pour égaliser : risques maximaux et gardien qui monte

**What to build:** Le « tout pour égaliser » n'est pas un mode qu'on active : c'est l'**extrémité de la courbe** du ticket 02 (fin de match, un but change le résultat), avec le même mécanisme : défenseurs centraux projetés, ligne très haute, ballons longs vers la surface, tirs tentés de plus loin.

Le seul comportement nouveau est **le gardien qui monte** : sur un corner ou un coup franc offensif proche de la surface, dans le temps additionnel de la seconde période, quand un but changerait le résultat, le gardien peut monter dans la surface adverse. Sa probabilité augmente quand le temps restant diminue et avec Eccentricity ; le style du coach module l'intensité, jamais l'existence. Il retourne vers son but dès la perte du ballon (course réelle, but vide exploitable par l'adversaire). L'arbitre ne siffle pas la fin avant l'exécution du coup de pied arrêté (ticket 03).

C'est un **événement rare**, comme dans la réalité.

**Attributs :** Determination ; Eccentricity du gardien (v2-attributs-restants/03) ; Taille, Jumping Reach et Heading du gardien pour le duel aérien (v2-attributs-restants/01) ; Pace et Stamina pour le retour.

**Blocked by:** 02, 03 ; v2-attributs-restants/01, 02b (corners et coups francs travaillés) et 03 (a, b ; Eccentricity au 03b).

**Status:** à faire (constantes à proposer avant le code)

**Point de vigilance :** risque de surcalibrage spectaculaire. Fréquence réelle (gardien monté sur coup de pied arrêté, puis but de gardien) à sourcer avant de fixer une constante ; à défaut, « non trouvé » et validation du propriétaire. Dans un match isolé (D-V09), « un but change le résultat » équivaut à « menée d'un but » ; la formulation générale servira pour les matchs à élimination directe.

- [ ] Définir dans `docs/INDICATEURS_V2.md` et ajouter à `scripts/v2_indicators.py` : joueurs dans la surface adverse, tirs tentés, occasions concédées dans le dos, gardien monté
- [ ] Mesure par scénarios forcés (score 0-1, minute 92, corner offensif, N graines ; N et intervalle fixés avant la mesure)
- [ ] Menée d'un but dans le temps additionnel : hauteur du bloc, joueurs dans la surface adverse et tirs tentés supérieurs au même état à la 60e (continuité de la courbe du ticket 02)
- [ ] Gardien monté uniquement si un but change le résultat, en fin de match, sur un coup de pied arrêté offensif ; jamais en menant
- [ ] Fréquence dans une fourchette réelle sourcée (ou validée par le propriétaire si non trouvée)
- [ ] Après perte du ballon, retour du gardien à sa vitesse réelle ; tir adverse dans le but vide possible
- [ ] Menée de deux buts ou plus : pas de gardien qui monte
- [ ] Constantes produit et critères chiffrés validés par le propriétaire avant le code
- [ ] Suite V2 verte ; V1 inchangée
