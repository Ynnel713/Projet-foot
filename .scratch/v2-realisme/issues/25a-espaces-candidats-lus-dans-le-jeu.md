# 25a: Espaces candidats lus dans le jeu, pas autour de la place

**Chantier :** `v2-realisme` (demande du propriétaire du 14/11/2026 : jeu sans ballon et placement dynamique comme cœur du jeu ; audit de la roadmap du même jour). **Priorité :** P1 (fondation des 25b à 25g). **Catégorie :** placement.

**Constat vérifié (14/11/2026) :** `off_ball.choose_space` évalue une grille fixe de 12 points (4 en profondeur × 3 en largeur, `_FORWARD_STEPS`, `_LATERAL_STEPS`) autour de la **place de référence** du joueur, dans un rayon réglé par Off the Ball (2 à 15 m). Le placement reste donc « une position assignée, un peu bougée » : un espace libre à 18 m de sa place, ou dans l'angle d'une ligne de passe du porteur, n'est jamais envisagé.

**What to build:** les points candidats sont produits par la lecture du jeu, en plus de la grille actuelle : (1) points sur les lignes de passe ouvertes depuis le porteur (angles où aucun adversaire perçu ne coupe la ligne, 08b) ; (2) points entre les lignes adverses (derrière les milieux, devant les défenseurs perçus) ; (3) points dans le dos du marqueur. Chaque point est noté comme aujourd'hui (passe trouvable, espacement de 8 m) plus la distance à la place de référence (ancre de structure : Teamwork règle combien il accepte de s'en éloigner, rayon existant de `Bloc.replacement`). Off the Ball garde son rayon (jusqu'où il cherche, justesse du choix). Positions des adversaires : celles que le joueur perçoit (08b), pas les vraies.

**Hors de ce ticket :** qui appelle (02g, inchangé) ; couloirs (09b) ; comportements des 25b à 25g, qui s'appuient sur ces candidats.

**Attributs :** Off the Ball (rayon existant), Teamwork (rayon existant : écart toléré à la place). Aucun nouvel effet.

**Ticket 24 en cours :** toute courbe d'attribut de ce ticket passe par `success_probability` / `duel_probability`, dont la forme change au 24 ; les constantes de niveau sont proposées après la livraison du 24.

**Blocked by:** 09b (même fonction `choose_space`, contrainte de couloir à garder).

**Bloque :** 25c, 25d, 25e, 25f, 25g.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : la notation actuelle des points (passe trouvable) suffit ; coût de calcul maîtrisé (au plus une vingtaine de points par joueur, recherche toutes les 1 s).
Temps machine, non compté : suite complète (environ 10 min) ; mesure 50 matchs.

## Tests

- **Scènes :** porteur au milieu, adversaire dans la ligne directe : le coéquipier choisit un point sur une ligne ouverte hors de la grille actuelle ; adversaire non perçu : la ligne est jugée ouverte.
- **Statistiques (50 matchs) :** solutions de passe ouvertes pour le porteur (indicateur du `v2-collectif/06`), regroupement, distance moyenne à la place de référence, temps de calcul.

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Solutions de passe ouvertes par décision du porteur en hausse, à graine égale, sans hausse du regroupement
- [ ] Structure gardée : distance moyenne à la place de référence bornée (valeur validée), Teamwork 99 plus près que 11
- [ ] Temps de calcul d'un match en hausse de 10 % au plus
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
