# 15a2: Maintien du premier désigné sur un ballon aérien

**Chantier :** `v2-realisme` (réserve A1 de l'expert au ticket `15a`, 23/11/2026, acceptée par le propriétaire : « Accepter, corriger en ticket »). **Priorité :** P2. **Catégorie :** décision.

**Constat vérifié (15a) :** dans `jeu_aerien.select_attackers`, la clé de tri est `(non receveur, pas à temps, instant du contact arrondi, arrivée − maintien, nom)` : le maintien de 0,3 s (`ATTACKER_HOLD_S`) ne départage que deux joueurs qui touchent le ballon au même pas de 0,1 s. Un coéquipier qui touche un pas plus tôt passe devant le désigné, même avec 0,04 s d'avance à l'arrivée. Mesure (50 matchs, `docs/INDICATEURS_V2.md` § 76) : le premier désigné change en moins de 1 s dans 12 % des désignations.

**What to build:** appliquer le maintien aussi à l'instant du contact du joueur déjà désigné (correctif proposé par l'expert : `round(contact_s − hold, 6)` dans la clé), sans changer le classement par portée hors maintien.

**Attributs :** aucun. **Constantes :** aucune nouvelle (`ATTACKER_HOLD_S` validée au 15a).

**Blocked by:** `15a` (livré). **À faire avant ou avec :** `15b`.

**Status:** à faire

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 5 min |
| Développement | 10 min |
| Tests unitaires et comportementaux | 15 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **50 min** |

Confiance : élevée. Temps machine, non compté : série de 50 matchs appariée (environ 37 min), suite complète (environ 17 min).

## Tests

- Scène : un coéquipier qui arrive 0,05 s plus tôt mais touche un pas avant ; le désigné reste premier. Un coéquipier qui arrive 0,4 s plus tôt le remplace.
- Série : « ballon aérien : changements du premier en moins de 1 s (part) » nettement sous 12 %.

## Acceptance criteria

- [ ] Scène du maintien à pas différents
- [ ] Changements rapides du premier nettement sous 12 % (50 matchs appariés)
- [ ] Déterminisme à graine fixée ; suite complète au compte attendu
