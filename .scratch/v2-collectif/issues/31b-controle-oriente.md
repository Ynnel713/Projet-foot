# 31b: Contrôle orienté

**Découpé du ticket 31 le 13/11/2026** (validé par le propriétaire). Détail : `31-premiere-touche.md`, point 2.

**What to build:** Le premier contact oriente le ballon vers l'espace libre ou vers la passe suivante, ce qui raccourcit le temps avant l'action suivante ; sans orientation, le contrôle reste comme aujourd'hui. S'appuie sur le type de réception (`v2-realisme/07c`) et le cap du corps (`07a`, `07e`).

**Hors de ce ticket :** jeu à une touche (31a), durée de réception selon les notes (31c), effet de l'orientation sur le temps de contrôle (`v2-realisme/07d`).

**Attributs :** First Touch (qualité du contact), Anticipation, Vision (choisir où orienter). Rayons à fixer dans la carte, sans double comptage.

**Blocked by:** 31a.

**Bloque :** 31c, `v2-realisme/07d`.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 30 min |
| **Total (travail effectif)** | **2 h 15** |

Confiance : moyenne. Temps machine, non compté : suite complète ; 50 matchs avant/après.

## Acceptance criteria

- [ ] Constantes et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Scène contrôlée : le contrôle orienté raccourcit le temps avant l'action suivante, mesurablement
- [ ] En match (50 matchs) : part des contrôles orientés, durée de possession individuelle, avant et après
- [ ] Rayon des attributs conforme à la carte ; test de rayon à jour
- [ ] Durée réelle relevée (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée ; suite V2 verte ; V1 inchangée

## Comments
