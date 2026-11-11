# 19e: Lecture de la chaîne d'un but et origine des buts

**Chantier :** `v2-realisme` (découpé du `19b` le 10/11/2026, recommandation de l'architecte validée par délégation du propriétaire). **Priorité :** P0 (avant 18a). **Catégorie :** mesure.

**What to build:** Outil `scripts/v2_chain.py` : remonter la chaîne d'un but ou d'une occasion dans `MatchTrace.events` (19b) et l'afficher. Classement de l'origine d'un but : en remontant depuis le but, premier événement qui donne le ballon à l'équipe qui marque : remise en jeu (coup de pied arrêté), perte sur contrôle raté ou touche trop longue (erreur), tacle, interception ou conduite perdue au contact (récupération), engagement (jeu placé). Statistiques sur 20 matchs : part des buts par origine. Lecture seule.

**Reprise de la réserve A1 de l'expert sur le 19b (10/11/2026), à faire en premier :** la faute avec avantage est écrite au moment où l'avantage se règle (`match._settle_advantage`), avec la minute de la faute : les minutes du journal ne sont pas toujours croissantes, et une faute réglée après un but a ce but pour cause. Correctif recommandé : écrire « faute (avantage) » dans `_foul` au moment où l'avantage est accordé, rien au règlement. Test : sur 20 matchs, minutes du journal croissantes et aucune faute causée par un but. (+ 15 min à l'estimation.)

**Constante à proposer avant le code :** ce qui compte comme coup de pied arrêté (touche ? coup franc indirect de hors-jeu, qui n'a pas d'événement de remise ?) et une éventuelle limite de temps (un but 3 minutes après une touche n'en est plus un).

**Attributs :** aucun

**Blocked by:** 19b.

**Bloque :** 18a.

**Status:** livré (11/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 10 min |
| Développement | 25 min |
| Tests unitaires et comportementaux | 15 min |
| Intégration et vérifications | 10 min |
| **Total (travail effectif)** | **1 h 00** |

Confiance : moyenne. Hypothèses : journal du 19b livré.
Temps machine, non compté : 20 matchs (environ 8 min en parallèle) ; suite complète (environ 25 min).

## Tests

- **Unitaires :** chaîne artificielle (corner → tête → but ; tacle → passe → but ; contrôle raté → tir → but) classée dans la bonne origine
- **Statistiques (séries de matchs) :** 20 matchs : part des buts par origine, comparée à l'ordre de grandeur réel (sourcé ou « non trouvé »)

## Acceptance criteria

- [x] Constante produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [x] `scripts/v2_chain.py` affiche la chaîne d'un but choisi
- [x] Origine classée pour chaque but de 20 matchs ; aucun but « inclassable » non expliqué
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes résultats sur deux exécutions
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Réalisation (11/11/2026)

- Estimation annoncée avant le code : 1 h 15 (1 h + 15 min pour la réserve A1), confiance moyenne.
- Constantes (recommandations retenues par délégation du propriétaire : « je valide automatiquement toutes les recommandations », 11/11/2026) : coup de pied arrêté = corner, coup franc (dont celui d'un hors-jeu), penalty ; touche comptée à part ; au-delà de `SET_PIECE_WINDOW_S` = 15 s entre la remise et le but, « jeu placé après <remise> » (le penalty n'a pas de limite). Repère réel : Opta Analyst, 23,5 % des buts de Premier League sur coup de pied arrêté hors penalties ; penalties, touches, récupérations, jeu placé : non trouvé.
- Critères chiffrés posés avant le code : minutes du journal croissantes et aucune faute causée par un but sur 20 matchs ; jeu identique (empreintes de 20 matchs avant et après) ; chaque but des 20 matchs classé, inclassables expliqués ; mêmes origines sur deux exécutions.
- Réserve A1 (19b) : `match._foul` écrit « faute (avantage) » à sa minute quand l'avantage est accordé ; `_settle_advantage` n'écrit plus rien ; si l'arbitre revient à la faute, `_whistle(after_advantage=True)` l'écrit à sa minute avec le détail « coup franc, après avantage » (ou « penalty, après avantage »). Aucun tirage ajouté ni déplacé.
- Code : `scripts/v2_chain.py` (`goal_origin`, `format_chain`, `origin_shares`, `play`, CLI). Lecture seule du journal.
- Tests : `tests/test_v2_chain.py`, 10 tests (corner, tacle, contrôle raté, touche trop longue, rebond et avantage qui ne rendent pas le ballon, hors-jeu, fenêtre de 15 s, inclassable expliqué, affichage, faute avec avantage écrite à l'octroi et au retour).
- Mesure (20 matchs, `docs/INDICATEURS_V2.md` section 24, `.scratch/v2-realisme/mesures/19e-avant.jsonl` et `19e-apres.jsonl`) : 108 buts, récupération 80,6 % (interception 52, conduite perdue 28, tacle 6, contre 1), erreur adverse 14,8 %, jeu placé 2,8 %, touche 0,9 %, coup de pied arrêté 0,9 % (1 corner), aucun inclassable ; délai médian 3,3 s. Écart majeur au réel (environ un quart des buts sur coup de pied arrêté) : à attribuer au 18a.
- Journal : minutes croissantes dans 20 matchs (11 sur 20 avant la correction), aucune faute causée par un but ; empreintes du jeu identiques 20 sur 20 ; origines identiques sur les deux exécutions. Exemple de chaîne : `19e-chaine-match7.txt` (sortie console Windows, accents en cp1252).
- Suite complète : 2 741 passés, 14 désélectionnés (2 731 + 10, `.scratch/v2-realisme/mesures/19e-suite.txt`, 28 min).
- Durée : estimée 75 min, réelle environ 85 min (analyse 20, développement 30, tests 20, intégration 15 ; estimée, non chronométrée), + 13 %. Temps machine hors total : 2 séries de 20 matchs (19 min chacune, contre 8 min estimées), suite complète (28 min).
- Points à vérifier : aucun à l'écran (journal et mesure).

## Comments

- 11/11/2026, passage 1 : expert APPROVED, QC VALIDÉ, clôture VALIDÉ. Améliorations facultatives de l'expert reportées au 19f (même famille d'outils de mesure) : A1 couper la remontée sur une perte ou un hors-jeu de l'équipe qui marque ; A3 test d'invariant du journal (minutes croissantes) sur un match court à graine fixée ; A4 erreur claire pour `--but` hors limites. A2 (perte sur ballon libre non écrite juste après une faute avec avantage) : à surveiller aux prochaines évolutions du journal.
