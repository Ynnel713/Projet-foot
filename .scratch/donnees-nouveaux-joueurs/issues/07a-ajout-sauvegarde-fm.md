# 07a: Ajout des 600 joueurs suivants d'une sauvegarde FM (script et essai à blanc)

**Status:** livré (24/11/2026), validé expert + QC

**Blocked by:** 06a (fonctions de lecture et de conversion réutilisées)

**What to build:** `scripts/add_fmsave_players.py`. Source : `data/fmsave-list-hommes.csv`, export de sauvegarde FM fourni par le propriétaire (53 450 joueurs, hommes uniquement, triés par note FM décroissante, mêmes colonnes que `fmsave-list.csv` sans date de naissance). Parcourt la liste dans l'ordre, saute les joueurs déjà dans `data/joueurs.xlsx` et ajoute les N suivants (défaut 600) avec toutes leurs caractéristiques. Essai à blanc par défaut ; écriture avec `--write` et fichier Excel des nations au ticket 07b.

**Décisions du propriétaire (23/11/2026) :**
- « ne reprends pas les joueurs que tu possèdes déjà, rajoute les 600 joueurs suivants » ; « reporte bien toutes leurs caractéristiques, attributs, taille etc ».
- Club : chacun dans son vrai club (club existant reconnu, sinon club créé en « Autres clubs ») ; plafond de 40 joueurs par club ; « Sans club » sans plafond (jamais jouable).
- Nationalité : « À renseigner » (valeur provisoire ; ignorée par la génération des sélections tant qu'elle n'est pas remplacée).
- Valeur marchande : laissée vide.
- Mêmes règles que le 06a pour les données reprises : jeu de 36 attributs du métier (poste principal), échelle × 5 (20 -> 99), Pieds (D/G, égalité : vide), Weak foot (/5) échelle de la base, Taille FM (cm), Postes FM naturels (format de la base, `STC` -> `ST`).

**Estimation (travail effectif) :** analyse 15 min, développement 50 min, tests 35 min, vérifications 15 min ; total 1 h 55 ; confiance moyenne.

## Mesures préalables (23/11/2026)
- Détection naïve (nom exact + âge ±1) : 600 « nouveaux » dont de nombreux joueurs déjà présents sous un autre nom ou un club non officiel (Fabián / Fabián Ruiz, Kim Min-Jae / Min-jae Kim, Zambo Anguissa / Frank Anguissa à « Parthenope » = Naples, Ez Abde / Abde Ezzalzouli à « Real Hispalis » = Betis).
- Noms de clubs non officiels de FM : 278 correspondances apprises sur les joueurs présents dans les deux sources (Parthenope -> SSC Napoli, Real Hispalis -> Real Betis Balompié, Lago -> Como 1907, Blu-neri Milano -> Inter Milan, Barcelone -> FC Barcelona).
- Détection renforcée (ci-dessous) : 600 nouveaux sur les 3 218 premières lignes (2 618 déjà présents sautés), note FM 192 -> 124 ; 29 vers un club des 9 championnats, 405 vers un club « Autres clubs » existant, 166 vers 64 clubs créés, 42 sans club.

## Critères d'acceptation
- [x] Déjà présent si, à ±1 an : même club (après correspondance apprise ou rapprochement de nom de club) et nom proche (≥ 0,75), ou même nom de famille et même initiale, ou nom d'usage seul du classeur contenu dans le nom complet ; ou même nom normalisé n'importe où ; ou nom très proche (≥ 0,9) n'importe où. Cas douteux (même club, un seul mot de 4 lettres ou plus en commun) : ni ajouté ni assimilé, listé « À_VÉRIFIER ».
- [x] Correspondance de clubs apprise : nom de club de la sauvegarde -> club du classeur le plus fréquent parmi ses joueurs présents des deux côtés (au moins 2 joueurs, au moins 60 %).
- [x] Ordre de la liste respecté ; N joueurs ajoutés au plus ; club plein (40, hors « Sans club ») -> joueur sauté et signalé ; club créé retrouvé ensuite sous son nom exact.
- [x] Ligne ajoutée : ID nouveaux et uniques, Prénom / Nom (nom d'usage seul : Prénom), Nationalité « À renseigner », Âge, Poste au format du classeur, Club, Championnat, 36 attributs du métier, Pieds, Weak foot, Taille FM, Postes FM naturels ; Valeur marchande, Moyenne joueur, Statut, Catégorie, Taille (cm) vides ; Tableau8 étendu.
- [x] Essai à blanc par défaut (classeur intact) ; rapport par ligne examinée et bilan (clubs créés, clubs « Autres clubs » complets / incomplets selon `clubs.is_playable_squad`).
- [x] Tests hors ligne ; suite complète passée (3557 passés = 3 543 + 14, 14 désélectionnés).

## Journal

23/11/2026 — implémenté.
- `scripts/add_fmsave_players.py` (nouveau), source `data/fmsave-list-hommes.csv` (copie de l'export fourni), rapport `data/fmsave_add_report.csv` (non suivi, identique d'une exécution à l'autre).
- Essai à blanc sur le classeur réel : 278 noms de clubs traduits ; 2 598 déjà présents sautés, 15 cas douteux (À_VÉRIFIER), 600 prévus sur les 3 213 premières lignes. Destination : 34 dans un club des 9 championnats, 364 dans un club « Autres clubs » existant, 161 dans des clubs créés, 41 sans club. Clubs « Autres clubs » recevant des joueurs : 2 complets, 195 incomplets. Classeur intact (même empreinte).
- Messi (rang 25 du fichier) et Griezmann (rang 194) sont dans les 600 (clubs créés : Inter Miami CF, Orlando City SC).
- Cas douteux : 9 manifestement déjà présents sous un autre nom (Zambo Anguissa, Ez Abde, Douvikas, Bonny, Sudakov, Urko González, Adrián Dela, Kostoulas, Lykogiannis) ; 6 probablement nouveaux, sautés par prudence (Paul Pogba, Federico Bonazzoli, Arnau Puigmal, Munir Mohand, Miguel Borja, Tommaso Barbieri).
- Défauts trouvés par la mesure et corrigés avant revue : règle « un mot en commun » trop large (Daniel James / James Justin, Conor Bradley / Bradley Barcola, Paul Pogba / Jean-Paul Boëtius) et premier candidat retenu au lieu du meilleur ; score 0,70 de `name_similarity` pour tout nom d'usage seul différent (Ez Abde / Natan) ; noms d'usage seuls du classeur (Alexsandro / Alexsandro Ribeiro) traités à part.
- Tests : 8 dans `tests/test_add_fmsave.py`.

## Comments

24/11/2026 — passage 1 de l'expert : REJECTED (empreinte 9557623d). A1 [BLOQUANT] : 38 joueurs vers des clubs en double (« BOT », « FLU », « Palermo F.C. », « Club de Fútbol Monterrey ») alors que le vrai club existe. A2 [RÉSERVE] : votes « Sans club » dans l'apprentissage des correspondances. Corrections :
- `clean_club_name` : sigles à points (« Palermo F.C. » -> « Palermo FC ») et « Fútbol » neutralisés avant le rapprochement de nom (fonctions partagées inchangées).
- Correspondances apprises : « Sans club » ne vote plus ; vote unique et unanime accepté en repli seulement (après le rapprochement de nom) : « FLU » -> Fluminense.
- Correspondances validées par le propriétaire (24/11/2026, `data/fmsave_club_aliases.csv`, prioritaires) : BOT -> Botafogo de Futebol e Regatas ; Çorum Futbol Kulübü A.Ş. -> Corum FK ; Unione Calcio Sampdoria -> UC Sampdoria ; ATP -> Club Athletico Paranaense ; Foolad Mobarakeh Sepahan Club -> Sepahan FC.
- Rapport : section « club créé » avec le club existant le plus probable (joueurs communs ou nom proche) pour relecture.
- Nouvel essai à blanc : destination 62 dans les 9 championnats, 415 dans un club « Autres clubs » existant, 41 sans club, 82 dans des clubs créés (au lieu de 161) ; plus aucun joueur dans « BOT », « FLU », « Palermo F.C. », « Club de Fútbol Monterrey » ; clubs créés restants relus : absents du classeur (Cremonese, Sporting Gijón, Eibar, LA Galaxy, clubs japonais…). DÉJÀ_PRÉSENT 2 598, À_VÉRIFIER 15 ; Messi et Griezmann toujours prévus (Inter Miami CF, Orlando City SC créés).
- Tests : 3 ajoutés (11 au total).

24/11/2026 — passage 2 de l'expert : REJECTED (empreinte da9920b1). A1 [BLOQUANT] : le repli « un seul joueur commun » rattache des effectifs entiers au club d'un transfuge (Oviedo -> Real Sociedad, Albacete -> Cagliari…, ≈ 40 joueurs). A2, A3 [RÉSERVES] : rapprochements de nom douteux et surnoms à relire. Corrections :
- Repli supprimé. Correspondance apprise retenue si : au moins 2 joueurs communs et 60 %, ou un seul joueur commun avec des noms de clubs apparentés (`clubs_related` : mot distinctif commun ou rapprochement ≥ 0,6 ; « 1. FC Nürnberg » / « 1.FC Nuremberg ») ; et strictement plus de joueurs communs que tout autre club de la sauvegarde pour le même club du classeur (« Real Sociedad » l'emporte sur « Oviedo » ; égalité : aucun retenu, chacun retombe sur le rapprochement de nom).
- Validé par le propriétaire (24/11/2026) : FLU -> Fluminense Football Club (`data/fmsave_club_aliases.csv`) ; doublons connus sous un surnom : Sávio (Tottenham) = Savinho (ID 37), Pote (ACF Fiorentina) = Pedro Gonçalves (ID 1803) (`data/fmsave_known_players.csv`, lu avant toute autre règle).
- Rapport : liste de toutes les correspondances apprises (retenues et écartées, votes, raison, joueurs concernés) ; liste des PRÉVU à un seul mot relue (seuls Sávio et Pote étaient des doublons).
- Nouvel essai à blanc : DÉJÀ_PRÉSENT 2 600, À_VÉRIFIER 14, PRÉVU 600 ; destination 28 dans les 9 championnats (tous plausibles : Capitolini Celesti -> SS Lazio, Laguna -> Venezia FC, Coruña -> Deportivo A Coruña…), 417 dans un club « Autres clubs » existant, 41 sans club, 114 dans 53 clubs créés, tous absents du classeur (leurs seuls indices sont des transferts isolés : Oviedo, Albacete, Darmstadt, Catanzaro, Granada…). Aucun joueur dans « BOT », « FLU », « Palermo F.C. », « Club de Fútbol Monterrey ». Rapport identique sur deux exécutions ; classeur intact.
- Tests : 13 dans `tests/test_add_fmsave.py` (repli remplacé par le cas du transfuge, égalité de votes, doublons validés).

24/11/2026 — passage 3 de l'expert : APPROVED_WITH_RESERVATIONS (empreinte 67989911). A1 (rapprochement de nom vers un club voisin : Aris -> Iraklis, Al-Ittihad Tripoli -> Al-Ittihad de Djeddah) et A2 (rapport sans la liste des rattachements par nom proche) corrigés plutôt que soumis à acceptation :
- `fmsave_club_aliases.csv` accepte la cible « (créer) », qui force la création du club sous son nom exact.
- Rapport : section « rattachement par nom proche » (club de la sauvegarde, club du classeur, score, joueurs concernés), relue : 20 rattachements, tous justes sauf Aris et Al-Ittihad Tripoli ; Al-Ahli Sports Club (Qatar) rattaché à « Al-Ahli SC » (1 joueur, Mayele) ; Al-Arabi Sports Club -> Al-Arabi SC (joueurs qataris : juste).
- Validé par le propriétaire (24/11/2026) : créer « AS Aris Thessalonikis » (4 joueurs), « Al-Ittihad Tripoli Sports and Cultural Social Club » (1) et « Al-Ahli Sports Club » (3, Bourigeaud, Draxler, Vlap).
- Essai à blanc : destination 28 dans les 9 championnats, 409 dans un club « Autres clubs » existant, 41 sans club, 122 dans des clubs créés ; rapport identique sur deux exécutions ; classeur intact.
- Test ajouté : création forcée contre un rapprochement faux (14 au total).

24/11/2026 — passage 4 de l'expert : APPROVED (empreinte f6483019). QC : VALIDÉ. Clôture journalisée : VALIDÉ.
- Remarques facultatives : une cible « (créer) » au nom exact d'un club existant écraserait sa fiche (aucun cas actuel) ; nom de la copie de secours horodaté.
- À faire au 07b : relire de nouveau la section « rattachement par nom proche » si le classeur ou la source changent avant l'écriture ; les 14 À_VÉRIFIER restent écartés (dont 6 probablement nouveaux : Pogba, Bonazzoli, Puigmal, Munir Mohand, Miguel Borja, Tommaso Barbieri).
- Durée : estimée 115 min, réelle environ 260 min (+ 126 %) : analyse 40, développement 95, tests 60, vérifications 65. Écart > 30 % : trois passages d'expert rejetés ou réservés (clubs en double, transferts isolés rattachant des effectifs entiers, rapprochements de nom vers un club voisin), chacun corrigé avec une nouvelle règle, des validations du propriétaire et une suite complète ; la détection des déjà présents a aussi été reprise deux fois (règle « un mot commun » trop large, score 0,70 des noms d'usage). Temps machine hors total : quatre suites complètes (13 à 17 min).
