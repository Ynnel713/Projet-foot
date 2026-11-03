# 05: Phases finales, simuler les manches une par une

**What to build:** retour du propriétaire du 02/11/2026 : « Les matchs à élimination directe doivent être simulables un par un et non les 2 en même temps. » Aujourd'hui `Simuler ce tour` joue l'aller et le retour de chaque confrontation d'un bloc (`knockout.py`, `simulate_tie`). Après ce ticket, on joue **l'aller du tour**, on le regarde, puis **le retour**. Découpé du lot 3 (changement de moteur et d'API), avis de l'architecte rendu le 03/11/2026.

**Status:** livré (03/11/2026), validé expert + QC

**Décisions du propriétaire (03/11/2026) :** « ok avec tes recommandations » → (a) à (e) tels que recommandés (une manche pour tout le tour, cumul provisoire visible après l'aller, « Simuler tout le tour » en secondaire, départage aux tirs au but inchangé, libellés proposés).

## Constat (code réel, lu par l'architecte)
- `simulate_tie` boucle `for leg_index in range(legs)` ; le nombre de manches n'est mémorisé nulle part. Après la dernière manche : agrégat, vainqueur, départage (`_resolve_tiebreak`, `_penalty_shootout_score`).
- Suspensions, blessures et forme sont déjà mises à jour manche après manche : découper ne change rien à la logique sportive.
- **Le moteur Poisson (`simulate_match`) et le 3c ne sont pas touchés**, aucun fichier protégé non plus : on coupe seulement la boucle des manches. Aucune exception nécessaire.
- Une confrontation à moitié jouée a `winner = None` : `Tie.played`, `Round.played` et `advance` (409) restent corrects sans changement.
- Le tirage utilise le `np.random` global : en gardant la boucle « confrontation par confrontation » dans `simulate_round`, le chemin « Simuler tout » reste identique à aujourd'hui.

## Décisions de conception proposées
- **Moteur** (`knockout.py`) : `simulate_tie_leg` (une manche, finalise après la dernière) ; `simulate_tie` devient une boucle dessus ; `simulate_round_leg` (une manche pour toutes les confrontations du tour ; les byes sautés) ; `simulate_round` inchangé.
- **Compétition perso** (`custom_competition.py`) : `simulate_bracket_leg()`, le nombre de manches venant de `_round_legs` (seule la finale peut différer).
- **API** : `POST /{comp_id}/bracket/simulate-leg`, sans paramètre, joue la prochaine manche de tout le tour ; 409 si le tour est fini. `simulate-round` joue toutes les manches restantes (inchangé). `BracketOut` gagne `current_legs` et `current_legs_played` (manches du tour courant, lues depuis `CustomCompetition.current_round_legs`) ; l'agrégat partiel est exposé sans vainqueur. **Écart de conception par rapport au premier jet (avis de l'architecte : `Tie.total_legs` + champs sur `TieOut`)** : le nombre de manches est connu du tour, pas de la confrontation (seule la finale diffère), donc deux champs au niveau du bracket suffisent et aucune sauvegarde ancienne n'a rien à migrer. Décision prise en implémentation ; soumise au propriétaire à la clôture.
- **UI** (`Bracket.jsx`, `client.js`) : le bouton principal de la barre d'action suit l'état du tour : « Simuler l'aller » → « Simuler le retour » → « Tour suivant → » ; « Simuler ce tour » si une seule manche. Action secondaire « Simuler tout le tour » (la `ActionBar` accepte déjà une action secondaire optionnelle). `TieCard` : confrontation à moitié jouée = aller affiché, retour en attente, vainqueur masqué.
- Le bouton d'animation d'une manche n'est actif que pour la **prochaine** manche à jouer ; un retour dont l'aller n'est pas joué est désactivé (aujourd'hui il simulait tout le tour).

## Points soumis au propriétaire (recommandation en premier)
- (a) **Grain** : **une manche pour tout le tour** (tous les allers, puis tous les retours) — recommandé : le tour est déjà l'unité du produit, aucun paramètre, aucun risque d'ordre. Alternative : confrontation par confrontation (bouton par carte), plus de code et un garde-fou « pas de retour avant l'aller », livrable après.
- (b) **Après l'aller** : afficher le score de l'aller et le cumul provisoire, masquer seulement le vainqueur — recommandé (l'aller est déjà joué donc visible). Alternative : « – – » jusqu'à la fin.
- (c) **Garder « Simuler tout le tour »** en secondaire — recommandé (parcours rapide conservé).
- (d) **Départage** : le code passe directement aux tirs au but après un cumul nul, sans prolongation jouée. Confirmer que c'est voulu (inchangé par ce ticket).
- (e) Libellés des boutons ci-dessus à valider. Aucune autre constante produit.

## Critères d'acceptation
- [x] Confrontation à 2 manches : après `simulate-leg`, `len(legs) == 1` et `winner is None` ; après le second appel, `winner` défini ; un troisième appel répond 409
- [x] `advance` répond 409 tant que le retour n'est pas joué ; `simulate-round` après l'aller termine le tour
- [x] Confrontation à 1 manche : `simulate-leg` finalise immédiatement (équivalent à `simulate-round`) ; byes sautés (`legs == []`) ; finale à `final_legs=2` avec `legs=1` ailleurs correcte
- [x] Tirs au but déclenchés à la dernière manche seulement ; suspensions et blessures de l'aller prises en compte au retour (test)
- [x] `simulate_round` / `simulate_bracket_round` gardent leur comportement : tous les tests existants passent sans modification
- [x] `BracketOut.current_legs` et `current_legs_played` exposés ; agrégat partiel sans vainqueur ; aucun champ ajouté à `Tie` (rien à migrer)
- [x] UI bureau et mobile : boutons « Simuler l'aller » / « Simuler le retour » / « Tour suivant → » selon l'état ; carte à moitié jouée correcte ; animation du retour désactivée avant l'aller ; cibles ≥ 44 px sur mobile
- [x] Parcours vérifié à l'écran : Ligue des Champions (barrages en deux manches), Coupe du Monde (manche unique), compétition perso avec finale à deux manches
- [x] `npm run build` OK ; `npm run lint` 0 erreur ; suite Python : 2 281 attendus + nouveaux tests, 0 échec (durée ~58 min)
- [x] Mise à jour de `Plan architecte Simulafoot.md` et `docs/TRD_MAJ.md` ; `docs/known_issues.md` : aucun ticket ouvert ni fermé, rien à y changer

## Hors périmètre
- Choix d'une confrontation isolée (voir a), prolongation jouée, Streamlit (`app.py` garde `simulate_bracket_round`), arbre des phases finales (lot 6).

## Comments

**03/11/2026 — implémentation et premier passage**
- Fichiers : `knockout.py`, `custom_competition.py` (`simulate_bracket_leg`, `current_round_legs`), `api/routers/competitions.py`, `schemas.py`, `serializers.py`, `ui/src/api/client.js`, `ui/src/routes/Bracket.jsx`, tests `test_knockout.py` (`TestLegByLeg`), `test_api_pitch_bracket.py`.
- Expert (passage 1) : APPROVED_WITH_RESERVATIONS (A1 écart d'API, A2 écrans et documentation non démontrés). Contrôle qualité (passage 1) : REFUSÉ (mêmes écarts + deux tests manquants). Corrigé : tests suspension aller → retour et finale à 2 manches ajoutés ; parcours vérifiés à l'écran (Ligue 1 à 2 manches, Ligue des Champions : barrages puis 8es à 2 manches, Coupe du Monde à manche unique, compétition perso avec finale à 2 manches : « Simuler ce tour » partout puis « Simuler l'aller » / « Simuler le retour » en finale, champion affiché) ; documentation à jour.

**03/11/2026 — second passage et clôture**
- Expert (passage 2) : APPROVED. Contrôle qualité (passage 2) : VALIDÉ. Clôture journalisée : VALIDÉ (expert APPROVED, QC VALIDÉ). Réserves du QC à retenir : animation par manche non vue à l'écran (drapeau LIVE à false ; retester `openLive` avec `simulateBracketLeg` à l'activation) ; écart d'API (champs au niveau du bracket) à confirmer par le propriétaire ; TRD non relu.
- Suite Python complète : 2 305 passés, 13 désélectionnés, 0 échec (1 h 13) sur l'arbre complet avant l'ajout des 2 derniers tests ; 20 passés sur les deux fichiers de tests touchés ensuite ; état exact revu (autres chantiers mis de côté) : 52 passés ; build OK, lint 0 erreur.

## À vérifier avant de coder
- `grep np.random.seed|default_rng` dans les tests bracket / LdC / Coupe du Monde / perso ; existence d'une sauvegarde disque de `CustomCompetition`.
