# 10n: Validation des transitions offensives et défensives

**Chantier :** `v2-realisme` (audit des transitions du 26/11/2026, demande du propriétaire, ticket proposé « T5 »). **Priorité :** P1. **Catégorie :** validation.

**Constat vérifié :**
- Les transitions ont leurs mécanismes livrés (`v2-collectif/03`, `10`, `11`) et une partie de leurs indicateurs :
  - repli (indicateur 7) ;
  - pertes en transition (8) ;
  - appelants simultanés par situation (19) ;
  - tirs de contre après récupération ;
  - origine des buts (19e).
- Aucun ticket de validation ne les rassemble, comme 09h, 10j ou 12g le font pour leur famille.
- Trois mesures manquent : durée effective du contre-pressing, nombre de joueurs projetés après une récupération, buts et occasions concédés en transition par équipe.

**What to build:** Banc seulement, moteur inchangé. Les nouvelles mesures sont définies dans `docs/INDICATEURS_V2.md` et ajoutées à `scripts/v2_indicators.py` :
1. durée réelle du contre-pressing, du moment de la perte à la récupération, à l'abandon ou au repli, et part des contre-pressings qui récupèrent en moins de 5 s ;
2. joueurs projetés au-delà du ballon 3 s et 6 s après une récupération ;
3. buts, tirs et grosses occasions concédés dans les 15 s d'une perte, par zone de perte.

**Taille de la série (décision du propriétaire, 26/11/2026) :** la série est fixée en nombre de buts, pas en matchs : on joue des matchs jusqu'à au moins 200 buts, nombre fixé avant la mesure. Pour qu'une part observée de 85 % donne une borne haute à 95 % sous 90 %, il faut 1,96 × √(0,85 × 0,15 / n) ≤ 5 points, soit n ≥ 196 buts. Une série fixée en matchs rendrait le critère plus dur à mesure que le moteur devient réaliste : 50 matchs donnent environ 270 buts à 5,4 buts par match (19e) mais environ 135 à 2,7, avec une borne haute vers 91 % qui échouerait même à 85 % observés. Ordre de grandeur : environ 40 matchs au rythme actuel, 75 à 80 au rythme réel.

Le rapport, sur cette série, reprend aussi les indicateurs existants (repli, pertes en transition, tirs de contre, origine des buts) et les compare aux repères réels sourcés, ou « non trouvé ».

**Attributs :** aucun

**Lien avec l'existant :** ne duplique pas 13i, qui mesure les signatures de style. Ce ticket mesure les transitions à style neutre ; ses indicateurs sont disponibles pour 13i, sans dépendance formelle.

**Blocked by:** 10m1 (Repli en hauteur et remontée de la ligne) ; 10m2 (Resserrement en largeur) ; 01e (séries longues et intervalles).

**Bloque :** `v2-collectif/22b`. Partage avec `v2-mise-en-scene/01b` la définition de l'action de contre-attaque (récupération sur l'adversaire, conclusion dans les 15 s) : une seule fonction publique dans `scripts/v2_indicators.py`, écrite par le premier livré (26/11/2026).

**Dépendance non réciproque :** 01e (livré) n'est pas modifié ; sa ligne « Bloque » ne cite pas 10n.

**Status:** à faire

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 40** |

Confiance : élevée. Hypothèses : situations de jeu, pertes et récupérations déjà tracées (`v2-collectif/03`, 19b).
Temps machine, non compté : suite complète (environ 10 min en session cloud) ; série d'au moins 200 buts (environ 40 à 80 matchs selon le nombre de buts par match).

## Tests

- **Unitaires (scène contrôlée) :** une perte suivie d'une récupération en 3 s donne une durée de contre-pressing de 3 s ; une récupération suivie de deux appels donne deux joueurs projetés
- **Statistiques (séries de matchs) :** rapport sur une série d'au moins 200 buts, avec le nombre de buts et de matchs joués et les intervalles de confiance

## Acceptance criteria

- [ ] Re-mesure, après la livraison de 10m1 et 10m2, de la part des buts issus d'un ballon gagné à l'adversaire, catégories « récupération » et « erreur adverse » du 19e rapportées séparément avec leur intervalle de confiance (avant : 95,4 % = 80,6 + 14,8, sur 108 buts en 20 matchs ; délai médian origine-but 3,3 s), valeur « avant » recalculée avec la même définition ; sur une série d'au moins 200 buts (voir Taille de la série), si la part totale ne descend pas à 85 % ou moins avec la borne haute de son intervalle de confiance à 95 % sous 90 %, un ticket est ouvert. **Seuil de 85 % : choix produit du propriétaire (26/11/2026), non sourcé.** Aucune valeur réelle de la part des buts après un ballon gagné n'a été trouvée (`docs/INDICATEURS_V2.md`, section 24 : « part des penalties, des touches, des récupérations et du jeu placé : non trouvé ») ; le seul repère connu est la part des buts sur coup de pied arrêté hors penalties, 23,5 % sur l'histoire de la Premier League et environ 27 % en 2025-2026 selon les définitions (Opta Analyst, même section). Ce seuil n'est pas un repère réel. Il est fixé avant toute mesure, y compris celle de 10m1, pour éviter de l'ajuster au résultat. Le ticket est ouvert sur la cause suivante, choisie sur la mesure : sortie de pressing adverse trop facile, force du contre-pressing, ou délai de réorganisation
- [ ] Définitions des trois nouvelles mesures et repères réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Indicateurs reproductibles à graine fixée, testés
- [ ] Rapport : repli, durée du contre-pressing, joueurs projetés après récupération, pertes en transition, occasions et buts concédés en transition, origine des buts ; chaque écart au réel renvoyé à un ticket, jamais réglé ici
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
