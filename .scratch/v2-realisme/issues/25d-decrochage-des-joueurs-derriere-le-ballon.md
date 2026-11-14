# 25d: Décrochage : les joueurs derrière ou à hauteur du ballon se proposent aussi

**Chantier :** `v2-realisme` (demande du propriétaire du 14/11/2026 : jeu sans ballon et placement dynamique comme cœur du jeu ; audit de la roadmap du même jour). **Priorité :** P1. **Catégorie :** décision.

**Constat vérifié (14/11/2026) :** `cerveau._call_rank` exclut tout joueur qui n'est pas devant le ballon, et les rôles défensifs (défenseur central, sentinelle, récupérateur, regista) ne sont dans aucune liste d'appelants. Un milieu défensif ne décroche donc jamais pour aider un porteur en difficulté ; le seul décrochage possible est le tiers arrière de la grille d'Off the Ball, pour des joueurs déjà devant le ballon.

**What to build:** un décrochage, qui étend la sélection « vers le porteur » du 25c (même mécanisme, pas un second rôle concurrent) : ouvert aux milieux (tous rôles) et aux attaquants pivots, et aux défenseurs en phase de construction (25b), quand le porteur a moins de solutions que le seuil validé ou qu'il est pressé. Plafond séparé de celui des appels vers l'avant (un ou deux décrochages à la fois, valeur validée), pour ne pas vider la profondeur. Le joueur qui décroche entraîne ou non son marqueur : c'est le marqueur (`defense.py`) qui décide, rien n'est scripté.

**Attributs :** Off the Ball (moment, rayon existant), Teamwork (accepter de quitter sa place ; rayon existant de tolérance). Pas de nouvel effet attendu.

**Blocked by:** 25a, 25b, 25c.

**Bloque :** 25f, 25h.

**Ticket 24 en cours :** toute courbe d'attribut de ce ticket passe par `success_probability` / `duel_probability`, dont la forme change au 24 ; les constantes de niveau sont proposées après la livraison du 24.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 45** |

Confiance : moyenne. Hypothèses : extension de la sélection du 25c dans `_runs_or_holds` ; pas de changement du 02g pour les appels vers l'avant.
Temps machine, non compté : suite complète ; mesure 50 matchs.

## Tests

- **Comportementaux :** central porteur pressé sans solution : la sentinelle décroche ; Off the Ball 99 contre 11 : délai et part de décrochages utiles (passe reçue).
- **Statistiques (50 matchs) :** décrochages par match et par poste, passes reçues après décrochage, appels vers l'avant (pas de baisse au-delà de la marge validée).

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Décrochage déclenché seulement quand le porteur manque de solutions ou est pressé (test)
- [ ] Appels vers l'avant par match dans la marge validée par rapport à avant
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
