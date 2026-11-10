# 16i: Coup franc centré : placement des deux équipes, ligne défensive et hors-jeu

**Chantier :** `v2-realisme` (audit de la roadmap du 10/11/2026, complément hors-jeu et coups de pied arrêtés, `docs/AUDIT_ROADMAP_V2.md` §12). **Priorité :** P2 (le coup franc latéral se joue comme un corner, avec en plus une ligne et un hors-jeu). **Catégorie :** placement.

**Constat vérifié :** sur un coup franc, chacun reste à sa place dans le bloc, les adversaires repoussés à 9,15 m (`restart.place`) ; 16a et 16b ne traitent que le corner, 16e que le coup franc frappé au but. Rien ne place les joueurs sur un coup franc excentré ou lointain centré dans la surface, ni la ligne défensive qui monte pour mettre les attaquants hors-jeu.

**What to build:** Sur un coup franc qui sera centré (distance, angle, choix du preneur), l'équipe qui attaque reprend le placement du corner (16a) en ligne, à la limite du hors-jeu ; l'équipe qui défend place sa ligne (hauteur selon la distance du ballon, piège possible au départ du centre) et ses marquages (16b). Les attaquants règlent leur départ sur la ligne (Off the Ball, rayon existant). Coup franc direct à portée : joueurs autour du mur pour le second ballon.

**Attributs :** aucun nouveau (Off the Ball, Marking : rayons existants).

**Lien avec l'existant :** `v2-attributs-restants/02b` (chapeau des coups de pied arrêtés travaillés).

**Blocked by:** 16a, 16b, 16e, 16h.

**Bloque :** 16g.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : même mécanisme de zones que le corner, avec une ligne au lieu d'un placement libre.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** coup franc à 35 m côté gauche : attaquants alignés sur la ligne, défenseurs en ligne à la hauteur prévue ; départ anticipé : hors-jeu
- **Statistiques (séries de matchs) :** 50 matchs : coups francs centrés, tirs et buts qui en découlent, hors-jeu sur coup franc

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Placement des deux équipes visible dans la trace et à l'écran
- [ ] Hors-jeu sur coup franc centré mesuré
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
