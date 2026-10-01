# Diagnostic -- buts de corner / coup franc / construction non racontes comme des buts

Echantillon de lecture du 01/10/2026 (`scripts/sample_nlg_output.py`, 14 matchs, graine 20261001).
Sur 36 buts, 31 sont racontes en scenario BUT ; **5 ne le sont pas**. Diagnostic AVANT correction.

## Cause : `receveur_id` n'est jamais envoye

`engine/nlg_ingestion.py` n'emet que `passeur_id` (le moteur n'a que `GoalEvent.assist`). Dans le NLG,
`select()` ecarte toute phrase dont un slot ne se resout pas (`template_filler.SlotResolutionError` sur
`context.receveur` = None, voir `phrase_selector._rendre_palier`). Les phrases qui exigent `{receveur}` sont donc
inrendables pour ces buts.

Phrases qui attendent `receveur` (lecture de `simulafoot_nlg/data/seed/scenarios.yml` et `v2/corner.yml`, slots et texte) :

| Scenario | Phrases | avec slot `receveur` | avec slot `passeur` |
|---|---|---|---|
| COUP_FRANC | 20 | **20** | 18 |
| CONSTRUCTION | 20 | **18** (les 2 autres : `{joueur}` seul) | 17 |
| CORNER | 30 | **18** (les 12 autres : corners ratés, sans receveur) | 20 |

Consequences sans `receveur_id` : COUP_FRANC -> aucune phrase rendable -> phrase de secours ; CONSTRUCTION -> seules
les 2 phrases `{joueur}` ; CORNER -> seules les 12 phrases sans receveur, donc des corners ratés.

## Les 5 cas (avant correction)

| Match | Minute | Gabarit | Passeur -> buteur | Scenario | Phrase produite |
|---|---|---|---|---|---|
| 2 PSG-Monaco | 89' | corner | Ansu Fati -> Mamadou Coulibaly | CORNER | « Ansu Fati envoie son corner au second poteau, mais personne ne parvient à le reprendre et la balle sort. » |
| 7 Man City-Man Utd | 35' | coup_franc | Phil Foden -> Matheus Nunes | COUP_FRANC (**secours**) | « Le coup franc est joué dans la zone dangereuse. » |
| 7 Man City-Man Utd | 52' | corner | Jérémy Doku -> Rayan Aït-Nouri | CORNER | « Manchester United repousse le ballon de la tête en catastrophe, mais le cuir retombe idéalement dans la surface pour une seconde tentative ! » |
| 7 Man City-Man Utd | 66' | coup_franc | Rayan Cherki -> Antoine Semenyo | COUP_FRANC (**secours**) | « Le coup franc est joué dans la zone dangereuse. » |
| 13 Leverkusen-Leipzig | 16' | construction_placee | Christopher Nkunku -> Willi Orbán | CONSTRUCTION | « Willi Orbán enchaîne les contrôles et repique dans l'axe après un long rush balle au pied, ouvrant un boulevard devant lui ! » |

Les 5 dicts ont `passeur_id` et pas de `receveur_id` (les buts sans passeur ne sont pas concernes : ils passent en
gabarit `percee_individuelle`, donc en scenario BUT).

## Verification de l'hypothese (sans modifier le code)

Les 5 evenements rejoues par le NLG avec `receveur_id = player_id` (base copiee, historique vide) : plus aucun
secours, passeur et buteur nommes dans chaque phrase. Les 5 phrases changent -- voir le rapport de correction.
