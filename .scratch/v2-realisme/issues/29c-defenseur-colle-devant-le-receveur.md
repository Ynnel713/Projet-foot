# 29c: Défenseur collé devant le receveur : il gagne trop peu le ballon

**Chantier :** `v2-realisme`. **Priorité :** P2. **Catégorie :** moteur (physique, réalisme).

**Constat vérifié (20/11/2026, `18o`) :** sur des matchs joués (graines 2400 à 2447 et 2500 à 2547), quand un adversaire est à moins de 1,5 m du receveur, entre le passeur et lui, la passe n'est pas perdue dans environ 61 % des cas ; sur la ligne et à moins de 0,5 m du bout du trajet, cet adversaire touche le ballon le premier dans environ 23 % des cas seulement (168 adversaires sur 96 matchs). Dans le cas statique du test `test_marked_receiver_at_contact_keeps_the_measured_engine_chance` (adversaire immobile 0,5 m devant le receveur, passe de 12 m), la chance évaluée vaut 0,72 : fidèle au moteur, sans doute irréaliste (un défenseur collé devant, entre le ballon et le receveur, devrait gagner le ballon le plus souvent). Réserve A2 de l'expert au `18n`.

**What to build :** mesurer d'abord, sur des situations construites (receveur et défenseur immobiles ou en mouvement, défenseur devant, à côté, derrière), qui touche le ballon le premier et pourquoi (portée de contrôle du receveur, `match.RECEIVER_REACH_M`, portée du défenseur, ordre de résolution des contacts, receveur qui vient au ballon). Chercher un ordre de grandeur réel (part des passes vers un joueur marqué de face interceptées). Corriger le seul facteur en cause ; puis remesurer la table de coupe et les facteurs du `18o` (la chance évaluée décrit le moteur). Toute constante nouvelle est proposée au propriétaire avant d'être codée.

**Critères d'acceptation (proposés) :** à fixer avec le propriétaire après la mesure (part des ballons gagnés par le défenseur collé devant, cas statique) ; réussite des passes de jeu au-dessus de 80 % (29b) ; critères du `18n` et du `18o` toujours tenus après remesure.

**Attributs :** à établir (portées, Anticipation, Positioning ; voir `docs/CARTE_ATTRIBUTS_V2.md`).

**Blocked by :** aucun.

**Status:** à faire

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code (résolution des contacts) | 30 min |
| Mesure sur situations construites, recherche d'un chiffre réel | 60 min |
| Développement | 45 min |
| Tests | 30 min |
| Intégration et vérifications (remesure de la coupe, matchs appariés) | 75 min |
| **Total (travail effectif)** | **4 h** |

Confiance : faible (cause physique non établie, remesure de la table du `18o` probable). Au-delà du seuil de 2 h : découpage proposé en mesure (1 h 30) puis correction et remesure, à confirmer avant le code. Temps machine, non compté : enregistrement et contrôle sur matchs joués, 50 appariés, suite complète.

## Comments

- 20/11/2026, création pendant le `18o` (décision du propriétaire : le test du receveur marqué fige la valeur du moteur, ticket de physique à part, « oui valide les 3 »).
