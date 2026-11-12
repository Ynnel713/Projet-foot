# 07f: Agility : vitesse de rotation du corps

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (avancé le 05/11/2026 sur décision du propriétaire : base du contrôle orienté et du jeu à une touche (`v2-collectif/31`)). **Catégorie :** physique.

**Constat vérifié :** Agility n'est lue nulle part dans `v2engine/` ; la carte des attributs lui donne « changer de direction, freiner, se retourner ».

**What to build:** La vitesse angulaire maximale du 07a dépend d'Agility (courbe partagée). Le freinage et les changements de trajectoire restent aux tickets 12a et 12b (même attribut, effets distincts, inscrits dans la carte).

**Attributs :** Agility (rotation du corps)

**Blocked by:** 07a (Orientation du corps : état propre et rotation bornée).

**Bloque :** 04h, 07g, `v2-collectif/31`.

**Status:** livré (12/11/2026), validé expert + QC

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

- [x] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code : 450°/s à Agility 99, 360°/s à 55, 270°/s à 11 (courbe partagée, ± 25 %) ; valeur réelle non trouvée (validé le 12/11/2026, « ok »)
- [x] Effet d'Agility mesuré en scène A/B : demi-tour en 0,4 s à 99, 0,5 s à 55, 0,7 s à 11 (0,67 s arrondi au pas de 0,1 s), même scène, même graine (`test_agility_ab_scene_half_turn_faster_at_99_than_at_11`)
- [x] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour : Agility lue dans `orientation` seulement (`tests/test_v2engine_rayon_attributs.py`), carte mise à jour (rotation branchée ; freinage 12a et virage 12b à créer)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions (jeu et cap) ; aucun effet sur le jeu : 20 matchs sur 20 identiques avant / après (44 buts, 694 tirs) ; temps de calcul + 0,1 % et − 1,0 % (`07f-empreintes.txt`)
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md` : 2 773 passés, 14 désélectionnés (2 771 au 18i + 2), 7 min 33 (`07f-suite.txt`)

## Comments

**12/11/2026, implémentation.** `orientation.turn_rate_rad_s(player)` : Agility par la façade `effective_rating`, courbe `success_probability` (baseline 360, amplitude 90, bornes 270 et 450°/s) ; `match._step_player` passe cette vitesse à `turn_towards`. `TURN_RATE_RAD_S` (360°/s) reste la valeur du joueur moyen. Le cap n'est toujours lu par rien : Agility n'a pas d'effet sur le jeu avant le 07b. Tests : 2 ajoutés (courbe 450 / 360 / 270 et plate entre 45 et 55 ; scène A/B), 2 tests du 07a adaptés (borne de rotation par joueur au lieu de 360°/s commun : un joueur sans note d'Agility vaut 60, soit 360,1°/s).

**12/11/2026, passage 1.** Expert : APPROVED (`07f-expert-1.md`, hors dépôt). QC : VALIDÉ. Clôture : VALIDÉ. Aucune réserve.
- Facultatif (expert) : ajouter Agility 55 (0,5 s) à la scène A/B et resserrer sa tolérance à ± 0,05 s.
- À surveiller (expert) : au 07b, mesurer l'effet d'Agility sur les indicateurs de jeu (duels, réception, pressing), plus seulement sur le cap.
- Remarque QC, non bloquante : preuves citées (`07f-empreintes.txt`, `07f-suite.txt`) présentes dans `.scratch/v2-realisme/mesures/`, commitées avec le ticket.

**Durée.** Estimée 1 h 25. Réelle environ 1 h 15, non chronométrée (analyse 15 min, développement 20 min, tests 25 min, intégration et vérifications 15 min) : − 12 %. Temps machine hors total : 3 séries de 20 matchs, suite complète (7 min 33).

