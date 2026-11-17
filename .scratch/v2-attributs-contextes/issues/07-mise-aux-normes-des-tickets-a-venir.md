# 07: Mise aux normes des tickets à venir : contexte et poids dans chaque ligne « Attributs »

**Chantier :** `v2-attributs-contextes` (ADR 0002). **Priorité :** P2. **Catégorie :** documentation.

**What to build:** reprendre la ligne « Attributs » des tickets ouverts pour y indiquer le contexte et les poids proposés (à valider à l'ouverture de chaque ticket), selon l'audit du 17/11/2026 :
- défense, `v2-realisme/10a` à `10j` (aujourd'hui « aucun » sur neuf tickets) : Positioning, Anticipation, Marking, Concentration, Decisions, Teamwork ;
- occupation et styles, `v2-realisme/09a` à `09f`, `13a` à `13i` : Work Rate (attaquant qui reste haut), Teamwork (adhésion à la consigne), Flair (dézoner) ;
- jeu aérien, `v2-realisme/15b` à `15d` : Jumping Reach dans tout le jeu aérien (duel, tête offensive, dégagement, contre), Anticipation (moment du saut), Bravery ;
- sans ballon, `v2-realisme/25c` à `25e` : Work Rate (volume des courses de soutien), Decisions (moment) ;
- dribbles et duels, `v2-realisme/04e` à `04j` : Balance, Agility, Acceleration (porteur), Anticipation, Positioning (défenseur), Flair (choix du geste) ;
- Concentration, `v2-collectif/21` et `v2-realisme/20b` : modulateur commun (R3) du contrôle, du marquage et de la ligne du hors-jeu ;
- coups de pied arrêtés, `v2-realisme/16d` à `16f` : Technique, Vision (choix de la cible), Composure, Strength (touche longue).

**Hors de ce ticket :** tout code ; les tickets `v2-collectif/15b`, `15c` et `v2-attributs-restants/03c`, déjà mis à jour le 17/11/2026.

**Blocked by:** aucun (peut suivre 01 et 02 pour citer les noms de contextes).

**Status:** à faire

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension | 25 min |
| Rédaction | 50 min |
| Vérifications | 15 min |
| **Total (travail effectif)** | **1 h 30** |

Confiance : moyenne. Hypothèses : une quarantaine de tickets, une ligne chacun.

## Acceptance criteria

- [ ] Chaque ticket listé porte des contextes et des poids proposés, ou « aucun » justifié
- [ ] Aucun attribut non spécialiste annoncé dans un seul contexte sans justification
