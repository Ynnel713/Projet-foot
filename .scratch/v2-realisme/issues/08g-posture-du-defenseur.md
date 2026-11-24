# 08g: Posture du défenseur : voir à la fois le ballon et son adversaire

**Chantier :** `v2-realisme` (demande du propriétaire du 24/11/2026, éléments sur la défense, point 2 « gestion du temps de réaction et de l'orientation »). **Priorité :** P2. **Catégorie :** perception.

**Constat vérifié (24/11/2026) :** le cap d'un joueur suit son sens de course au-dessus de 19,8 km/h, sinon il regarde le ballon (`movement.desired_facing`, ticket `07a`) ; un défenseur sans ballon voit dans son cône (`08a`) et rafraîchit sa mémoire par des scans réglés par Vision (`scan.py`, `08c`) ; le marquage et la ligne jugent les attaquants sur ces positions perçues (`08e`). Aucun défenseur ne se place de trois-quarts pour garder dans son cône à la fois le ballon et l'attaquant ou la zone dans son dos : il regarde le ballon, et l'appel dans son dos n'est vu qu'au prochain scan.

**What to build:** un défenseur qui marque ou tient sa zone près de sa dernière ligne oriente son corps de trois-quarts, entre le ballon et l'adversaire ou la zone qu'il surveille, tant que les deux tiennent dans son cône (`08a`) ; sinon il garde le ballon devant lui (comme aujourd'hui) et compte sur ses scans. Effets par la mécanique existante : l'attaquant dans le cône est perçu sans attendre un scan (`08b`), et la rotation pour suivre un appel dans le dos est plus courte (`07a`, `07f`), sans bonus de réaction. Mal orienté (pris de court, lancé dans une autre direction), il réagit en retard, ce qui existe déjà.

**Attributs (ADR 0002) :** à trancher avec la carte avant le code : géométrie seule, sans attribut, ou Positioning (justesse de la posture, dans son rayon de placement). Ni Vision (scans), ni Anticipation (élan) : pas de double comptage (R1).

**Blocked by:** `08e`, `07f` (livrés).

**Bloque :** `09k`, `40`, `v2-collectif/22a`.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 35 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 45** |

Confiance : moyenne. Hypothèses : le cap voulu passe par `movement.desired_facing` (une cible de regard en plus) ; l'effet sur le jeu vient de la perception existante. Temps machine, non compté : série de 50 matchs (environ 40 min), suite complète (environ 20 min).

## Tests

- **Scènes :** marqueur côté but, ballon sur l'aile, attaquant qui part dans son dos : appel perçu plus tôt avec la posture de trois-quarts qu'en regardant le ballon ; ballon et attaquant opposés (plus de 100°) : posture inchangée.
- **Statistiques (50 matchs, avant / après) :** appels dans le dos vus en retard (indicateur du `08e`), passes en profondeur réussies, buts (dans le bruit).

## Acceptance criteria

- [ ] Constantes produit (angle de la posture, conditions) et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Posture tracée ; scènes ci-dessus
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Comments
