# 03: Résumé du match (« Temps forts », 10 à 15 minutes)

**Chantier :** `v2-mise-en-scene` (réécrit le 26/11/2026, audit du mode « moments clés », décisions du propriétaire). **Catégorie :** mode de visionnage.

**What to build:** le mode long, affiché « Temps forts » dans le sélecteur (EM-19) : **tout le Tier 1, puis le Tier 2 par score d'intérêt** jusqu'au budget, dans l'ordre chronologique, avec les constructions montrées (fenêtres du `01c`).

1. **Durée : 10 à 15 minutes à ×1** (décision du propriétaire, 26/11/2026 ; remplace les 8 à 12 minutes du 03/11/2026). Un match riche va vers 15, un match pauvre vers 10.
2. **Plancher et match pauvre** (position du propriétaire du 26/11/2026, à trancher avec les constantes, pas avant) : **10 minutes restent la cible**. Le Tier 2 n'entre que s'il dépasse un score minimal. Un résumé de moins de 10 minutes n'est admis que si la mesure préalable montre qu'un match n'a pas assez de Tier 2 au-dessus de ce score ; le rapport de mesure (jamais l'écran) le signale alors match par match : « ce match n'a produit que X moments, résumé à Y min ». **On ne comble jamais avec du jeu sans intérêt** (construction molle), ce que le mode veut justement éviter.
3. **Non-répétition** : pas plus de N moments consécutifs de même type et de même issue ; plafonds par type du `01d`.
4. **Tier 3 en surimpression** pendant les moments (01g), jamais comme moment.
5. **Durée cachée** (décision du propriétaire, 26/11/2026, cruciale pour le suspense) : rien à l'écran ne laisse deviner la durée du résumé ni le nombre de moments restants (règles des `01f` et `01g`) ; la durée variable de 10 à 15 minutes ne doit jamais devenir un indice.
6. **Entrées à leur livraison, sans bloquer** : belles constructions (`v2-realisme/31b`), poteaux (`v2-collectif/35c`), célébrations (`04`), échauffourées (`v2-attributs-restants/09c`), cartons et remplacements en Tier 3.

**Ordre de grandeur :** à environ 35 s par moment (fenêtre et contexte), 10 à 15 minutes demandent 17 à 25 moments, soit 8 à 15 Tier 2 en plus du Tier 1. Le nombre de candidats Tier 2 au-dessus du seuil est inconnu aujourd'hui : à mesurer avant de fixer les constantes. C'est le principal risque du ticket.

**Attributs :** aucun.

**Constantes à proposer avant le code :** bornes de durée dans 10 à 15 minutes selon l'intérêt du match ; score minimal du Tier 2 ; N de non-répétition. **Aucune constante n'est proposée avant la mesure** du nombre de candidats Tier 2 par match (50 matchs, graine d'audit), faite en tête de ticket et rapportée : les fixer avant reviendrait à calibrer sur une hypothèse (décision du propriétaire, 26/11/2026).

**Blocked by:** 01d, 01g, 02.

**Bloque :** 07a.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 35 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 25 min |
| **Total (travail effectif)** | **1 h 45** |

Confiance : moyenne. Hypothèses : assez de candidats Tier 2 dans un match moyen (sinon, révision de la taxonomie du `01b`, nouvelle estimation annoncée).
Temps machine, non compté : suite complète (environ 10 min) ; 50 matchs (environ 2 h 30).

## Tests

- Trace pauvre contre trace riche (construites) : le résumé du match pauvre est plus court ; aucun moment sous le score minimal.
- Non-répétition testée sur une trace à dix arrêts semblables.
- 50 matchs : durée par match (médiane, 10e et 90e centiles), part des matchs sous 10 minutes, part de Tier 2.

## Acceptance criteria

- [ ] Mesure des candidats Tier 2 sur 50 matchs faite et rapportée **avant** toute proposition de constantes ; constantes validées par le propriétaire sur cette mesure, avant le code
- [ ] 100 % du Tier 1 présent ; Tier 2 au-dessus du score minimal seulement
- [ ] Durée entre 10 et 15 minutes à ×1 sur au moins la part de matchs fixée avec les constantes ; chaque match sous 10 minutes signalé dans le rapport (« ce match n'a produit que X moments, résumé à Y min ») et justifié par le manque de Tier 2 au-dessus du score minimal
- [ ] Durée du résumé et nombre de moments invisibles pendant le visionnage (vérifié avec les règles des `01f` et `01g`)
- [ ] Non-répétition respectée (test)
- [ ] Sans spoiler ; déterminisme à graine fixée
- [ ] `npm run build` et `npm run lint` OK
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Comments

- 26/11/2026 : réécrit. Les blocages d'origine `v2-collectif/29`, `30` et `31` sont levés (livrés) ; 28c remplacé par `01a`. Le score d'intérêt est défini au `01b` et commun aux modes.
