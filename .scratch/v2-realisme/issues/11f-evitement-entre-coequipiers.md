# 11f: Évitement entre coéquipiers : ralentir ou infléchir sa course

**Chantier :** `v2-realisme` (constat du ticket 11e, 15/11/2026). **Priorité :** P0, **priorité absolue fixée par le propriétaire le 15/11/2026** (rythme de jeu). **Catégorie :** déplacement.

**Constat vérifié (11e, 50 matchs, `docs/INDICATEURS_V2.md` section 44) :** 997 contacts francs par match (plus de 2 m/s de rapprochement), dont **337 entre coéquipiers** ; 1 099 déséquilibres par match (12c : vitesse perdue et délai avant d'agir). Aucun évitement dans le code : chaque joueur court droit vers sa cible (`movement.step`, appelé par `match.py:1166` avec `intention.target`) ; seule la collision corrige après coup (`match._resolve_player_collisions`, 11a-11b).

**What to build:** Conscience spatiale de base : avant de se déplacer, le joueur regarde devant lui, le long de sa course voulue, sur un court horizon. Si un coéquipier occupe ce couloir, il **infléchit** sa course (contournement par le côté le plus libre) ou, si l'inflexion ne suffit pas, **ralentit** pour ne pas le percuter. Ajustement de la cible et de l'intensité avant `movement.step`, sans toucher à `step` lui-même. Les adversaires ne sont pas évités (le contact avec eux est un duel : 11b, 11c, tacle) ; le ballon libre disputé par deux coéquipiers relève de qui y va (`cerveau`, chasseur désigné) : le non-désigné s'écarte.

**Attributs :** aucun (règle R1 : locomotion de base, chacun évite ses coéquipiers). Piste à trancher par le propriétaire : n'éviter que les coéquipiers **perçus** (champ de vision, 08a), ce qui ferait jouer la perception sans nouvel attribut.

**Constantes à proposer avant le code (valeurs indicatives, non validées) :** horizon d'anticipation 0,8 s de course ; couloir = somme des rayons + 0,3 m de part et d'autre ; inflexion au plus 35° par rapport à la course voulue, côté le plus libre ; si aucun cap à 35° ou moins n'est libre, vitesse ramenée à celle du coéquipier le long de la course (au plus 50 % de freinage par pas, borné par `decel_max_mps2`). Chiffre réel : non trouvé (ordre de grandeur : des coéquipiers ne se percutent qu'exceptionnellement, quelques fois par match).

**Lien avec l'existant :** réduit les contacts du 11a et les déséquilibres du 12c ; mesuré par les indicateurs du 11e (`contacts francs entre coéquipiers par match`).

**Blocked by:** aucun (11e livré).

**Bloque :** 11g.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 55** |

Confiance : moyenne. Hypothèses : un seul point d'application avant `movement.step` ; boucle sur les coéquipiers seulement (11 x 10 paires par pas, coût à mesurer) ; validation en match au 11g (découpe : le ticket complet était estimé à 2 h 50).
Temps machine, non compté : suite complète (environ 12 min) ; deux matchs de contrôle.

## Tests

- **Unitaires (scène contrôlée) :** deux coéquipiers qui se croisent à 6 m/s : aucun chevauchement, inflexion ≤ 35° ; coéquipier arrêté dans le couloir : contourné ; couloir fermé des deux côtés : freinage, pas de contact ; adversaire dans le couloir : pas d'évitement (duel inchangé) ; course libre : trajectoire identique à avant.
- **Statistiques :** au 11g.

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Scène : aucun contact franc entre deux coéquipiers qui se croisent, sur 20 graines
- [ ] Course sans coéquipier dans le couloir : trajectoire inchangée (empreinte de scène identique)
- [ ] Coût par pas mesuré (durée d'un match : + 10 % au plus)
- [ ] Rayon des attributs inchangé (aucun attribut) ; test de rayon à jour
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
