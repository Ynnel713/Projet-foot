# 10m: Le marqueur collé empêche le receveur de se retourner

**Chantier :** `v2-realisme` (demande du propriétaire du 24/11/2026, éléments sur la défense, point 3 « contact, épaule contre épaule : empêcher l'attaquant de se retourner ou de recevoir proprement »). **Priorité :** P1. **Catégorie :** exécution.

**Constat vérifié (24/11/2026) :** le marqueur se place côté but à une distance réglée par Marking (`defense.marking_distance_m` : 1 m à 99, 2,5 m à 55, 4 m à 11) ; le receveur s'ouvre librement vers le jeu si la rotation bornée le permet (`reception.open_facing`, `07a`, `07c`), et son temps de contrôle dépend du type de réception (`07d`), jamais du marqueur dans son dos. Mesure du `07c` : 0,5 % des passes reçues dos au jeu, 0,4 % pour l'avant-centre, irréaliste ; cause notée alors : « un marqueur collé dans son dos qui l'empêche de se tourner, mécanisme absent ».

**What to build:** un receveur qui a un adversaire au contact dans son dos (à moins d'une distance proposée, côté but) ne peut pas s'ouvrir vers le but avant la réception : il reçoit dos au jeu (`07c`, durée du `07d`) et ne se retourne ensuite qu'en éliminant (gestes du dribble) ou en remise ; le marqueur peut aller au contact au moment du contrôle (duel d'épaule du `11c`, Strength) ou couper la passe s'il la lit (`anticipation.pass_readers`, existant). L'effet de la note vient de la distance de marquage existante (un bon marqueur est collé plus souvent), sans courbe nouvelle.

**Attributs (ADR 0002) :** aucun nouveau : Marking (distance, existant), Strength (contact, `11c`), Aggression (fréquence d'engagement, existante). Côté attaquant, la protection du ballon reste au `04i`.

**Blocked by:** `07c`, `07d`, `11c` (livrés) ; `04i` (protection du ballon dos au défenseur, pour l'issue du contact).

**Bloque :** `10l` (sortir fort sur le receveur dos au jeu), `40`, `v2-collectif/22a`.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 50** |

Confiance : moyenne. Hypothèses : la condition s'ajoute à `reception.open_facing` ; le contact au contrôle réutilise le duel d'épaule. Temps machine, non compté : série de 50 matchs (environ 40 min), suite complète (environ 20 min).

## Tests

- **Scènes :** avant-centre avec un marqueur à 1 m dans son dos : reçu dos au jeu, temps avant de jouer vers l'avant plus long qu'avec un marqueur à 4 m ; Marking 99 contre 11 : plus de réceptions dos au jeu imposées par le 99, plus de retournements concédés par le 11.
- **Statistiques (50 matchs, avant / après) :** part des réceptions dos au jeu par poste (repère du `07c` : 0,4 % pour l'avant-centre), remises, pertes de l'avant-centre, buts (dans le bruit).

## Acceptance criteria

- [ ] Constantes produit (distance « au contact ») et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Réception empêchée de s'ouvrir tracée (marqueur, distance)
- [ ] Scènes ci-dessus ; part des réceptions dos au jeu de l'avant-centre en hausse
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Comments
