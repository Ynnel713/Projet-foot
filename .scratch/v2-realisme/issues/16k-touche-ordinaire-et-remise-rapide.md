# 16k: Touche ordinaire : appels, marquage et remise rapide

**Chantier :** `v2-realisme` (audit de la roadmap du 10/11/2026, complément hors-jeu et coups de pied arrêtés, `docs/AUDIT_ROADMAP_V2.md` §12). **Priorité :** P2 (une touche se joue à plusieurs : des appels et un marquage, parfois très vite). **Catégorie :** placement.

**Constat vérifié :** sur une touche, chacun reste à sa place dans le bloc pendant 15 s de ballon mort (`restart.DEAD_S`, `restart.place`) ; le lanceur choisit ensuite la meilleure passe parmi les coéquipiers à 25 m (`restart_target`). Personne ne se démarque, personne ne marque, et une remise ne peut jamais être jouée vite pour surprendre une défense pas replacée.

**What to build:** Sur une touche, deux ou trois coéquipiers proches viennent proposer (un court, un dans la profondeur), les adversaires proches les marquent ; l'appel suit la logique des appels existants (02g, Off the Ball). Remise rapide : si la défense adverse n'est pas replacée (joueurs en retard sur leur place), le lanceur ou le preneur d'un coup franc peut jouer avant la fin du temps mort (choix du porteur, Decisions). Pas de hors-jeu sur une touche (déjà juste).

**Hors de ce ticket :** touche longue (16f) ; coup franc centré (16i).

**Attributs :** aucun nouveau (Off the Ball, Marking, Decisions : rayons existants).

**Blocked by:** `v2-collectif/29` (livré) ; 02g (livré).

**Bloque :** 16g.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 45** |

Confiance : moyenne. Hypothèses : mêmes appels qu'en jeu, limités au voisinage du ballon.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** touche au milieu de terrain : au moins deux solutions proposées ; défense pas replacée : remise rapide possible
- **Statistiques (séries de matchs) :** 50 matchs : touches conservées (repère sourcé ou « non trouvé »), remises rapides par match

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Appels et marquage visibles sur une touche
- [ ] Touches conservées et remises rapides rapportées
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
