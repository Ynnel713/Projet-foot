# 18j: Portée du défenseur qui lit la passe

**Chantier :** `v2-realisme`. **Catégorie :** défense, exécution.

**Origine :** réserve A3 de l'expert sur le ticket 18i (12/11/2026), acceptée par le propriétaire (« ok A1 A2 A3, crée le 18j »). Depuis le 18i, le receveur visé d'une passe touche le ballon à 1,0 m (`match.RECEIVER_REACH_M`, jambe tendue) ; tout autre joueur à 0,41 m (`match.CONTROL_RADIUS_M`), y compris le défenseur qui a lu la passe (`anticipation.pass_readers`, `ball.readers`) et court la couper. Sur 50 matchs après le 18i : passes chez l'adversaire 11,6 % (repère 15 à 20 %). Le défenseur qui anticipe se jette lui aussi sur le ballon.

**What to build :** Donner une portée propre au seul défenseur qui a lu la passe, entre 0,41 m et 1,0 m, éventuellement après un délai de réaction comme le contre d'un tir (`shooting.BLOCK_REACTION_S`). Un défenseur qui n'a pas lu la passe garde 0,41 m. Remesurer la table de coupe du 18g et l'indicateur de calibration de la passe, puisque la coupe change en jeu.

**Hors de ce ticket :** défenseurs sans rôle qui traitent une passe adverse en vol comme un ballon libre (`cerveau.interpret`, `BALLON_LIBRE`) ; presseur qui vise le point de rencontre du receveur ; calibration finale des passes (`v2-collectif/22a`).

**Attributs :** Anticipation (déjà : qui lit la passe), aucun rôle nouveau (règle anti double comptage de `docs/CARTE_ATTRIBUTS_V2.md`).

**Blocked by :** 18i.

**Bloque :** `v2-collectif/22a`.

**Status :** à faire (constantes à proposer avant le code : portée du lecteur, délai éventuel)

## Estimation

| Poste | Durée |
|---|---|
| Analyse | 30 min |
| Développement | 30 min |
| Tests | 30 min |
| Intégration et vérifications (table du 18g remesurée) | 45 min |
| **Total (travail effectif)** | **2 h 15** |

Confiance : moyenne (mécanisme local, comme le 18i ; la remesure de la table peut demander un tour de plus). Hypothèses : `_ball_contacts` du 18i étendu aux lecteurs ; diagnostic du 18i réutilisable (`.scratch/v2-realisme/mesures/18i-diag-script.py`). Temps machine, hors total : séries de 50 matchs (environ 25 min chacune), suite complète (8 min).

## Acceptance criteria

- [ ] Portée du lecteur (et délai éventuel) proposée avec chiffres réels sourcés ou « non trouvé », validée par le propriétaire avant le code
- [ ] Scène : un lecteur à 0,8 m de la trajectoire touche le ballon, un non-lecteur à 0,8 m ne le touche pas ; le receveur garde 1,0 m
- [ ] Passes chez l'adversaire et réussie par longueur mesurées avant/après sur 50 matchs, comparées au repère (15 à 20 %) et au réel (89,4 / 87,1 / 51,7 %)
- [ ] Table de coupe du 18g remesurée ; indicateur de calibration de la passe sous 5 points par tranche d'au moins 100 passes
- [ ] Suite complète comparée à l'attendu de `CLAUDE.md`

## Comments
