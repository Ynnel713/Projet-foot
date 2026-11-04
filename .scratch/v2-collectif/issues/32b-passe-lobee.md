# 32b: Passe lobée

**Découpé du ticket 32 le 04/11/2026** (audit de granularité). Détail : `32-types-de-passes.md`, point 1.

**What to build:** une passe par-dessus la défense vers un joueur lancé ou un espace. Elle passe au-dessus des joueurs selon la vraie hauteur du ballon (`v2-hauteur-ballon/03`) : un joueur ne l'intercepte que là où elle est dans sa portée, en pratique près du point de chute. Plus difficile qu'une passe au sol sur la même distance. C'est une option de plus dans la décision du porteur (ticket 33), à côté des passes du 32a.

**Attributs :** Passing (exécution), Vision, Decisions, Flair ; Technique si la carte le prévoit. Rayons à fixer dans `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage.

**Blocked by:** 32a (même cadre de choix), `v2-hauteur-ballon/03`.

**Bloque :** 22a.

**Status:** à faire (constantes à proposer avant le code)

**Chiffres réels :** part de passes lobées : **non trouvée, à sourcer**.

## Acceptance criteria

- [ ] Constantes et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Test de cohérence (scène fixe) : la lobée est plus fréquente quand la ligne de passe au sol est fermée et qu'il y a de l'espace derrière la défense
- [ ] Une passe lobée n'est pas interceptée par un joueur hors de portée sur son trajet (test)
- [ ] Tracée avec sa hauteur et affichée à l'écran
- [ ] Rayon des attributs conforme à la carte, sans double comptage (repris du ticket 32)
- [ ] En match (50 matchs, graine d'audit) : part et réussite des lobées, comparées avant et après
- [ ] Déterminisme à graine fixée ; suite V2 verte ; V1 inchangée
