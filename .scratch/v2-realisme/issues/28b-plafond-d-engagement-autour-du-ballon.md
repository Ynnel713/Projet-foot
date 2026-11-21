# 28b: Plafond d'engagement autour du ballon

**Chantier :** `v2-realisme` (audit de réalisme du propriétaire du 21/11/2026, point « effet grappe »). **Priorité :** P1. **Catégorie :** décision.

**Constat vérifié :** voir `28a` (4,6 joueurs de champ à moins de 10 m du ballon contre 3,4 dans le suivi réel Metrica, 7,5 contre 5,9 à 15 m ; largeur et décalage du bloc conformes).

**What to build:** Selon le diagnostic du 28a, limiter par équipe le nombre de joueurs qui s'engagent vers le ballon (chasseur, presseur, suiveurs, soutien) : au-delà du plafond validé, un joueur garde ou rejoint sa place de référence ou un espace libre (`off_ball.choose_space`), avec une durée minimale d'engagement pour éviter les allers-retours. Le choix de qui reste engagé suit le temps d'arrivée (comme le chasseur du `11l`).

**Attributs :** Teamwork (rayon existant : tenir sa place plutôt que suivre le ballon), Positioning et Work Rate seulement si la carte (`docs/CARTE_ATTRIBUTS_V2.md`, ADR 0002) le permet sans double comptage.

**Constantes à proposer avant le code :** plafond d'engagés par équipe avec et sans ballon, durée minimale d'engagement ; valeurs issues du 28a. Chiffre réel : la référence des joueurs à moins de 10 / 15 m du 28a.

**Lien avec l'existant :** à coordonner avec `v2-collectif/27` (pressing et solutions de passe, à faire), qui touche les suiveurs ; pas de dépendance bloquante.

**Blocked by:** 28a ; `11l` (chasseur désigné stable).

**Bloque :** 09h, 10j, 25h (contrôles d'occupation, de défense et de jeu sans ballon après correction de la grappe).

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications (50 matchs appariés) | 30 min |
| **Total (travail effectif)** | **2 h 05** |

Confiance : faible (dépend du diagnostic du 28a ; si plusieurs intentions sont en cause, découpage à examiner). Hypothèses : un seul point de sélection des engagés dans `cerveau` ; pas de changement de l'évitement (`11f`).
Temps machine, non compté : suite complète ; série appariée de 50 matchs.

## Acceptance criteria

- [ ] Constantes validées par le propriétaire avant le code
- [ ] Scène : avec N engagés au plafond, le joueur suivant tient sa place ou un espace libre ; pas d'aller-retour sous la durée minimale
- [ ] Joueurs de champ à moins de 10 m du ballon : de 4,6 vers la référence réelle du 28a (cible indicative 3,4 ± 0,5, à confirmer), même chose à 15 m
- [ ] Pas de régression mesurée (50 matchs appariés) : solutions faciles laissées au porteur (`v2-collectif/27`), ballons libres repris, buts, tirs, passes réussies, rapportés avec intervalle
- [ ] Largeur d'équipe et décalage côté ballon toujours dans les quartiles réels
- [ ] Déterminisme à graine fixée ; durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 %
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
