# 04: Feuille de match V1 (destination du clic sur un match joué)

**What to build:** Lot 4 de la refonte UX/UI (direction validée le 01/11/2026 ; lot 4 avancé avant le lot 3 le 02/11/2026 : « Oui, lot 4 d'abord »). Un clic sur un match joué ouvre une feuille de match statique, dans l'espace de la compétition (onglets visibles), construite uniquement avec les données que `GET /competitions/{id}/pitch` renvoie déjà. Le live textuel et l'animation restent désactivés (`LIVE_AND_ANIMATION_ENABLED = false`).

**Status:** livré (03/11/2026), validé expert + QC

**Pourquoi avant le lot 3**
- Le lot 3 doit refaire `MatchRow.jsx`, `Groups.jsx`, `Bracket.jsx` et `Simulation.jsx`, qui portent des modifications non commitées du chantier animation. Le lot 4 n'y touche pas : ces écrans ouvrent déjà `/competition/:id/pitch?…` avec les bons paramètres.
- Depuis le lot 2, ce clic renvoie sur l'onglet d'origine (redirection de `PitchView.jsx`) : on clique, rien ne s'ouvre, et « Précédent » semble sans effet au premier appui (réserve A1 de l'expert, lot 2).

**Contenu de la feuille (données existantes de `PitchViewOut`, aucune modification d'API)**
1. **En-tête** : écussons, noms, score en `font-display`, contexte (Journée N · Groupe X, journée N · Tour N, aller/retour), formations.
2. **Faits du match** : chronologie des événements factuels du champ `live`, filtrés sur `goal`, `penalty_missed`, `yellow`, `second_yellow`, `red`, `sub` ; affichés en minute + icône + joueur(s) (morceaux `parts` marqués `player`), côté domicile à gauche, extérieur à droite. Les événements narratifs (`shot_off`, `save`, `defense`, `start`, `end`) et le texte de commentaire ne sont pas affichés (live textuel désactivé en V1).
3. **Statistiques** : possession, tirs, tirs cadrés, xG (`home_stats`/`away_stats`) ; bloc omis si absentes (club sans effectif réel).
4. **Compositions** : titulaires par équipe, rangés par ligne (G, défense, milieu, attaque selon `poste`), avec note de match, buts et cartons ; remplaçants (minute d'entrée mise en évidence), indisponibles (blessé/suspendu), entraîneur. Clic sur un joueur → fiche joueur (route existante).
5. **Erreurs** : 404 (match introuvable) et 409 (match sans effectif réel) → message clair et lien vers l'onglet d'origine, jamais l'accueil.

**Décisions de conception (dans la direction validée)**
- Route : `/competition/:id/pitch` passe sous `CompetitionLayout` (onglets visibles) ; l'onglet d'origine reste actif (déduit des paramètres, comme la redirection actuelle).
- Nouveau fichier `ui/src/routes/MatchSheet.jsx`, rendu quand le drapeau est à `false` ; `PitchView.jsx` (live + animation) reste intact pour une réactivation future, seule sa redirection devient inutile.
- Plus de bouton « Retour » (`navigate(-1)`) : les onglets et le lien de contexte suffisent ; la redirection en `replace` disparaît, donc plus de doublon d'historique.
- Mobile 375 px : une colonne (en-tête, faits, stats, compositions avec bascule Domicile / Extérieur) ; bureau ≥ 1024 px : liste domicile · terrain · liste extérieur. Listes denses à filets (pas de cartes), tokens et échelle typographique de `docs/DESIGN.md`, rien sous 11 px.

**Points soumis au propriétaire avant implémentation**
- (a) Petit terrain avec les compositions placées (`PitchField` + `x`/`y`, déjà existant) : **tranché le 02/11/2026, terrain sur bureau seulement (≥ 1024 px)**. Sur mobile, listes seules (22 noms se chevauchent à 375 px). Sur bureau, terrain vertical réutilisant `PitchField` (domicile en haut, extérieur en bas, clic sur un joueur → sa fiche), placé entre les deux listes de compositions, qui restent affichées (notes, remplaçants, indisponibles).
- (b) Couleur des notes de match (échelle /10, base `BASE_RATING`) : **tranché le 02/11/2026, chiffre neutre** (`gray-100`) en V1. Les seuils de couleur `fmTier` sont faits pour l'échelle 0-100 des attributs ; en créer pour l'échelle /10 serait une nouvelle constante produit.

**Hors périmètre (volontairement)**
- `MatchRow.jsx`, `Groups.jsx`, `Bracket.jsx`, `Simulation.jsx` (lot 3, fichiers du chantier animation).
- Live textuel, animation 2D, multiplex, alertes buts (drapeau inchangé).
- API (`journee` dans `MatchOut`, cache, persistance) : décisions en attente, non nécessaires ici.
- Fichiers interdits par `CLAUDE.md`. Seule exception Python, validée par le propriétaire le 02/11/2026 (« Oui, corrige l'API ») : `_find_match_in_bracket`.

## Critères d'acceptation

- [x] Clic sur un match joué depuis Journée (championnat), Phase de ligue / Poules et Phase finale (aller et retour) → feuille de match du bon match, onglets visibles, onglet d'origine actif — Journée mesurée à l'écran ; phase de ligue et manches aller/retour comparées à l'API (37 matchs, 0 écart) ; match retour vu à l'écran par le propriétaire le 03/11/2026 (« Vu, ça marche »)
- [x] URL `/competition/:id/pitch?…` ouverte directement (rechargement) → même feuille de match
- [x] Score et buteurs de la feuille identiques à ceux de la ligne de match cliquée (vérifié sur 5 matchs au moins, dont un avec carton rouge et un avec remplacement) — 37 matchs comparés aux événements du moteur (L1 27, LdC 6, élimination directe 4), dont 14-15 avec carton rouge et 37 avec remplacement : 0 écart
- [x] Faits : uniquement les 6 types factuels, triés par minute, côté correct ; aucun texte de commentaire affiché
- [x] Stats absentes → bloc omis sans erreur ; 404 et 409 → message + lien vers l'onglet d'origine, jamais l'accueil
- [x] « Précédent » du navigateur après ouverture d'une feuille → retour immédiat à l'onglet d'origine (un seul appui)
- [x] Mobile 375 px : aucun défilement horizontal de page, cibles ≥ 44 px, rien sous 11 px ; bureau 1440 px : compositions côte à côte, terrain entre elles, les 22 titulaires visibles et cliquables sans chevauchement de pastilles ; terrain absent sous 1024 px
- [x] Clic sur un joueur (titulaire ou remplaçant) → sa fiche joueur dans la compétition — vérifié : nom dans les faits (Bukayo Saka), titulaire (Joseph Kalulu) et remplaçant (Carlens Arcus)
- [x] `LIVE_AND_ANIMATION_ENABLED` toujours `false` ; aucun bouton LIVE ni animation visible
- [x] `npm run build` OK ; `npm run lint` : 0 erreur, 5 avertissements au plus
- [x] Suite Python complète passée (+2 tests `tests/test_api_pitch_bracket.py`) ; aucun fichier interdit par `CLAUDE.md` touché

## Comments

**02/11/2026 — implémentation**
- Fichiers : `ui/src/routes/MatchSheet.jsx` (nouveau), `ui/src/utils/matchOrigin.js` (nouveau, onglet d'origine partagé), `App.jsx` (route `pitch` imbriquée sous `CompetitionLayout` quand le drapeau est à `false`, vue plein écran conservée sinon), `CompetitionLayout.jsx` (onglet d'origine actif), `PitchView.jsx` (redirection V1 retirée, vue non routée en V1), `AppShell.jsx` (ajouté au périmètre sur demande de la revue : l'en-tête global ne disparaît plus sur `/pitch` en V1).
- Build OK ; lint 0 erreur, 5 avertissements (préexistants).
- Mesures dans la page (navigateur intégré masqué, pas de capture) : bureau 1280 px, terrain 384 × 593 px, 22 pastilles visibles, aucun chevauchement, pas de défilement horizontal ; mobile 375 px, terrain absent, bascule Domicile/Extérieur (2 × 44 px) fonctionnelle, aucune cible < 44 px, aucun texte < 11 px, pas de défilement horizontal. Clic sur Angers–Strasbourg (J1) → feuille, onglet Journée actif ; « Précédent » → Journée en un appui (historique +1) ; URL inconnue → « Match introuvable. » + lien « Journée 1 ». 5 faits « but » pour un score de 1-4.
- API (appels directs) : phase de ligue (LdC, journée 8) 200 ; tour 1 aller 200 ; match non joué 409 (message adapté : « pas encore joué ou sans effectif réel »).
- Écart constaté : le texte du fil (NLG) ne cite pas les joueurs dans un ordre fixe (un remplacement s'affichait inversé). Rôles déduits des compositions (`factPlayers`) : entrant = remplaçant entré à cette minute ; buteur = seul nom crédité d'un but ou entré avant la minute ; sinon noms sans rôle (jamais de « passe » faux).
- Revue `simulafoot-reviewer` : accepter après corrections. Corrigés : (M1) en-tête global masqué sur la feuille → `AppShell` ; (M2) inversion possible buteur/passeur → repli sans rôle ; libellé « Aller » d'un match sec (seul « Retour » est nommé) ; poste `ATT` classé en attaque ; « Suspendu » en `draw` (et non `tier-avg`, réservé aux notes) ; `role="img"` sur les marques ; `h1` masqué (équipes et score) ; doublons de noms retirés. Non traités (limites des données) : remplaçants buteurs ou avertis sans marque (`BenchPlayerOut` n'a ni buts ni cartons), pas de « sorti à X' » pour les titulaires, faits dépendant du fil NLG (un événement écarté par le NLG manquerait).
- **Défaut préexistant, décision du propriétaire en attente** : match retour de phase finale → 404. `Bracket.jsx` envoie le club qui reçoit au retour, `_find_match_in_bracket` (`api/routers/competitions.py`) cherche l'ordre du tie (domicile de l'aller). Masqué jusqu'ici par la redirection de `PitchView`. Correction proposée : accepter les deux sens dans `_find_match_in_bracket` (Python, hors périmètre de ce ticket).
- Non vérifié à l'œil : rendu visuel (captures impossibles, panneau masqué) ; feuille de LdC (phase de ligue, phase finale) à l'écran ; clic sur un joueur (route existante, non exercée) ; contrôle des 5 matchs (carton rouge, remplacement) à compléter.

**02/11/2026 — correction des matchs retour (décision du propriétaire : « Oui, corrige l'API »)**
- `api/routers/competitions.py::_find_match_in_bracket` : le tie est trouvé quel que soit le sens des deux clubs (`{t.home, t.away} == {home, away}`), donc le domicile de la manche retour envoyé par `Bracket.jsx` est accepté. Profite aussi à la route `/animation` (même recherche via `_locate_match`). Seul hunk de ce lot dans ce fichier, qui porte des modifications non commitées d'un autre chantier (préchauffage des animations) : à isoler au commit.
- Test : `tests/test_api_pitch_bracket.py` (nouveau, 2 tests, KNOCKOUT à 2 manches sur 4 clubs de Ligue 1) : retour trouvé avec son propre domicile, score identique à la manche ; aller toujours trouvé ; paire inconnue toujours 404. 2 passés.
- Non vérifié en direct : l'API de démonstration (port 8000) appartient à une autre session et n'a pas été relancée.
- Suite complète (`PYTHONHASHSEED=0 uv run pytest tests -q -p no:cacheprovider`) : 2 281 passés, 13 désélectionnés, 0 échec (39 min). Référence CLAUDE.md : 2 124 le 31/10/2026 ; l'écart vient des tests non commités d'autres chantiers présents dans l'arbre (dont `tests/test_v2engine_compensations.py`) et des 2 tests de ce lot.

**02/11/2026 — retours du propriétaire après essai à l'écran**
- Joueurs cliquables dans les faits du match (buteur, passeur, averti, entrant, sortant) → fiche joueur ; lignes de faits à 44 px sur mobile. Vérifié : clic sur « Bukayo Saka » → `/clubs/Arsenal FC/players/Bukayo Saka`.
- Milieu à 3 avec 1 MDC + 2 MC/MOC sur la même ligne : à l'affichage seulement (`withHoldingMid`), la sentinelle passe au centre (x = 50 %) et recule de 5 % vers son but ; les autres se répartissent symétriquement sur la largeur d'origine. Vérifié sur Dortmund–Arsenal (LdC, J8) : Zubimendi 50 % / 73,7 %, Rice 25 %, Guimarães 75 % (68,7 %), défense à 79,3 % ; aucune pastille chevauchée. `pitch_layout.place_starting_xi` non modifié : il fournit aussi les positions de départ de l'animation. Constante d'affichage `HOLDING_DROP = 5` validée par le propriétaire le 02/11/2026 (« Oui, 5 % »).
- Build OK, lint 0 erreur / 5 avertissements.
- Reportés hors de ce ticket : classement en un bloc sans V/N/D avec matchs à droite et sans défilement, clic buteur → fiche joueur dans la ligne de match (lot 3, `Groups.jsx`/`MatchRow.jsx`) ; simulation des manches à élimination directe une par une (moteur/API, ticket à part).

**03/11/2026 — preuves pour la validation**
- V1 (demande de l'expert) : script hors dépôt `v1_faits.py`, 37 matchs, 0 écart sur les critères (a) à (f) (buts par côté, minutes, buteurs, rouges, remplacements, noms dans l'effectif, ordre chronologique).
- V2 : suite complète sur l'état revu exact (préchauffage d'un autre chantier mis de côté pendant la revue) : 2 282 passés, 13 désélectionnés, 0 échec.
- V3 : match retour de phase finale ouvert à l'écran par le propriétaire : « Vu, ça marche ».
- Clic sur une ligne de composition (titulaire et remplaçant) : vérifié.

**03/11/2026 — passage 2 de /valider-ticket-simulafoot** (base 819e7e9, empreinte f5142b67…)
- 1er passage : expert APPROVED_WITH_RESERVATIONS (réserve A1 : match retour non vu à l'écran), QC BLOQUÉ (preuves manquantes, aucun défaut de code). Preuves apportées (V1, V2, clics, constante validée), match retour vu à l'écran par le propriétaire (« Vu, ça marche »), réserve levée par ce constat et non acceptée sans l'avoir vu.
- 2e passage : expert APPROVED, QC VALIDÉ. Facultatif : A2 champ structuré buteur/passeur et entrant/sortant dans `LiveEventOut` (supprimerait la déduction des rôles) ; A3 `Groups.jsx:88` envoie toujours `matchday = groups_matchday - 1` (lot 3). Limites connues : remplaçants buteurs ou avertis sans marque (`BenchPlayerOut` n'a ni buts ni cartons), faits dépendants du fil NLG (rejouer `v1_faits.py` si `api/nlg_live.py` évolue).
- Clôture : VALIDÉ (cloture.py decision, journal `refonte-ui/04/cloture`).
- Restent à voir en vrai avec captures : rendu visuel fin (mesures dans la page seulement).
