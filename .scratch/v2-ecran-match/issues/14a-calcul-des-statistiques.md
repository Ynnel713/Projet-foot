# EM-14a — Statistiques : calculs (V) — 60 min (moyenne)

**Status:** livré (19/11/2026), validé expert + QC (réserve A1 acceptée, correctif en `v2-attributs-restants/02a`)

Ticket parent : `14-panneau-de-statistiques.md` (découpé en 14a calculs, 14b panneau). Dépendance : EM-18 (journal des
événements envoyé pendant le calcul, livré le 19/11/2026).

## Comments

### 19/11/2026 — définitions, estimation et critères

- **Définitions validées par le propriétaire** (19/11/2026) : tirs = tous les tirs, contrés compris ; tirs cadrés = tir
  suivi d'un but ou d'un arrêt (capté, claqué, repoussé) ; corners = remises « corner » (équipe qui le tire) ; fautes =
  fautes commises (avantage compris), à l'équipe fautive ; hors-jeu = signalés contre l'équipe ; possession « dernier
  porteur » : part du temps lu où l'équipe a le ballon, un ballon sans porteur comptant pour l'équipe du dernier porteur
  (total 100 %) ; cartons : « — » tant que `v2-attributs-restants/09a` n'existe pas.
- **Lecture des événements** : un tir est cadré quand son issue (événement dont `cause` est le tir : `but` ou `arrêt`)
  est déjà lue ; un événement compte quand sa minute est ≤ au temps lu (jamais de futur, recommandation A1 de l'expert
  d'EM-18).
- **Estimation** (travail effectif) : analyse 10 min, développement 20 min, tests 20 min, clôture 10 min, **total
  1 h**, confiance moyenne. Temps machine hors total : suite complète.
- **Critères d'acceptation** : valeurs = somme des événements lus jusqu'au temps lu ; aucune valeur ne recule quand le
  temps lu avance, aucun événement futur compté (test sur trace réelle à chaque minute) ; tirs cadrés ≤ tirs, buts ≤ tirs
  cadrés ; possession domicile + extérieur = 100 % ; calcul de la possession par sommes cumulées (pas de parcours des
  images à chaque image affichée) ; `npm test`, lint 0 erreur, build OK ; suite Python 3 438 passés.

### 19/11/2026 — implémentation

- **Code** : `ui/src/utils/matchStats.js` (nouveau, sans import) : `eventStats(events, minute)` (tirs, cadrés, corners,
  fautes, hors-jeu, événements lus seulement ; un arrêt est compté pour l'équipe du tireur, via la cause) ;
  `holderTeams(ticks)` ; `possessionPrefix(teams)` (sommes cumulées « dernier porteur ») ; `possessionAt(prefix, index)`
  (entiers, total 100, null avant le premier porteur) ; `matchStats({ events, prefix, minute, tickSeconds })` (cartons :
  null). Pas encore branché à l'écran (14b).
- **Tests** : `utils/matchStats.test.js` (5 tests) sur un cas construit et sur la trace réelle réduite
  `utils/fixtures/stats-om-ol.json` (OM–OL 6-3 : 189 événements utiles, porteur des 12 480 images, 31 Ko) : définitions,
  issue pas encore lue, « jamais de futur » et valeurs qui ne reculent pas, vérifiés toutes les 15 s de match de 0' à
  104' (buts ≤ cadrés ≤ tirs, possession à 100 %), totaux de fin de match, possession « dernier porteur » ; ajoutés au
  script `npm test` (82 passés).
- **Valeurs OM–OL** : à 45' possession 59-41, tirs 13-9, cadrés 4-5, corners 2-0, fautes 2-14, hors-jeu 0-1 ; à 104'
  possession 56-44, tirs 31-19, cadrés 11-7 (9 buts + 9 arrêts), corners 3-3, fautes 12-23, hors-jeu 2-2.
- **Vérifications** : lint 0 erreur, 5 avertissements ; build OK ; suite Python 3 438 passés, 0 ignoré, 14 désélectionnés.
- **Déterminisme** : calcul pur, sans aléa ni horloge.

### 19/11/2026 — revue experte (passage 1), contrôle qualité et clôture

- Expert (empreinte `21459c73`) : **APPROVED_WITH_RESERVATIONS**. Attribution par équipe et rattachement but/arrêt → tir
  vérifiés dans le moteur ; correspondance minute → image exacte (images continues, sans trou à la mi-temps).
  - A1 [réserve] un penalty arrêté compte comme tir non cadré : le moteur n'écrit pas d'« arrêt » au journal pour un
    penalty raté (`v2engine/match.py:546-557`) ; correctif côté moteur recommandé (pas de cas particulier à l'écran).
  - A2 [facultatif] en 14b, passer la minute du moteur (pas la minute affichée) et le `tick_seconds` de la trace.
- Contrôle qualité : **VALIDÉ** (remarques : test de fin de match en partie tautologique ; conversion minute → image
  testée indirectement).
- **Réserve acceptée par le propriétaire** : « J'accepte, correctif en 02a » (19/11/2026) ; consignée dans
  `v2-attributs-restants/issues/02a-penalty.md`.
- **Décision de clôture** : VALIDÉ.
- **Durée** : estimée 1 h ; réelle environ 50 min (analyse 10, développement 15, tests 15, clôture 10), écart − 17 %.
  Temps machine hors total : suite complète (14 min 56).
