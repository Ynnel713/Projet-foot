# 10: Types de finition

**What to build:** Phase 7 du plan V2 (gestes offensifs). Une fois l'occasion et son issue réalistes (`v2-collectif/28`), le tireur choisit **comment** finir, d'abord selon la situation, pour que les buts soient variés **et** cohérents :

1. **La situation ouvre les options** : distance, angle, gardien avancé ou sur sa ligne, pression, ballon reçu en mouvement ou arrêté.
2. **Decisions choisit** parmi les options ouvertes ; **Flair** ajoute les options risquées ; les **gestes préférés** (ticket 05 : Places Shots, Shoots With Power, Tries First Time Shots, Curls Ball, Likes To Lob Keeper, Likes To Round Keeper…) biaisent seulement la fréquence, jamais la réussite.
3. **Faisable dès T1 livré** : frappe placée ou puissante (compromis précision contre temps de réaction du gardien) ; enroulée (Technique) ; première intention ou volée (Technique, carte des attributs) ; côté ouvert ou côté fermé selon la position du gardien (et le pied fort après le ticket 04).
4. **Après le ticket 03 (sortie du gardien, Rushing Out)** : lob et dribble du gardien ; le dribble du gardien se résout par Dribbling contre One on Ones, coordonné avec le ticket 07 (pas de second duel en double).

**Attributs :** Decisions, Flair, Technique, Finishing ; Dribbling et One on Ones (dribble du gardien) ; gestes préférés en penchants.

**Blocked by:** v2-collectif/28, v2-collectif/19 (principe des penchants), v2-collectif/22 ; lob et dribble du gardien : 03 et 07.

**Status:** découpé (04/11/2026, audit de granularité) en 10a (placée, puissante, enroulée, première intention) et 10b (lob et dribble du gardien). Ticket chapeau : ne pas l'implémenter tel quel ; le texte ci-dessous reste la référence de détail. Une référence à ce ticket sans lettre vaut pour tous ses morceaux.

**Origine (03/11/2026) :** consultation de l'expert demandée par le propriétaire ; recommandations acceptées.

**Hors périmètre :** têtes et centres (01) ; mesure geste par geste des gestes de tir (05, qui s'appuie sur les penchants posés par 10a et 10b) ; notes du gardien (03) ; penalties et coups francs (02).

**Point de vigilance :**
- Variété artificielle interdite : tirer un type au hasard dans une liste donne de la variété sans cohérence. Le type doit dépendre de la situation (test de cohérence ci-dessous) ; sinon le ticket est refusé.
- Pas de double comptage : Technique (enroulée, volée) ne recouvre pas Finishing ; Flair et gestes préférés ne changent que la fréquence.
- D-V03 : lob, enroulée et volée sont des catégories résolues à plat (géométrie et tirage pondéré), sans trajectoire 3D ; un lob n'est pas contré comme une passe au sol. Le rendu rejoue le type et l'issue tracés.
- Fréquences réelles des lobs, dribbles du gardien, frappes enroulées, côté ouvert ou fermé, première intention : **non trouvées** à ce jour.

## Acceptance criteria

- [ ] Constantes produit (poids de chaque type selon la situation) et critères validés par le propriétaire avant le code
- [ ] Test de cohérence (scènes fixes) : la part de lobs est nettement plus forte gardien avancé que gardien sur sa ligne ; la frappe placée est plus fréquente avec Finishing élevé ; la première intention suit un ballon reçu en mouvement
- [ ] Chaque type apparaît au moins une fois sur 50 matchs et aucun ne domine (pas de valeur visée faute de chiffre réel)
- [ ] Diversité des buts mesurée sur 50 matchs ou plus (zone × type × issue × origine), comparée avant / après
- [ ] Type de finition tracé et rejoué par le rendu, sans changer l'issue
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage (ticket v2-collectif/18)
- [ ] Déterminisme à graine fixée ; suite V2 verte ; V1 inchangée
