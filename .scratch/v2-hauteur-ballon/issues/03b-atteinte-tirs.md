# 03b: Interception selon la hauteur : tirs

**Découpé du ticket `03` le 23/11/2026** (décision du propriétaire). Référence : `03-interception-selon-hauteur.md` ; réserve A1 de l'expert au `02a2` (7 contres sur 348 au-dessus de 2,5 m, 2 arrêts sur 324 au-dessus de la barre, sur 50 matchs).

**What to build:** le contre (`match._blocked`) et l'arrêt par portée (`match._keeper_reaches`) lisent la hauteur réelle du tir au point de contact (`ShotEvent.block_z_m`, `keeper_z_m`, ticket `02a2`) avec l'atteinte du `03a` : un défenseur ne contre qu'un ballon à sa portée, le gardien n'arrête qu'un ballon à la portée de ses mains. L'issue des tirs peut changer (contres, arrêts) : mesurée.

**Attributs :** ceux du `03a` (taille, Jumping Reach) ; aucun nouveau.

**Blocked by:** `03a`.

**Bloque :** `02b` (recommandation de l'expert au `02a2` : aucun contre au-dessus de la tête à l'écran).

**Status:** à faire

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 10 min |
| Développement | 20 min |
| Tests unitaires et comportementaux | 15 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h** |

Confiance : moyenne. Temps machine, non compté : deux séries de 50 matchs (environ 40 min chacune), suite complète (environ 17 min).

**Constantes :** celles du `03a` ; aucune nouvelle.

## Acceptance criteria

- [ ] Scènes : tir au-dessus de l'atteinte d'un défenseur sur sa ligne : non contré ; tir à portée : contré comme avant
- [ ] 50 matchs : 0 contre et 0 arrêt au-dessus de l'atteinte du joueur ; contres, arrêts, buts avant/après, écarts expliqués
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 %
- [ ] Déterminisme ; suite complète au compte attendu ; V1 inchangée
