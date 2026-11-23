# EM-22 — Regagner la fluidité de l'écran V2

**Status:** à faire (créé le 23/11/2026 à la clôture de `v2-hauteur-ballon/02b`, décision du propriétaire : « Accepter, ticket de suite »)

**Constat mesuré** (`.scratch/v2-hauteur-ballon/mesures/02b-fluidite.txt`) : images par seconde de l'écran de match V2, même trace (Auxerre – Monaco, graine 20261123), lecture ×1, processeur ralenti 6 fois, Chromium sans affichage de la session cloud, API simulée, build de production :

| Version | Images par seconde |
|---|---|
| `41e573e` (base du ticket `v2-hauteur-ballon/01`) | 59,5 |
| `f42dc68` (ticket `v2-hauteur-ballon/01`) | 58,5 |
| `443e8c9` (interpolation courbe, `v2-correctifs-ecran/04b`) | 59,3 |
| `618c78c` (EM-04, écran en trois zones) | 55,4 |
| `1a9a38d` (EM-05) / `00dca4c` (EM-06) | 56,0 / 55,6 |
| `c057086` (EM-07, marqueurs en relief) | 52,6 |
| `6de4140` (EM-21a, ballon qui roule, traînée) | 46,9 |
| `b43d942` (juste avant `v2-hauteur-ballon/02b`) | 47,8 |
| `v2-hauteur-ballon/02b` | 49,0 |

La baisse (− 18 % depuis la base) vient surtout de l'EM-21a : `BallMarker` reconstruit à chaque image ses `<defs>` (motif de panneaux `pattern`, dégradés), et de l'EM-04 et de l'EM-07 (structure de l'écran, relief des marqueurs).

**What to build:** retrouver au moins 54 images par seconde (base − 10 %) dans les mêmes conditions de mesure, sans changer ce que voit l'utilisateur : profilage (Chrome DevTools sur la trace), puis par exemple `<defs>` du ballon posés une fois et déplacés par `transform`, filtres du relief des marqueurs remplacés par des dégradés, mémoïsation des zones qui ne changent pas à chaque image.

**Mesure :** script de mesure du 02b (dans le dossier de mesures du chantier `v2-hauteur-ballon`, à reprendre dans `scripts/` si ce ticket le généralise) ; limite : Chromium sans affichage, pas un navigateur visible (choix du propriétaire du 23/11/2026).

**Blocked by:** aucun.

## Acceptance criteria

- [ ] Images par seconde ≥ 54, même trace, ×1, processeur ralenti 6 fois, 30 s, trois lectures alternées avec la version d'avant
- [ ] Captures avant / après identiques à l'œil (ballon, motif, traînée, marqueurs, hauteur du ballon)
- [ ] `npm run build`, `npm run lint` (0 erreur), `npm test`
