# 10g: Marquage dans la surface : homme ou zone

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (arbitrer entre suivre son attaquant et tenir sa zone). **Catégorie :** décision.

**Constat vérifié :** le marquage dans les 25 m ne connaît que le marquage individuel côté but (`defense.py:341-350`).

**What to build:** Un défenseur de zone (10f) prend l'attaquant qui entre dans sa zone et le laisse au suivant quand il en sort ; un attaquant non couvert par une zone est marqué individuellement par le libre le plus proche. Marking garde son rayon (distance à l'attaquant marqué).

**Attributs :** Marking (rayon existant)

**Blocked by:** 10f (Défense de la surface : premier poteau, second poteau, point de penalty, retrait).

**Bloque :** 10j.

**Status:** livré (22/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : pas encore de consigne d'équipe homme / zone (13).
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** attaquant qui traverse deux zones : pris puis rendu ; attaquant hors zones : marqué individuellement

## Résultat (22/11/2026, `docs/INDICATEURS_V2.md` section 62)

Diagnostic avant le code (8 matchs, 143 passes de jeu vers un receveur dans la surface, `.scratch/v2-realisme/mesures/10g-diag.py`) : receveur marqué 99 %, attaquants dans la surface marqués 100 % ; le marqueur est le libre le plus proche, réattribué à chaque pas, avant les zones du 10f : le défenseur de zone prend déjà l'attaquant qui entre dans sa zone et le rend quand il en sort, et un attaquant hors zone est marqué par le libre le plus proche. **Rien à construire** (recommandation retenue par délégation du propriétaire, 22/11/2026) : moteur inchangé ; deux tests figent le comportement demandé (`tests/test_v2engine_marquage_surface.py`, scènes du ticket). Écart restant : distance de marquage (2,98 m en médiane à la passe, 31 % des attaquants à 2 m ou moins), courbe Marking validée au `v2-collectif/07` laissée telle quelle ; piste pour le `v2-collectif/22c`.

Durée : estimée 2 h, réelle environ 45 min (analyse et diagnostic 25 min, tests 10 min, documentation 10 min), écart − 63 % : la prémisse du ticket (attaquants non couverts) ne se vérifie pas, aucun code moteur. Temps machine hors total : diagnostic de 8 matchs, suite complète.

## Acceptance criteria

- [x] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code : aucune constante (rien à construire)
- [x] Attaquants libres dans la surface au moment d'une passe dans la surface : part rapportée (0 % non marqués, 31 % à 2 m ou moins d'un défenseur ; `docs/INDICATEURS_V2.md` section 62)
- [x] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour : Marking inchangé
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : moteur inchangé
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md` : 3 488 passés, 0 ignoré, 14 désélectionnés (3 486 au `05l` + 2 tests)

## Comments

**Entrée du 18m (21/11/2026, réserve A1 acceptée par le propriétaire).** Après la sélection des frappes de loin (`docs/INDICATEURS_V2.md` section 57, 50 matchs) : conversion dans la surface 16,1 % (réel 14,7 %), hors surface 13,3 % (réel 4,2 %), part des buts hors surface 25,1 % (réel 11,7 %), 4,86 buts par match. Les frappes de loin gardées partent ligne de tir libre, tireur peu gêné à 20 m : la défense de la surface et de ses abords doit fermer ces lignes. Mesurer avant / après sur ces chiffres.

**Entrée du 10f (21/11/2026).** Zones de la surface livrées (`docs/INDICATEURS_V2.md` section 58) : rôle `zone de surface`, poteaux tenus seulement ballon à 20 m ou moins. À mesurer ici, avant / après, sur la même série (`.scratch/v2-realisme/mesures/10f-serie.py`) : buts par match (+ 0,56 ± 0,89 au 10f, même sens sur trois versions), profondeur de l'avant-dernier défenseur et hors-jeu aux instants sur l'aile, répartition par poste des joueurs en zone (facultatif A2 de l'expert).

**Clôture du 22/11/2026, passage 1 :** expert APPROVED ; QC VALIDÉ ; clôture VALIDÉ. Réserve facultative A1 : marqueur réattribué à chaque pas sans marge de titulaire (`defense.py:583`), alternance possible entre deux défenseurs à égale distance, à mesurer au `10j` ou au `v2-collectif/22c` (changements de marqueur par attaquant et par seconde dans la surface).
