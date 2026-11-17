# 03: Work Rate offensif : soutien et repli après la perte

**Chantier :** `v2-attributs-contextes` (ADR 0002). **Priorité :** P2. **Catégorie :** attributs.

**Constat (audit du 17/11/2026, corrigé le 17/11/2026 au lancement du ticket) :** Work Rate n'a aucun contexte du registre, mais il n'est pas lu que par le pressing : il règle aussi le replacement sans ballon et le trot en possession (`defense.replacement_intensity`, ticket `v2-realisme/12d`) et le repli après la perte (`cerveau`, rôle REPLI, à `press_intensity`, ticket `v2-collectif/10`). Le ticket `v2-realisme/12d` l'a écarté des appels (« seul Off the Ball »).

**What to build (réduit le 17/11/2026) :** le repli après la perte (rôle REPLI de `cerveau.py`, aujourd'hui à `defense.press_intensity`, Work Rate seul) devient le contexte « repli après la perte » du registre, Work Rate + Teamwork. Le soutien offensif est abandonné : il ajouterait des tirs à un écart de buts déjà fort (ticket `03m`).

**What to build (d'origine, avant réduction) :** Work Rate entre dans deux contextes nouveaux : « soutien offensif » (volume des courses pour se proposer au porteur, avec Off the Ball pour le moment et le choix de l'espace) et « repli après la perte » (intensité et délai du retour derrière le ballon, avec Teamwork). L'intensité de l'appel lui-même reste à Off the Ball (pas de double comptage avec 12d).

**Attributs :** Work Rate, Off the Ball, Teamwork (poids à proposer).

**Blocked by:** 01, 02.

**Status:** à faire, périmètre réduit le 17/11/2026 (décision du propriétaire : « Accepter, 03 réduit », après le ticket `03m`) : seul le repli après la perte, mis au registre ; constantes à valider avant le code

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 35 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 35 min |
| Intégration et vérifications | 30 min |
| **Total (travail effectif)** | **2 h 30** |

Confiance : faible. Hypothèses : les rôles soutien et replacement du cerveau (`cerveau.py`) portent déjà une intensité. Au-dessus du seuil de 2 h : découpage à examiner (soutien, puis repli).
Temps machine, non compté : suite complète ; séries de 50 matchs avant et après ; banc de profils de l'attribut (`scripts/measure_v2.py --profil`).

## Acceptance criteria

- [ ] Contexte, poids et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Contexte déclaré dans le registre et documenté dans la carte ; entrée retirée de la liste de transition du test de rayon
- [ ] Scène reproductible : 99 contre 11 sur l'attribut, effet probabiliste, jamais binaire
- [ ] 50 matchs avant/après sur l'indicateur visé ; profils 99 / 11 dans le plafond d'écart de la carte ; pas de double comptage (R1)
- [ ] Déterminisme à graine fixée ; suite complète passée, compte comparé à l'attendu de `CLAUDE.md`
- [ ] Durée réelle relevée et comparée à l'estimation

## Constat au lancement (17/11/2026, avant tout code)

Banc de profils `scripts/measure_v2.py 10 --profil "Work Rate"` (équipe à 99 contre équipe à 11) : km par joueur 12,75 contre 11,46 (+ 11 %) ; course intense 1 197 contre 676 m (+ 77 %) ; vitesse de repli à 1,5 s 2,03 contre 1,39 m/s (+ 46 %) ; appels par joueur 43,9 contre 34,3 (+ 28 %, effet indirect) ; temps de pressing 1 046 contre 963 s ; écart de tirs + 11,6 par match et de buts + 2,4 par match (4,5 contre 2,1, IC 95 % de 0,5 à 4,3), significatifs. Repère réel : à poste égal, la distance à haute intensité varie nettement d'un joueur à l'autre (FIFA, Coupe du monde 2022, https://www.fifatrainingcentre.com/en/fwc2022/physical-analysis/what-distances-did-various-positions-cover.php ; Bradley et al. 2009, https://sure.sunderland.ac.uk/id/eprint/3478/) ; lien entre volume d'effort et écart de buts : non trouvé.

Conclusion : Work Rate a déjà un rayon large (par lectures directes) et un effet fort sur le résultat. Brancher le soutien offensif et un repli plus intense augmenterait l'écart de buts. Décision du propriétaire : ne rien brancher, mesurer d'abord le plafond d'écart (ticket `03m`) ; Work Rate reste dans la liste de transition.

Durée passée sur ce ticket avant mise en attente : environ 30 min (analyse et constat). Temps machine : banc de profils de 10 matchs.
