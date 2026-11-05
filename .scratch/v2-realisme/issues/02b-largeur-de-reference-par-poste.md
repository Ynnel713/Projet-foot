# 02b: Largeur de référence propre à chaque poste

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (latéraux et ailiers doivent occuper les couloirs, l'axe doit rester tenu). **Catégorie :** placement.

**Constat vérifié :** `formation.py` répartit une bande à espacement égal sur 58 m : dans une ligne de 4, le latéral est à environ 16,6 m de la ligne de touche, le même écart que l'ailier d'une ligne de 4 ; un MDC seul est au centre par hasard d'effectif.

**What to build:** Donner à chaque poste une distance de référence à l'axe (latéral, ailier, milieu axial, défenseur central, attaquant), appliquée à la forme de départ que `bloc.py` met ensuite à l'échelle. Plusieurs joueurs du même poste axial se répartissent symétriquement.

**Attributs :** aucun

**Blocked by:** 02a (Côté gauche ou droit selon le poste, et non selon le nom).

**Bloque :** 02d, 02e, 02h.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 50** |

Confiance : moyenne. Hypothèses : valeurs de départ proposées puis validées ; la mise à l'échelle de `bloc.py` reste inchangée.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 20 matchs.

## Tests

- **Unitaires (scène contrôlée) :** 4-3-3 : ailiers plus près de la touche que les latéraux au coup d'envoi ; MDC dans l'axe à 1 m près
- **Statistiques (séries de matchs) :** 20 matchs : position latérale moyenne par poste rapportée

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Distances à l'axe par poste documentées dans le module
- [ ] Position latérale moyenne par poste en match rapportée (20 matchs)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
