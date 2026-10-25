# 04: Fonction de difficulté commune à toutes les actions

**What to build:** défaut T3 de la revue : passe, contrôle, tir et tacle ont une réussite qui ne dépend que de la note, jamais de la situation. Poser une fonction de difficulté partagée (distance, pression, vitesse du ballon, angle, couloir encombré) et une résolution commune « note contre difficulté » (courbe partagée `duel_probability`), que les tickets passe, contrôle, tir, duel consommeront ensuite. Ce ticket ne pose QUE le mécanisme et l'applique à un premier cas pilote (la passe), le reste suit dans l'étape « passe et contrôle ».

**Blocked by:** None (indépendant de 01 à 03 ; à faire avant l'étape « passe et contrôle »).

**Status:** livré (25/10/2026), validé QC — receveur visé, passes longues et calibration reportés au ticket 05 (décision du propriétaire)

- [ ] (REPORTÉ au ticket 05) Le receveur visé récupère le ballon dans au moins 50 % des passes
- [x] (repris du ticket 01) Au plus 25 % des passes finissent chez l'adversaire
- [x] Une passe facile (courte, sans pression) réussit à au moins 90 % à partir de 50 en Passing (voir « Écart assumé »)
- [ ] (REPORTÉ au ticket 05) Réussite des passes longues (plus de 32 m) proche du réel : environ 47 % (Opta)
- [x] Réussite globale des passes par équipe dans la fourchette réelle 70-90 %
- [x] Constantes produit et critères chiffrés (données réelles sourcées, voir `docs/REVUE_ATTRIBUTS_V2.md`) validés par le propriétaire avant le code
- [ ] (REPORTÉ au ticket 05) Recalibration unique de fin de socle (tirs par équipe 8-15, buts par match 2-3,5, passes perdues) avec `scripts/measure_v2_decisions.py`
- [x] Suite V2 verte ; V1 inchangée

**Constantes (validées 25/10/2026)** : difficulté de passe = 10 jusqu'à 10 m, +1,8 par mètre au-delà ; pression sur le passeur jusqu'à +15 (nulle à 5 m), réduite par Composure (99 -> moitié, 11 -> entière) ; +12 par adversaire à moins de 2 m de la trajectoire ; +10 si le receveur est marqué (adversaire à moins de 2 m). Réussite = Passing contre difficulté (courbe partagée : 50 % à égalité, ~97 % avec 40 points d'avance, bornes 5-98 %). Technique sort de la passe. Passe ratée : déviation de 10 à 25 % de sa longueur. Dosage : arrivée à ~6 m/s, passe à 30 m/s au plus, erreur de vitesse +/- 30 % (Passing 11) à +/- 5 % (99), passe dans la course 0 % (11) à 100 % (99). Contrôle : First Touch contre difficulté = 10 + 1 par m/s d'écart à 6 m/s + pression réduite par Composure.

**Écart assumé (décision du propriétaire, 25/10/2026)** : « passe facile à ~97 % pour tout le monde » ne vaut qu'à partir de 50 en Passing ; un 30 réussit ~56 % de ses passes faciles, un 11 ~50 %, conforme au guide (un 25 rate des ballons à 10 m). Concerne 11 joueurs de champ sur 407 en Ligue 1 sous 40, 43 sous 50 (médiane 60).

**Mesures (25/10/2026, 2 matchs pour le diagnostic de passes, 6 pour la calibration)** : passes réussies 79,7 % (réel 70-90 %, ~80 %) ; chez l'adversaire 20,3 % (critère 25 %) ; receveur visé 36,1 % (cible 50 %) ; passes de plus de 32 m : 71 % réussies (réel ~47 %) mais 0,8 % des passes (réel 10-19 %) ; tirs 27,8 par équipe, 6,8 buts par match. **Nouveau constat** : ~4 100 passes par match (réel de l'ordre de 900-1 000, à sourcer) -> ticket 06.
