# 10l: Marqueur au contact du receveur dos au but : coller, gêner le retournement ou passer devant

**Chantier :** `v2-realisme` (audit duels, protection de balle, jeu dos au but, 26/11/2026). **Priorité :** P1 (sans marqueur collé, le jeu dos au but n'existe presque pas). **Catégorie :** décision.

**Constat vérifié (26/11/2026) :** le 07c mesure 0,4 % de réceptions dos au jeu pour l'avant-centre et l'explique ainsi : « le dos au jeu réel de l'avant-centre vient surtout d'un marqueur collé dans son dos qui l'empêche de se tourner, mécanisme absent ici » (renvoyé aux 04i et 08c, qui ne le couvrent pas : le 04i est côté porteur, le 08c porte sur le scan). Le marquage (`defense.py`, `v2-collectif/07`) règle une distance au marqué, pas un choix entre le coller dans le dos, passer devant pour intercepter ou rester à distance pour l'empêcher de se tourner. Le 10d2 place un milieu dans la poche axiale, sans ce choix.

**What to build:** quand une passe part vers l'attaquant qu'il marque, le défenseur choisit entre trois conduites :
1. **coller dans son dos** : au contact à l'arrivée du ballon, ce qui force une réception dos au jeu et ouvre la protection (04i) ;
2. **passer devant** : tenter l'interception (anticipation existante, `v2-cerveau-joueurs/04`) ; s'il arrive en retard, il est éliminé par le retournement (04o) ;
3. **rester à distance**, entre l'attaquant et son but, pour le contenir sans risquer d'être éliminé.
Le choix dépend de ce qu'il perçoit (08b) : distance et vitesse de la passe, zone (plus près de son but, plus prudent), couverture derrière lui. Rien n'est scripté.

**Attributs :** Marking (coller à son homme, rayon existant), Anticipation (passer devant, rayon existant), Aggression (engager tôt et fort : la carte lui donne déjà « le bas laisse l'adversaire se retourner »), Decisions (choisir, contexte « choix défensif » du `v2-attributs-contextes/04a`). Aucun effet nouveau ; poids et cumul à vérifier dans `docs/CARTE_ATTRIBUTS_V2.md` (ADR 0002, R1).

**Constantes à proposer avant le code :** distance de contact visée, bornes de la décision (distance de passe, zone), poids des trois conduites. Chiffre réel : part des réceptions d'avant-centre dos au jeu, à sourcer, sinon « non trouvé ».

**Blocked by:** 07c, 08b, `v2-attributs-contextes/04a` (livrés).

**Bloque :** 04o (retournement au contact), 04q (validation).

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 25 min |
| **Total (travail effectif)** | **2 h 05** |

Confiance : moyenne (légèrement au-dessus de 2 h : découpage examiné, non retenu, les trois conduites partagent une seule décision). Hypothèses : le choix s'insère dans le marquage existant (`defense.py`) sans nouveau rôle ; l'interception reste celle du `v2-cerveau-joueurs/04`.
Temps machine, non compté : suite complète ; série appariée de 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** passe courte et lente vers un avant-centre marqué, couverture en place : le défenseur colle ; même passe, sans couverture près de son but : il reste à distance plus souvent ; passe lente et marqueur à Anticipation haute : il passe devant plus souvent.
- **Comportementaux (profils comparés) :** Marking 90 contre 40 : contact à l'arrivée du ballon plus fréquent.

## Acceptance criteria

- [ ] Constantes et chiffre réel (sourcé ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Les trois conduites existent, sont tracées et apparaissent toutes sur 50 matchs ; aucune ne dépasse la part validée
- [ ] Part des réceptions dos au jeu de l'avant-centre : nettement au-dessus de 0,4 %, dans la fourchette validée
- [ ] Interceptions et passes réussies vers les attaquants rapportées (50 matchs appariés), sans régression non expliquée
- [ ] Tenue de la ligne (réserve A2 de l'expert, 26/11/2026) : un central qui colle un attaquant qui décroche ne laisse pas de trou gratuit ; indicateurs du 10j (écart entre centraux) et passes en profondeur réussies dans l'espace laissé, sur 50 matchs appariés, sans régression non expliquée ; lien avec 10b, 10b2, 10c, 10c2
- [ ] Rayon des attributs conforme à la carte, sans double comptage ; test de rayon à jour
- [ ] Déterminisme à graine fixée ; durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 %
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
