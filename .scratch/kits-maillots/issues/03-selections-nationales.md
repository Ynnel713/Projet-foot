# KM-03 — Couleurs des sélections nationales (S) — 95 min (élevée)

**Status:** livré (09/11/2026), validé expert + QC

Chantier : `.scratch/kits-maillots/spec.md`. Dépend de KM-02.

- **Objectif** : donner aux sélections leurs couleurs réelles (packs `Nations - *`).
- **Constat** : une sélection est une équipe nommée « <drapeau> <nom français> » (`ligue1sim.nations`) ; aucune n'avait
  d'entrée dans `kits.CLUB_KIT`, donc toutes étaient grises. Même table que les clubs : les compétitions internationales
  (Coupe du Monde, Compétition Perso) les colorent aussitôt, en V1 comme en V2.
- **Composants** : `scripts/extract_kit_colors.py` (129 lignes de correspondance), `src/ligue1sim/kit_colors_data.py`
  (régénéré par la commande `--module`), tests.
- **Critères** : les 129 sélections du jeu (complètes ou non) colorées, chaque fichier visé existant ; France aux couleurs
  extraites ; module régénéré à l'octet près ; couleurs des 185 clubs inchangées ; suite complète sans échec.

## Réalisé

- Correspondance nom français -> fichier anglais écrite à la main pour les 129 sélections (aucune absente des packs) ;
  les 105 autres maillots de sélections des packs (Guam, Tahiti…) n'ont pas d'équipe dans le jeu.
- Module régénéré par la vraie commande : 314 entrées (185 clubs, identiques à KM-02, + 129 sélections) ;
  `CLUB_KIT` : 341 kits. Motif « trim » pour les sélections.
- Tests : `test_every_national_team_has_its_real_colors` ; comptes des tests KM-01/KM-02 mis à jour ; la table ne vise
  que des clubs ou sélections existants.
- Planche des sélections envoyée au propriétaire (fichier local, non versionné).

## Acceptance criteria

- [x] 129 sélections du jeu colorées ; chaque fichier visé existe ; table sans doublon
- [x] France aux couleurs extraites (domicile `#233a6f`, extérieur `#bddddd`)
- [x] Module régénéré à l'octet près ; 185 clubs identiques à KM-02
- [x] Suite complète : 2 623 passés, 14 désélectionnés (34 min 38 s) = 2 622 + 1 test ajouté

## Durée

Estimée 95 min, confiance élevée. Réelle (estimée, non chronométrée) : environ 70 min (− 26 %), sous le seuil de 30 % :
aucune sélection absente des packs. Temps machine hors total : extraction 2 min, suite 35 min.

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
