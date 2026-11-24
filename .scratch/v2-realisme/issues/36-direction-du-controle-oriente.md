# 36: Direction du contrôle orienté : vers l'espace, loin du presseur, vers la suite

**Chantier :** `v2-realisme` (demande du propriétaire du 24/11/2026, éléments sur la technique, point 1 « contrôle orienté » et « prise de balle sous pression », priorité 1). **Priorité :** P1. **Catégorie :** décision et exécution.

**Constat vérifié (24/11/2026) :** le contrôle orienté (`v2-collectif/31b`, livré) est un tirage oui ou non (`possession.orients_control`, First Touch, ballon dur et Technique au 31c) ; réussi, il tourne seulement le corps « vers le jeu, côté but » (`match._orient`, `reception.open_facing`) et raccourcit le délai avant la décision (x 0,6). Le ballon, lui, est posé au pied (`ball.position = player.position`, vitesse nulle) ; puis, pendant la réception, le joueur avance au pas de contrôle **vers le but adverse** quoi qu'il arrive (`cerveau.py`, rôle porteur, `ball.receiving`). La direction de la touche ne tient donc compte ni de l'espace libre, ni du presseur qui arrive (même dans le dos, perçu ou non), ni de la passe ou de la course préparée.

**What to build:** au contact, le receveur qui oriente son contrôle choisit la **direction de sa touche** parmi quelques candidates, dans la monnaie commune de la décision (`decision.py`, `v2-collectif/33`), sur ce qu'il perçoit (`08b`, `08c`) :
- vers l'**espace libre** le plus proche (candidats du `25a` s'il est livré, sinon points libres de la conduite) ;
- **à l'opposé du presseur** (celui qu'il a vu au scan ; un presseur non perçu dans son dos n'est pas évité, d'où la valeur du scan) ;
- dans l'axe de la **passe suivante préparée** (plan de passe du `v2-collectif/14`) ou de sa **course** (lien `38`).
La touche pousse le ballon d'une courte distance dans cette direction (ballon à distance du pied, `04e`), le corps suit (`_orient`, rotation bornée du `07a`), et la réception se joue vers cette direction au lieu du but. L'issue de la touche (distance, écart) reste celle du `26a`, centrée sur la direction choisie : ce ticket fixe l'**intention**, le `26a` sa **dispersion**. Contrôle non orienté : inchangé.

**Hors de ce ticket :** dispersion du contrôle (`26a`) ; contrôle d'un ballon aérien (`37`) ; contrôle dans la course lancée (`38`) ; protection du corps à la réception (`04i`).

**Attributs (ADR 0002, poids à proposer) :** aucun effet nouveau d'attribut sur la réussite (First Touch reste la chance d'orienter, `31b`) ; le choix de la direction passe par Decisions (erreur de perception existante) et la perception (Vision, scans) déjà branchées. À vérifier dans la carte : pas de second bonus de First Touch (R1).

**Blocked by:** `26a` (dispersion autour de l'intention), `04e` (ballon à distance du pied) ; `v2-collectif/31b`, `08c` (livrés).

**Bloque :** `38`, `39`, `v2-collectif/22a`.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : `26a` livré avant (le contrôle a déjà une direction et une distance) ; trois à quatre directions candidates suffisent ; la valeur réutilise celle de la conduite (`decision.dribble_options`). Temps machine, non compté : série de 50 matchs (environ 40 min), suite complète (environ 20 min).

## Tests

- **Scènes :** presseur perçu arrivant de la gauche : touche orientée à droite plus souvent qu'à gauche ; même presseur non perçu (pas de scan) : pas d'évitement ; espace libre sur l'aile et but bouché : touche vers l'aile ; passe suivante préparée : touche dans son axe.
- **Statistiques (50 matchs, avant / après) :** pertes dans les 3 s après une réception sous pression (presseur à moins de 3 m), temps par possession de joueur, passes par minute de jeu effectif, buts (dans le bruit).

## Acceptance criteria

- [ ] Constantes produit (directions candidates, longueur de la touche orientée) et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Direction de la touche tracée (`ReceptionEvent` : direction choisie, raison)
- [ ] Scènes ci-dessus ; un presseur non perçu n'est jamais évité
- [ ] Pertes après réception sous pression en baisse, sans dérive des buts au-delà du bruit (50 matchs appariés)
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Comments
