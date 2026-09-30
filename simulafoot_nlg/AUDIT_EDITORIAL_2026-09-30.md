# Audit éditorial de la banque de phrases — 2026-09-30

Périmètre : 281 phrases / 9 scénarios / 12 variantes, `data/seed/scenarios.yml`,
avant `import-seed`. Décision de portée validée avant ce tour : audits 1, 2, 3, 6
complets ; 4 et 5 en mode statique rigoureux (sans `template_filler.render`, qui
n'existe pas) ; 7 en dette bloquante documentée (voir `SPEC_ANTI_REPEAT.md`).
Zéro ligne ajoutée dans `engine/`. Script support : `scripts/audit_editorial_banque.py`
(hors moteur, ne remplace aucun squelette).

## Verdict global par scénario

| Scénario | n | Verdict | Raison principale |
|---|---|---|---|
| CARTON_ROUGE | 31 | **Importable** | Fluide, conditions cohérentes (agressivité/preferred_moves alignées au texte) |
| BUT | 60 | **Importable** | 3 variantes fluides ; PENALTY internement cohérente ; 1 phrase à corriger (pied droit non conditionné, voir Audit 5) |
| PENALTY_RATE | 15 | **Importable** | Fluide, pas de condition complexe |
| COUP_FRANC | 20 | **À corriger** | 35 % de signatures syntaxiques jumelles (Audit 2), au-dessus du seuil de 30 % fixé par le brief |
| CONSTRUCTION | 20 | **Importable** | Fluide, diversité correcte (10 % signatures jumelles) |
| ARRET_GARDIEN | 38 | **Importable** | Fluide, conditions cohérentes (taille/force pour les arrêts "physiques") |
| SITUATION_MATCH | 30 | **Importable** | Fluide, diversité correcte |
| DEBUT_MATCH | 30 | **Importable** | Fluide, bonne diversité (63 % 1er-mot-partagé, le plus bas du lot) |
| GESTE_SIGNATURE/SURNOM | 7 | **Importable** | Le meilleur lot de l'audit : concis, vivant, aucune trace "IA" |
| **GESTE_SIGNATURE/DEFAUT** | 30 | **À corriger avant import** | 25/30 phrases (83 %) suivent un moule à 2 clauses systématique, la 2e clause lisant comme un commentaire de scout écrit, pas de la commentaire live — voir Audit 6 |

**Pas d'import-seed tant que 1, 4 et 5 ne sont pas propres (contrainte du brief)** :
1 est propre (0 % cassée, 1,1 % à retravailler, sous le seuil de 5 %). 4 est propre
en mécanique isolée mais expose une dépendance réelle non résolue
(`post_process.apply`, squelette). 5 est propre sur les 22 phrases à conditions
multiples, mais révèle 1 défaut concret hors de ce filtre (voir plus bas). Donc :
**import possible pour 8 des 9 scénarios une fois GESTE_SIGNATURE/DEFAUT corrigé
et la phrase BUT/DEFAUT #6 (pied droit) amendée.**

---

## Audit 1 — Fluidité (échantillon seedé, `random.seed(42)`, 10/scénario, 90 phrases)

Méthode : `rng = random.Random(42)`, échantillonnage par scénario dans l'ordre
du YAML (reproductible — voir `scripts/audit_editorial_banque.py::audit1`).
Lecture à voix haute mentale, verdict par phrase. Liste brute complète dans
`scripts/_audit1_out.txt`.

**Résultat : 0/90 cassée (0 %), 1/90 à retravailler (1,1 %)** — largement sous le
seuil de 5 % fixé par le brief. Pas d'arrêt nécessaire.

La seule phrase à retravailler :

> `[14] BUT/DEFAUT :: {joueur} envoie un missile du pied droit : la barre
> transversale tremble encore avant que le ballon ne finisse au fond des
> filets !`

Séquence ambiguë à l'oral : on ne sait pas si le tir touche la barre avant de
rentrer (auquel cas ce n'est plus un tir direct au fond des filets, incohérent
avec "envoie un missile... au fond des filets") ou si "la barre tremble" est une
image hyperbolique de la puissance du tir sans contact réel. Proposition de
réécriture :

> `{joueur} envoie un missile du pied droit qui ne laisse aucune chance au
> gardien, la barre transversale semble vibrer sous l'impact !`
> — lève l'ambiguïté en indiquant explicitement que le tremblement est un
> effet de l'impact du but, pas un rebond sur la barre.

Toutes les autres phrases échantillonnées sont grammaticalement correctes et
sonnent naturelles à l'oral. Voir Audit 6 pour un problème distinct
(authenticité, pas fluidité) sur GESTE_SIGNATURE/DEFAUT.

---

## Audit 2 — Variété intra-scénario

Méthode (limite assumée, documentée en tête de script) : deux mesures
automatiques faute de parseur syntaxique dans ce dépôt —
**(a)** 1er mot après retrait des slots, **(b)** signature = 4 premiers mots
après retrait slots/ponctuation. Une signature partagée par ≥ 2 phrases prouve
un moule identique ; l'inverse n'est pas garanti (deux signatures différentes
peuvent quand même partager une structure plus profonde — voir la découverte
manuelle sur GESTE_SIGNATURE ci-dessous, qui échappe totalement à cette
heuristique).

| Scénario | n | 1er mot partagé | Signature 4-mots partagée |
|---|---|---|---|
| CARTON_ROUGE | 31 | 74,2 % | 0,0 % |
| BUT | 60 | 78,3 % | 0,0 % |
| PENALTY_RATE | 15 | 100,0 % | 13,3 % |
| **COUP_FRANC** | 20 | 85,0 % | **35,0 %** ⚠ |
| CONSTRUCTION | 20 | 80,0 % | 10,0 % |
| ARRET_GARDIEN | 38 | 78,9 % | 0,0 % |
| SITUATION_MATCH | 30 | 86,7 % | 6,7 % |
| DEBUT_MATCH | 30 | 63,3 % | 0,0 % |
| GESTE_SIGNATURE | 37 | 94,6 % | 0,0 % (heuristique aveugle, voir ci-dessous) |

**COUP_FRANC dépasse le seuil de 30 %** fixé par le brief : 5 phrases sur 20
commencent par "sur ce coup franc" mot pour mot (ex. #33, #34), et 2 par
"{passeur} centre le coup". Signal réel de redondance perçue à l'usage (même
scénario, joueurs différents à chaque fois, mais l'amorce ne change pas assez).
Recommandation : reformuler au moins 3 des 5 phrases "sur ce coup franc" pour
varier l'amorce (ex. déplacer l'info sur la position du coup franc en fin de
phrase, ou démarrer par l'action du passeur).

**Découverte manuelle hors heuristique — GESTE_SIGNATURE/DEFAUT** : l'heuristique
4-mots ne capte rien (0,0 %) parce que la PREMIÈRE clause varie bien d'une
phrase à l'autre. Mais un second passage ciblé (regex sur la 2e phrase de
chaque gabarit) montre que **25 des 30 phrases DEFAUT (83,3 %) ont une seconde
phrase qui commence par un déterminant + nom abstrait** ("Une habitude...",
"Cette discipline...", "Une alchimie...", "Cette mobilité...", "Ce sang-froid...").
C'est une redondance de *moule* bien plus sévère que ce que l'heuristique
automatique peut voir avec 4 mots seulement — je le signale explicitement pour
ne pas donner un faux sentiment de sécurité au 0,0 % affiché dans le tableau.
Voir Audit 6 pour le détail et la recommandation.

---

## Audit 3 — Cohérence inter-variantes (scénario BUT, 60 phrases)

Méthode : dump complet des 3 variantes (DEFAUT 30, PENALTY 15, SURNOM 15),
classement manuel action-par-action. Sortie complète : `scripts/_audit3_out.txt`.

**Mise en garde méthodologique (honnêteté demandée par le brief)** : le test tel
que formulé ("les variantes doivent sonner comme des prises différentes du même
événement") suppose que chaque variante EST une re-narration du même instant.
Ce n'est pas le design réel de BUT : DEFAUT est un pool générique couvrant tout
type de but (tir, tête, volée, coup franc, dribble...), PENALTY est spécifique
aux penalties, SURNOM est organisé par archétype de joueur (pas par type de
but). Le test "même action racontée autrement" s'applique donc proprement à
**PENALTY seule** (15 phrases, toutes effectivement des penalties, aucune
intruse) ; l'appliquer à DEFAUT/SURNOM produirait un faux positif systématique
puisque l'hétérogénéité y est voulue. Je le signale plutôt que de forcer un
verdict qui ne voudrait rien dire.

- **PENALTY (15 phrases)** : cohérent. Aucune phrase ne décrit une action
  incompatible avec un penalty (pas de frappe lointaine perdue dans le lot).
  **Importable.**
- **DEFAUT (30) et SURNOM (15)** : pas d'incohérence FACTUELLE relevée (aucune
  phrase ne contredit son propre scénario BUT), mais le test de "cohérence
  inter-variantes" tel que spécifié ne s'applique pas à leur design. **Importable,
  avec cette réserve documentée plutôt qu'un verdict par défaut.**

---

## Audit 4 — Substitution de slots (mécanique isolée, PAS `template_filler.render` réel)

**Avertissement obligatoire (répété du brief) : ce qui suit ne teste PAS
l'intégration `template_filler` réelle — la fonction lève `NotImplementedError`,
squelette. Seule la mécanique de substitution + élision, réécrite dans
`scripts/audit_editorial_banque.py::substituer_slots_dans_audit`, est testée
ici, isolément.**

Slots réellement utilisés dans la banque (aucun `dictionary_key`, `slots.yml`
est vide — tout passe par `expression`) :

| Slot | Expression | Occurrences |
|---|---|---|
| `joueur` | `player.full_name` | 159 |
| `adversaire` | `context.opponent_team` | 102 |
| `club` | `context.player_team` | 65 |
| `receveur` | `context.receveur.full_name` | 38 |
| `passeur` | `context.passeur.full_name` | 35 |
| `minute` | `context.minute` | 1 |

20 cas limites de noms testés (voir `scripts/_audit4_out.txt` pour le détail
complet) : nom 3/20 lettres, composé, apostrophe (`N'Golo Kanté`, `O'Brien`),
particule (`De Bruyne`, `van der Berg`, `Di Maria`), initiale voyelle/h muet/h
aspiré, tiret, majuscule accentuée. **Résultat : substitution + élision OK sur
les 20 cas** avec une règle simple (voyelle/h → élision).

**Fragilité réelle mise en évidence, pas juste théorique** : la banque contient
**91 occurrences du patron `"de {slot}"`** (`de {adversaire}` ×61, `de {club}`
×16, `de {joueur}` ×6, `de {receveur}` ×6, `de {passeur}` ×2). Le module
responsable de l'élision dans le pipeline réel n'est **pas** `template_filler`
mais `post_process.apply` — **également un squelette non implémenté**
(`engine/post_process.py`). Sans lui, un club ou un joueur dont le nom
commence par une voyelle (`Arsenal`, `Inter`, `Ajax`, `Everton`, `Olympique de
Marseille`...) produira littéralement "de Arsenal" à l'écran/à l'oral au lieu
de "d'Arsenal" — faute de grammaire visible dès la 1ʳᵉ utilisation en
production.

Second point de fragilité, documenté aussi dans la docstring de
`post_process.py` elle-même : les "h aspirés" à la française ne s'appliquent
pas de la même façon aux noms propres anglophones/néerlandais couramment
prononcés avec le H sonore par les commentateurs français (ex. "Harry Kane" se
dit souvent "de Harry Kane", pas "d'Harry Kane", par convention orale, malgré
la règle graphique classique). Une simple règle voyelle/h ne suffira pas — il
faudra une table d'exceptions, comme `post_process.py` le prévoit déjà en
commentaire.

**Verdict Audit 4 : mécanique de base saine, mais dépend d'un squelette non
implémenté (`post_process.apply`) pour être correcte en production sur les 91
occurrences "de {slot}" de la banque actuelle. Dette identifiée, pas
bloquante pour l'import de la banque elle-même (le texte source est correct,
c'est le rendu futur qui est à risque).**

---

## Audit 5 — Combinaisons condition × phrase (inspection statique, `evaluate_condition` réel)

**Avertissement obligatoire : inspection statique, pas de génération
dynamique de phrase.** `conditions.py` est réellement implémenté (89 tests,
99,62 % couverture) — utilisé tel quel, sans contournement.

22 phrases ont ≥ 2 atomes de condition (conjonction "et"). Les 22 ont été
inspectées une par une (liste complète dans le rapport de session, dump dans
`scripts/audit_editorial_banque.py::audit5`) : hauteur/tête (`height_cm` +
`Heading`), vitesse/sprint (`Pace` + `minute`), technique/dribble
(`Technique`/`Dribbling`), force/coup-franc (`Strength` +
`preferred_moves`), agressivité/tacle (`Aggression` + `preferred_moves`).
**Vérification mécanique** (`evaluate_condition` contre un contexte qui
satisfait tout et un qui échoue tout) : **0 anomalie sur 22** — aucune
condition ne plante, aucune logique inversée.

**Verdict sens football sur les 22 : aucune incohérence trouvée.** Les
conditions physiques citées correspondent bien au contenu narratif (un
"colosse" qui marque de la tête est bien conditionné sur `height_cm >= 190`,
un "feu follet" qui slalome est bien conditionné sur `height_cm <= 170`, etc.)
— design solide sur ce sous-ensemble.

**Défaut réel trouvé HORS de ce filtre** (1 seule condition, pas 2+, donc
invisible si on s'était limité strictement aux "conditions complexes") :

> BUT/DEFAUT : *"{joueur} envoie un missile du pied droit : la barre
> transversale tremble encore..."*
> Condition unique : `preferred_moves contient "Shoots With Power"`.

Aucune condition sur `foot` (pied fort) ni `weak_foot` (qualité du pied
faible) : un joueur gaucher pur (`foot="Left"`, `weak_foot` bas) peut
déclencher cette phrase, qui affirme pourtant un tir du pied droit — exactement
le type de non-sens football cité en exemple dans le brief
("weak_foot=5 mais le joueur n'a pas de pied gauche"). Comparaison utile :
BUT/SURNOM *"Ambidextre redoutable..."* conditionne correctement sur
`weak_foot >= 4` avant de mentionner le pied "qu'on n'attendait pas" — la
banque sait faire, cette phrase précise a juste été oubliée.

**Correction proposée** : ajouter une condition `foot == "Right"` (ou
`weak_foot <= 2`, à trancher selon la sémantique voulue : "il est droitier" vs
"son pied faible est trop faible pour qu'on lui prête un tir puissant du
gauche") à cette phrase avant import.

---

## Audit 6 — Authenticité commentateur

Relecture des 90 phrases de l'Audit 1, critère : "pourrait sortir de la bouche
de Margotton ou Genin en direct" vs "sonne écriture rédigée/analytique".

**Résultat sur 8 scénarios/9 (CARTON_ROUGE, BUT, PENALTY_RATE, CONSTRUCTION,
ARRET_GARDIEN, SITUATION_MATCH, DEBUT_MATCH, GESTE_SIGNATURE/SURNOM) : aucune
phrase flaguée.** Le vocabulaire est correct (pressing, contre, second poteau,
retournée, Panenka, etc.), les images restent orales, pas de métaphore
générique creuse ni d'adjectifs empilés façon IA.

**GESTE_SIGNATURE/DEFAUT (30 phrases) : problème systémique, pas ponctuel.**
Les 30 phrases suivent un moule identique en 2 clauses :
1. Description factuelle d'une action/habitude du joueur (correcte,
   spécifique, bien écrite isolément) ;
2. Une seconde phrase analytique qui commence quasi-systématiquement par
   un déterminant + nom abstrait — **25/30 (83,3 %)**, vérifié
   mécaniquement (regex `\.\s+(Une?|Ce|Cette)\s+\w+`) : "Une habitude qui le
   rend...", "Cette discipline défensive qui limite...", "Une alchimie
   particulière semble s'installer...", "Cette mobilité horizontale
   constante complique...", "Ce sang-froid sous pression rassure...".

Aucun commentateur en direct ne prononce ce genre de deuxième clause
pendant un match — c'est le registre du rapport de scout écrit ou de
l'analyse d'après-match, pas du commentaire live. C'est très exactement le
"texte de scout" que la maquette visuelle vous a fait exclure par ailleurs
(fiche joueur) : le même biais rédactionnel s'est glissé ici, dans un
scénario qui est censé être de la commentaire live.

**Contre-exemple instructif dans le même scénario** : GESTE_SIGNATURE/SURNOM
(7 phrases) est au contraire le meilleur lot de tout l'audit — concis, une
seule clause, exclamatif, vivant :
> *"Le feu follet slalome dans des espaces minuscules où personne d'autre ne
> pourrait se faufiler !"*

**Recommandation concrète** : ne pas réécrire les 30 phrases DEFAUT une par
une — couper systématiquement la seconde clause analytique et ne garder que
la première (factuelle, déjà bonne), à la manière du style SURNOM. Exemple
sur la phrase #5 :
- Avant : *"{joueur} multiplie les appuis et les contrôles supplémentaires
  pour ramener systématiquement le ballon sur son pied fort, quitte à perdre
  un temps précieux face à la pression de {adversaire}. Une habitude qui le
  rend parfois prévisible, mais rarement prise en défaut sur la qualité
  d'exécution."*
- Après : *"{joueur} multiplie les appuis et les contrôles supplémentaires
  pour ramener systématiquement le ballon sur son pied fort, quitte à perdre
  un temps précieux face à la pression de {adversaire} !"*

**Verdict : GESTE_SIGNATURE/DEFAUT à corriger avant import (dette non
documentable en l'état — le seuil "au feeling" ne s'applique pas ici, la
mesure est mécanique à 83,3 %).**

---

## Audit 7 — Anti-répétition

Dette bloquante documentée intégralement dans `SPEC_ANTI_REPEAT.md` : 3
décisions d'architecture non tranchées (notion de "matchs écoulés" absente du
schéma, `phrase_cooldowns` vide pour les 281 phrases — donc refus systématique
si branché tel quel, `similarity_penalty` dépendante d'un texte rendu qui
n'existe pas). Aucune implémentation ce tour, conformément à la décision de
portée.

---

## Synthèse des actions avant import-seed

| Action | Bloquant pour import ? |
|---|---|
| Réécrire BUT/DEFAUT #6 (pied droit → ajouter condition `foot`/`weak_foot`) | Oui (Audit 5) |
| Couper la 2e clause analytique des 30 phrases GESTE_SIGNATURE/DEFAUT | Oui (Audit 6, systémique) |
| Reformuler 3-5 phrases COUP_FRANC pour varier l'amorce "sur ce coup franc" | Non, dette documentée acceptable (Audit 2) |
| Clarifier BUT/DEFAUT #14 (barre transversale, ambiguïté oral) | Non, dette documentée acceptable (Audit 1) |
| Décider format `cooldown_matches` par phrase + table `matches` | Non pour l'import de la banque, mais bloquant pour tout usage réel ensuite (Audit 7) |
| Implémenter `post_process.apply` (élision) avant mise en prod du rendu | Non pour l'import, bloquant avant tout affichage réel (Audit 4) |
