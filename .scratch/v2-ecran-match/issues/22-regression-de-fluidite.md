# 22: Régression de fluidité de l'écran de match V2 (− 21 % depuis le ticket hauteur-ballon/01)

**Ouvert le 27/11/2026** (décision du propriétaire, « ok », à la clôture du `v2-hauteur-ballon/02b2`).

**Constat (02b2, mesure sans affichage, processeur ralenti 6 fois, même match, vitesse ×1, 30 s après 10 s de lecture ; script `.scratch/v2-hauteur-ballon/mesures/02b2-fps.js`, résultats `02b2-fps-resultats.jsonl`)** :

| État | Images par seconde |
|---|---|
| `41e573e` (base du 02b) | 59,9 |
| `f42dc68` (ticket hauteur-ballon/01) | 59,9 |
| `1923ec0` (avant le 02b) | 45,9 (4 passages alternés) |
| final du 02b2 | 47,3 (4 passages alternés) |

Le 02b ne coûte rien de mesurable ; la perte (environ − 21 %, des images de plus de 50 ms apparaissent) est entre `f42dc68` et `1923ec0` : 25 commits qui touchent l'écran (`git log f42dc68..1923ec0 -- ui/src/components/match ui/src/utils ui/src/hooks ui/src/routes/V2Match.jsx`), dont `v2-correctifs-ecran/04a-04b` (piste fine, Catmull-Rom), `v2-ecran-match/04` à `21b` (écran en trois zones, bancs, marqueurs en relief, ballon dessiné et traînée avec `<defs>` reconstruits à chaque image, filet qui ondule, HUD, frises, compositions, statistiques).

**What to build:**
1. **Bissection** sur ces 25 commits avec le même banc (réponses d'API figées, `02b2-fixture-fps.py`), 3 passages par état ; identifier le ou les commits responsables et la part de chacun.
2. **Correction** ciblée du coût (sans changer ce qui est affiché), ou, si le coût est inhérent à un choix d'affichage validé, proposition chiffrée au propriétaire.
3. Mesure finale : baisse de 10 % au plus par rapport à `41e573e` (critère du 02b2, non tenu à sa clôture).

**Blocked by:** aucun.

**Bloque :** aucun.

**Estimation** (27/11/2026) : analyse 15 min, bissection (pilotage, lecture) 30 min, correction 30 min, tests et intégration 15 min ; total 1 h 30 ; confiance faible (cause inconnue). Temps machine à part : environ 5 états × 3 passages × 50 s, plus suite complète.

**Status:** livré (27/11/2026), validé expert + QC (diagnostic seul ; critère de fluidité non tenu, réserve A3 acceptée par le propriétaire : correction au ticket `22b`)

## Acceptance criteria

- [x] Commit(s) responsable(s) identifié(s) par bissection, part de chacun chiffrée : `618c78c` (v2-ecran-match/04, écran en trois zones) − 11,7 images/s, environ 55 % de la perte ; le reste diffus, par pas de 2 à 5 images/s proches du bruit (voir Comments)
- [ ] Fluidité finale ≥ 90 % de celle de `41e573e` : **non tenu**, aucune correction dans ce ticket ; décision du propriétaire du 27/11/2026 (« B ») : mécanisme et correction reportés au ticket neuf `22b-cout-de-mise-en-page-du-terrain.md`
- [x] Affichage inchangé : aucun fichier de l'interface modifié (le correctif du 21a essayé en cours de route est annulé, voir Comments)
- [x] `npm run build`, `npm run lint`, `npm test` : sans objet, aucun fichier de `ui/` modifié ; suite complète au compte attendu (voir Comments) ; V1 inchangée

## Comments

**27/11/2026, implémentation (diagnostic).** Banc : `mesures/22-banc.sh` (un worktree détaché par état, `vite preview`, passages alternés), `mesures/22-fps.js` (copie de `02b2-fps.js` : ralenti réglable `FPS_RATE`, fenêtre de mesure identique pour tous les états), trace figée régénérée sur `145a292` et reproductible (empreintes : `mesures/22-trace-figee.json`), résultats de toutes les séries : `mesures/22-fps-resultats.jsonl` (champ `serie`, conteneur, fenêtre).
- **Le banc du 02b2 était biaisé.** Il attendait `[data-ball]` (apparu au 21a) jusqu'à 60 s avant de se rabattre sur un cercle quelconque : pour tout état d'avant le 21a, la mesure (10 s plus tard, 30 s) tombait après l'arrêt de la lecture (vers 1 min de match sur cette trace, au premier but, remise au coup d'envoi), sur une page immobile, d'où environ 60 images/s. Constaté par comptage des mutations du terrain sur 2 s (comptages **non archivés**, réserve A2) : 10 000 à 31 000 à 3 s et à 30 s pour `41e573e`, `c057086` et `6de4140`, 0 à 70 s pour les trois. Le « − 21 % depuis le ticket 01 » du 02b2 et toute bissection faite avec ce banc désignent donc le 21a à tort. `22-fps.js` attend le terrain (cercle présent) puis mesure de 10 à 40 s de lecture pour tous les états.
- **Le résultat dépend de la machine.** Premier conteneur : tous les états au plafond (58,9 à 59,7 images/s, ralenti × 6 ; 54,5 à 55,0 au ralenti × 12 ; même avec 2 ou 4 cœurs saturés), fenêtre biaisée comprise. Session reprise ensuite dans un autre conteneur (Intel Xeon 2,10 GHz, 4 cœurs) : écarts nets. Une mesure de fluidité ne vaut qu'en passages alternés, sur une même machine, en vérifiant que la page s'anime pendant la fenêtre.
- **Bissection à fenêtre égale** (deuxième conteneur, ralenti × 6, 2 passages alternés, images/s) : base `41e573e` 58,0 ; `75c2558` et `f42dc68` (caméra inclinée) 55,4 et 55,2 ; `5bd30e1`, `a2ad96b`, `9856e48`, `abd4360` 57,6, 56,5, 54,5, 56,6 ; `443e8c9` (04b) 51,9 (54,2 et 49,5) ; **`618c78c` (04) 40,2** ; `1a9a38d` 41,5 ; `00dca4c` 41,4 ; `c057086` (07) 38,0 ; série à fenêtre égale précédente : `6de4140` (21a) 37,6, `145a292` 36,0, base 58,5. Perte totale environ − 22 images/s (− 38 %) ; `618c78c` en porte − 11,7 (environ 55 %), le reste par pas de 2 à 5 images/s (caméra, 04b, 07, 21a et suite), chacun proche du bruit (même état : jusqu'à 5 images/s d'écart entre deux passages).
- **Mécanisme, partiel** (compteurs `Performance.getMetrics` sur 30 s ; chiffres avant / après le 04 **non archivés**, réserve A2 : seule la sonde `contain` est dans le jsonl, série 7) : fil principal saturé avant et après le 04 (environ 29,8 s sur 30) ; script inchangé (9,5 → 8,2 s) ; une mise en page par image avant comme après, mais chacune coûte deux fois plus (3,9 s pour 1 500 → 7,2 s pour 1 300, soit 2,6 → 5,5 ms). Sonde (worktree jetable, hors dépôt) : `contain: strict` sur la zone terrain ne change rien (6,7 → 6,6 s de mise en page) ; le coût est dans la mise en page du SVG lui-même, pas dans la grille. Pistes non vérifiées : taille de rendu du terrain (agrandi par le 04, + 150 % à 1920 × 1080), textes SVG, dimensionnement `w-full h-full` du `<svg>`.
- **Correctif du 21a essayé puis annulé** (accord du propriétaire pour le coder, sur le verdict « 21a » du banc biaisé) : `<defs>` du ballon figés (motif ancré par un groupe déplacé, traînée dans son propre repère). Sans effet à fenêtre égale (33,3 contre 36,0 pour l'état d'origine), la mise en page par image restant identique avec un ballon réduit à un cercle sans ressource. Tout le code est revenu à l'état du dépôt.
- **Fausses pistes, pour mémoire** : verdict « artefact de mesure » rendu sur le premier conteneur, puis contredit sur le second ; une série de compteurs faussée par un `vite preview` orphelin (lancé à la main) qui servait encore le port : `22-banc.sh` refuse désormais de mesurer si le port est occupé et tue le groupe de processus du serveur.
- **Décision du propriétaire du 27/11/2026** : « B » (clôture sur le diagnostic, mécanisme et correction au ticket neuf `22b`).

**27/11/2026, clôture, passage 1.** Expert : APPROVED_WITH_RESERVATIONS. QC : VALIDÉ. Clôture : VALIDÉ (réserves acceptées).
- A1 [réserve] : bissection fine à 2 passages par état au lieu de 3 ; les pas diffus de 2 à 5 images/s restent dans le bruit ; le 22b mesure en 3 passages alternés ou plus.
- A2 [réserve] : compteurs de mise en page avant / après le 04 et comptages de mutations cités mais non archivés (marqués ci-dessus) ; archivage au 22b.
- A3 [réserve] : critère de fluidité ≥ 90 % non tenu (62 %), reporté au 22b (décision « B »).
- A4, A5 [facultatif] : champ `fenetre` global aux séries 1 à 4 (le biais ne touche que les états d'avant le 21a) ; phrase de PLAN_V2 « tous les états au plafond sur processeur rapide » déduite de mesures en fenêtre biaisée. Non traités (le jsonl est un fichier revu).
- Réserves acceptées par le propriétaire : « J'accepte les 3 réserves A1, A2 et A3. »
- Durée : estimée 2 h 10 (60/30/25/15, annoncée avant le code) ; réelle environ 4 h (150/35/25/30), + 85 % ; cause au registre `docs/agents/suivi-estimations.md` (banc biaisé découvert tard, premier verdict contredit, correctif du 21a inutile, bissection refaite).

