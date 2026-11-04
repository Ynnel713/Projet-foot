# 01: Buts et lecteur

**What to build:** Premier mode de visionnage V2 et le lecteur qui rend possibles tous les suivants.

1. **Trace enrichie** : le but reçoit son buteur et son passeur (`GoalEvent` n'a aujourd'hui que minute et équipe, `v2engine/trace.py`).
2. **Moments calculés par le serveur** : la réponse de `POST /api/v2/matches` contient, en plus de la trace, une liste de moments (début, fin, type, score d'intérêt, issue). Dans ce ticket, un moment est un but, de quelques secondes avant à quelques secondes après (durées proposées).
3. **Mode Buts** : le lecteur ne montre que les buts, dans l'ordre.
4. **Lecteur** : le mode (Match complet, Buts ; Résumé et Moments clés s'ajoutent plus tard) se choisit avant le lancement et change en cours de lecture. Barre de progression avec repères qui n'apparaissent qu'à mesure que les moments sont joués, boutons précédent et suivant, vitesse actuelle conservée.
5. **Sans spoiler** : aucun score ni repère futur visible avant le moment (comme le score révélé au but aujourd'hui).

**Attributs :** aucun.

**Blocked by:** —

**Status:** à faire (constantes à proposer avant le code)

**Constantes à proposer :** durée avant et après un but ; transition entre deux moments (coupure franche ou fondu).

## Acceptance criteria

- [ ] Constantes validées par le propriétaire avant le code
- [ ] Le but porte son buteur et son passeur dans la trace et la réponse API (test API)
- [ ] La liste de moments est calculée côté serveur, déterministe pour une graine, testée sur des scènes fixes (aucun but : liste vide ; deux buts proches : deux moments distincts ou fusionnés selon la règle écrite)
- [ ] Le mode Buts ne montre que les buts, dans l'ordre, sans score ni repère futur avant chaque but
- [ ] Le changement de mode en cours de lecture reprend à la bonne minute ; précédent et suivant sautent d'un moment à l'autre
- [ ] `npm run build` OK, `npm run lint` sans erreur nouvelle ; suite V2 verte ; V1 inchangée
