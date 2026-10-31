# 26: Le passeur reprend sa propre passe (correctif du ticket 25)

**What to build:** Depuis le ticket 25 (contact sur le trajet du ballon), plus d'une passe sur deux revient dans les pieds de son propre passeur, dès le pas suivant. Le passeur ne doit jamais toucher la passe qui part de ses pieds ; il ne peut la reprendre que si elle revient vers lui ou s'il la rattrape réellement, une fois qu'elle est sortie de son rayon de contact.

**Attributs :** aucun (correctif de géométrie, pas de constante produit).

**Blocked by:** aucun. **Bloque :** la recalibration du hors-jeu (diagnostic du 30/10/2026, `.scratch/v2-collectif/diagnostic-hors-jeu-30-10-2026.md`) et toute mesure de passes, de possession et de buts depuis `4d71418`.

**Status:** livré (31/10/2026), validé expert + QC

**Origine :** diagnostic du hors-jeu, piste B validée par le propriétaire le 31/10/2026. Les attaquants ne sont pas plus loin de la ligne qu'avant le ticket 25 (attaquant le plus avancé à 6,9 m de la ligne en médiane, contre 8,7 m), mais les passes vers un receveur hors-jeu ne sont plus sifflées (3 % contre 41 %, 8 matchs) : 69 % reviennent au passeur (4 matchs).

## Constat (31/10/2026, état `c379ba6`, 2 matchs, graine d'audit)

- 2 236 passes sur 4 210 (53 %) sont reprises par leur passeur ; 19,5 % seulement arrivent au receveur visé.
- Reprise au pas suivant (0,1 s en médiane), ballon à 0,31 m de son point de départ, passe partie à 11,7 m/s en médiane.
- Cause (`v2engine/match.py`, `_contacts`) : le passeur est exclu tant que le ballon « s'éloigne de lui », jugé par le signe de `r0 · seg` (position relative de départ × déplacement relatif). Au départ, `r0` est presque nul ; sa direction n'est que l'erreur d'estimation de la position du passeur en début de pas (`position - vitesse × dt`, fausse dès qu'il accélère ou freine). Le signe est donc tiré à pile ou face.

## Correctif

« Le ballon s'éloigne de lui » se juge sur la distance : elle ne diminue pas pendant le pas (`|r1| >= |r0|`). Une ligne dans `_contacts`, aucune constante.

## Critères d'acceptation (définis avant le code)

- [x] Test : un passeur en mouvement (qui accélère, freine ou tourne) ne touche pas la passe qui part de ses pieds, quelle que soit la direction de la passe et le pas (0,05 / 0,1 / 0,15 s) ; le test échoue avant le correctif
- [x] Le passeur peut toujours reprendre une passe qui revient vers lui (test existant ou ajouté)
- [x] Mesure (2 matchs au moins) : passes reprises par leur passeur dans la seconde qui suit moins de 1 % (53 % avant)
- [x] Mesure avant/après 20 matchs, mêmes graines : hors-jeu, passes réussies, possession, tirs, buts (indicateurs, pas objectifs : la recalibration du hors-jeu et le ticket 22 suivent)
- [x] Suite V2 verte ; V1 inchangée

## Résultats (31/10/2026)

- Test de la passe qui part (96 cas : 8 directions de passe × 4 de course × 3 pas) : 36 échecs avant le correctif, 0 après ; test de la passe qui revient ajouté. Fichier de cinématique : 140 passés.
- Retour au passeur (2 matchs, copie figée) : 53,1 % → **0,8 %** (23 passes sur 2 858, reprises 3 s après en médiane, ballon à 11,9 m : de vrais rattrapages ou ballons revenus) ; receveur visé 19,5 % → 59,1 %.
- Avant/après 20 matchs (mêmes graines, `c379ba6` contre `c379ba6` + correctif), indicateurs :

| Indicateur | Avant | Après |
|---|---|---|
| Receveur visé (part des passes) | 19,5 % | 60,8 % |
| Passes réussies | 75,4 % | 64,3 % |
| Passes chez l'adversaire | 24,6 % | 35,6 % |
| Passes par minute | 23,8 | 16,2 |
| Hors-jeu par match | 0,2 | 0,75 |
| Tirs par équipe | 18,2 | 8,2 |
| Buts par match | 4,3 | 1,75 |
| Possession d'équipe (s) | 8,9 | 9,7 |

  Les chiffres d'avant étaient faussés : une passe sur deux restait au passeur (comptée réussie). Les passes vont maintenant au bout ; 36 % finissent chez l'adversaire, ce qui pèse sur les tirs et les buts (à traiter par la recalibration du hors-jeu, le ticket 22 et un suivi de la précision des passes).
- Suite V2 : 342 passés.

## Comments

- 31/10/2026, passage 1 (base `7318838`, empreinte `d825077d`) : expert APPROVED, QC VALIDÉ, clôture VALIDÉ. Aucune anomalie bloquante. Points facultatifs de l'expert : A1, le test de la passe qui revient part à 1 m, hors du rayon de contact, et ne passe donc pas par la branche modifiée (cas à 0,3 m à ajouter) ; A2, un passeur rapide qui double sa propre passe lente ne la touche pas (non observé, à surveiller si des une-deux courts arrivent) ; A3, lignes vides dans le test. QC : référence de 2 124 tests de `CLAUDE.md` à mettre à jour (2 222 passés, 13 désélectionnés). À retenir pour la suite : 35,6 % de passes chez l'adversaire et 8,2 tirs par équipe deviennent la base de la recalibration du hors-jeu et du ticket 22.
