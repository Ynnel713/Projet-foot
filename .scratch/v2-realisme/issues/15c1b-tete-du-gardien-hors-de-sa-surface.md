# 15c1b: Tête du gardien hors de sa surface

**Chantier :** `v2-realisme` (remarque du propriétaire du 24/11/2026 : « le gardien qui sort en dehors de sa surface et qui met la tête pour dégager le ballon car il est hors de sa surface, il ne peut pas prendre avec les mains »). **Priorité :** P2. **Catégorie :** décision.

**Constat vérifié (24/11/2026) :** hors de sa surface, le gardien touche déjà un ballon à hauteur de tête comme un joueur de champ (`atteinte.body_part` : mains seulement dans sa surface, `uses_hands`), mais il est exclu du choix du geste de la tête (`match._step_loose_ball`, condition `player.poste != "GK"`, ticket `15c1`) : il amortit toujours, jamais de dégagement de la tête en une touche. Il n'est pas non plus compté comme adversaire dans un duel aérien (`duel_aerien.rival` et `under` : `p.poste != "GK"`, ticket `15b1`), donc un attaquant et un gardien sorti ne se disputent pas un ballon en l'air.

**What to build:** un gardien hors de sa surface (il ne joue pas à la main) passe par le même choix du geste de la tête que les joueurs de champ (`15c1` : en pratique surtout le dégagement, dans sa moitié). À trancher avec le propriétaire avant le code : inclure ou non le gardien hors de sa surface comme adversaire du duel aérien (`15b1`) et de la bascule (`15b2`).

**Attributs :** aucun rôle nouveau (choix : Decisions, Vision, rôles existants ; sa sortie : Rushing Out, Anticipation, existants).

**Mesure préalable proposée :** nombre de contacts de la tête d'un gardien hors de sa surface par match (sans toucher au moteur).

**Blocked by:** `15c1` (livré). **Bloque :** rien.

**Status:** à faire (décision sur le duel aérien à prendre avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 10 min |
| Développement | 10 min |
| Tests unitaires et comportementaux | 15 min |
| Intégration et vérifications | 10 min |
| **Total (travail effectif)** | **45 min** (sans le duel aérien ; avec : environ 1 h 15) |

Confiance : moyenne. Temps machine, non compté : série de 50 matchs (environ 45 min), suite complète (environ 23 min).

## Acceptance criteria

- [ ] Scène : gardien sorti hors de sa surface sur un ballon aérien en profondeur, pressé : il dégage de la tête ; dans sa surface : il prend à la main, pas de geste de la tête
- [ ] Contacts de la tête du gardien hors de sa surface mesurés en série (rapportés, non réglés) ; indicateurs globaux dans le bruit
- [ ] Déterminisme à graine fixée ; suite complète au compte attendu ; durée réelle relevée

## Comments
