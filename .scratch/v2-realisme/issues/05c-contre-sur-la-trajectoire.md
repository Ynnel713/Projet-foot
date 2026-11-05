# 05c: Contre : le défenseur touche réellement le tir

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (le contre doit naître de la trajectoire, pas d'un tirage préalable). **Catégorie :** exécution.

**Constat vérifié :** `match.py:461` tire le contreur avant le départ du tir (`draw_blocker`, cône et chance de 0,6 par part couverte, `shooting.py`) ; le ballon repart ensuite d'un angle tiré au hasard.

**What to build:** Le tir simulé pas à pas (05a) touche un joueur de champ qu'il frôle (détection de contact existante) ; un défenseur sur la trajectoire tente de contrer avec une chance qui dépend de sa distance au tireur (temps de réaction) ; la valeur `BLOCK_CHANCE` devient cette chance au contact. Le contre est tracé avec l'endroit du contact.

**Hors de ce ticket :** déviation après contact (05d) ; Bravery (17b).

**Attributs :** aucun

**Lien avec l'existant :** remplace le tirage préalable du ticket 33 / 28a (livrés, non modifiés).

**Blocked by:** 05a (Tir : le ballon part vers son point d'arrivée, le but n'est plus tiré au départ).

**Bloque :** 05d, 05e, 05g, 17b.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 35 min |
| Intégration et vérifications | 25 min |
| **Total (travail effectif)** | **2 h 10** |

Confiance : moyenne. Hypothèses : la décision du porteur garde son estimation du contre (`block_probability`) jusqu'au 05e.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** défenseur à 1 m sur l'axe : contre fréquent ; à 8 m : moins fréquent (temps de réaction) ; hors axe : jamais
- **Statistiques (séries de matchs) :** 50 matchs : part des tirs contrés (repère 20-28 %, indicatif)

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Plus de tirage préalable du contreur
- [ ] Part contrée rapportée (50 matchs)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
