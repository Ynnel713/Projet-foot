# 12b: Perte de vitesse en virage

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (un changement de direction coûte de la vitesse, plus ou moins selon Agility). **Catégorie :** physique.

**Constat vérifié :** un changement de direction passe par le freinage commun (`movement.step`, branche « freine ») ; aucune limite liée au rayon de courbe.

**What to build:** La vitesse maximale dans un virage est limitée par une accélération latérale maximale qui dépend d'Agility ; un virage serré oblige à ralentir.

**Attributs :** Agility (changement de direction)

**Lien avec l'existant :** découpe (validée le 05/11/2026) de `v2-attributs-restants/07b` : changement de direction.

**Blocked by:** 12a (Freinage individualisé : Agility).

**Bloque :** 12g.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 55** |

Confiance : moyenne. Hypothèses : limite d'accélération latérale : valeur à sourcer.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 20 matchs.

## Tests

- **Unitaires (scène contrôlée) :** virage à 90° à pleine vitesse : vitesse minimale dans le virage sous la vitesse de départ
- **Comportementaux (profils comparés) :** Agility 99 contre 11 : perte plus faible

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Perte de vitesse en virage mesurée en scène
- [ ] Km par joueur rapportés
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Comments

**13/11/2026, lien avec le 07b (double comptage à éviter).** Depuis `v2-realisme/07b`, la vitesse max dépend de l'angle entre la direction voulue et le cap (`movement.direction_speed_factor` : 100 % jusqu'à 45°, 80 % à 90°, 65 % à 180°), et le cap tourne à `turn_rate_rad_s(Agility)`. Un crochet coûte donc déjà de la vitesse tant que le corps n'a pas tourné, avec Agility par la vitesse de rotation (07f). La limite d'accélération latérale de ce ticket s'ajoute au freinage et au plafond du 07b : vérifier en scène qu'un virage à 90° ne cumule pas les deux pertes au-delà du réel, ou réduire l'une quand l'autre joue.
