# 06: Volume de passes réaliste (fin du ping-pong)

**What to build:** constat du ticket 04 (25/10/2026) : ~4 100 passes par match pour les deux équipes, contre un ordre de grandeur réel de 900 à 1 000 (à sourcer avant le code). Les joueurs se repassent le ballon en ping-pong : le porteur décide dès la réception, puis toutes les 0,5 s, et une passe courte facile est presque toujours la meilleure option. Rendre le rythme réaliste : temps avant la première décision après un contrôle, conduite avant de passer, et ce que fait un vrai porteur (lever la tête, attendre un appel, fixer un adversaire). Chaque levier devra correspondre au rayon d'un attribut (voir `docs/CARTE_ATTRIBUTS_V2.md`), par exemple First Touch (contrôle orienté qui fait gagner du temps) ou Decisions.

**Blocked by:** None.

**Status:** fait (25/10/2026), en attente de commit

- [x] Nombre de passes par match dans la fourchette réelle (chiffre à sourcer : Opta ou FBref)
- [x] Durée moyenne de possession par joueur et nombre de touches avant de passer dans les ordres de grandeur réels (à sourcer)
- [x] Les acquis du ticket 04 tiennent (passes réussies 70-90 %, passes perdues au plus 25 %)
- [x] Constantes produit et critères chiffrés (données réelles sourcées, voir `docs/REVUE_ATTRIBUTS_V2.md`) validés par le propriétaire avant le code
- [x] Suite V2 verte ; V1 inchangée

## Réalisé (25/10/2026)

Décisions du propriétaire (25/10/2026), données réelles :
- Passes : 15 à 17 par minute de jeu effectif (Opta : 849 à 941 par match pour 55 à 58 min de ballon en jeu).
- Temps par possession de joueur : 2 à 3 s (réel 2,49 s, gardien 4,61 s, arXiv 2308.05460). Possession d'équipe : 11 à 16 s (réel 13,7 s). Passes par possession : 3 à 5 (CIES, Opta).
- Tacles : 30 à 40 tentés par match (Premier League ~33, premierleague.com).

Leviers :
1. Temps de réception avant la première décision (`possession.reception_delay_s`), selon First Touch : 99 → 1,7 s, 55 → 2,3 s, 11 → 2,9 s (fourchette validée 1,7-2,5 s pour 55, calée sur 20 matchs). La pression le réduit jusqu'à moitié au contact. Le gardien ne joue jamais avant 3,5 s sans pression.
2. Cause principale du ping-pong : le tacle était tiré à chaque tick (~5 700 tentatives par match). Il devient un taux par seconde de contact : 0,03/s pour un joueur moyen, écart Aggression conservé.
3. Pendant sa réception, le porteur avance à 40 % de sa vitesse max (réel ~2,9 m/s, Ligue 1, UCLan). Sans ce réglage, les tirs doublaient (24 par équipe, 8 buts).

Mesures sur 20 matchs (graines 20260923+i) : 15,1 passes/min ; 2,03 s par joueur ; possession d'équipe 14,7 s, 3,70 passes ; 11,8 tirs par équipe ; 3,45 buts par match ; 36,9 tacles ; passes réussies 75,8 %, chez l'adversaire 24,2 %. Avant : 45 passes/min, 0,28 s, 2,5 s, 1,87 passe.

Les valeurs sont proches des bords des fourchettes (passes/min, temps par joueur, buts) : à surveiller au ticket 05 (calibration de fin de socle).
