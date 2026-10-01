# Couverture de la banque de commentaire — import du 30/09/2026

> **Cette banque n'est PAS livrable en production. Elle sert à valider le
> moteur de bout en bout (import → sélection → rendu), pas à commenter un
> vrai match.**

## Chiffres

- **281 phrases**, **9 scénarios**, **13 variantes**.
- Couverture estimée : **~33 % des événements d'un match réel** (~100
  événements couverts sur ~300 événements commentables dans un match
  complet — estimation, pas une mesure instrumentée sur un vrai match).

## Scénarios couverts (9)

CARTON_ROUGE, BUT, PENALTY_RATE, COUP_FRANC, CONSTRUCTION, ARRET_GARDIEN,
SITUATION_MATCH, DEBUT_MATCH, GESTE_SIGNATURE.

## Scénarios absents (12) — rien dans la banque

- DÉFENSE (tacle réussi, interception, dégagement)
- CORNER
- FAUTE_SIMPLE (faute non sanctionnée d'un carton)
- TIR_NON_CADRÉ
- HORS-JEU
- REMPLACEMENT
- CARTON_JAUNE
- MI_TEMPS / FIN_MATCH
- STATISTIQUES_PÉRIODIQUES (possession, tirs cumulés à la mi-temps, etc.)
- VAR
- AMBIANCE (hors SITUATION_MATCH — chants, tifos, incidents de tribune)
- BLESSURE

Voir [PLAN_V2_EDITORIAL.md](PLAN_V2_EDITORIAL.md) pour le chiffrage et la
priorisation de ces 12 scénarios.

## Scénarios sous-alimentés (4) — présents mais fragiles à l'usage

| Scénario | Phrases | Cooldown | Risque |
|---|---|---|---|
| CONSTRUCTION | 20 | 2 matchs | Phase la plus fréquente d'un match réel (dizaines d'occurrences/match) contre seulement 20 gabarits — épuisement du pool probable dès la 1ʳᵉ mi-temps d'un match simulé. |
| ARRET_GARDIEN | 38 | 2 matchs | Fréquence élevée (plusieurs arrêts/match), pool le plus large des sous-alimentés mais encore court face à un cooldown de seulement 2 matchs. |
| SITUATION_MATCH | 30 | 1 match | Cooldown le plus court du lot (par design, voir justification dans `convert_commentary_xlsx_to_yaml.py`) — un pool de 30 phrases avec un cooldown de 1 match s'épuise vite sur un match à commentaire dense. |
| COUP_FRANC | 20 | 3 matchs | Pool le plus petit des scénarios "action" restants ; 35 % de redondance structurelle corrigée à 10 % lors de l'audit du 30/09/2026, mais la taille du pool reste limitante. |

## VIABILITÉ DES CONDITIONS — ajouté le 01/10/2026

> **Ces phrases peuvent ne jamais se déclencher sur la majorité des
> matchs.** 281 phrases importées ne veut pas dire 281 phrases également
> jouables — voir [AUDIT_COUVERTURE_DONNEES_JOUEUR.md](AUDIT_COUVERTURE_DONNEES_JOUEUR.md)
> pour le détail complet, la méthode et les trois options de remédiation.

**63 des 109 phrases à conditions joueur (57,8 %) sont limitées par la
donnée**, pas par un seuil narratif voulu — un joueur qui aurait le trait
qualifiant ne peut même pas être testé, faute de valeur renseignée pour
lui. Groupées par attribut responsable :

| Attribut en cause | Couverture réelle (7563 joueurs) | Phrases limitées par la donnée | Particularité |
|---|---|---|---|
| `preferred_moves` | 4,8 % (362 joueurs) | ~56 phrases concernées, dont la quasi-totalité des phrases GESTE_SIGNATURE/DEFAUT | **Concentré sur 35 clubs seulement (sur 836)** — les 20 clubs Premier League sont couverts à 100 %, presque tout le reste à 0 %. Pour un match hors Premier League, le taux réel de déclenchement de ces phrases tend vers 0 %, pas vers 4,8 %. |
| `height_cm` | 11,7 % (887 joueurs) | 7 phrases (BUT/SURNOM "Le colosse"/"Le feu follet", ARRET_GARDIEN/SURNOM "Le mur"/"La muraille"/"Le géant", etc.) | Cause identifiée avec certitude (lecture de code) : `scripts/scrape_fminside_attributes.py` écrit la taille scrapée dans la colonne Excel **"Taille FM (cm)"**, mais `data/import/import_players.py` lit la colonne **"Taille (cm)"** (sans "FM") — deux colonnes différentes. Les 11,7 % viennent d'une source antérieure au scraping FM, pas d'un échec du scraper. |
| `foot` | 39,1 % (2957 joueurs, valeurs D/G) | 1 phrase (BUT/DEFAUT "...pied droit...", corrigée le 30/09/2026) | Partiel mais pas critique — aucun scénario n'en dépend massivement. |

Répartition des 63 phrases data-limitées par scénario : **GESTE_SIGNATURE
32/37 (86 %)**, **BUT 23/60 (38 %)**, **CARTON_ROUGE 5/31 (16 %)**,
**ARRET_GARDIEN 3/38 (8 %)**.

**Nuance obligatoire** : 39 autres phrases tombent aussi sous 10 % de
taux de déclenchement théorique mais ne sont PAS un problème de donnée —
elles conditionnent sur un attribut bien peuplé (`Aggression`, `Strength`,
93 % de couverture) avec un seuil élitiste voulu (peu de joueurs ont
vraiment 85+ d'agressivité, et c'est le but : un carton rouge doit rester
rare). Ne pas confondre les deux catégories lors d'une future lecture de
ce fichier.

### 32 phrases GESTE_SIGNATURE — PL-only jusqu'à enrichissement (décision du 01/10/2026)

**Statut assumé, pas un oubli.** 32 des 37 phrases GESTE_SIGNATURE
(variante DEFAUT quasi entière) ne se déclenchent aujourd'hui que pour un
match impliquant un des 20 clubs de Premier League (seule compétition
simulée où `preferred_moves` est couvert à 100 % des effectifs) — 0 % de
probabilité de déclenchement pour tout autre championnat simulé (Ligue 1,
Serie A, Bundesliga, Liga Portugal, Jupiler Pro League, Eredivisie...).

Décision : **garder ces 32 phrases en base, documentées PL-only, plutôt
que les retirer temporairement.** Les retirer puis les réintégrer après
l'enrichissement coûte deux cycles d'import/test/commit pour un état
transitoire — coût jugé supérieur au bénéfice (voir
[ENRICHISSEMENT_PREFERRED_MOVES.md](ENRICHISSEMENT_PREFERRED_MOVES.md)
pour les 3 options considérées).

**Ce statut est temporaire par construction** : un enrichissement de
`preferred_moves` est planifié, cible 90 % de couverture joueur (contre
4,8 % aujourd'hui) — voir le fichier dédié pour le scoping complet. Le
critère de vérification de cet enrichissement (avant tout démarrage du
travail) doit être en place avant que le workstream ne commence, pas
après. Une fois la cible atteinte, cette section n'aura plus lieu d'être
et devra être retirée.

## Pourquoi importer quand même

Décision assumée (30/09/2026) : importer une banque partielle permet de
faire tourner le pipeline (scenario_engine → conditions → sélection → rendu,
une fois ces deux derniers implémentés) et de découvrir en pratique ce qui
manque, plutôt que de le théoriser indéfiniment avant tout import. Voir le
smoke test du même jour pour ce que ça a révélé concrètement.

## Ne pas confondre avec une banque complète

Dans trois mois, sans ce fichier : 281 phrases importées et un moteur qui
tourne peuvent donner l'illusion d'un système fini. Ce n'est pas le cas —
voir la clause en tête de document.
