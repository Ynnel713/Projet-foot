# 04: Fonction de difficulté commune à toutes les actions

**What to build:** défaut T3 de la revue : passe, contrôle, tir et tacle ont une réussite qui ne dépend que de la note, jamais de la situation. Poser une fonction de difficulté partagée (distance, pression, vitesse du ballon, angle, couloir encombré) et une résolution commune « note contre difficulté » (courbe partagée `duel_probability`), que les tickets passe, contrôle, tir, duel consommeront ensuite. Ce ticket ne pose QUE le mécanisme et l'applique à un premier cas pilote (la passe), le reste suit dans l'étape « passe et contrôle ».

**Blocked by:** None (indépendant de 01 à 03 ; à faire avant l'étape « passe et contrôle »).

**Status:** ready-for-agent (constantes à proposer avant le code)

- [ ] (repris du ticket 01) Le receveur visé récupère le ballon dans au moins 50 % des passes
- [ ] (repris du ticket 01) Au plus 25 % des passes finissent chez l'adversaire
- [ ] Une passe facile (courte, sans pression) réussit à au moins 90 % quelle que soit la note
- [ ] Réussite des passes longues (plus de 32 m) proche du réel : environ 47 % (Opta)
- [ ] Réussite globale des passes par équipe dans la fourchette réelle 70-90 %
- [ ] Constantes produit et critères chiffrés (données réelles sourcées, voir `docs/REVUE_ATTRIBUTS_V2.md`) validés par le propriétaire avant le code
- [ ] Recalibration UNIQUE de fin de socle (tickets 01 à 04) (tirs par équipe 8-15, buts par match 2-3,5, passes perdues) avec `scripts/measure_v2_decisions.py`
- [ ] Suite V2 verte ; V1 inchangée
