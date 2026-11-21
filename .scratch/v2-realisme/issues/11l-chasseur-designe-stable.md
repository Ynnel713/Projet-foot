# 11l: Chasseur désigné stable sur ballon libre

**Chantier :** `v2-realisme` (constat du ticket 11k, 15/11/2026 ; réserve A1 du 11g). **Priorité :** P1. **Catégorie :** décision.

**Constat vérifié (11k, 50 matchs, `docs/INDICATEURS_V2.md` section 47) :** 618 désignations de chasseur par match, 139 changements de chasseur, **21 % des désignations changent de joueur en moins de 1 s** : le chasseur est recalculé à chaque pas au plus proche (`cerveau.nearest_field_player`), sans maintien. Référence de mesure : série « après » du 11k (485,8 épisodes disputés par match, délai avant la prise 1,55 s, repris par l'équipe qui l'avait 0,751) ; l'écart avec l'avant 11f n'est pas comparable (définitions d'épisode, réserve A2 de l'expert au 11k).

**What to build:** Désigner le chasseur de champ par le **temps d'arrivée au point du ballon** (pas la distance), avec une **marge de maintien** : le chasseur en place le reste tant qu'un coéquipier n'arrive pas nettement avant lui. Plan accepté par le propriétaire le 15/11/2026 (réserve A1 du 11g, « Accepter, mesurer au 11k »).

**Attributs :** aucun nouveau (le temps d'arrivée lit déjà vitesse et accélération : `defense.arrival_time_s`, règle anti double comptage à vérifier dans `docs/CARTE_ATTRIBUTS_V2.md`).

**Constantes à proposer avant le code :** marge de maintien (valeur indicative, non validée : 0,3 s d'avance sur le chasseur en place). Chiffre réel : non trouvé.

**Blocked by:** 11k (livré).

**Bloque :** `v2-realisme/28b` (ajouté le 21/11/2026, audit de réalisme).

**Status:** à faire

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 30 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 25 min |
| **Total (travail effectif)** | **1 h 40** |

Confiance : moyenne. Hypothèses : un seul point de désignation (`cerveau.nearest_field_player`, lu par `interpret` et par la priorité d'évitement de `match._step_player`) ; maintien porté par l'état du pas précédent (intentions).
Temps machine, non compté : suite complète ; série appariée de 50 matchs (une seule série à la fois : deux en parallèle dépassent la mémoire, 11k).

## Acceptance criteria

- [ ] Constante de maintien validée par le propriétaire avant le code
- [ ] Scènes : chasseur conservé tant que l'écart de temps d'arrivée reste sous la marge ; changé au-delà ; gardien exclu (11g)
- [ ] Changements de chasseur en moins de 1 s : de 21 % à 5 % des désignations au plus (cible indicative, à confirmer)
- [ ] Ballons libres repris par l'équipe qui les avait et délai avant la prise rapportés (contre `11k-apres-serie.txt`, 50 matchs appariés)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 %
- [ ] Déterminisme à graine fixée ; suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
