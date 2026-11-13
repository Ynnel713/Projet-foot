# 31c: Durée de réception selon First Touch, Technique, pression et vitesse du ballon

**Découpé du ticket 31 le 13/11/2026** (validé par le propriétaire). Détail : `31-premiere-touche.md`, point 3.

**What to build:** La durée de réception (`possession.reception_delay_s`) dépend déjà de First Touch et de la pression ; elle dépendra aussi de Technique et de la vitesse du ballon reçu, au lieu d'une plage commune.

**Hors de ce ticket :** effet de l'orientation du corps sur le temps de contrôle (`v2-realisme/07d`, qui s'y ajoute sans double comptage).

**Attributs :** First Touch, Technique. Rayons à fixer dans la carte, sans double comptage.

**Blocked by:** 31b.

**Bloque :** `v2-realisme/07d`.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 30 min |
| Tests unitaires et comportementaux | 20 min |
| Intégration et vérifications | 25 min |
| **Total (travail effectif)** | **1 h 30** |

Confiance : moyenne. Temps machine, non compté : suite complète ; 50 matchs avant/après.

## Acceptance criteria

- [ ] Constantes et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Scène contrôlée : ballon plus rapide, réception plus longue ; Technique élevée, réception plus courte
- [ ] En match (50 matchs) : durée de possession individuelle et rythme (passes par minute) avant et après
- [ ] Rayon des attributs conforme à la carte ; test de rayon à jour
- [ ] Durée réelle relevée (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée ; suite V2 verte ; V1 inchangée

## Comments
