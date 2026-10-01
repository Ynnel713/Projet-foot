# Spec anti_repeat.py — dette bloquante documentée (audit du 2026-09-30)

`engine/anti_repeat.py` est un squelette (`NotImplementedError` sur les 3
fonctions publiques). Ce document n'implémente rien — c'est le cahier des
charges du prochain tour, tel que demandé par l'audit éditorial de la
banque de 281 phrases. Zéro ligne ajoutée à `engine/` pendant cet audit.

## Interface attendue (déjà figée dans la docstring du squelette)

```python
def recency_penalty(conn: Connection, phrase: Phrase, player: Player, match_id: str) -> float:
    """[0, 1]. 0 = cooldown largement écoulé. 1 = cooldown pas écoulé."""

def similarity_penalty(conn: Connection, candidate_text: str, player: Player) -> float:
    """[0, 1], croissante avec la similarité au texte le plus proche déjà vu."""

def update_cooldown(conn: Connection, phrase: Phrase, player: Player, match_id: str, rendered_text: str) -> None:
    """Enregistre l'usage après rendu (template_filler + post_process)."""
```

Ces trois signatures ne sont **pas** en cause — elles correspondent au
schéma existant (`phrase_history`, `phrase_cooldowns`,
`similarity_signatures`, voir `data/schema.sql`). Le blocage n'est pas
l'interface, c'est l'état des données qu'elle suppose disponible.

## Trois décisions d'architecture non tranchées (bloquantes, pas des détails)

### 1. "Matchs écoulés" n'existe nulle part dans le schéma
`phrase_history.used_at` est un timestamp (`datetime('now')`), pas un
compteur de matchs. Il n'y a **aucune table `matches`** qui séquence les
`match_id` dans l'ordre chronologique par joueur/compétition — `match_id`
est un simple `TEXT` libre partout (`phrase_history`, `MatchContext`).

`recency_penalty` ne peut donc pas répondre à "combien de matchs se sont
écoulés depuis le dernier usage" sans qu'une des deux décisions suivantes
soit prise :
- **(a)** ajouter une table `matches(id, played_at, journee, ...)` et
  joindre `phrase_history.match_id` dessus pour dériver un rang ;
- **(b)** faire porter ce calcul à l'appelant (le moteur de simulation, qui
  connaît déjà l'ordre des matchs) et lui faire passer un compteur explicite
  (`matches_since: int`) en plus de `match_id`, au prix d'un changement de
  signature de `recency_penalty`.

C'est exactement le doute que le squelette documentait déjà ("a definir :
soit un compteur de matchs explicite... soit derive de match_id via une
table de matchs a venir") — cet audit confirme qu'aucune des deux n'a
depuis été tranchée, ni dans le schéma ni dans le code.

### 2. `phrase_cooldowns` est vide pour les 281 phrases — le cooldown obligatoire n'a pas de source
Le format YAML (`scenarios.yml`) n'a **aucun champ cooldown** par phrase, et
`scripts/import_seed.py` ne peuple `phrase_cooldowns` nulle part (recherche
confirmée : zéro occurrence de "cooldown" dans ce script). Or le README est
explicite : *"phrase_selector.select devra refuser toute phrase sans ligne
dans phrase_cooldowns, ou dont cooldown_matches est NULL"*.

Conséquence concrète : si `phrase_selector`/`anti_repeat` étaient branchés
aujourd'hui sur la banque telle qu'importée, **les 281 phrases seraient
refusées**, sans exception — le refus binaire (cooldown non défini)
intervient AVANT toute pénalité continue de `recency_penalty`. Il faut
décider :
- **(a)** ajouter un champ `cooldown_matches` par phrase dans le format
  YAML/xlsx (donc modifier `scripts/convert_commentary_xlsx_to_yaml.py` et
  le classeur source), ou
- **(b)** une valeur par défaut globale documentée (ex. "3 matchs pour
  toute phrase sans valeur explicite") appliquée au moment de l'import.

Sans cette décision, tester `anti_repeat` sur la banque réelle est
impossible : il n'y a rien à pénaliser progressivement, tout est refusé en
amont.

### 3. `similarity_penalty` a besoin d'un texte qui n'existe pas encore
Le schéma est clair : `similarity_signatures.signature` correspond au texte
de `phrase_history.rendered_text`, c'est-à-dire le texte **après**
`template_filler.render` et `post_process.apply` — deux squelettes
également non implémentés. Calculer une signature MinHash/k-shingles sur
les *gabarits bruts* (avant substitution des `{slot_name}`) serait un proxy
différent de ce que le schéma documente : deux gabarits identiques rendus
pour deux joueurs différents produisent des textes différents (noms
distincts) mais la même signature de gabarit, ce qui sous-estimerait la
diversité perçue par un spectateur. À l'inverse, ignorer ce proxy revient à
attendre l'implémentation de `template_filler`/`post_process` avant de
pouvoir tester quoi que ce soit ici.

### 4. `similarity_penalty` doit couvrir la répétition THÉMATIQUE, pas seulement lexicale (ajouté le 01/10/2026)

Trouvé en auditant la séquence du pilote DÉFENSE (28 phrases, voir
`data/seed/PLAN_V2_EDITORIAL.md`) : sur un tirage aléatoire donné, 3
phrases à thème "duel aérien"/tête se sont retrouvées consécutives alors
qu'aucune ne partageait le moindre n-gramme de texte avec une autre (zéro
collision lexicale, vérifié mécaniquement). Un `similarity_penalty` basé
sur une signature MinHash/k-shingles du texte rendu (voir point 3
ci-dessus) ne détecterait PAS ce cas : les textes sont lexicalement
distincts, seul le THÈME narratif (ici : "contact aérien") se répète.

Implication pour l'implémentation future : `similarity_penalty` (ou un
mécanisme complémentaire à spécifier) devra pouvoir comparer les
candidats sur un axe thématique/tag (ex. un tag "aérien" porté par la
Phrase ou dérivé de ses conditions `Heading`/`height_cm`), pas uniquement
sur la similarité textuelle du rendu. Piste à creuser à l'implémentation
réelle, pas tranchée ici : soit un tag explicite par phrase (colonne
`tags`/`phrase_tags`, déjà présente dans le schéma mais actuellement
libre et non structurée), soit une heuristique dérivée des attributs
conditionnants communs entre phrases d'un même scénario.

## Ce qui N'est PAS bloquant (déjà en place)
- Le schéma SQL (`phrase_history`, `phrase_cooldowns`,
  `similarity_signatures`) est cohérent avec l'algorithme documenté dans le
  squelette — pas de refonte de schéma nécessaire, seulement les décisions
  1 et 2 ci-dessus.
- `engine/db.py` fournit déjà les connexions SQLite (WAL, FK).
- Les 281 phrases donnent une base de gabarits suffisante pour mesurer la
  diversité structurelle *en amont* (voir Audit 2 du rapport principal) —
  ce n'est pas une mesure d'anti-répétition en usage réel, mais un signal
  de risque : un scénario à faible diversité de gabarits (ex. COUP_FRANC,
  35 % de signatures jumelles) produira mécaniquement plus de collisions
  perçues même avec un `anti_repeat` parfait, simplement parce que le pool
  de départ est plus petit.

## Séquencement proposé pour le prochain tour
1. Trancher les décisions 1 et 2 ci-dessus (architecture, pas code).
2. Implémenter `template_filler.render` + `post_process.apply` (prérequis
   factuel : sans texte rendu réel, `similarity_penalty` n'a rien à
   comparer).
3. Implémenter `phrase_selector.select` (consommateur direct
   d'`anti_repeat`).
4. Implémenter `anti_repeat.*` pour de vrai, avec les tests que
   `tests/test_anti_repeat.py` ne fait aujourd'hui que documenter en creux
   (contrat `NotImplementedError`).
5. Alors seulement : rejouer un match simulé (90 minutes, ~25 tirs, ~12
   corners, ~3 buts) pour mesurer répétitions exactes et structurelles sous
   5 minutes d'écart, comme demandé par l'audit initial — impossible avant
   les étapes 1 à 4.

**Verdict : dette bloquante, spec livrée, aucune implémentation ce tour.**
