# 03: Résumé du match (« Temps forts », 10 à 15 minutes)

**Chantier :** `v2-mise-en-scene` (réécrit le 26/11/2026, audit du mode « moments clés », décisions du propriétaire). **Catégorie :** mode de visionnage.

**What to build:** le mode long, affiché « Temps forts » dans le sélecteur (EM-19) : **tout le Tier 1, puis le Tier 2 par score d'intérêt** jusqu'au budget, dans l'ordre chronologique, avec les constructions montrées (fenêtres du `01c`).

1. **Durée : 10 à 15 minutes à ×1** (décision du propriétaire, 26/11/2026 ; remplace les 8 à 12 minutes du 03/11/2026). Un match riche va vers 15, un match pauvre vers 10.
2. **Plancher et match pauvre** : le Tier 2 n'entre que s'il dépasse un score minimal. Si un match n'a pas assez de candidats au-dessus de ce score pour atteindre 10 minutes, le résumé est plus court et le cas est compté. **On ne comble pas avec des moments sans intérêt** (construction molle) ; règle à confirmer par le propriétaire.
3. **Non-répétition** : pas plus de N moments consécutifs de même type et de même issue ; plafonds par type du `01d`.
4. **Tier 3 en surimpression** pendant les moments (01g), jamais comme moment.
5. **Entrées à leur livraison, sans bloquer** : belles constructions (`v2-realisme/31b`), poteaux (`v2-collectif/35c`), célébrations (`04`), échauffourées (`v2-attributs-restants/09c`), cartons et remplacements en Tier 3.

**Ordre de grandeur :** à environ 35 s par moment (fenêtre et contexte), 10 à 15 minutes demandent 17 à 25 moments, soit 8 à 15 Tier 2 en plus du Tier 1. Le nombre de candidats Tier 2 au-dessus du seuil est inconnu aujourd'hui : à mesurer avant de fixer les constantes. C'est le principal risque du ticket.

**Attributs :** aucun.

**Constantes à proposer avant le code :** bornes de durée dans 10 à 15 minutes selon l'intérêt du match ; score minimal du Tier 2 ; N de non-répétition. Proposées après une mesure du nombre de candidats Tier 2 sur 50 matchs.

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

- [ ] Constantes validées par le propriétaire avant le code, sur la mesure des candidats Tier 2
- [ ] 100 % du Tier 1 présent ; Tier 2 au-dessus du score minimal seulement
- [ ] Durée entre 10 et 15 minutes à ×1 sur au moins la part de matchs fixée avec les constantes ; matchs plus courts comptés et expliqués
- [ ] Non-répétition respectée (test)
- [ ] Sans spoiler ; déterminisme à graine fixée
- [ ] `npm run build` et `npm run lint` OK
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Comments

- 26/11/2026 : réécrit. Les blocages d'origine `v2-collectif/29`, `30` et `31` sont levés (livrés) ; 28c remplacé par `01a`. Le score d'intérêt est défini au `01b` et commun aux modes.
