# 16f: Touche longue (Long Throws)

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P2 (arme de certains joueurs près de la surface). **Catégorie :** exécution.

**Constat vérifié :** Long Throws n'est lu nulle part ; les touches sont jouées comme des passes courtes (ticket 29).

**What to build:** Près de la surface adverse, un joueur à Long Throws élevé peut lancer long dans la surface ; distance et précision selon Long Throws ; ballon aérien disputé (15a).

**Attributs :** Long Throws

**Lien avec l'existant :** découpe (validée le 05/11/2026) de `v2-attributs-restants/02b` : touches longues.

**Blocked by:** 15a (Qui attaque la trajectoire aérienne) ; 16j (Tireurs désignés) (ajouté le 10/11/2026, audit de la roadmap).

**Bloque :** 16g.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 35** |

Confiance : moyenne. Hypothèses : trajectoire aérienne disponible.
Temps machine, non compté : suite complète (environ 40 min).

## Tests

- **Comportementaux (profils comparés) :** Long Throws 99 contre 11 : distance moyenne plus grande

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Effet de l'attribut mesuré
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
