# 15c: Qualité de la tête : Heading

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P2 (gagner le duel ne suffit pas à bien jouer le ballon). **Catégorie :** exécution.

**Constat vérifié :** voir 15b.

**What to build:** Le vainqueur du duel joue le ballon de la tête (tir, passe, dégagement) avec une précision et une puissance réglées par Heading ; la tête au but passe par la résolution physique du tir (05a).

**Attributs :** Heading

**Lien avec l'existant :** découpe (validée le 05/11/2026) de `v2-attributs-restants/01` : tête.

**Blocked by:** 15b (Duel aérien : taille, Jumping Reach, Strength au contact); 05a (Tir : le ballon part vers son point d'arrivée, le but n'est plus tiré au départ).

**Bloque :** 15d, 15f.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 55** |

Confiance : moyenne. Hypothèses : tête au but : vitesse plus faible qu'un tir du pied.
Temps machine, non compté : suite complète (environ 40 min).

## Tests

- **Comportementaux (profils comparés) :** Heading 99 contre 11 : têtes cadrées plus souvent

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Effet de Heading mesuré en scène A/B
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
