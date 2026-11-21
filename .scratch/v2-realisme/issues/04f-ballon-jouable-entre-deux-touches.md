# 04f: Ballon jouable par un adversaire entre deux touches

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (la touche trop longue est l'erreur la plus courante en conduite). **Catégorie :** exécution.

**Constat vérifié :** voir 04e : sans ballon séparé du porteur, aucun adversaire ne peut le toucher pendant une conduite hors tacle.

**What to build:** Entre deux touches, le ballon peut être touché par un adversaire qui l'atteint avant le porteur (même détection de contact que les passes, `match._contacts`) ; la perte de conduite du 04a est alors en partie remplacée par ce mécanisme physique, sans double comptage (le tirage du 04a ne vaut plus que pour la dépossession au contact).

**Attributs :** aucun

**Blocked by:** 04e (Le ballon n'est plus collé au porteur).

**Bloque :** rien.

**Status:** livré (21/11/2026), validé expert + QC (périmètre revu : interception sans objet, à reprendre au `04i`)

**Point de vigilance :** ne pas cumuler le tirage du 04a et l'interception physique.

## Périmètre revu (21/11/2026, par délégation du propriétaire : « Je valide automatiquement tes recommandations et les conseils d'experts », 20/11/2026)

**Réserve A1 du 04e** (condition : corrigée au début du 04f) : profil de touche asymétrique, `match.TOUCH_PUSH_SHARE` = 0,4 (poussée avec fin en douceur sur 40 % de la période, puis retour linéaire au pied) ; le ballon n'avance jamais moins vite que 0,21 fois le porteur (Dribbling 11), 0,44 (Dribbling 55). Réserve A2 du 04e (retour du ballon au pied à la passe et au tir) : renvoyée à un ticket d'écran, comme le permettait la clôture du 04e.

**Mesure avant l'interception** (`.scratch/v2-realisme/mesures/04f-diag-script.py`, 12 matchs, graines 0 à 11, profil du 04f, sans interception) : en conduite, ballon loin du pied 2 663 ticks par match ; touches où un adversaire frôlerait le ballon à moins de `CONTROL_RADIUS_M` : **96,5 par match**, pour 27,3 pertes de conduite tirées par match (04a). Distance porteur - adversaire à chaque contact : 0,5 à 1 m, 183 par match ; 1 à 1,5 m, 39 ; au-delà de `TACKLE_RADIUS_M` (1,5 m) : **0**. Tous ces contacts sont dans la zone du duel, que résolvent déjà le tacle (11p) et la dépossession tirée du 04a.

**Décision** : interception physique entre deux touches **sans objet** dans le moteur actuel. Hors duel (au-delà de 1,5 m), elle n'arrive jamais ; dans le duel, elle doublerait le tacle et le tirage du 04a (point de vigilance du ticket : « ne pas cumuler »), à 3,5 fois le volume des pertes tirées. À reprendre quand la perte au contact deviendra physique (`04i`, protection du ballon). Critères remplacés ci-dessous.

**Critères d'acceptation (périmètre revu) :**
- [x] Profil de touche : le ballon n'avance jamais moins vite que 0,2 fois le porteur (Dribbling 11 à 99, 3 à 9 m/s), avance maximale à 40 % de la période, retour linéaire (tests de scène). **`tests/test_v2engine_touche_de_balle.py`, 6 cas ajoutés (5 vitesses ou notes, profil), 1 adapté (avance maximale à 0,24 s).**
- [x] Mesure des contacts entre deux touches, par distance au porteur et par tranche de gêne, comparée aux pertes tirées (12 matchs) ; décision documentée (`docs/INDICATEURS_V2.md`). **Section 65 : 96,5 contacts par match, tous à moins de 1,5 m du porteur.**
- [x] Calibration du 04c sur 50 matchs : écart évalué / perte avec tacle sous 3 points par tranche de gêne et de Dribbling. **Défaut du banc corrigé (tirages de rotation du 07e comptés comme intervalles : jusqu'à − 2,8 points) ; après correction, au plus 1,1 point, sauf gêne 0,9 et plus (5 tirages, bruit). Test ajouté (`test_rotation_loss_draws_stay_out_of_the_carry_calibration`).**
- [x] 50 matchs appariés (banc, graines 0 à 49) : passes, pertes, tirs, buts dans le bruit, tout écart significatif expliqué. **Tout dans le bruit (réussite 85,03 %, + 0,13 ± 0,40).**
- [x] Déterminisme à graine fixée ; suite complète comparée à l'attendu (3 473 + tests ajoutés). **Empreinte des comptes du match 3 `fc45d722b5eaff9e` deux fois ; suite complète 3 480 passés (3 473 + 7), 0 ignoré, 14 désélectionnés.**

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 35 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h 05** |

Confiance : faible. Hypothèses : réglage de la répartition entre tirage et physique à proposer.

Réestimation annoncée le 21/11/2026 : 2 h 50 avec la réserve A1 du 04e (45 min), puis **3 h 30** avec la mesure préalable imposée par le volume trouvé (96 contacts par match).
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** défenseur sur la trajectoire de la touche : il récupère le ballon
- **Statistiques (séries de matchs) :** 50 matchs : la calibration du 04c reste sous 3 points

## Acceptance criteria

- [x] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Interceptions entre deux touches tracées (remplacé, voir « Périmètre revu »)
- [x] Courbe de calibration du 04c toujours respectée
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
- 21/11/2026, périmètre revu par délégation du propriétaire (« Je valide automatiquement tes recommandations et les conseils d'experts. Finis donc ce ticket et enchaîne avec les 2 suivants dans un ordre logique sans me solliciter », 20/11/2026) : profil de touche (A1 du 04e) livré, interception physique sans objet après mesure, défaut du banc de calibration corrigé ; A2 du 04e renvoyée à un ticket d'écran. Rapport : `docs/INDICATEURS_V2.md` section 65 ; scripts et sorties `.scratch/v2-realisme/mesures/04f-*`.
- 21/11/2026, clôture : expert APPROVED (empreinte 34d1d089), QC VALIDÉ, clôture VALIDÉ. Améliorations facultatives non faites : A1 (commentaire du bloc des constantes du 04e, « demi-onde » et « interception au 04f », à mettre à jour au prochain passage dans `match.py`), A2 (impulsion de départ de la touche, 16,7 m/s relatifs à Dribbling 11 : à regarder à l'écran, poussée moins concave si le saut paraît sec), A3 (filtre du banc par durée : passer un indicateur de rotation explicite si les rotations dépassent un jour 0,5 s). À surveiller : reprise de l'interception au 04i en retirant la part correspondante du tirage du 04a.

## Durée réelle

Environ 2 h 30 de travail effectif pour 3 h 30 réestimées (− 29 %) ; 2 h 05 à l'origine (+ 20 %) : analyse 25 min, mesure des contacts 35 min (deux reprises du script), développement 20 min (profil, correction du banc), tests 20 min, intégration et vérifications 50 min (calibration relancée après la correction du banc, appariés, rapport). Interception non codée (sans objet), d'où l'écart sous la réestimation. Durée estimée à l'horloge de la session hors attentes machine, non chronométrée ; temps machine hors total : 3 x 12 matchs de mesure, 2 x 50 matchs de calibration, 50 matchs appariés, suite complète (16 min).
