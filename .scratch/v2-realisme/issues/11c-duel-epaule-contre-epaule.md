# 11c: Duel épaule contre épaule à la course

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (deux joueurs qui courent vers le même ballon se disputent la position). **Catégorie :** exécution.

**Constat vérifié :** deux joueurs qui courent côte à côte ne font que se repousser géométriquement ; le premier arrivé au ballon le joue.

**What to build:** Deux joueurs au contact, de côté, courant vers le même point : un duel d'épaule (Strength, et Balance pour rester sur sa course, à répartir sans double comptage avec 12c) décale le perdant de sa trajectoire et lui fait perdre de la vitesse ; faute possible (Aggression, déjà branchée).

**Attributs :** Strength (gagner le contact) ; Balance seulement via 12c

**Blocked by:** 11b (Collision asymétrique : Strength).

**Bloque :** 11e, 21c (ajouté le 10/11/2026, audit de la roadmap).

**Status:** implémenté (15/11/2026) — en attente de /valider-ticket-simulafoot

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h** (réestimé à 2 h 15 le 15/11/2026, avant le code : faute de charge et compteurs du banc) |

Confiance : moyenne. Hypothèses : déclencheur : contact latéral et cible commune.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** deux joueurs côte à côte vers un ballon libre : duel tracé
- **Comportementaux (profils comparés) :** Strength 90 contre 40 : le plus fort atteint le ballon plus souvent

## Acceptance criteria

- [x] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code (« Je suis ok », 15/11/2026 ; fréquence réelle des duels d'épaule : non trouvée)
- [x] Duel tracé et affiché : événement `duel d'épaule` du journal (gagnant, perdant, issue « plus fort / plus faible / égalité », « , faute ») ; affiché dans le rapport du banc (`measure_v2` : duels par match, part gagnée par le plus fort, fautes de charge), l'écran étant laissé au chantier `v2-mise-en-scene` (décision du propriétaire du 15/11/2026)
- [x] Effet de Strength mesuré : scène 90 contre 40, le plus fort atteint le ballon 54 fois sur 60 (27 sur 60 à force égale) ; en match, 69 % des duels gagnés par le plus fort quand les notes diffèrent ; 50 matchs appariés (décalage lissé) : fautes + 1,24, buts, tirs et passes sans écart significatif (`docs/INDICATEURS_V2.md` section 42)
- [x] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour (Strength lue seulement dans `duel.py` ; Balance seulement via le contact perdu du 12c ; Aggression dans `duel.py`, déjà autorisée ; carte mise à jour)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`) : environ 2 h 10 pour 2 h 15 réestimées (− 4 %), corrections des réserves A1 et A2 comprises
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions (courses de la scène rejouées à l'identique dans le test ; fichier exécuté deux fois, 15 passés)
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md` : 3 088 passés, 0 ignoré, 14 désélectionnés (3 073 + 15 tests ajoutés), 11 min 28 ; aucun fichier V1 ni protégé touché

## Comments

**14/11/2026, pistes retenues par le propriétaire pendant le 11b** (recommandation suivie, à chiffrer et à faire valider comme constantes avant le code ; elles élargissent le périmètre : réestimer au démarrage) :
- **Stabilité sur appuis** : un joueur arrêté et campé résiste mieux qu'un joueur pris en déséquilibre ou en course latérale ; au 11b, sa « masse » de contact ne dépend que de Strength (`duel.contact_share`). Bonus de stabilité selon la vitesse et l'orientation au contact, à répartir avec Balance (12c) sans double comptage.
- **Taille comme facteur de masse au sol** (« Taille FM (cm) », 152 à 203 cm dans la base) : un 190 cm pèse ~85 kg, un 170 cm ~68 kg (rapport ~1,25), mais Strength contient déjà en partie le gabarit. Petit facteur seulement, plafonné à environ ± 10 % de la part du contact ; étendre d'abord le rayon de Taille dans `docs/CARTE_ATTRIBUTS_V2.md` (aujourd'hui : jeu aérien seul, 15b et 03a), puis le test de rayon.

## Comments

**15/11/2026, constantes validées par le propriétaire** (« Je suis ok ») : déclencheur (contact à la somme des rayons + 0,3 m, deux joueurs à 3 m/s ou plus, courses à 45° au plus, contact par le côté à 60° au moins, même ballon libre à moins de 20 m et 30° devant), un duel par paire toutes les 1,0 s, gagnant sur la courbe de duel partagée (Strength seule), perdant décalé de 0,5 m puis contact perdu du 12c, faute de charge à 0,15 fois la faute du tacle (Aggression), sifflée tout de suite ; duel affiché dans le banc, l'écran étant laissé au chantier `v2-mise-en-scene`.

**15/11/2026, implémentation.** `duel.py` : `shoulder_contact`, `shoulder_win_probability`, `shoulder_foul_probability`, `resolve_shoulder_duel` (flux DUEL) ; `match._shoulder_duels` après la résolution des collisions, ballon libre en jeu seulement (ni porteur, ni remise, ni tir en vol) ; événement `duel d'épaule` du journal ; fabrique de scènes alignée (`tests/scenes.py`) ; compteurs du banc (`v2_indicators.on_events`, `measure_v2.report`). Mesure (`docs/INDICATEURS_V2.md` section 42) : 35,6 duels par match, 68 % gagnés par le plus fort, 1,76 faute de charge par match ; fautes + 1,72, buts, tirs, passes et tacles sans écart significatif. Première suite complète : 2 échecs (part « gagnés par le plus fort » à NaN sans duel entre notes différentes, NaN ≠ NaN dans deux tests d'égalité du banc), corrigés par la convention du banc (division par `max(1, …)`).

**15/11/2026, passage 1 de l'expert : APPROVED_WITH_RESERVATIONS.** A1 [réserve] : une charge fautive sifflée pendant un avantage effaçait la première faute de `trace.fouls`. A2 [réserve] : décalage de 0,5 m appliqué en un seul pas. A3 [facultatif] : deux pertes de contact possibles dans le même pas (non traité). **Décisions du propriétaire** : A1 « Corriger maintenant », A2 « Lisser maintenant ». **Corrections** : `_settle_advantage` avant le sifflet de la charge (test : les deux fautes tracées) ; décalage réparti sur `SHOULDER_PUSH_STEPS` = 3 pas (0,3 s), au plus 0,17 m par pas (test). Nouvelle série de 50 matchs (décalage lissé) : 36,4 duels par match, 69 % au plus fort, 1,42 faute de charge ; fautes + 1,24, buts, tirs, passes sans écart significatif.
