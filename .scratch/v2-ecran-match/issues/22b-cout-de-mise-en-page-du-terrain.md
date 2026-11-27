# 22b: Coût de mise en page du terrain V2 depuis l'écran en trois zones (EM-04)

**Ouvert le 27/11/2026** (décision du propriétaire, « B », à la clôture du diagnostic `22-regression-de-fluidite.md`).

**Constat (ticket 22, banc `mesures/22-banc.sh` à fenêtre égale, deuxième conteneur, ralenti × 6)** : fluidité 58,0 images/s à `41e573e`, 36,0 à `145a292` (− 38 %). La marche principale est `618c78c` (v2-ecran-match/04, écran en trois zones et responsive) : 51,9 → 40,2 images/s, environ 55 % de la perte ; le reste est diffus (caméra inclinée, 04b, 07, 21a et suite : 2 à 5 images/s chacun, proche du bruit). Au 04, le fil principal est saturé avant comme après ; le script ne coûte pas plus ; chaque mise en page (une par image) coûte deux fois plus (2,6 → 5,5 ms). `contain: strict` sur la zone terrain n'y change rien : le coût est dans la mise en page du SVG.

**What to build:**
1. **Mécanisme** : sondes dans des worktrees jetables, une variable à la fois, à partir de `618c78c` puis de l'état courant : taille de rendu du terrain (le 04 l'a agrandi), dimensionnement `w-full h-full` du `<svg>`, textes SVG (numéros, noms), éléments ajoutés au terrain par le 04 ; compteurs `Performance.getMetrics` (durée et nombre de mises en page) en plus des images par seconde.
2. **Correction** ciblée du coût, sans changer ce qui est affiché ; si le coût est inhérent à un choix d'affichage validé, proposition chiffrée au propriétaire.
3. **Mesure finale** à fenêtre égale, passages alternés avec `41e573e` sur la même machine.

**Points de vigilance (leçons du 22)** :
- Vérifier que la page s'anime pendant la fenêtre de mesure (mutations du terrain), pour chaque état mesuré.
- Ne comparer que des passages alternés sur une même machine ; noter le processeur ; un état au plafond (60 images/s) ne prouve rien.
- Trace figée : régénérer une fois (`02b2-fixture-fps.py`), noter son empreinte (`mesures/22-trace-figee.json` pour la série du 22).
- Port du serveur libre avant chaque mesure (`22-banc.sh` le vérifie).
- Réserves du 22 (acceptées par le propriétaire) : au moins 3 passages alternés par état (A1) ; archiver dans le jsonl les compteurs `getMetrics` et le contrôle d'animation de chaque état mesuré (A2) ; critère ≥ 90 % de la base repris ici (A3).

**Blocked by:** aucun.

**Bloque :** aucun.

**Estimation** (27/11/2026) : analyse (sondes) 45 min, développement 30 min, tests et mesures 45 min, intégration 30 min ; total 2 h 30 ; confiance faible (mécanisme inconnu, deux hypothèses déjà écartées au 22). Au-delà du seuil de 2 h : découpage possible en « mécanisme » et « correction » si les sondes ne concluent pas en 45 min. Temps machine à part : environ 6 états × 3 passages × 1 min 40, plus suite complète.

**Status:** à faire

## Acceptance criteria

- [ ] Mécanisme identifié par sonde, avec la part du coût de mise en page qu'il explique
- [ ] Fluidité finale ≥ 90 % de celle de `41e573e` sur le même banc et la même machine (ou écart accepté par le propriétaire sur proposition chiffrée)
- [ ] Affichage inchangé (captures avant / après sur les mêmes instants)
- [ ] `npm run build` OK, `npm run lint` sans nouvelle erreur, `npm test` vert ; suite complète au compte attendu ; V1 inchangée

## Comments
