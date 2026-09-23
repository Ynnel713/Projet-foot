# Inventaire des durées et structures des 12 gabarits

Source unique : [`src/ligue1sim/animation/templates.py`](../src/ligue1sim/animation/templates.py) (numéros de ligne donnés
pour la déclaration du `Template` et pour le wrapper `build_xxx`). Aucun code
modifié — document d'inventaire uniquement, produit pour calibrer les durées
du lecteur de clips du résumé narratif (voir brief du 23/09/2026).

Convention utilisée pour ce document :

- **Segment** : intervalle entre deux `t_ratio` consécutifs, dans l'ordre où
  ils apparaissent dans le gabarit.
- **Tag physique** : valeur de `Template.physics_tags` attachée au `t_ratio`
  de DÉBUT du segment (`pass_ground`, `shot`, `cross`, `deflect`, `pass_lob`
  — ou `aucun` si ce `t_ratio` n'apparaît pas dans `physics_tags`, auquel cas
  `animation.ball.ball_state_at` retombe sur une inférence par défaut,
  hors scope de cet inventaire).
- **Phase de construction** : segment(s), avant le DERNIER segment (celui qui
  mène à `t_ratio=1.0`, l'action décisive), où le ballon change de porteur
  entre deux joueurs NOMMÉS et DISTINCTS (`ball_owner` change de rôle). Un
  porteur qui garde le ballon en dribble solitaire, ou un rôle unique du
  début à la fin, ne compte PAS comme une phase de construction au sens de
  ce document (aucune circulation entre plusieurs joueurs).

Aucun des 12 gabarits n'utilise le tag `pass_lob` aujourd'hui (seuls
`pass_ground`, `cross`, `deflect` et `shot` apparaissent dans
`physics_tags`) — à noter pour la calibration, ce n'est pas une omission de
cet inventaire.

## Convention de classification (`Verdict`, tranchée le 23/09/2026, Tâche 1)

Deux règles distinctes, appliquées dans cet ordre, à TOUS les gabarits sans
exception — le nombre de passes n'entre JAMAIS en jeu, seule la durée compte :

1. **Seuil d'existence (`direct` vs le reste)** : une phase de construction
   existe dès qu'AU MOINS UN changement de porteur entre deux rôles distincts
   (ou vers un ballon disputé, `ball_owner=None`) survient avant le segment
   décisif — qu'il s'agisse d'une seule passe isolée ou de plusieurs. Une
   seule passe COMPTE donc comme construction (ce n'est pas le nombre de
   passes qui est discriminant, voir point 3) : durée de construction = 0 s
   → `direct` ; durée de construction > 0 s → `mixte` ou `construit` selon
   le point 2.
2. **Seuil de poids (`mixte` vs `construit`)** : parmi les gabarits qui
   passent le seuil d'existence, `construit` si la durée de construction
   représente STRICTEMENT PLUS de 50 % de la durée totale (la construction
   domine le clip), `mixte` sinon (construction minoritaire ou exactement à
   50 %, cas limite tranché du côté `mixte` — voir `une_deux` ci-dessous).
3. **Pourquoi la durée et pas le nombre de passes** : une seule passe peut
   porter une vraie construction si elle est précédée d'un long temps de
   circulation/portage avant d'être jouée (ex. `construction_placee` :
   `support1` porte et circule 4,2 s avant de céder le ballon, une seule
   passe mais 60 % de la durée totale) — inversement, une seule passe peut
   être quasi instantanée (ex. `decalage_enroulee`, `assist` statique cède
   le ballon dès le départ). Compter les passes plutôt que leur poids aurait
   classé ces deux gabarits de façon identique alors qu'ils ne se
   ressemblent pas visuellement ; la durée est le signal directement
   pertinent pour calibrer un player vidéo, pas le nombre d'événements.

**Application à `profondeur_1v1`** : sa phase de construction existe (1,8 s,
une passe `assist` → `scorer` avant le 1v1 conclu au tir) donc passe le
seuil d'existence (point 1) — mais elle ne pèse que 30 % de la durée totale
(1,8 s / 6,0 s), sous le seuil de 50 % du point 2 → **`mixte`, pas `direct`**
(verdict inchangé par rapport à la première version de cet inventaire).

**Correction entraînée par l'application stricte de cette convention** :
`recuperation_haute` passait à tort pour `mixte` dans la première version de
ce document (jugement qualitatif, "pressing plutôt que possession organisée")
— sa durée de construction (2,75 s / 5,0 s = 55 %) dépasse pourtant
strictement le seuil de 50 % du point 2. Appliquée sans exception, la
convention le reclasse en **`construit`** (voir tableau Synthèse corrigé
ci-dessous). Aucune autre ligne du tableau Synthèse ne change : les 10
autres verdicts, recalculés avec cette même règle, tombent tous du même côté
qu'avant (voir le detail par gabarit ci-dessus, section durée
construction/durée totale).

---

## 1. contre_attaque (ligne 527, builder ligne 825)

- Durée totale : **8.0 s**
- Keyframes : 3 (`t_ratio` = 0.0, 0.4, 1.0)
- Segments : 2

| Segment | Durée | Tag physique | Description (3 mots) |
|---|---|---|---|
| 0.0 → 0.4 | 3.2 s | aucun | course balle conduite |
| 0.4 → 1.0 | 4.8 s | shot | passe puis frappe |

- Phase de construction : **Oui** — 3.2 s (segment 1 : `support1` récupère
  et conduit le ballon, passe à `assist` exactement au keyframe t=0.4).
- Le segment décisif (0.4 → 1.0, tag `shot`) contient LUI-MÊME un second
  relais (`assist` → `scorer`) avant le tir : la construction réelle est
  donc courte et le tir est amorcé par une passe imbriquée dans le même
  segment, cohérent avec le nom du gabarit (contre-attaque = rapide).

## 2. construction_placee (ligne 560, builder ligne 829)

- Durée totale : **14.0 s**
- Keyframes : 4 (0.0, 0.3, 0.6, 1.0)
- Segments : 3

| Segment | Durée | Tag physique | Description (3 mots) |
|---|---|---|---|
| 0.0 → 0.3 | 4.2 s | aucun | récupération circulation ballon |
| 0.3 → 0.6 | 4.2 s | aucun | passe en profondeur |
| 0.6 → 1.0 | 5.6 s | shot | remise puis frappe |

- Phase de construction : **Oui** — 8.4 s (segments 1+2 : `support1` porte
  le ballon puis le cède à `assist` avant le dernier tiers).
- C'est le gabarit le plus long et le seul dont la phase de construction
  dépasse l'action décisive en durée (60 % / 40 %) — cohérent avec son nom.

## 3. debordement_centre_tete (ligne 581, builder ligne 833)

- Durée totale : **6.0 s**
- Keyframes : 3 (0.0, 0.6, 1.0)
- Segments : 2

| Segment | Durée | Tag physique | Description (3 mots) |
|---|---|---|---|
| 0.0 → 0.6 | 3.6 s | aucun | débordement aile solitaire |
| 0.6 → 1.0 | 2.4 s | shot | centre puis tête |

- Phase de construction : **Non** — seul `assist` porte le ballon de 0.0 à
  0.6 (dribble solitaire sur le côté), aucun autre rôle ne le touche avant
  le centre. Ce qui manque : le gabarit commence directement par le
  débordement de `assist`, pas de relais depuis le milieu/la défense avant
  que le porteur n'entame sa course — pour en avoir une il faudrait un rôle
  supplémentaire (ex. un `support1` qui joue `assist` en profondeur avant
  le débordement), ce qui touche à la structure des rôles du gabarit.

## 4. percee_individuelle (ligne 596, builder ligne 837)

- Durée totale : **7.0 s**
- Keyframes : 4 (0.0, 0.4, 0.75, 1.0)
- Segments : 3
- Un seul rôle déclaré (`scorer`) — gabarit solo par construction.

| Segment | Durée | Tag physique | Description (3 mots) |
|---|---|---|---|
| 0.0 → 0.4 | 2.8 s | aucun | contrôle balle initial |
| 0.4 → 0.75 | 2.45 s | aucun | dribble progression solitaire |
| 0.75 → 1.0 | 1.75 s | shot | frappe au but |

- Phase de construction : **Non** — un seul rôle (`scorer`) existe dans le
  gabarit, aucune circulation entre joueurs n'est possible par construction.
  Ce qui manque : il faudrait introduire un ou plusieurs rôles supplémentaires
  (passeurs/appuis) avant le dribble pour qu'une phase de construction ait un
  sens — mais cela contredirait le concept même de "percée individuelle"
  (action solo assumée).

## 5. une_deux (ligne 607, builder ligne 841)

- Durée totale : **4.0 s**
- Keyframes : 3 (0.0, 0.5, 1.0)
- Segments : 2

| Segment | Durée | Tag physique | Description (3 mots) |
|---|---|---|---|
| 0.0 → 0.5 | 2.0 s | aucun | passe initiale sol |
| 0.5 → 1.0 | 2.0 s | shot | remise puis frappe |

- Phase de construction : **Oui** — 2.0 s (segment 1 : `scorer` donne le
  ballon à `assist`). Très courte (50 % de la durée totale, 2.0 s), cohérente
  avec la nature du une-deux (échange bref, pas une construction étendue).

## 6. coup_franc (ligne 621, builder ligne 845)

- Durée totale : **5.0 s**
- Keyframes : 3 (0.0, 0.7, 1.0)
- Segments : 2
- `starts_at_restart=True` — le tireur démarre déjà en position (progress=0.8
  dès t=0), pas à sa position de formation. Un seul rôle (`scorer`).

| Segment | Durée | Tag physique | Description (3 mots) |
|---|---|---|---|
| 0.0 → 0.7 | 3.5 s | aucun | placement avant frappe |
| 0.7 → 1.0 | 1.5 s | shot | frappe coup franc |

- Phase de construction : **Non** — un seul rôle (`scorer`), action arrêtée
  (`starts_at_restart`). Ce qui manque : par nature un coup franc direct n'a
  pas de circulation de balle entre joueurs avant la frappe — non applicable
  ici, pas un manque à corriger.

## 7. corner (ligne 636, builder ligne 849)

- Durée totale : **7.0 s**
- Keyframes : 4 (0.0, 0.3, 0.6, 1.0)
- Segments : 3
- 3 rôles (`assist`, `support1`, `scorer`) — enrichi le 23/09/2026 (2→3 rôles,
  3→4 keyframes, voir commentaire ligne 637).

| Segment | Durée | Tag physique | Description (3 mots) |
|---|---|---|---|
| 0.0 → 0.3 | 2.1 s | pass_ground | marche vers corner |
| 0.3 → 0.6 | 2.1 s | cross | centre en cloche |
| 0.6 → 1.0 | 2.8 s | deflect | ballon disputé tête |

- Phase de construction : **Oui** — 4.2 s (segments 1+2 : `assist` porte le
  ballon au point de corner pendant que `support1`/`scorer` font leurs appels,
  puis centre). Action décisive = le duel aérien contesté (`ball_owner=None`
  à t=0.6, résolu en tête de `scorer` à t=1.0).

## 8. profondeur_1v1 (ligne 672, builder ligne 853)

- Durée totale : **6.0 s**
- Keyframes : 3 (0.0, 0.3, 1.0)
- Segments : 2

| Segment | Durée | Tag physique | Description (3 mots) |
|---|---|---|---|
| 0.0 → 0.3 | 1.8 s | aucun | appel puis passe |
| 0.3 → 1.0 | 4.2 s | shot | 1v1 face gardien |

- Phase de construction : **Oui, mais courte** — 1.8 s (segment 1 : `assist`
  joue `scorer` en profondeur). Une seule passe avant un long segment décisif
  solo (le 1v1 conclu au tir, 4.2 s).

## 9. recuperation_haute (ligne 691, builder ligne 857)

- Durée totale : **5.0 s**
- Keyframes : 4 (0.0, 0.3, 0.55, 1.0)
- Segments : 3
- 3 rôles (`support1`, `support2`, `scorer`) — enrichi le 23/09/2026
  (1 rôle/2 keyframes → 3 rôles/4 keyframes, voir commentaire ligne 692).

| Segment | Durée | Tag physique | Description (3 mots) |
|---|---|---|---|
| 0.0 → 0.3 | 1.5 s | aucun | pressing haut collectif |
| 0.3 → 0.55 | 1.25 s | deflect | ballon disputé pressing |
| 0.55 → 1.0 | 2.25 s | shot | récupération relais frappe |

- Phase de construction : **Oui, de type pressing** — 2.75 s (segments 1+2 :
  `support1`/`support2` pressent, le ballon devient disputé — `ball_owner=None`
  à t=0.3 — puis `support1` le récupère). Ce n'est pas une circulation de
  possession organisée mais une séquence de pressing collectif avant la
  récupération, comptée ici comme construction au sens large de "plusieurs
  joueurs impliqués avant l'action décisive".

## 10. decalage_enroulee (ligne 728, builder ligne 879)

- Durée totale : **6.0 s**
- Keyframes : 3 (0.0, 0.4, 1.0)
- Segments : 2
- Seul gabarit à poster-traiter le spin du tir (`_DECALAGE_ENROULEE_SHOT_SPIN_RAD_S`,
  ligne 876) sur la keyframe `physics_tag == "shot"`.

| Segment | Durée | Tag physique | Description (3 mots) |
|---|---|---|---|
| 0.0 → 0.4 | 2.4 s | aucun | décalage passe statique |
| 0.4 → 1.0 | 3.6 s | shot | frappe enroulée |

- Phase de construction : **Oui, minimale** — 2.4 s (segment 1 : `assist`,
  statique — `ANCHOR_STATIC` — cède le ballon à `scorer`). Une seule passe,
  pas de mouvement du passeur ; le reste (3.6 s) est un contrôle + frappe
  enroulée en solo.

## 11. penalty (ligne 742, builder ligne 888)

- Durée totale : **4.0 s**
- Keyframes : 4 (0.0, 0.5, 0.85, 1.0)
- Segments : 3
- `starts_at_restart=True`. 3 rôles (`support1`, `support2`, `scorer`) mais
  seul `scorer` touche jamais le ballon (`support1`/`support2` : simple pas
  de côté via `ANCHOR_LATERAL_SHIFT`, ne portent jamais le ballon).

| Segment | Durée | Tag physique | Description (3 mots) |
|---|---|---|---|
| 0.0 → 0.5 | 2.0 s | aucun | placement avant penalty |
| 0.5 → 0.85 | 1.4 s | aucun | attente coéquipiers piétinent |
| 0.85 → 1.0 | 0.6 s | shot | élan puis frappe |

- Phase de construction : **Non** — `scorer` est seul porteur du ballon du
  début à la fin, action arrêtée. Ce qui manque : par nature un penalty n'a
  pas de circulation de balle entre joueurs — non applicable, pas un manque
  à corriger.

## 12. but_gag (ligne 777, builder ligne 892)

- Durée totale : **5.0 s**
- Keyframes : 4 (0.0, 0.35, 0.65, 1.0)
- Segments : 3
- 3 rôles (`support1`, `support2`, `scorer`) — enrichi le 23/09/2026 (2
  rôles/3 keyframes → 3 rôles/4 keyframes, voir commentaire ligne 778).

| Segment | Durée | Tag physique | Description (3 mots) |
|---|---|---|---|
| 0.0 → 0.35 | 1.75 s | aucun | centre première déviation |
| 0.35 → 0.65 | 1.5 s | aucun | rebond second contact |
| 0.65 → 1.0 | 1.75 s | shot | rebond final but |

- Phase de construction : **Oui, chaotique** — 3.25 s (segments 1+2 : le
  ballon passe de `scorer` à `support1` puis à `support2`, deux déviations
  successives avant le but). Type "double rebond" plutôt que possession
  organisée, mais correspond bien à une circulation entre plusieurs joueurs
  avant l'action décisive.

---

## Synthèse

Trié par durée totale croissante.

| Gabarit | Durée totale | Durée construction | Durée action décisive | Verdict |
|---|---|---|---|---|
| une_deux | 4.0 s | 2.0 s | 2.0 s | mixte |
| penalty | 4.0 s | 0.0 s | 0.6 s | direct |
| coup_franc | 5.0 s | 0.0 s | 1.5 s | direct |
| recuperation_haute | 5.0 s | 2.75 s | 2.25 s | construit |
| but_gag | 5.0 s | 3.25 s | 1.75 s | construit |
| debordement_centre_tete | 6.0 s | 0.0 s | 2.4 s | direct |
| decalage_enroulee | 6.0 s | 2.4 s | 3.6 s | mixte |
| profondeur_1v1 | 6.0 s | 1.8 s | 4.2 s | mixte |
| percee_individuelle | 7.0 s | 0.0 s | 1.75 s | direct |
| corner | 7.0 s | 4.2 s | 2.8 s | construit |
| contre_attaque | 8.0 s | 3.2 s | 4.8 s | mixte |
| construction_placee | 14.0 s | 8.4 s | 5.6 s | construit |

Répartition des verdicts (convention ci-dessus, section "Convention de
classification") : 4 `construit` (construction_placee, corner, but_gag,
recuperation_haute), 4 `mixte` (contre_attaque, une_deux, profondeur_1v1,
decalage_enroulee), 4 `direct` (debordement_centre_tete, percee_individuelle,
coup_franc, penalty).

Sur les 4 gabarits `direct` : 3 le sont par conception assumée (solo ou
action arrêtée — percee_individuelle, coup_franc, penalty) et 1 seul
(debordement_centre_tete) pourrait bénéficier d'une vraie phase de
construction sans contredire son concept.

---

## Recommandations

Pour chaque gabarit : une durée cible pour le player canvas (basée sur la
durée totale actuelle du gabarit, qui régit déjà la physique du ballon via
`Keyframe.t = t_ratio * template.duration`) et si un enrichissement
(ajout d'une phase de construction) serait nécessaire pour l'atteindre.

| Gabarit | Durée cible clip | Enrichissement nécessaire ? |
|---|---|---|
| une_deux | 4.0 s (durée actuelle) | Non — la brièveté est la nature du geste (échange à une touche), l'allonger contredirait le concept. |
| penalty | 4.0 s (durée actuelle) | Non — court par nature (action arrêtée, brief du 23/09/2026 le confirme explicitement pour les penaltys), et solo par conception. |
| coup_franc | 5.0 s (durée actuelle) | Non — court par nature (action arrêtée, brief du 23/09/2026 le confirme explicitement pour les coups francs), solo par conception. |
| recuperation_haute | 5.0 s (durée actuelle) | Non — la brièveté sert le concept de transition rapide après pressing ("immédiate", voir commentaire ligne 698). |
| but_gag | 5.0 s (durée actuelle) | Non — déjà enrichi le 23/09/2026 (double contact), la construction chaotique existante suffit. |
| debordement_centre_tete | 6.0 s (durée actuelle) | Oui, potentiellement — un relais avant le débordement donnerait une vraie phase de construction, mais nécessite d'ajouter un rôle/keyframe au gabarit (`templates.py`) : **escaladé, pas corrigé ici** (règle d'escalade du brief). |
| decalage_enroulee | 6.0 s (durée actuelle) | Optionnel — un relais supplémentaire avant le décalage enrichirait la mise en scène, mais nécessite un rôle intermédiaire dans `templates.py` : **escaladé, pas corrigé ici** si jugé prioritaire. |
| profondeur_1v1 | 6.0 s (durée actuelle) | Optionnel — une phase de construction avant l'appel en profondeur serait un plus visuel, mais nécessite un rôle supplémentaire dans `templates.py` : **escaladé, pas corrigé ici** si jugé prioritaire. |
| percee_individuelle | 7.0 s (durée actuelle) | Non — solo par conception (percée "individuelle"), une construction contredirait le nom du gabarit. |
| corner | 7.0 s (durée actuelle) | Non — déjà enrichi le 23/09/2026 (3 rôles, phase de préparation explicite), la construction actuelle suffit. |
| contre_attaque | 8.0 s (durée actuelle) | Non — une construction longue contredirait le concept de contre-attaque (rapidité), la structure actuelle (1 passe puis relais+tir) est cohérente. |
| construction_placee | 14.0 s (durée actuelle) | Non — déjà le gabarit modèle pour une construction lente et étendue (60 % de la durée), rien à enrichir. |

**Lecture globale pour le calibrage du player** : les durées actuelles des
gabarits suivent déjà la logique attendue par le brief ("court pour les
coups francs et penaltys, plus long pour les actions construites") —
`penalty` (4.0 s) et `coup_franc` (5.0 s) sont parmi les plus courts,
`construction_placee` (14.0 s) est de loin le plus long et le seul dont la
phase de construction dépasse l'action décisive. Réutiliser directement
`Template.duration` comme durée cible du clip narratif pour les 12 gabarits
semble donc défendable sans modification de `templates.py` — voir points
d'escalade ci-dessus pour les 3 gabarits où un enrichissement futur serait
possible mais optionnel.

## Points d'escalade

1. **debordement_centre_tete** n'a aucune phase de construction (dribble
   solitaire de `assist` puis centre direct) alors que son concept
   (débordement + centre + tête) s'y prêterait bien. En ajouter une
   nécessiterait un rôle supplémentaire dans `templates.py` — non fait ici,
   signalé seulement (règle d'escalade du brief).
2. **profondeur_1v1** et **decalage_enroulee** ont une phase de construction
   minimale (une seule passe, 1.8 s et 2.4 s respectivement) suivie d'un
   long segment décisif solo. L'enrichir nécessiterait aussi un rôle
   intermédiaire dans `templates.py` — non fait ici, signalé seulement.
3. Le tag physique `pass_lob` n'est utilisé par AUCUN des 12 gabarits
   actuels (seuls `pass_ground`, `cross`, `deflect`, `shot` apparaissent
   dans `physics_tags`) — à garder en tête pour la calibration du player,
   ce n'est pas un défaut de cet inventaire mais un fait de l'état actuel
   du code.
