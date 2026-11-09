# EM-02 — Couleurs de maillot dans l'API (D) — 60 min (élevée)

**Status:** livré (09/11/2026), validé expert + QC

Chantier : `.scratch/v2-ecran-match/spec.md` (audit, direction artistique, décisions).

- **Objectif** : fournir à l'écran `primary` et `secondary` de chaque club du match.
- **Problème** : la V2 n'a aucune couleur de club (`/api/v2/lineup` n'en donne pas).
- **Résultat** : `LineupOut` gagne `color` et `secondary` (via `kits.CLUB_KIT`, lecture seule) ; clubs sans kit : gris du kit
  par défaut, repéré par un indicateur `known_kit`.
- **Périmètre** : sérialisation ; ni moteur ni données joueurs.
- **Composants** : `api/routers/v2.py` (`LineupOut`, `numbered_lineup`), `tests/`.
- **Critères** : PSG renvoie ses deux couleurs ; club inconnu renvoie le défaut et `known_kit=false` ; route existante
  inchangée pour les autres champs.
- **Tests** : tests `pytest` de la route (club connu, club sans kit, 404).
- **Dépendances** : aucune. **Risques** : nul pour le moteur ; la suite complète dure environ 40 min (temps machine).

## Réalisé

- `src/ligue1sim/kits.py` : fonction publique `kit_for(club)` (kit du club, ou le kit par défaut gris) ; rien d'autre ne
  change (règle « API publique seulement » : `api/` n'importe pas `_DEFAULT_KIT`). Aucune constante nouvelle.
- `api/routers/v2.py` : `LineupOut` gagne `color` (principale), `secondary` et `known_kit` (`club in CLUB_KIT`),
  remplis par `numbered_lineup`. Autres champs et 404 inchangés.
- `tests/test_v2engine_trace.py` : 2 tests (PSG : `#0a1a4a` / `#da1a35` / `known_kit` vrai, couleurs remplacées le 09/11/2026 par les extraites `#293657` / `#7d2537`, mêmes clés qu'avant plus les
  trois couleurs ; club sans kit : `#6b7280` / `#d1d5db` / faux). Le 404 reste couvert par
  `test_lineup_route_rejects_unknown_club`.
- Constat : 656 des 816 clubs des données n'ont pas de kit dédié (gris par défaut) ; c'est l'indicateur `known_kit` qui
  permettra à EM-03 de les traiter à part.
- Pour EM-03 : les traces du banc EM-00 ont été enregistrées avant ce ticket, leurs feuilles de match n'ont pas ces trois
  champs ; ne pas réenregistrer les traces (réserve A1 d'EM-00) mais prévoir le repli dans l'écran.

## Acceptance criteria

- [x] PSG renvoie ses deux couleurs (`#0a1a4a`, `#da1a35`) et `known_kit=true`
  - Remplacé par la décision du propriétaire du 09/11/2026 (« Tout extraire », ticket `kits-maillots/02`) : le PSG
    renvoie désormais ses couleurs extraites `#293657` / `#7d2537` (réserve A2 de l'expert).
- [x] Club sans kit : `#6b7280`, `#d1d5db`, `known_kit=false`
- [x] Route inchangée pour les autres champs ; 404 conservé
- [x] Suite complète : 2 613 passés, 14 désélectionnés (43 min 07 s, 09/11/2026) = 2 611 d'avant (dont +1 du 06c en cours,
  hors ticket) + 2 tests ajoutés ; aucun échec

## Durée

Estimée 60 min (analyse 10, développement 15, tests 15, intégration 20), confiance élevée. Réelle (estimée, non
chronométrée) : environ 55 min (analyse 15, développement 10, tests 15, intégration 15), − 8 %. Temps machine hors
total : suite complète 43 min.

## Comments

- 09/11/2026, revue commune `kits-maillots/01-03+v2-ecran-match/02` (EM-02, KM-01, KM-02, KM-03) :
  - passage 1 : expert **REJECTED** (A1 bloquant : `match_kit_colors` laissait deux équipes de la même couleur en V1 pour
    les maillots unis, ex. Arsenal / Manchester United) ; QC VALIDÉ ; clôture REFUSÉ.
  - correctifs A1 à A5 appliqués par délégation du propriétaire (« Considère que je valide automatiquement toutes tes
    recommandations et celles des experts », 05/11/2026) : repli sur le vrai maillot extérieur en cas de clash, critère
    EM-02 annoté, test du module indépendant des fins de ligne, docstring, import de Pillow local.
  - passage 2 : expert APPROVED ; QC **REFUSÉ** (import de Pillow placé après `Image.new` dans `contact_sheet`).
  - passage 3 : expert **APPROVED** (A1 facultatif : archives ouvertes par `contact_sheet` jamais fermées) ; QC
    **VALIDÉ** ; clôture **VALIDÉ** (empreinte `1878931e…b827`, base `5bd30e1`). Suite : 2 626 passés, 14 désélectionnés.
