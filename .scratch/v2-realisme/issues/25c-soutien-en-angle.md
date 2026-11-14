# 25c: Soutien en angle : offrir une ligne de passe, pas courir au ballon

**Chantier :** `v2-realisme` (demande du propriétaire du 14/11/2026 : jeu sans ballon et placement dynamique comme cœur du jeu ; audit de la roadmap du même jour). **Priorité :** P1. **Catégorie :** décision.

**Constat vérifié (14/11/2026, corrigé après la revue de l'expert) :** en match, aucun coéquipier ne vient offrir une solution courte au porteur. Le rôle `SOUTIEN` (`cerveau.interpret`, dernière ligne ; `decide`, « aller au ballon ») est inatteignable depuis 02f et 02g : `think` appelle `interpret` avec `runs_enabled` vrai (`match.py` fournit toujours le dictionnaire `runs`), et tout coéquipier du porteur reçoit alors `APPEL` ou `TENIR` (`_runs_or_holds`). La branche `SOUTIEN` ne sert plus qu'aux tests unitaires sans `runs`. Un porteur pressé n'a donc que les appelants (devant le ballon, vers un espace autour de leur place) et les joueurs qui tiennent leur place.

**What to build:** une sélection « vers le porteur » dans `_runs_or_holds`, à côté de la sélection des appelants du 02g : quand le porteur est pressé (presseur à moins de `PRESSED_M`) ou a moins de solutions que le seuil validé, au plus un coéquipier (plafond validé, séparé de `CALLER_CAP`) prend le rôle de soutien. Il est choisi parmi les plus proches non appelants, et vise un point à distance de passe courte (bornes validées) sur une ligne ouverte (candidats du 25a), de préférence en diagonale pour former un triangle avec un autre coéquipier proche. Si la ligne se ferme, il se décale (nouvelle recherche, délai d'Off the Ball). Ce mécanisme de sélection est le seul « vers le porteur » : le décrochage du 25d l'étend, il n'en crée pas un second (sinon deux rôles concurrents convergent sur le porteur et recréent le regroupement). La branche `SOUTIEN` morte est réutilisée pour ce rôle ou retirée, avec les tests unitaires qui en dépendent adaptés.

**Attributs :** Off the Ball (rayon existant : justesse et délai), Decisions (bon moment pour se proposer, cumul justifié selon la règle R2 révisée ou rien si le rayon est déjà pris : à trancher avec la carte).

**Blocked by:** 25a.

**Bloque :** 25d, 25h.

**Ticket 24 en cours :** toute courbe d'attribut de ce ticket passe par `success_probability` / `duel_probability`, dont la forme change au 24 ; les constantes de niveau sont proposées après la livraison du 24.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 35 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **2 h** |

Confiance : faible. Hypothèses : sélection ajoutée dans `_runs_or_holds` sans toucher au classement des appelants du 02g ; un soutien à la fois ; triangle jugé sur trois joueurs, pas plus ; tests unitaires de la branche `SOUTIEN` à adapter.
Temps machine, non compté : suite complète ; mesure 50 matchs.

## Tests

- **Scènes :** presseur entre le soutien et le porteur : le soutien se décale hors de l'ombre ; porteur libre : le soutien ne colle pas (distance minimale validée).
- **Statistiques (50 matchs) :** triangles par possession, pertes sous pression, passes courtes réussies sous pression.

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Porteur pressé : solution courte ouverte plus souvent qu'avant (même graine)
- [ ] En match (dictionnaire `runs` fourni), un coéquipier prend le rôle de soutien quand le porteur est pressé (test)
- [ ] Le soutien n'entre pas dans le rayon de regroupement du porteur hors duel ; jamais plus de soutiens que le plafond validé
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
