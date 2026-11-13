# 05k: Tir masqué : le gardien voit partir le ballon en retard

**Chantier :** `v2-realisme`. **Priorité :** P1. **Catégorie :** tir, gardien, perception.

**Origine :** propriétaire, 13/11/2026, pendant le 08a : « le gardien peut être masqué sur une frappe également si un joueur lui masque le ballon et donc peut voir le ballon arriver plus tard ». Aucun ticket ne le couvrait (recherche « masqué », « écran »).

**Constat vérifié :** la portée du gardien sur un tir croît avec le temps écoulé depuis la frappe (`shooting.keeper_reach_m`, tickets 05b et 06a) ; ce temps part de la frappe, quels que soient les joueurs placés entre le ballon et le gardien.

**What to build :** Un tir est masqué quand un joueur (coéquipier ou adversaire du gardien) se trouve près de la ligne ballon-gardien au départ du tir et assez près du gardien pour couvrir le ballon à ses yeux. Le gardien voit alors le ballon plus tard : son temps de réaction part de l'instant où le ballon sort du masque (ou d'un retard fixe à proposer). Même loi pour l'évaluation du tir par le tireur (chance de but) et pour la résolution (principe du 18g). Tracé (tir masqué ou non, retard).

**Hors de ce ticket :** champ de vision et mémoire des joueurs de champ (08a, 08b) ; déviation (05d, 05i).

**Attributs :** aucun (masquage géométrique). Un effet éventuel d'un attribut du gardien (lecture, placement) est à proposer, sans double comptage avec Reflexes.

**Blocked by :** 05b (arrêt par portée du gardien) ; 08a (géométrie de la vision).

**Bloque :** `v2-collectif/22c` (calibration des tirs).

**Status :** à faire (constantes à proposer avant le code : largeur du masque, distance au gardien, retard)

## Estimation

| Poste | Durée |
|---|---|
| Analyse (dont sources : effet du tir masqué sur la conversion) | 30 min |
| Développement | 45 min |
| Tests | 30 min |
| Intégration et vérifications (50 matchs) | 30 min |
| **Total (travail effectif)** | **2 h 15** |

Confiance : moyenne. Hypothèses : le retard s'ajoute au temps écoulé de `keeper_reach_m` sans autre changement du modèle du gardien ; l'évaluation du tir (`occasion_quality`) lit la même géométrie. Temps machine, hors total : série de 50 matchs (environ 25 min), suite complète (environ 9 min).

## Tests

- **Unitaires (scène contrôlée) :** défenseur sur la ligne, à 2 m du gardien : tir masqué, retard appliqué ; défenseur écarté de 3 m : non masqué
- **Statistiques (série de matchs) :** part des tirs masqués, conversion masqués contre non masqués, comparées à une source si trouvée

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Tir masqué détecté, retard appliqué et tracé ; même loi à l'évaluation et à la résolution (test)
- [ ] Part des tirs masqués et conversion mesurées sur 50 matchs, avant / après
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Comments
