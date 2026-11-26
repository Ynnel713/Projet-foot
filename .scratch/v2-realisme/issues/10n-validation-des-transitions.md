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

Le rapport sur 50 matchs reprend aussi les indicateurs existants (repli, pertes en transition, tirs de contre, origine des buts) et les compare aux repères réels sourcés, ou « non trouvé ».

**Attributs :** aucun

**Lien avec l'existant :** ne duplique pas 13i, qui mesure les signatures de style. Ce ticket mesure les transitions à style neutre ; ses indicateurs sont disponibles pour 13i, sans dépendance formelle.

**Blocked by:** 10m (Repli du bloc à la perte) ; 01e (séries longues et intervalles).

**Bloque :** `v2-collectif/22b`.

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
Temps machine, non compté : suite complète (environ 40 min) ; série de 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** une perte suivie d'une récupération en 3 s donne une durée de contre-pressing de 3 s ; une récupération suivie de deux appels donne deux joueurs projetés
- **Statistiques (séries de matchs) :** rapport sur 50 matchs avec intervalles de confiance

## Acceptance criteria

- [ ] Définitions des trois nouvelles mesures et repères réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Indicateurs reproductibles à graine fixée, testés
- [ ] Rapport : repli, durée du contre-pressing, joueurs projetés après récupération, pertes en transition, occasions et buts concédés en transition, origine des buts ; chaque écart au réel renvoyé à un ticket, jamais réglé ici
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
