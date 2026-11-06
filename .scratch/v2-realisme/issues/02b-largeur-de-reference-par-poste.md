# 02b: Largeur de référence propre à chaque poste

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (latéraux et ailiers doivent occuper les couloirs, l'axe doit rester tenu). **Catégorie :** placement.

**Constat vérifié :** `formation.py` répartit une bande à espacement égal sur 58 m : dans une ligne de 4, le latéral est à environ 16,6 m de la ligne de touche, le même écart que l'ailier d'une ligne de 4 ; un MDC seul est au centre par hasard d'effectif.

**What to build:** Donner à chaque poste une distance de référence à l'axe (latéral, ailier, milieu axial, défenseur central, attaquant), appliquée à la forme de départ que `bloc.py` met ensuite à l'échelle. Plusieurs joueurs du même poste axial se répartissent symétriquement.

**Attributs :** aucun

**Blocked by:** 02a (Côté gauche ou droit selon le poste, et non selon le nom).

**Bloque :** 02d, 02e, 02h.

**Status:** livré (06/11/2026), validé expert + QC

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

## Comments

- 06/11/2026 : constantes proposées par Claude, sans source chiffrée trouvée (ordres de grandeur), validées par délégation du propriétaire : ailier 26 m, latéral 22 m de l'axe ; écart entre joueurs d'un même poste axial DC 16, MDC 12, MC 16, MOC 14, SA/BU/ATT 14 (`v2engine/formation.py`). Mesure 20 matchs (distance moyenne à l'axe, m) : AG 21,3 ; AD 20,7 ; LB 18,8 ; RB 18,7 ; MC 10,0 ; DC 9,4 ; MDC 7,2 ; BU 7,0 ; MOC 6,6 (SA et ATT absents de l'échantillon). Déterminisme : même empreinte sur deux exécutions (`af9c7e9e13354fb8`).
- 06/11/2026 : passage 1 de l'expert `APPROVED_WITH_RESERVATIONS` (A1 ordre de la lineup, A2 test fragile, A3 déterminisme non rapporté) ; corrigées, puis passage 2 `APPROVED_WITH_RESERVATIONS` (seule réserve : durée réelle, ci-dessous). QC `VALIDÉ`, clôture `VALIDÉ` (journal). Un premier calcul de clôture est `BLOQUÉ` dans le journal : mon fichier de rapport omettait la section « Identification », recopiée en entier ensuite. Réserves acceptées d'office, règle permanente du propriétaire. Le test de transition joue désormais jusqu'à 5 graines (l'assertion est inchangée) ; le chiffre « Attendu » de `CLAUDE.md` (2 399) est à mettre à jour : 2 415 en comptant 02a et 02b, calculé et non obtenu en un seul passage.
- Durée : estimée 1 h 50, réelle environ 2 h 05 (non chronométrée), écart environ + 14 % : deux passes de l'expert et correction de l'ordre de la lineup. Temps machine, hors total : mesure 20 matchs 9 min 40 s (deux fois), suite complète environ 15 min (trois passages, dont un faussé par la charge).
