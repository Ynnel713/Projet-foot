# 07b: Agility et Balance

**Découpé du ticket 07 le 04/11/2026** (audit de granularité). Détail : `07-duels-agility-dribbling.md`.

**What to build:**
- **Agility** : changer de direction, freiner, se retourner sans perdre de vitesse (porteur qui crochète, défenseur qui suit, gardien qui se relève) ; remplace le freinage commun `DECEL_MAX_MPS2` de v2-collectif/25 par un freinage modulé.
- **Balance** : rester debout et continuer l'action **après** un contact perdu (levée de la dérogation A3).

**Attributs :** Agility, Balance.

**Blocked by:** `v2-collectif/25` (livré) : démarrable. Indépendant de 07a (cinématique, pas décision).

**Bloque :** `v2-collectif/22a`.

**Status:** découpé (05/11/2026, chantier `v2-realisme`, validé par le propriétaire) en `v2-realisme/12a` (freinage, Agility), `12b` (perte de vitesse en virage, Agility), `12c` (Balance après le contact, levée de la dérogation A3), avec `07f` (rotation du corps, Agility). Ticket chapeau : ne pas l'implémenter tel quel ; le texte ci-dessous reste la référence de détail. Une référence à ce ticket sans lettre vaut pour tous ses morceaux.

**Point de vigilance :** Strength gagne le contact, Balance joue après : ne pas compter deux fois (v2-collectif/18).

## Acceptance criteria

- [ ] Agility élevée : moins de vitesse perdue dans un changement de direction (mesuré sur les trajectoires)
- [ ] Balance élevée : plus d'actions poursuivies après un contact perdu ; dérogation A3 levée
- [ ] Constantes produit et critères chiffrés validés par le propriétaire avant le code
- [ ] Déterminisme à graine fixée ; suite V2 verte ; V1 inchangée
