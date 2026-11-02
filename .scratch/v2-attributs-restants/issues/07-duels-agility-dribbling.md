# 07: Duels : Agility, Dribbling, Balance après contact

**What to build:** `docs/CARTE_ATTRIBUTS_V2.md` renvoie Agility et Dribbling à une « étape duels » qui n'existe ni dans `docs/PLAN_V2.md` ni dans les tickets. Brancher :

- **Dribbling** : chance d'éliminer en un contre un et de garder le ballon en conduite serrée (côté porteur du duel de v2-socle/03).
- **Agility** : changer de direction, freiner, se retourner sans perdre de vitesse (porteur qui crochète, défenseur qui suit, gardien qui se relève) ; remplace le freinage commun `DECEL_MAX_MPS2` de v2-collectif/25 par un freinage modulé.
- **Balance** : rester debout et continuer l'action **après** un contact perdu (levée de la dérogation A3).

**Attributs :** Dribbling, Agility, Balance.

**Blocked by:** —

**Status:** à faire (constantes à proposer avant le code)

**Point de vigilance :** Strength gagne le contact, Balance joue après : ne pas compter deux fois (v2-collectif/18).

- [ ] Dribbling élevé : plus de duels gagnés par le porteur, à défenseur égal
- [ ] Agility élevée : moins de vitesse perdue dans un changement de direction (mesuré sur les trajectoires)
- [ ] Balance élevée : plus d'actions poursuivies après un contact perdu ; dérogation A3 levée
- [ ] Constantes produit et critères chiffrés validés par le propriétaire avant le code
- [ ] Suite V2 verte ; V1 inchangée
