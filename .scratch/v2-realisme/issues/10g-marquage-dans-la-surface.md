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

- [ ] Repris de la réserve A1 du ticket v2-realisme/07c (acceptée le 12/11/2026) : répartition des types de réception par poste remesurée (`.scratch/v2-realisme/mesures/07c-repartition.py`) ; au 07c, dos au jeu 1,1 % (BU 1,7 %), parce que 1,2 % seulement des passes partent vers un receveur marqué à moins de 2 m et que 86 % des receveurs n'ont aucun adversaire à moins de 5 m ; à remesurer après ce ticket
- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Attaquants libres dans la surface au moment d'une passe dans la surface : part rapportée
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
