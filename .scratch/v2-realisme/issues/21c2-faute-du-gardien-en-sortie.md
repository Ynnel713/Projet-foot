# 21c2: Faute du gardien dans ses sorties sur un ballon libre

**Chantier :** `v2-realisme`, découpage du ticket 21c (16/11/2026, validé par le propriétaire). **Priorité :** P1. **Catégorie :** arbitrage.

**Constat vérifié :** la course au ballon du gardien (`gardien.race`) ne produit jamais de faute : un gardien qui sort sur un ballon libre ne percute jamais l'attaquant.

**What to build:** Quand le gardien et un attaquant arrivent ensemble sur un ballon libre, contact possible ; si le gardien arrive en retard, faute (penalty dans sa surface, coup franc hors de la surface). Prudence de surface du 21c1. Le volet aérien (poing qui percute) va au 21c7 ; le face-à-face (gardien qui fauche le dribbleur) reste au `v2-attributs-restants/10b`.

**Attributs :** Rushing Out et/ou One on Ones, à trancher avec le propriétaire selon `docs/CARTE_ATTRIBUTS_V2.md` (pas de double comptage avec leur rôle actuel) ; Decisions (prudence de surface, 21c1).

**Blocked by:** 21c1.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 30 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 30** |

Confiance : moyenne. Hypothèses : la course au ballon expose déjà les deux arrivants et leurs temps d'arrivée.
Temps machine, non compté : suite complète (environ 10 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** gardien en retard qui percute l'attaquant dans sa surface : penalty ; gardien en avance : pas de faute
- **Statistiques :** 50 matchs : fautes de gardien et penalties qui en découlent, par match

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Source tracée (« faute du gardien en sortie »)
- [ ] Penalties par match rapportés (repère réel à chercher, ou « non trouvé »)
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md` ; test de rayon à jour
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
