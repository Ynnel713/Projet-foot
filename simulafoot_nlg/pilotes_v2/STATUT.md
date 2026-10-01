# Statut du chantier V2 éditoriale — 01/10/2026

Ce fichier existe parce qu'une session de travail a cherché les pilotes
DÉFENSE/FAUTE_SIMPLE/CORNER sur disque et ne les a pas trouvés : ils
n'avaient été livrés qu'en conversation (fichiers `_pilote_*.py` jetables,
supprimés après chaque validation), jamais committés. **Ce dossier corrige
ça** — les trois pilotes validés sont maintenant de vrais fichiers suivis
par git, avec leur statut d'audit documenté en tête de chaque fichier.

## Ce qui est déjà fait et commité (HEAD actuel, ne pas refaire)

Dans l'ordre chronologique, un commit = un sujet :

1. **`ac3bd30`** — Import de la banque réelle (281 phrases, 9 scénarios) en
   base, étiqueté "PAS livrable en production". Voir `data/seed/COUVERTURE.md`.
2. **`785d305`** — Audit de couverture des données joueur (7563 joueurs) :
   `preferred_moves` à 4,8 % à l'époque, concentré sur 35 clubs dont les
   20 de Premier League à 100 %. Voir `data/seed/AUDIT_COUVERTURE_DONNEES_JOUEUR.md`.
3. **`8b2796c`** — Fix d'un bug de non-reproductibilité dans le smoke test
   + section "VIABILITÉ DES CONDITIONS" dans COUVERTURE.md.
4. **`0100be2`** — Scoping de l'enrichissement `preferred_moves` (cible
   90 %, voir `data/seed/ENRICHISSEMENT_PREFERRED_MOVES.md`) + cascade de
   variantes DEFAUT→SURNOM formalisée dans le **docstring** de
   `engine/phrase_selector.py` (étape 7) — **aucun code exécutable**, le
   squelette lève toujours `NotImplementedError`.
5. **`fdbe739`** — Investigation "55 vs 48 moves" close : le réservoir
   canonique (`PREFERRED_MOVE_TRANSLATIONS`, `scripts/make_phrase_template.py`)
   a 55 entrées, pas 48 — 48 est juste le nombre de moves DISTINCTS
   utilisés par les 281 phrases actuelles, un sous-ensemble strict, zéro
   move inventé. Garde-fou d'import ajouté (`convert_commentary_xlsx_to_yaml.py`
   refuse un move hors des 55 connus).
6. **`c1314a0`** (HEAD) — **`height_cm` corrigé et DÉJÀ APPLIQUÉ, pas en
   attente.** `data/import/import_players.py` priorise désormais
   `"Taille FM (cm)"` sur `"Taille (cm)"` (bug de nom de colonne entre le
   scraper et l'import). Vérifié avant bascule : 91/93 et 82/84 joueurs à
   valeur sentinelle (152,4 cm/154,9 cm) récupérables côté FM26, aucune
   casse. `import-players` relancé sur la vraie base : couverture passée
   de 11,7 % à **93,4 %**. 3 tests ajoutés (`tests/test_import_players.py`).
   **Si une session te redemande de faire ce correctif ("4 lignes dans
   import_players.py et un test") : ne le refais pas, vérifie juste qu'il
   est bien là (il l'est, dans ce commit).**

   Aussi dans ce commit : note H3 dans `SPEC_ANTI_REPEAT.md` (répétition
   THÉMATIQUE, pas juste lexicale — trouvée en auditant la séquence du
   pilote DÉFENSE), et confirmation que le re-tirage du pilote DÉFENSE sur
   4 seeds (42/43/44/45) a déjà été fait : la concentration de 3 phrases
   aériennes consécutives n'apparaît que sur seed=42 (run max 1, 1, 2 sur
   les 3 autres) — **H1 "seed malheureux" déjà confirmée, pas à refaire.**

## Les 3 pilotes validés (ce dossier)

| Fichier | Scénario | Phrases | Audits passés |
|---|---|---|---|
| `defense.py` | DÉFENSE | 32 (26 DEFAUT + 6 SURNOM ; +4 neutres repli α le 01/10/2026) | n-grammes, structurel, séquence (4 seeds) |
| `faute_simple.py` | FAUTE_SIMPLE | 26 (20 DEFAUT + 6 SURNOM) | n-grammes, structurel (1 faux positif vérifié), séquence |
| `corner.py` | CORNER | 30 (24 DEFAUT + 6 SURNOM ; +4 neutres repli α le 01/10/2026) | n-grammes (2 résidus acceptés comme vocabulaire naturel), structurel, séquence |

Chaque fichier porte son propre détail d'audit en docstring de module.
L'outil réutilisable qui a servi aux trois : `scripts/audit_structure_phrases.py`
(détecteur structurel sujet/verbe/complément — calibré par test d'injection,
voir son docstring). **Ces pilotes ne sont PAS importés dans la banque
réelle** (`data/seed/scenarios.yml`, le classeur xlsx) — ce sont des
brouillons validés en attente d'intégration formelle, à faire quand
l'ensemble du Tier 1 (6 scénarios) sera couvert.

## TIER 1 CLOS (01/10/2026) — 6 pilotes, 165 phrases V2

(157 à la clôture ; +8 le 01/10/2026 : repli α, 4 phrases neutres ajoutées à DÉFENSE et à
CORNER, voir SPEC_ANTI_REPEAT.md section 6.) DÉFENSE 32, FAUTE_SIMPLE 26, CORNER 30, TIR_NON_CADRÉ 28, REMPLACEMENT 21,
CARTON_JAUNE 28 (REMPLACEMENT et CARTON_JAUNE validés par l'architecte sous
réserves traitées : calcul d'intersection de l'outil vérifié, « jaune/avertissement »
68 % → 43 %). Constat de jouabilité sur DÉFENSE/FAUTE_SIMPLE/CORNER : voir plus bas.

**Tier 2 en cours : AMBIANCE validé** (`ambiance.py`, 24 phrases DEFAUT, 4 types, pas
de SURNOM). **HORS-JEU** (`hors_jeu.py`, 24 phrases : 19 DEFAUT + 5 SURNOM) écrit — en
attente de validation. BLESSURE (dette données `status`) et MI_TEMPS_FIN_MATCH (dette
`score_display`) attendent. Un seul scénario en vol.

## Ce qui reste à faire (Tier 1, dans l'ordre déjà arbitré)

1. ~~DÉFENSE~~ ✅ ~~FAUTE_SIMPLE~~ ✅ ~~CORNER~~ ✅
2. **TIR_NON_CADRÉ** (~10/match) — pilote écrit (`tir_non_cadre.py`, 28 phrases : 22 DEFAUT + 6 SURNOM), audits n-grammes/structurel/séquence passés, `tests/test_pilote_tir_non_cadre.py` (9 tests). **En attente de validation architecte.** Jouabilité mesurée contre la base (`scripts/audit_conditions_pilote.py`) : conditions ajustées le 01/10/2026, 0 condition dominante, 0 SURNOM fantôme.
3. **REMPLACEMENT** — pilote écrit (`remplacement.py`, 21 phrases : 16 DEFAUT + 5 SURNOM), audits n-grammes/structurel/chutes/jouabilité passés, `tests/test_pilote_remplacement.py`. **En attente de validation architecte** (conventions à trancher listées en tête du fichier : conditions sur l'entrant, `score_context` non utilisé, pas de « retour de blessure »).
4. **CARTON_JAUNE** (~3-4/match) — pilote écrit (`carton_jaune.py`, 28 phrases : 22 DEFAUT + 6 SURNOM), audits n-grammes/structurel/chutes/jouabilité passés, `tests/test_pilote_carton_jaune.py`. Seuils d'`Aggression` gradués (le plan proposait ≥ 60 = 57 % des joueurs de champ) ; « Argues With Officials » écarté (18 joueurs = fantôme). **En attente de validation architecte** — dernier du Tier 1.

Puis Tier 2 (HORS-JEU, MI_TEMPS_FIN_MATCH, BLESSURE, AMBIANCE) et Tier 3
(STATISTIQUES_PÉRIODIQUES, VAR) — voir `data/seed/PLAN_V2_EDITORIAL.md`
pour les fiches complètes des 12 scénarios.

## Méthode à reproduire pour chaque nouveau scénario

1. Caractériser le registre SURNOM existant en 3 bullets (rythme,
   vocabulaire, structure) avant d'écrire le DEFAUT.
2. Écrire 20-30 phrases (DEFAUT + SURNOM), conditions sur attributs
   confirmés viables uniquement (`Aggression`, `Tackling`, `Pace`,
   `Strength`, `Technique`, `Vision`, `Heading`, `height_cm` — tous
   désormais ≥82 % de couverture réelle, voir `AUDIT_COUVERTURE_DONNEES_JOUEUR.md` ;
   `preferred_moves` en cours d'enrichissement, cible 90 %, à utiliser
   avec prudence jusqu'à confirmation).
3. Audit n-gramme (4 mots) sur toutes les paires de phrases.
4. Audit structurel (`scripts/audit_structure_phrases.py::audit`) — lit
   les faux positifs à la main avant de conclure à un vrai doublon.
5. Lecture en séquence (ordre `random.seed(42)`, joueurs réels substitués)
   — relire à voix haute, signaler les échos honnêtement plutôt que les
   maquiller.
6. Vérifier les recouvrements de conditions avec les scénarios déjà
   validés (même sens = cohérent, sens opposé sur le même attribut =
   à examiner).

## Constat de jouabilité sur les pilotes validés (01/10/2026)

Voir `pilotes_v2/ATTRIBUTS_PILOTES.md` : FAUTE_SIMPLE a 12 phrases sur 26 à
sélectivité > 50 %, DÉFENSE 3 SURNOM fantômes, CORNER 2 SURNOM fantômes
(« lutin » : 3 joueurs). Non modifiés (consigne) ; arbitrage à rendre.

## Garde-fous permanents

`tests/test_pilotes_v2_garde_fous.py` découvre automatiquement chaque `pilotes_v2/*.py` et plafonne ses collisions de 4 mots à 2 (CORNER en porte 2 réelles, tous les autres 0). Un nouveau pilote est couvert sans modifier ce fichier.

## Ce qu'on ne fait pas

- Ne pas réécrire les 281 phrases existantes.
- Ne pas démarrer deux scénarios Tier 1 en parallèle.
- Ne pas exécuter `scripts/scrape_fminside_attributes.py` ni modifier
  `data/joueurs.xlsx`.
- Ne pas coder `engine/anti_repeat.py`/`phrase_selector.py` (restent des
  squelettes `NotImplementedError` — seul leur docstring a été enrichi).
