# 10d2: Protection de l'axe : un milieu prend en charge l'adversaire qui décroche entre les lignes

**Chantier :** `v2-realisme` (suite du ticket `10d`, 19/11/2026). **Priorité :** P2, en attente d'une référence réelle (voir Condition de lancement). **Catégorie :** placement.

**Constat vérifié (ticket 10d, diagnostic de 20 matchs)** : les passes adverses reçues en zone 14 (29,5 par match, 2,84 % des passes reçues) arrivent à 89 % en défense placée, dans la poche entre le milieu et la dernière ligne : un écran placé 8 m devant la ligne n'était entre le receveur et son but que dans 20 % des cas, et l'a laissée inchangée (− 0,1 % sur 100 matchs appariés). Aucun rôle défensif ne vise l'adversaire qui décroche dans l'axe devant la ligne : le marquage suit des attaquants désignés, la couverture se place derrière le porteur.

**What to build:** En défense placée, un milieu axial (même désignation que l'essai du 10d : sentinelle, regista, récupérateur, puis le plus bas de la forme) prend en charge l'adversaire qui entre dans la poche axiale devant sa dernière ligne : il se place entre lui et son but, au contact ; sans adversaire dans la poche, il garde sa place devant la ligne, dans l'axe. Rôle défensif dans `v2engine/defense.py`, priorité à fixer face au presseur et au marquage. Base de départ possible : `.scratch/v2-realisme/mesures/10d-ecran-retire.patch` (désignation, tests de scène).

**Attributs :** à proposer (Positioning, Anticipation : lecture du décrochage ; règle anti double comptage de `docs/CARTE_ATTRIBUTS_V2.md`).

**Blocked by:** —

**Condition de lancement :** une référence réelle (passes reçues en zone 14 par match ou part des passes reçues) montrant que 29,5 par match est trop ; sinon le ticket reste en attente.

**Status:** à faire (en attente d'une référence réelle ; constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 30 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 40 min |
| Intégration et vérifications | 30 min |
| **Total (travail effectif)** | **2 h 30** |

Confiance : faible. Hypothèses : priorité face aux rôles existants à trancher, interaction avec la couverture du central (10b2) ; à examiner pour découpage avant le code (au-delà de 2 h).
Temps machine, non compté : suite complète (environ 15 min) ; 200 matchs appariés (environ 2 h 30) ; diagnostic de 20 matchs.

## Acceptance criteria

- [ ] Référence réelle de la zone 14 sourcée et constantes validées par le propriétaire avant le code
- [ ] Passes adverses reçues en zone 14 en baisse significative (IC à 95 %, 100 matchs appariés) ; buts, tirs, passes en profondeur réussies et hors-jeu rapportés
- [ ] Part des passes reçues en zone 14 où le milieu désigné est entre le receveur et son but : au-dessus des 20 % de l'essai du 10d
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 %
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
