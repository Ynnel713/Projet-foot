# 25g: Contre-appel : se défaire de son marqueur

**Chantier :** `v2-realisme` (demande du propriétaire du 14/11/2026 : jeu sans ballon et placement dynamique comme cœur du jeu ; audit de la roadmap du même jour). **Priorité :** P1. **Catégorie :** décision.

**Constat vérifié (14/11/2026) :** un joueur marqué cherche un espace libre (`off_ball.choose_space`) mais ne fait jamais de feinte de course : pas de départ dans un sens pour repartir dans l'autre, pas de changement de rythme pour lâcher un marqueur collé. Le 09i (à faire) couvre la course en deux temps de l'attaquant le long de la ligne du hors-jeu, pas le joueur marqué au milieu.

**What to build:** un joueur marqué de près (marqueur perçu à moins de la distance validée) qui veut recevoir fait d'abord quelques mètres dans la direction opposée à l'espace visé, puis repart vers l'espace. Le gain vient de la physique déjà modélisée : temps de réaction du marqueur, freinage (12a), virage (12b), orientation (07b). Le marqueur perçoit la feinte avec sa mémoire de perception (08b), donc il peut la suivre ou non.

**Attributs :** Off the Ball (moment de la feinte, rayon existant), Acceleration et Agility (exécution, rayons existants), Anticipation du marqueur (lire la feinte, rayon existant). Aucun nouvel effet.

**Blocked by:** 25a, 09i (même course en deux temps).

**Bloque :** 25h.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 45** |

Confiance : moyenne. Hypothèses : la course en deux temps du 09i est réutilisable ; le marqueur garde ses règles actuelles.
Temps machine, non compté : suite complète ; mesure 50 matchs.

## Tests

- **Scènes :** marqueur collé, même Pace : écart obtenu après la feinte au moins égal à la valeur validée ; marqueur à Anticipation 99 : écart plus faible qu'à 11.
- **Statistiques (50 matchs) :** contre-appels par match, distance au marqueur à la réception.

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] La séparation obtenue vient de la physique (aucun bonus de distance codé) : test qui le vérifie
- [ ] Contre-appel visible dans la trace (intention, puis changement de direction)
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
