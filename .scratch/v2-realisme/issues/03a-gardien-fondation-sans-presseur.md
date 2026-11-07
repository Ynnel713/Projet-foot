# 03a: Gardien : sous-système propre, fin du presseur générique

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (le gardien fausse aujourd'hui tous les tirs). **Catégorie :** placement.

**Constat vérifié :** le gardien est exclu des rôles défensifs, mais `cerveau.interpret` lui applique la règle générale : à moins de 15 m d'un porteur adverse il prend `PRESSEUR` (`cerveau.py:123-128`) et court au ballon ; à moins de 15 m de son propre porteur il prend `SOUTIEN`. Sinon il garde sa place de coup d'envoi (`bloc.py:184`, `bloc.py:224`).

**What to build:** Créer un module `v2engine/gardien.py` et un rôle `GARDIEN` : le gardien ne passe plus par la règle générale (ni presseur, ni soutien, ni indiscipline), seulement par son module, avec des états tracés (placement, sortie, intervention, relance). Dans ce ticket, l'état « placement » garde la place actuelle : seul le comportement de presseur disparaît.

**Hors de ce ticket :** placement sur l'angle (03b) et sorties (03d, 03e). le ticket `v2-attributs-restants/03b` ajoutera les tendances et notes du gardien (Rushing Out, Eccentricity, One on Ones…) sur ces mécanismes neutres ; aucun attribut de gardien ici.

**Attributs :** aucun

**Blocked by:** 01f (Fabrique de scènes de test partagée).

**Bloque :** 03b.

**Status:** livré (07/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 50** |

Confiance : élevée. Hypothèses : les remises en jeu (`restart.py`) gardent leur logique propre du gardien.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 20 matchs.

## Tests

- **Unitaires (scène contrôlée) :** porteur adverse à 10 m du gardien : le gardien ne court plus vers lui ; porteur de son équipe à 10 m : idem
- **Statistiques (séries de matchs) :** 20 matchs : distance maximale du gardien à son but rapportée avant / après

## Acceptance criteria

- [x] Rôle `GARDIEN` et états tracés (`v2engine/gardien.py`, `cerveau._keeper` ; l'état est la première partie de la raison de l'intention)
- [x] Plus aucune intention « presser » ou « aller au ballon » du gardien hors ballon libre à sa portée (tests de scène et trace d'un match de 4 minutes ; « à sa portée » : ballon libre à moins de 15 m ou gardien le plus proche de son équipe, règle déjà en place pour tout joueur)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions (`3537d7b499db9678`, 15 minutes, graine 20260923)
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md` : 2 478 passés, 14 désélectionnés (07/11/2026, 16 min 45 s, état final) ; attendu 2 473 + 5 nouveaux

## Comments

- 07/11/2026 : **Critères chiffrés posés avant le code** : (1) le gardien n'a plus jamais le rôle presseur, soutien ni ballon libre (rôle `GARDIEN` seul, hors remises en jeu, ticket 29) ; (2) quatre états tracés dans la raison de l'intention : placement, sortie, intervention, relance ; (3) placement = la place actuelle (`home_target`), sans nouvelle constante ; (4) 20 matchs à la graine d'audit, distance maximale et moyenne du gardien à son but rapportées avant et après ; (5) deux exécutions, même empreinte. Aucune constante produit ajoutée.
- 07/11/2026 : **Réalisé** (`v2engine/gardien.py` nouveau, `v2engine/cerveau.py`, `scripts/v2_indicators.py`, `GLOSSARY.md`, tests). `interpret` renvoie `GARDIEN` pour tout poste `GK` avant les règles générales ; `decide` appelle `_keeper`, qui choisit l'état (`gardien.state`) et réutilise le geste de la règle générale seulement pour la relance (porteur), l'intervention (receveur visé ou passe lue) et la sortie (ballon libre). Le placement vise sa place de départ. Indicateur du banc ajouté : distance du gardien à son but (maximale et moyenne, par gardien et par match).
- 07/11/2026 : **Mesure (20 matchs, graine d'audit, avant `490ae3d` + banc → après)** : distance maximale du gardien à son but, en moyenne par match, **99,3 → 47,9 m** (avant, le gardien pouvait presser un porteur à l'autre bout du terrain) ; distance moyenne **11,8 → 5,8 m**. Diagnostic de 2 matchs complets : 103 ticks sur environ 24 000 à plus de 25 m (sortie sur ballon libre 40, placement de retour 44, relance 12, intervention 4, replacement 3). Reste de 48 m : le gardien le plus proche de son équipe sur un ballon libre y va, pour que quelqu'un le joue (règle générale conservée, signalée à l'expert). Effets sur le jeu, à graine égale, bruit à lire (écart-type d'un match 2,1 buts, soit 0,47 sur 20 matchs) : buts 3,95 → 4,45 par match, tirs par équipe 26,4 → 24,2, arrêts 17,9 → 14,9 par match, conversion des tirs 6,0 → 7,4 %, corners 12,3 → 14,0, tacles 34,8 → 31,6, passes 1 046 → 1 025, solutions de passe ouvertes 2,12 → 2,16, hors-jeu 1,05 → 1,05. Le gardien ne presse plus : moins de tirs, moins d'arrêts, davantage de buts par tir.
- Tests : 5 nouveaux ou réécrits (gardien près de son porteur : il tient sa place ; près d'un porteur adverse : il ne presse pas ; états relance, intervention, sortie ; sortie seulement à sa portée ; trace d'un match de 4 minutes ; distance du gardien dans le banc), 2 tests existants adaptés parce que leur comportement est l'objet du ticket (`test_keeper_near_his_own_holder_...` ex-soutien, `test_goalkeeper_near_an_opposing_holder_...` ex-« presse le porteur adverse »), 1 test dépendant de la graine : graine de `test_half_time_resets_everyone_and_the_other_team_kicks_off` passée de 20260927 (prolongation d'une minute) à 20260928, logique inchangée, comme aux tickets 01a et 02a. Une retouche à la marge : « play the whistle » (hors-jeu) change encore la raison du gardien comme celle de tous.
- Durée : estimée 1 h 50 (110 min ; 20/40/30/20), réelle environ 1 h 55 (115 min ; 20/25/30/40, non chronométrée), écart environ + 5 % : développement plus court (la règle réutilise les branches existantes), intégration plus longue (mesure avant, deux échecs de suite à corriger, diagnostic des 48 m). Temps machine, hors total : mesures de 20 matchs environ 10 min chacune, suites complètes environ 28 min (parallèle) puis 22 min.
- 07/11/2026 : **Clôture.** Expert `APPROVED_WITH_RESERVATIONS` (empreinte `758da6aa`), QC `VALIDÉ` (un seul passage), clôture `VALIDÉ` (journal). Réserves acceptées d'office par le propriétaire (consigne du 06/11/2026 : « Je valide par défaut toutes tes recommandations ainsi que celles des experts »). **A1** : la sortie du gardien reprend la règle générale du ballon libre (le plus proche de son équipe, même au-delà de 15 m, et passes de son équipe en vol) : pointes de 48 m en moyenne par match ; à borner aux tickets 03d et 03e (rayon propre, passes de son équipe exclues). **A2** : les effets de jeu mesurés (tirs, arrêts, conversion, buts 3,95 → 4,45) ne sont pas des gains validés (n = 20, dans le bruit, causalité non isolée) ; ne pas les prendre pour référence au 03b, mesure de 50 à 100 matchs avant tout calage. Facultatifs : A3 (l'étiquette « relance » couvre encore la conduite vers le but d'avant, à traiter avec la relance du gardien), A4 (borne de distance dans le test de trace dès que 03b fixe le placement). Remarque de l'expert et du QC retenue : le gardien porteur ne bénéficie plus du délai de réaction à la perte (rôle `GARDIEN` hors des rôles offensifs), effet négligeable non traité.
