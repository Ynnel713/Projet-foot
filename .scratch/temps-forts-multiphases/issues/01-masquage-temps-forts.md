# 01: Masquage des temps forts à venir (barre de progression)

**What to build:** quand un utilisateur ouvre l'animation d'un match, la barre de progression du lecteur n'affiche plus tous les marqueurs de temps forts dès le chargement. Chaque marqueur n'apparaît qu'au moment où son temps fort commence à être lu ; un temps fort déjà visionné garde son marqueur visible si l'utilisateur revient en arrière. Le moteur, la narration et le contrat réseau (`/animation`) ne sont pas touchés — uniquement l'affichage côté lecteur (`render/canvas.html`).

**Blocked by:** None (can start immediately).

**Status:** livré (22/10/2026, `f7e9d39`) ; statut mis à jour le 04/11/2026 d'après `git log` (l'ancien statut n'avait pas été reporté)

- [x] Au lancement d'un match, aucun marqueur n'est visible au-delà du temps fort en cours ou déjà passé — vérifié visuellement (`scripts/render_player_preview.py`)
- [x] Un marqueur apparaît exactement quand son temps fort commence à être lu — idem
- [x] Revenir en arrière sur un temps fort déjà vu reste possible, son marqueur reste visible — idem
- [x] Aucune régression sur le reste du lecteur (lecture, pause, enchaînement de clips) — suite `tests/test_canvas_html.py` (35/35) + suite complète du projet (1781 passés) + revue `simulafoot-reviewer`
- [ ] Propriétaire valide qu'il ne peut pas deviner, en début de match, combien de temps forts il reste à voir — reste à valider par le propriétaire

**Note :** `render/canvas.html` est un fichier sous exception (`CLAUDE.md`) — exception accordée par le propriétaire pour ce ticket (22/10/2026).

**Correction ajoutée pendant la revue (`simulafoot-reviewer`) :** le compteur `#clipCounter` ("Clip N / Total") affichait le nombre total de temps forts dès le premier clip, ce qui contredisait le dernier critère ci-dessus. Corrigé dans le même ticket : le total ne s'affiche désormais qu'une fois le dernier clip atteint.
