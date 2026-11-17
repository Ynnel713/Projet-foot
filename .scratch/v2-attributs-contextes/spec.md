# Chantier v2-attributs-contextes : attributs multidimensionnels

**Décision :** ADR 0002 (`docs/adr/0002-attributs-multidimensionnels.md`), validée par le propriétaire le 17/11/2026 (« tout est validé »).

**But :** qu'un attribut serve dans plusieurs contextes de jeu, par des poids déclarés dans un registre central, au lieu d'être enfermé dans un seul effet ; sans double comptage (R1 réécrite : « un effet, un calcul »).

**Constat de départ (audit du 17/11/2026) :** 11 attributs sur 27 n'ont qu'un effet : Work Rate (pressing), Positioning (erreur de placement dans le bloc), Decisions (porteur et remises ; en défense, seulement le renoncement au tacle hors urgence, ticket `v2-realisme/11h`), Flair (idée de talonnade), Marking, Balance, Strength (duels), Tackling, note agrégée du gardien (Reflexes, One on Ones, Handling). Cause principale : la liste blanche par module et l'interdiction par défaut des mélanges dans `tests/test_v2engine_rayon_attributs.py`.

## Ordre validé

1. `01` registre des contextes, sans changement de jeu ;
2. `02` test de rayon transformé ;
3. contexte « lecture du pressing » au ticket `v2-collectif/15b` (Vision, Anticipation, Decisions) ;
4. lots de branchement : `03` Work Rate offensif (en attente le 17/11/2026 : Work Rate a déjà un effet fort, + 2,4 buts par match entre 99 et 11 sur 10 matchs ; mesure du plafond au `03m`), `04a` Decisions en défense, `04b` Positioning en défense, `05` Flair et goût du risque, `06` Balance après contact ;
5. séparation de la note du gardien : ticket existant `v2-attributs-restants/03b` ;
6. `07` mise aux normes des tickets à venir (lignes « Attributs » avec contexte et poids) ;
7. `08` solde de la liste de transition de la garde (ajouté au ticket 02 le 17/11/2026, choix du propriétaire : seuls les contextes du registre comptent) : second contexte pour les attributs encore cloisonnés sans autre ticket, à découper en lots.

## Règles communes

- Chaque poids est une constante produit, proposée au propriétaire avant le code.
- Chaque branchement change le jeu : mesure avant/après sur 50 matchs, banc de profils (`scripts/measure_v2.py --profil`), plafond d'écart 99 / 11 de la carte.
- Lecture des notes par la façade `condition.effective_rating` uniquement (R6).
