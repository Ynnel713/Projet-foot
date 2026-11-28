# 15a2: Sélection des joueurs qui attaquent le ballon aérien

**Chantier :** `v2-realisme`. **Ouvert le 27/11/2026**, découpage du ticket 15a (validé par le propriétaire le 27/11/2026). **Catégorie :** décision.

**What to build:** au lancement d'un ballon aérien (passe lobée, remise aérienne), chaque équipe retient au plus deux joueurs de champ éligibles au point d'attaque (`15a1`) ; règles et constantes du ticket 15a (validées le 27/11/2026) : marge 0 s, epsilon 1e-6 s, départage par le nom, receveur éligible toujours retenu, receveur non éligible sans place mais cible prioritaire, gardien exclu. Sélection stable jusqu'au premier contact (sol ou joueur), puis règle du 11g. Défenseurs retenus : point de lecture = leur point d'attaque (rôle `LECTURE`) ; second attaquant : rôle dédié. Non retenus : rôle actuel (second ballon au `15e`). Sélection tracée.

**Blocked by:** 15a1.

**Bloque :** 15b, 15e, 16a, 16f.

**Status:** à faire

## Estimation

| Poste | Durée |
|---|---|
| Analyse | 10 min |
| Développement | 35 min |
| Tests | 25 min |
| Intégration et vérifications | 40 min |
| **Total (travail effectif)** | **1 h 50** |

Confiance : moyenne. Temps machine hors total : série de 50 matchs avant et après, suite complète.

## Acceptance criteria

- [ ] Scène : dégagement long : les deux plus aptes de chaque équipe attaquent le ballon, les autres non
- [ ] Scène : receveur non éligible : deux coéquipiers éligibles retenus, le receveur vise quand même le point d'attaque
- [ ] Scène : égalité de marge à l'epsilon près : départage par le nom, même résultat sur deux exécutions
- [ ] Sélection tracée ; indicateur « joueurs qui attaquent un ballon aérien, par équipe »
- [ ] 50 matchs avant/après : passes longues réussies, interceptions, possession, buts ; joueurs autour du ballon (28b) ; écarts expliqués
- [ ] Déterminisme à graine fixée ; suite complète au compte attendu ; V1 inchangée
- [ ] Durée réelle relevée et comparée

### Critères repris des réserves acceptées au `15a1` (propriétaire, 28/11/2026 : « J'accepte A2, A3 et A4 »)

1. **A2** : sourcer le repère réel de réussite des passes longues (environ 50 %, avancé de mémoire au 15a1, non vérifié) **avant le code du 15a2**, puis en faire un critère chiffré de la série de 50 matchs (15a1 : 68,9 %).
2. **A3** : mesurer la distance entre le receveur et le défenseur le plus proche au moment des réceptions aériennes, avant et après ; vérifier la cause de la baisse d'engagement de l'équipe sans possession relevée au 15a1 (distance au coéquipier le plus proche 12,8 → 13,2 m).
3. **A4** : suivre les touches par match (15a1 : 16,2 → 12,0 ; repère réel ≈ 42, fourchette 30 à 55, `docs/INDICATEURS_V2.md`) et expliquer, chiffres en main, l'écart au réel ; **sans cette explication, le 15a2 est bloqué**.

### Checklist des ballons aériens (série et scènes du 15a2)

- [ ] Instant du contact : premier instant sous le plafond retenu (tête si disputé, poitrine pour le receveur seul), tranche touchée tracée
- [ ] Cas d'usage séparés : relance longue, dégagement, corner centré, coup franc lobé (quand il existe), touche longue (16f)
- [ ] Touches par match (A4)
- [ ] Distance receveur / défenseur le plus proche à la réception aérienne (A3)
