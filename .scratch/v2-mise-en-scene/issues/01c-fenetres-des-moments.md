# 01c: Fenêtres des moments : construction, ancre, suite, fusion

**Chantier :** `v2-mise-en-scene` (audit du mode « moments clés », 26/11/2026). **Catégorie :** lecture de la trace (moteur inchangé).

**Constat vérifié (26/11/2026) :** le journal donne la chaîne causale de chaque événement (`trace.chain`, `v2-realisme/19b`), de l'engagement jusqu'à lui ; les remises en jeu (`RestartEvent`), pertes et récupérations y sont. Rien ne borne aujourd'hui le début d'une action.

**What to build:** dans le module du `01b`, transformer chaque candidat en **moment** `[début, fin]` autour de son ancre :
1. **Construction** (contre la construction molle) : le début est le dernier changement de possession ou la dernière remise en jeu avant l'ancre, lus dans la chaîne causale. Il est ramené dans un intervalle `[minimum, maximum]` avant l'ancre : une action trop longue commence au maximum, une action très courte (contre éclair, corner) garde au moins le minimum pour donner le contexte.
2. **Suite** : après l'ancre, jusqu'à l'issue (ballon mort, remise, changement de possession) dans une limite ; après un but, jusqu'à la célébration et l'engagement, dans une limite plus longue.
3. **Absorption (pas de double comptage)** : un seul moment par action. Ordre de priorité du type retenu : but > penalty > grosse occasion > Tier 2. Cas obligatoires : but issu d'une grosse occasion ; tir repoussé puis second tir ; faute sifflée penalty puis penalty ; tir au sein d'une grosse occasion.
4. **Fusion et doublons** : deux moments qui se chevauchent, ou dont les ancres sont à moins de 5 s, deviennent un seul moment (union des fenêtres, type du plus prioritaire, score du plus fort). Fusion bornée par une durée maximale de moment ; au-delà, les deux moments restent distincts et **leurs fenêtres sont coupées au début de la seconde action** (changement de possession ou remise lu dans la chaîne ; à défaut, au milieu entre les deux ancres), si bien qu'ils ne se chevauchent jamais. La durée maximale de fusion est au moins égale à la plus longue fenêtre simple plus 5 s, pour que deux ancres à moins de 5 s soient toujours fusionnées.
5. **Limites de période** : aucune fenêtre ne franchit la mi-temps ni la fin du match.

**Attributs :** aucun.

**Constantes à proposer avant le code :** minimum et maximum de construction ; limite de suite (cas général et but) ; durée maximale d'un moment fusionné (au moins la plus longue fenêtre simple plus 5 s). La suite d'une grosse occasion part de `ChanceEvent.end`, instant où le danger passe sous le plancher (01a). L'écart de 5 s entre ancres est fixé par le propriétaire (26/11/2026).

**Blocked by:** 01b.

**Bloque :** 01d.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 45** |

Confiance : moyenne. Hypothèses : la chaîne causale suffit pour trouver le début de possession (sinon, repli sur le dernier porteur adverse lu dans `ball_track`) ; les cas d'absorption se testent sur traces construites.
Temps machine, non compté : suite complète (environ 10 min).

## Tests

- Traces construites : but après une grosse occasion : 1 moment de type but ; tir repoussé puis but 3 s plus tard : 1 moment ; penalty : 1 moment qui commence avant la faute ; deux grosses occasions à 20 s d'intervalle sans changement de possession : 2 moments si les ancres sont à plus de 5 s et les fenêtres disjointes ; deux actions longues dont les fenêtres se chevauchent et dont l'union dépasse la durée maximale : 2 moments disjoints, coupés au début de la seconde action ; variante sans changement de possession (circulation autour de la surface) : 2 moments disjoints, le second commence à la coupure au milieu entre les ancres.
- Construction : action longue coupée au maximum ; contre éclair allongé au minimum ; début jamais dans la période précédente.
- Sur 3 traces réelles du banc EM-00 : 0 chevauchement, 0 paire d'ancres à moins de 5 s.

## Acceptance criteria

- [ ] Constantes validées par le propriétaire avant le code
- [ ] Les quatre cas d'absorption testés : un seul moment chacun
- [ ] 0 chevauchement et 0 ancres à moins de 5 s sur les traces testées
- [ ] Chaque début de moment est un changement de possession, une remise en jeu, la borne de construction ou une coupure entre deux moments (règle du point 4) (test)
- [ ] Aucune fenêtre à cheval sur deux périodes
- [ ] Fonction pure, sortie identique sur deux exécutions
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
