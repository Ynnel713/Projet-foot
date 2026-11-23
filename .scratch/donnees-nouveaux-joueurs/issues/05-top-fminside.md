# 05: Mode « top N » : les 4 000 premiers joueurs de fminside (extraction vers un Excel séparé)

**Status:** livré (23/11/2026), validé expert + QC

**Blocked by:** 04 (règle « club jouable » réutilisée pour le rapport)

**What to build:** `scripts/fminside_new_players.py --top 4000`. Lit les N premières lignes de la liste fminside (hommes, ordre par défaut du site, pages de 50) et ajoute ceux qui manquent au classeur, dans l'ordre du site : dans leur club s'il existe déjà (n'importe quel championnat), sinon dans un club créé en « Autres clubs » sous son nom FM ; sans club -> « Sans club ». Mêmes exclusions et même plafond de 40 que le ticket 01. Rapports `fminside_top_players_report.csv` et `fminside_top_clubs_report.csv` ; ce dernier classe chaque club « Autres clubs » touché (ou déjà jouable) en complet (jouable, `clubs.is_playable_squad`) ou incomplet (sélections nationales seulement), avec sa composition GK/DEF/MID/ATT.

**Décisions du propriétaire (23/11/2026) :** ordre par défaut du site ; clubs absents rangés en « Autres clubs » (« ils serviront principalement à alimenter les équipes nationales, par contre dans Autres clubs il est important de distinguer les effectifs complets donc jouables des incomplets ») ; plafond de 40 maintenu.

**Estimation (travail effectif) :** analyse 15 min, développement 50 min, tests 30 min, vérifications 20 min ; total 1 h 55 ; confiance moyenne. Hypothèses : l'ordre par défaut et la pagination « loadmore » au-delà de 500 lignes (le script de base s'arrêtait à 10 pages) ne sont pas vérifiables hors ligne ; la lecture s'arrête si une page n'apporte aucune fiche nouvelle. Temps machine hors total : collecte chez le propriétaire, 80 pages + une fiche par joueur ajouté (au plus 4 000 requêtes, environ 1 h 30 à 1 s).

## Critères d'acceptation
- [x] `FMInside.top(n)` : au plus n lignes, sans doublon, mises en cache ; arrêt si une page n'apporte rien de nouveau.
- [x] Rattachement : nom identique normalisé, nom fminside appris du cache, puis similarité ≥ 0,8 avec les seuls clubs du classeur ; club d'un championnat préféré à une ligne isolée d'« Autres clubs » ; club inconnu créé en « Autres clubs » et retrouvé seulement sous son nom FM exact.
- [x] Exclusions et plafond identiques au ticket 01 (déjà présent, fiche en double, 40 max : `CLUB_PLEIN` au rapport).
- [x] Rapport des clubs « Autres clubs » : complet / incomplet selon la règle du ticket 04, composition, nouveau club ou non ; en dry-run, composition prévue d'après les postes de la liste.
- [x] Dry-run : ni fiche téléchargée, ni classeur écrit.
- [x] Mode « par club » (ticket 01) inchangé : ses 16 tests passent sans modification, ajout de ligne factorisé dans `RowWriter`.
- [x] `--top N --extract-only` (option B du propriétaire, 23/11/2026) : écrit `data/fminside_top<N>.xlsx` (feuille « Top fminside » : rang, statut de la fiche, URL, nom, club, nationalité FM et française, âge FM, postes, poste au format du classeur, note FM, taille, weak foot, preferred moves, 47 attributs), dans l'ordre du site ; `joueurs.xlsx` n'est ni lu pour écriture ni modifié ; fiche illisible -> ligne sans attributs ; erreur bloquante -> lignes déjà lues écrites, message de relance (reprise par le cache) ; cinq premiers noms affichés pour contrôler l'ordre.
- [x] Tests hors ligne ; suite complète passée (3532 passés après correction des réserves = 3 518 après le 04 + 14 du 05, 14 désélectionnés).

## Journal

23/11/2026 — implémenté.
- `scripts/scrape_fminside_attributes.py` : `FMInside.top(n)`. `scripts/fminside_new_players.py` : `RowWriter` (ajout commun aux deux modes, extrait de `discover`), `read_all_clubs`, `ClubResolver`, `squad_groups`, `discover_top`, option `--top`, rapports `fminside_top_*`.
- Mesure hors ligne sur le classeur réel (faux client, dry-run) : 4 000 lignes simulées = 3 000 joueurs de la base (URL et club réels) + 1 000 inconnus répartis sur 400 clubs inconnus -> 3 000 DÉJÀ_PRÉSENT, 1 000 PRÉVU, 400 nouveaux clubs incomplets, 40 clubs « Autres clubs » complets (ceux déjà jouables), 5,6 s.
- Défaut trouvé par cette mesure et corrigé avant la revue : la comparaison approchée incluait les clubs créés pendant l'exécution (deux clubs FM voisins, Al Ahli / Al Ahly, auraient été fusionnés). Test `test_top_deux_clubs_inconnus_aux_noms_voisins_restent_distincts`.
- Limite connue : `norm_club` ignore les nombres et les mots génériques ; « Real Madrid Castilla » est rattaché au Real Madrid (déjà relevé au ticket 01, à surveiller au ticket 03 via `fm_club`).
- Tests : 6 ajoutés (22 dans `tests/test_fminside_new_players.py`).

23/11/2026 — mis en pause sur décision du propriétaire (« sinon j'extrais les données dans un excel et on fera la fusion proprement ensuite »). Le code (mode `--top`, `RowWriter`, `ClubResolver`, rapport complet/incomplet, 6 tests ; suite complète passée à 3 524 sur l'arbre 04 + 05) est conservé dans `.scratch/donnees-nouveaux-joueurs/05-top-fminside.patch` (`git apply` depuis la racine, vérifié sur `873a305`). Suite prévue : réorienter vers une fusion depuis l'Excel du propriétaire (source = fichier au lieu de `FMInside.top`), en réutilisant rattachement au club, exclusions, plafond et rapport ; à réestimer quand un extrait du fichier est disponible.

23/11/2026 — repris sur décision du propriétaire (« option B, prépare le script ») : le patch est réappliqué (fichier d'archive supprimé), et l'extraction seule est ajoutée : `extract_row`, `extract_top`, `write_extract`, options `--extract-only` et `--out`. La fusion depuis ce fichier fera l'objet du ticket 06.
- Estimation de la reprise : analyse 10 min, développement 40 min, tests 25 min, vérifications 20 min ; total 1 h 35 ; confiance moyenne (ordre et pagination du site non vérifiables hors ligne).
- Tests : 4 ajoutés (26 dans `tests/test_fminside_new_players.py`), dont un essai de bout en bout de la commande qui vérifie que `joueurs.xlsx` reste identique octet pour octet.

## Comments

23/11/2026 — passage 1 de l'expert : APPROVED_WITH_RESERVATIONS (empreinte 487b4857). Réserves corrigées plutôt que soumises à acceptation :
- A1 (erreur de fiche inattendue, HTTPError en 404 : extraction perdue) : `extract_top` traite toute exception autre que `RuntimeError` comme une fiche illisible (ligne sans attributs), comme `RowWriter.add`.
- A2 (liste tronquée gardée en cache, message « relance » en boucle) : `FMInside.top` ne met en cache qu'une liste complète ; la commande distingue « la liste du site s'arrête à X joueurs » d'une extraction interrompue (`extract_top` renvoie aussi le nombre listé).
- A3 (facultatif, plafond sous-compté) : effectif d'un club compté sur toutes ses lignes, tous championnats confondus.
- A4 (facultatif, caractères de contrôle) : retirés avant l'écriture de l'Excel.
4 tests ajoutés (30 au total), 2 adaptés (signature d'`extract_top`, effectif du club en double).

23/11/2026 — passage 2 de l'expert : APPROVED (empreinte beefc4f4). QC : VALIDÉ. Clôture journalisée : VALIDÉ.
- Remarque facultative non traitée : une erreur HTTP non bloquante pendant la lecture de la liste (avant toute fiche) sort avec une trace Python au lieu d'un message « ARRÊT » ; rien n'est perdu.
- À contrôler à la première collecte chez le propriétaire : les 5 premiers noms affichés (ordre du site), une liste qui dépasse 500 lignes, essai `--top 50 --extract-only` avant 4 000.
- Durée (code initial du 23/11 + reprise en extraction) : estimée 115 + 95 = 210 min, réelle environ 205 min (− 2 %) : analyse 25, développement 85, tests 50, vérifications 45 (dont la correction des réserves A1-A4 et la mise en pause). Temps machine hors total : trois suites complètes (14 min chacune).
