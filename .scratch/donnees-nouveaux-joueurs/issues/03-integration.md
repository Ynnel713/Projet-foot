# 03: Intégration des nouveaux joueurs après la collecte

**Status:** à faire (bloqué par la collecte du propriétaire)

**Blocked by:** 01, 02 ; collecte `scripts/fminside_new_players.py` lancée par le propriétaire depuis son poste.

**What to build:** une fois `data/joueurs.xlsx` enrichi : `scripts/compute_moyenne_fm.py`, puis `scripts/generate_national_teams.py`, vérifications, mesures V1 avant/après, suite complète, mise à jour de l'attendu de `CLAUDE.md`.

**Estimation (travail effectif) :** analyse 15 min, développement 15 min, tests 30 min, intégration et vérifications 30 min ; total 1 h 30 ; confiance moyenne (dépend de ce que la collecte renvoie). Temps machine hors total : suite complète, série de matchs V1.

## Points à surveiller (revues des tickets 01 et 02)
- `fm_club` dans `fminside_new_players_report.csv` : joueurs d'équipes réserves (« Real Madrid Castilla », U19) rattachés à l'équipe première.
- Total réellement ajouté comparé à 2 000 (2 004 places sous le plafond de 40) ; clubs `INTROUVABLE` ou `CLUB_DIFFÉRENT` dans `fminside_new_clubs_report.csv`.
- `Tableau8` : pas de lignes vides entre l'ancienne fin et les nouvelles lignes.
- Lignes signalées « laissées vides » par `compute_moyenne_fm.py` : à traiter avant tout chargement (le chargeur V1 exige `Moyenne FM`).
- Nationalités restées en anglais (liste affichée en fin de collecte).

## Critères d'acceptation
- [ ] Aucune URL FMInside en double dans le classeur ; aucun effectif au-delà de 40 ; IDs uniques.
- [ ] Moyenne FM des 7 473 joueurs existants inchangée ; aucune ligne sans Moyenne FM.
- [ ] Chargeur V1 (`load_clubs`, `load_all_clubs`) sans erreur sur les 9 championnats.
- [ ] Mesure V1 avant/après sur le pipeline réel (graine d'audit) publiée ici.
- [ ] Suite complète passée ; attendu de `CLAUDE.md` mis à jour.
