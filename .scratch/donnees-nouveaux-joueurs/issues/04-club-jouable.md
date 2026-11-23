# 04: Club jouable = effectif ET composition minimale

**Status:** livré (23/11/2026), validé expert + QC

**Blocked by:** —

**What to build:** le vivier de la Compétition Perso (`clubs.list_perso_clubs`, Streamlit et API) ne retient aujourd'hui que les clubs d'au moins 18 joueurs. Le top 4 000 de fminside (ticket 05) va gonfler des clubs « Autres clubs » avec leurs seules vedettes (souvent sans gardien) : un compte de 18 ne suffit plus à dire qu'un effectif est complet. Nouvelle règle, exposée par une fonction publique réutilisée par le script de collecte : au moins 18 joueurs **et** au moins 2 gardiens, 5 défenseurs, 3 milieux et 4 attaquants (groupe du poste principal).

**Décision du propriétaire (23/11/2026) :** règle ci-dessus, seuils = plus petites valeurs observées dans les 174 clubs des 9 championnats (GK 2, DEF 5, MID 3, ATT 4). Les clubs incomplets restent dans la base (sélections nationales).

**Estimation (travail effectif) :** analyse 10 min, développement 20 min, tests 20 min, vérifications 20 min ; total 1 h 10 ; confiance élevée.

## Critères d'acceptation
- [x] `is_playable_squad` publique dans `ligue1sim.clubs` ; `list_perso_clubs` l'utilise (un seul endroit pour la règle).
- [x] Les 174 clubs des 9 championnats restent tous dans le vivier (mesuré).
- [x] Vivier avant/après sur le classeur actuel mesuré et publié ici, clubs retirés nommés.
- [x] Tests : seuil d'effectif, chaque seuil de groupe, cas limite à égalité ; suite complète passée (3 524 passés, 14 désélectionnés, arbre des tickets 04 et 05).

## Journal

23/11/2026 — implémenté.
- `src/ligue1sim/clubs.py` : `MIN_PERSO_GROUP_COUNTS`, `is_playable_squad` (publique) ; `list_perso_clubs` l'utilise.
- Mesure sur le classeur actuel : vivier de 214 clubs avant comme après, aucun retiré ni ajouté ; les 174 clubs des 9 championnats y sont. La règle ne change rien aujourd'hui ; elle compte pour les clubs que le top fminside va gonfler (ticket 05).
- Tests : `test_is_playable_squad_requires_size_and_minimum_composition`, `test_perso_pool_keeps_every_league_club` (`tests/test_clubs.py`).

## Comments

23/11/2026 — expert : APPROVED (empreinte e0b94da6). QC : VALIDÉ. Clôture journalisée : VALIDÉ.
- Remarques facultatives : le test fige 174 clubs de championnat (à mettre à jour si le classeur en gagne un) ; docstring préexistante de `tests/test_clubs.py` citant `_MIN_PERSO_SQUAD_SIZE` (hors périmètre).
- À surveiller à l'intégration du top fminside : mesurer que le vivier exclut les clubs « Autres clubs » gonflés mais incomplets, et les nommer.
- Durée : estimée 70 min, réelle environ 45 min (− 36 %) : analyse 10, développement 10, tests 15, vérifications 10. Écart > 30 % : règle courte, mesure avant/après en une commande, une seule passe d'expert. Temps machine hors total : suite complète (14 min 09, partagée avec le 05).
