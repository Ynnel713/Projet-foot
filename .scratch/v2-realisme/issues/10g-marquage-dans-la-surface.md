# 10g: Marquage dans la surface : homme ou zone

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (arbitrer entre suivre son attaquant et tenir sa zone). **Catégorie :** décision.

**Constat vérifié :** le marquage dans les 25 m ne connaît que le marquage individuel côté but (`defense.py:341-350`).

**What to build:** Un défenseur de zone (10f) prend l'attaquant qui entre dans sa zone et le laisse au suivant quand il en sort ; un attaquant non couvert par une zone est marqué individuellement par le libre le plus proche. Marking garde son rayon (distance à l'attaquant marqué).

**Attributs :** Marking (rayon existant)

**Blocked by:** 10f (Défense de la surface : premier poteau, second poteau, point de penalty, retrait).

**Bloque :** 10j.

**Status:** à faire (constantes à proposer avant le code)

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

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Attaquants libres dans la surface au moment d'une passe dans la surface : part rapportée
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Comments

**Entrée du 18m (21/11/2026, réserve A1 acceptée par le propriétaire).** Après la sélection des frappes de loin (`docs/INDICATEURS_V2.md` section 57, 50 matchs) : conversion dans la surface 16,1 % (réel 14,7 %), hors surface 13,3 % (réel 4,2 %), part des buts hors surface 25,1 % (réel 11,7 %), 4,86 buts par match. Les frappes de loin gardées partent ligne de tir libre, tireur peu gêné à 20 m : la défense de la surface et de ses abords doit fermer ces lignes. Mesurer avant / après sur ces chiffres.
