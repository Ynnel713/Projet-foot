# 08: Colonne « Retraite internationale »

**Status:** livré (24/11/2026), validé expert + QC

**Blocked by:** 07b (Messi et Griezmann ajoutés)

**What to build:** une colonne « Retraite internationale » dans « Infos principales » (« oui » ou vide), remplie depuis `data/retraites_internationales.csv` (ID;Joueur) par `scripts/set_international_retirement.py` ; `scripts/generate_national_teams.py` écarte ces joueurs des sélections. Ils restent jouables en club.

**Demande du propriétaire (23/11/2026) :** « rajoute un champ retraite internationale dans la base tu y mettras, Messi, Neymar, Lukaku, Cristiano Ronaldo, Griezmann, Benzema, Giroud, Dzeko, Sadio Mané ». Effet retenu (sens du nom du champ) : exclusion des sélections nationales, aucun effet en club.

**Estimation (travail effectif) :** analyse 15 min, développement 30 min, tests 25 min, vérifications 20 min ; total 1 h 30 ; confiance élevée.

## Critères d'acceptation
- [x] Colonne ajoutée à droite, `Tableau8` étendu ; « oui » pour les 9 joueurs (ID 7654 Messi, 7655 Griezmann, 2521 Neymar, 3813 Lukaku, 2679 Cristiano Ronaldo, 2610 Benzema, 1522 Giroud, 1086 Džeko, 2676 Sadio Mané), vide ailleurs ; aucune autre cellule modifiée.
- [x] Script idempotent ; ID absent du classeur signalé, rien d'inventé.
- [x] Sélections régénérées : aucun des 9 dans les onglets Europe / Afrique / Amérique ; autres joueurs inchangés hors remplaçants des 9.
- [x] Chargeurs V1 sans erreur ; tests hors ligne ; suite complète passée.

## Journal

24/11/2026 — implémenté.
- `data/retraites_internationales.csv` (9 joueurs, ID vérifiés un par un), `scripts/set_international_retirement.py` (nouveau), `scripts/generate_national_teams.py` : `_retired_ids` et exclusion dans `_players_by_nationality`.
- Application : colonne « Retraite internationale » ajoutée à droite (69 -> 70 colonnes, `Tableau8` A1:BQ8074 -> A1:BR8074), « oui » pour les 9, 0 cellule modifiée dans les colonnes existantes ; relance à vide : 0 cellule.
- Sélections régénérées : 129 pays, 91 complets (inchangé) ; aucun des 9 sélectionné. Changements : Bosnie-Herzégovine Džeko -> Imad Rondić ; Belgique Lukaku -> Alexis Saelemaekers ; Brésil Neymar -> Lucas Paquetá ; Sénégal Sadio Mané -> Ismaïla Sarr. Cristiano Ronaldo, Benzema et Giroud n'étaient déjà pas retenus (note) ; Messi et Griezmann ont la nationalité « À renseigner » : ils seront écartés dès qu'elle sera remplie.
- Tests : 4 dans `tests/test_international_retirement.py` ; suite complète 3561 passés, 14 désélectionnés.

## Comments

24/11/2026 — expert : APPROVED (empreinte 3828a80e). QC : VALIDÉ. Clôture journalisée : VALIDÉ.
- Remarques facultatives : Messi et Griezmann écartés seulement quand leur nationalité sera renseignée ; style des cellules de données de la nouvelle colonne non copié (cosmétique) ; compte attendu de `CLAUDE.md` (3 452) périmé (3 561).
- Après toute modification de `data/retraites_internationales.csv` : relancer `set_international_retirement.py` puis `generate_national_teams.py`.
- Durée : estimée 90 min, réelle environ 60 min (− 33 %) : analyse 10, développement 20, tests 15, vérifications 15. Écart > 30 % : génération des sélections déjà centralisée dans une fonction, un seul point de filtre ; un seul passage d'expert. Temps machine hors total : suite complète (18 min).
