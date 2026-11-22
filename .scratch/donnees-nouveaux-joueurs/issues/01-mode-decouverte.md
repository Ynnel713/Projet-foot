# 01: Mode découverte des nouveaux joueurs dans le script de collecte

**Status:** livré (22/11/2026), validé expert + QC

**Blocked by:** —

**What to build:** `scripts/fminside_new_players.py`. Pour chaque club des 9 championnats, interroge le filtre « club » de fminside, écarte les joueurs déjà dans la base, choisit les nouveaux joueurs à tour de rôle entre les clubs (le meilleur FM restant de chaque club à chaque tour, clubs aux plus petits effectifs servis d'abord, effectif plafonné à 40) jusqu'à 2 000, puis récupère leur fiche et ajoute une ligne par joueur.

**Estimation (travail effectif) :** analyse 20 min, développement 60 min, tests 30 min, intégration et vérifications 20 min ; total 2 h 10 ; confiance moyenne. Hypothèses : le champ `club` du filtre fminside accepte le nom du club (non vérifiable hors ligne : le script le contrôle à l'exécution et s'arrête sinon). Temps machine hors total : collecte chez le propriétaire, environ 2 400 requêtes à 1 s, soit environ 1 h.

## Critères d'acceptation
- [x] Aucun joueur ajouté dont l'URL FMInside est déjà dans la base ; aucun ajouté qui ressemble à un joueur du même club dans la base (similarité de nom ≥ 0,80), ni qui porte le même nom qu'un joueur de la base avec ±1 an d'écart d'âge.
- [x] Aucun effectif au-delà de 40 joueurs ; total ajouté ≤ 2 000 ; entre deux clubs non plafonnés, les quotas diffèrent d'au plus 1.
- [x] Ordre de sélection déterministe (même entrée, même sortie).
- [x] Ligne écrite : ID nouveau et unique, Prénom/Nom (nom d'usage seul : Prénom, Nom vide, convention existante), Nationalité en français si connue, Âge = âge FM + 1, Poste au format de la base (`BU / AG`), Club et Championnat de Simulafoot, 47 attributs, URL, postes naturels, taille, weak foot. Moyenne joueur, Valeur marchande, Note transfermrkt, Statut, Catégorie et Pieds restent vides (rien d'inventé).
- [x] Le tableau Excel `Tableau8` couvre les nouvelles lignes.
- [x] Filtre club ignoré par le site (lignes renvoyées, aucune du club) : arrêt avec message clair, rien n'est écrit.
- [x] `--dry-run` : aucune fiche téléchargée, aucun fichier Excel écrit, rapport produit.
- [x] Tests hors ligne (faux client fminside, classeur en mémoire, aucun appel réseau) ; suite complète au compte attendu + nouveaux tests (3 516 passés = 3 499 + 17 : 16 du ticket 01 et 1 du ticket 02, 14 désélectionnés, 12 min 48).

## Journal

22/11/2026 — implémenté.
- `scripts/fminside_new_players.py` (nouveau) ; `scripts/scrape_fminside_attributes.py` : `FMInside.search` accepte `club` (clé de cache inchangée quand il est vide : le cache existant reste valable).
- Nom fminside de chaque club : `fminside_clubs.csv` (correction manuelle) > nom le plus fréquent dans le cache des fiches déjà reliées > nom Simulafoot.
- Contrôle du filtre : plus de 3 clubs différents dans une réponse sans aucune ligne du club -> arrêt `FilterIgnored`, rien d'écrit. 1 à 3 clubs sans correspondance -> `CLUB_DIFFÉRENT` au rapport des clubs, avec les noms vus.
- Erreur bloquante pendant les fiches (Cloudflare, cookie) : les lignes déjà ajoutées sont enregistrées, le rapport écrit ; une relance ne les réajoute pas (URL déjà dans la base).
- Mesure sur le classeur réel (hors ligne) : 174 clubs cibles, prochain ID 7 654, **2 004 places libres sous le plafond de 40**. La cible de 2 000 remplit donc presque tous les effectifs à 40 ; le total sera inférieur si fminside n'a pas assez de joueurs pour certains clubs (visible dans `fminside_new_clubs_report.csv`).
- Non vérifiable ici : le format attendu par le champ `club` du filtre fminside (robots.txt du site fermé aux agents d'Anthropic, aucune requête faite). Premier essai conseillé : `--clubs "<un club>" --dry-run`.
- Tests : 13 dans `tests/test_fminside_new_players.py`.

## Comments

22/11/2026 — passage 1 de l'expert : APPROVED_WITH_RESERVATIONS (empreinte 7601e613). QC non lancé (sous-agents un par un). Réserves corrigées plutôt que soumises à acceptation :
- A1 (cache gardant des recherches non filtrées) : `purge_club_searches` retire du cache les recherches par club quand `FilterIgnored` est levée ; les fiches et les recherches du script de base restent.
- A2 (fiche sans attributs bloquante) : nouvelle exception `ProfileUnreadable` (sous-classe de `RuntimeError`, donc toujours bloquante dans le script de base) ; le mode découverte passe au joueur suivant. Le test de fiche illisible lève désormais cette erreur réelle.
- A3 (doublon d'URL dans une exécution) : URL retenue ajoutée à l'index, une même fiche n'est prise qu'une fois (dry-run compris).
- A5 (facultatif, trous dans les ID) : poste contrôlé avant l'attribution de l'ID.
- A4 (facultatif) : non traité ; l'essai conseillé sur un club se fait sur un club moyen, et la collecte complète s'arrête avant toute écriture.
3 tests ajoutés (16 au total).

22/11/2026 — passage 2 de l'expert : APPROVED (empreinte b5d12d7f). QC : VALIDÉ. Clôture journalisée : VALIDÉ (expert APPROVED, QC VALIDÉ).
- Remarques facultatives non traitées : arrêt après N fiches illisibles consécutives (expert, passage 2, A1) ; détection du filtre ignoré sur un essai à un seul grand club (passage 1, A4).
- Durée : estimée 130 min, réelle environ 145 min (+ 12 %, sous 30 %) : analyse 25, développement 55, tests 30, intégration et vérifications 35 (dont correction des réserves A1-A3, A5). Temps machine hors total : deux suites complètes (13 min 30, 12 min 48).
