# 07f: Agility : vitesse de rotation du corps

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (avancé le 05/11/2026 sur décision du propriétaire : base du contrôle orienté et du jeu à une touche (`v2-collectif/31`)). **Catégorie :** physique.

**Constat vérifié :** Agility n'est lue nulle part dans `v2engine/` ; la carte des attributs lui donne « changer de direction, freiner, se retourner ».

**What to build:** La vitesse angulaire maximale du 07a dépend d'Agility (courbe partagée). Le freinage et les changements de trajectoire restent aux tickets 12a et 12b (même attribut, effets distincts, inscrits dans la carte).

**Attributs :** Agility (rotation du corps)

**Blocked by:** 07a (Orientation du corps : état propre et rotation bornée).

**Bloque :** 04h, 07g, `v2-collectif/31`.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 30 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 25** |

Confiance : élevée. Hypothèses : courbe partagée de `attributes`.
Temps machine, non compté : suite complète (environ 40 min).

## Tests

- **Comportementaux (profils comparés) :** Agility 99 contre 11 : demi-tour plus rapide d'un rapport validé

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Effet d'Agility mesuré en scène A/B
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
