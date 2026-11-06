# 02d: Place de référence avec ballon selon le rôle

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (une équipe en possession n'est pas une copie agrandie de sa forme de départ). **Catégorie :** placement.

**Constat vérifié :** avec ballon, `Bloc.reference` (`bloc.py:186-199`) étire la forme de départ à 42 × 46 m et la monte de 8 m pour tous ; un latéral offensif et un latéral défensif ont la même place.

**What to build:** Ajouter à la place de référence avec ballon un décalage propre au rôle (profondeur et largeur) : latéral offensif haut et large, latéral défensif en retrait, milieu récupérateur sous le ballon, ailier de couloir sur la ligne, ailier intérieur rentré. Le décalage s'applique avant la mise à l'échelle du bloc et garde la forme sur le terrain.

**Attributs :** aucun

**Blocked by:** 02b (Largeur de référence propre à chaque poste); 02c (Rôle de poste par défaut, porté par le joueur et tracé).

**Bloque :** 02f, 02h, 09b, 09d, 09e.

**Status:** livré (06/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : décalages exprimés en mètres sur la forme de départ.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 20 matchs.

## Tests

- **Unitaires (scène contrôlée) :** même équipe, latéral offensif contre défensif : place avec ballon plus haute d'au moins la valeur validée
- **Statistiques (séries de matchs) :** 20 matchs : position moyenne en possession par rôle

## Acceptance criteria

- [x] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [x] Décalages par rôle documentés
- [x] Positions moyennes en possession différentes selon le rôle, dans le sens attendu (20 matchs)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Comments

- 06/11/2026 : constantes proposées par Claude (`ROLE_PLACE_WITH_BALL`, `v2engine/bloc.py`), validées par délégation ; chiffres réels non trouvés (ordres de grandeur tactiques). Décalage (avance, écart à l'axe) appliqué à la forme de départ avant la mise à l'échelle ; la forme décalée sert à mesurer le bloc avec ballon, qui garde son centre, sa longueur et sa largeur (42 x 46 m) : les rôles redistribuent les joueurs dans le bloc calibré. Sans ballon, rien ne change. Piston (+12 m, +4 m de largeur), latéral (+5, +1), latéral défensif (−3, −2), récupérateur (−6), regista (−4), pivot (−5), ailier de couloir (+8, +2), ailier intérieur (+6, −8), etc. ; table complète dans le module.
- Mesure, 20 matchs (graine d'audit 20260923, `scripts/measure_roles_v2.py`, avant puis après, mêmes matchs), progression moyenne en possession : piston +8,5 à +9,2 m, latéral +3,5, latéral défensif −4,4 (et rentre de 2,2 m), récupérateur −5,4 à −5,8, regista −9,7 (MDC), pivot −3,9, ailier de couloir +4,0, ailier intérieur +3,0 à +3,7 et rentre de 5,3 m. Les rôles sans décalage reculent un peu (défenseur central −0,7, avant-centre −1,3 : conservation de la moyenne du bloc). Comparer deux rôles entre eux est faussé par les équipes (les latéraux défensifs viennent d'équipes qui jouent plus haut) : lire les écarts avant/après par rôle.
- Effet sur le jeu (`measure_v2`, 20 matchs) : tirs par équipe 30,1 → 26,6 (−11 %), buts par match 4,15 → 4,05, tirs de près 4,7 → 4,5. Les attaquants (pivot, avant-centre) reculent d'un peu en possession. Calibration des tirs à revoir dans les tickets 05 et 06, pas ici.
- Déterminisme : deux exécutions à graine fixée, même empreinte (`af5358598c953fd0`). Suite complète : 2 446 passés, 14 désélectionnés, 27 min 14 s (attendu 2 440 + 6 tests ajoutés).
- Durée : estimée 2 h, réelle environ 1 h 35 (non chronométrée), écart environ − 21 %. Temps machine, hors total : suite complète 27 min (en parallèle des mesures), mesures 20 matchs.
- 06/11/2026 : passage 1 de l'expert `APPROVED_WITH_RESERVATIONS`, QC `VALIDÉ`, clôture `VALIDÉ` (journal). Réserves acceptées d'office, règle permanente du propriétaire. A1 : la table est un décalage RELATIF à la moyenne de l'équipe (mètres avant mise à l'échelle et recentrage), pas une avance absolue ; mesuré sur 20 matchs, la mezzala MC (+2 nominal) recule de 3,4 m, l'avant-centre (+3) de 1,3 m, le buteur axial (+5) est stable, le second attaquant (−2) recule de 3,6 à 6,4 m. 02f, 09b et suivants doivent partir de l'effet mesuré, pas de la table. A2 : tirs par équipe −11 % (30,1 → 26,6), écart de l'ordre de 3 erreurs-types (non quantifié) ; ne pas recaler 05 et 06 sans repartir de cette mesure et donner l'écart-type à la reprise. A3 : constantes validées par délégation, confirmée par le propriétaire (règle permanente). Facultatifs non faits (changeraient l'empreinte revue) : commentaire de la table à préciser (« décalage relatif »), commentaire de `movement.py:88` périmé, commentaire du test latéral inexact (l'écart est dilaté, 15 m deviennent environ 21 m, et non comprimés) : à reprendre en 02e.
