# 20g: Blessures sans contact, coups et crampes selon la charge

**Chantier :** `v2-realisme` (audit de la roadmap du 10/11/2026, `docs/AUDIT_ROADMAP_V2.md`). **Priorité :** P2 (la fatigue augmente le risque sans le rendre automatique ; un joueur frais peut aussi se blesser). **Catégorie :** physique.

**Constat vérifié :** `v2-attributs-restants/09b` ne prévoit que la blessure sur un contact (Bravery, tacle dur) ; rien ne relie la blessure à la charge (sprints répétés, réserve basse) ; pas de joueur touché qui continue diminué.

**What to build:** Risque de blessure musculaire sans contact à chaque sprint, qui croît avec la charge (12f) et la réserve basse sans jamais être nul pour un joueur frais. Après un contact, un « coup » réduit la capacité (vitesse maximale, gestes par la façade) pour un temps ou jusqu'à la sortie. Crampes rares en fin de match, selon la réserve. Le blessé ralentit, ne sprinte plus et sort au prochain arrêt (09b, `v2-coach-et-gestion-de-match/05a`). Fréquences sourcées (études d'incidence en football professionnel) ou « non trouvé ».

**Attributs :** aucun nouveau (Natural Fitness reste hors du match, D-V10).

**Blocked by:** 12f, 19a ; `v2-attributs-restants/09b`.

**Bloque :** rien.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h** |

Confiance : faible. Hypothèses : fréquences réelles rares : séries longues nécessaires pour les mesurer.
Temps machine, non compté : suite complète (environ 40 min) ; 1 000 matchs (01e).

## Tests

- **Unitaires (scène contrôlée) :** même joueur, 200 sprints frais puis 200 sprints réserve basse : risque plus élevé, jamais nul frais
- **Statistiques (séries de matchs) :** 1 000 matchs : blessures sans contact, coups, crampes par match ; part en fin de match

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Fréquences dans des fourchettes sourcées ou « non trouvé » assumé
- [ ] Un joueur touché court moins vite et le montre dans la trace jusqu'à sa sortie
- [ ] Arrêt pour soins compté dans le temps additionnel ; visible à l'écran
- [ ] Toute note lue passe par la façade de la condition (`v2-realisme/19a`), jamais par `player_attribute` directement
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
