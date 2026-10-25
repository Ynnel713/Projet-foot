# 06: Volume de passes réaliste (fin du ping-pong)

**What to build:** constat du ticket 04 (25/10/2026) : ~4 100 passes par match pour les deux équipes, contre un ordre de grandeur réel de 900 à 1 000 (à sourcer avant le code). Les joueurs se repassent le ballon en ping-pong : le porteur décide dès la réception, puis toutes les 0,5 s, et une passe courte facile est presque toujours la meilleure option. Rendre le rythme réaliste : temps avant la première décision après un contrôle, conduite avant de passer, et ce que fait un vrai porteur (lever la tête, attendre un appel, fixer un adversaire). Chaque levier devra correspondre au rayon d'un attribut (voir `docs/CARTE_ATTRIBUTS_V2.md`), par exemple First Touch (contrôle orienté qui fait gagner du temps) ou Decisions.

**Blocked by:** None.

**Status:** ready-for-agent (constantes à proposer avant le code)

- [ ] Nombre de passes par match dans la fourchette réelle (chiffre à sourcer : Opta ou FBref)
- [ ] Durée moyenne de possession par joueur et nombre de touches avant de passer dans les ordres de grandeur réels (à sourcer)
- [ ] Les acquis du ticket 04 tiennent (passes réussies 70-90 %, passes perdues au plus 25 %)
- [ ] Constantes produit et critères chiffrés (données réelles sourcées, voir `docs/REVUE_ATTRIBUTS_V2.md`) validés par le propriétaire avant le code
- [ ] Suite V2 verte ; V1 inchangée
