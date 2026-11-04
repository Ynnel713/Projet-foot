# 01: POC — un but refusé pour hors-jeu, sur un gabarit pilote

**What to build:** pour une occasion non-but choisie sur le gabarit pilote (ex. `contre_attaque`), le ballon franchit la ligne de but exactement comme pour un vrai but (réutilise la physique existante), le tableau de score s'illumine brièvement comme pour un vrai but, PUIS un bandeau indique « Hors-jeu » et le score réel ne change jamais — ni dans les métadonnées du clip, ni dans le résultat du match. Le `GoalEvent` du moteur n'est à aucun moment touché ou recréé : ceci reste une réécriture de mise en scène d'une « occasion » déjà existante, jamais un vrai but reconverti.

**Blocked by:** None.

**Status:** en sommeil (04/11/2026) : animation V1 désactivée depuis `70ca9d1` (drapeau `LIVE_AND_ANIMATION_ENABLED = false`, décision du propriétaire du 24/10/2026, effort porté sur la V2). À reprendre tel quel si l'animation V1 est rallumée.

- [ ] Sur l'échantillon de référence, au moins un clip montre un but refusé pour hors-jeu, visuellement indiscernable d'un vrai but jusqu'au bandeau d'annulation
- [ ] Le score affiché (scoreboard, métadonnées du clip, résultat du match) ne change JAMAIS sur ce clip — identique avant/après
- [ ] Aucun `GoalEvent` du moteur n'est créé, modifié ou supprimé pour produire ce clip (vérifiable : le clip provient d'une `occasion` existante du moteur, pas d'un but)
- [ ] Le bandeau « Hors-jeu » apparaît après le flash du tableau de score, jamais avant (ordre de révélation respecté : célébration puis annulation, comme en vrai)
- [ ] Déterminisme bit-à-bit vérifié (sha256 de `event_ref`, jamais `random`/`hash()`/horloge)
- [ ] Résultat sportif (score, buteurs, cartons, remplacements) strictement identique à avant
- [ ] Les gabarits hors de ce POC sont 100 % identiques clip à clip
- [ ] Propriétaire valide visuellement que la scène est crédible (célébration → annulation) sur un échantillon de clips

**Note :** `narrative.py`, `templates.py` et `render/canvas.html` sont sous exception (`CLAUDE.md`) — exception à demander explicitement au propriétaire avant de coder. Ce sont parmi les fichiers les plus protégés du projet (moteur narratif + mécanisme de score déjà très travaillé dans `canvas.html`) — étude technique courte (TRD) recommandée avant de coder, vu la sensibilité.
