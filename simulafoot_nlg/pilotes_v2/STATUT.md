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
| `defense.py` | DÉFENSE | 28 (22 DEFAUT + 6 SURNOM) | n-grammes, structurel, séquence (4 seeds) |
| `faute_simple.py` | FAUTE_SIMPLE | 26 (20 DEFAUT + 6 SURNOM) | n-grammes, structurel (1 faux positif vérifié), séquence |
| `corner.py` | CORNER | 26 (20 DEFAUT + 6 SURNOM) | n-grammes (2 résidus acceptés comme vocabulaire naturel), structurel, séquence |

Chaque fichier porte son propre détail d'audit en docstring de module.
L'outil réutilisable qui a servi aux trois : `scripts/audit_structure_phrases.py`
(détecteur structurel sujet/verbe/complément — calibré par test d'injection,
voir son docstring). **Ces pilotes ne sont PAS importés dans la banque
réelle** (`data/seed/scenarios.yml`, le classeur xlsx) — ce sont des
brouillons validés en attente d'intégration formelle, à faire quand
l'ensemble du Tier 1 (6 scénarios) sera couvert.

## Ce qui reste à faire (Tier 1, dans l'ordre déjà arbitré)

1. ~~DÉFENSE~~ ✅ ~~FAUTE_SIMPLE~~ ✅ ~~CORNER~~ ✅
2. **TIR_NON_CADRÉ** (prochain, fréquence ~10/match) — pas commencé.
3. **REMPLACEMENT** — pas commencé. Slots : `sortant`/`entrant` (nouveau
   patron à deux joueurs, voir `data/seed/PLAN_V2_EDITORIAL.md`).
4. **CARTON_JAUNE** (dernier du Tier 1, le plus exigeant éditorialement)
   — pas commencé.

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

## Ce qu'on ne fait pas

- Ne pas réécrire les 281 phrases existantes.
- Ne pas démarrer deux scénarios Tier 1 en parallèle.
- Ne pas exécuter `scripts/scrape_fminside_attributes.py` ni modifier
  `data/joueurs.xlsx`.
- Ne pas coder `engine/anti_repeat.py`/`phrase_selector.py` (restent des
  squelettes `NotImplementedError` — seul leur docstring a été enrichi).
