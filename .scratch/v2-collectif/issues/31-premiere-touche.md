# 31: Première touche : passe à une touche et contrôle orienté

**What to build:** Toute réception coûte aujourd'hui 1,7 à 2,9 s, même pour un excellent joueur (`possession.reception_delay_s`, `possession.py:136-176`). Il n'existe aucune passe à une touche, ni remise, ni jeu direct, et un contrôle est réussi ou raté sans orientation. À l'écran, tout le monde contrôle puis joue. Ce ticket ajoute :

1. **Jeu à une touche** : sur une passe qui arrive, le receveur peut jouer sans contrôler (remise, passe à une touche, jeu direct) quand la passe suivante est prête, que la pression est supportable et que sa technique le permet. Decisions choisit entre jouer de première et contrôler ; le plan de passe du ticket 14 donne la suite préparée.
2. **Contrôle orienté** : le premier contact oriente le ballon vers l'espace libre ou vers la passe suivante, ce qui raccourcit le temps avant l'action suivante. Sans orientation, le contrôle reste comme aujourd'hui.
3. **Durée de réception** : elle dépend de First Touch, de Technique, de la pression et de la vitesse du ballon, et non plus d'une plage commune.

**Attributs :** First Touch, Technique (jeu de première), Anticipation (préparer le geste), Decisions (choisir). Le rayon exact de chacun est fixé dans `docs/CARTE_ATTRIBUTS_V2.md` avant le code, sans double comptage (ticket `v2-collectif/18`).

**Blocked by:** 14 (plan de passe, livré) ; `v2-realisme/07a` (orientation du corps), `07c` (réception de face, de profil ou dos au jeu), `07e` (réorientation avant l'action), `08c` (scan avant la réception).

**Complément (05/11/2026, décision du propriétaire) :** orientation et prise d'information sont avancées avant ce ticket et en forment la base. Le contrôle orienté s'appuie sur le type de réception (`v2-realisme/07c`) et sur le cap du corps (`07a`, `07e`) ; le jeu à une touche suppose que le receveur ait vu la suite (mémoire et scan, `08b`, `08c`). L'effet de l'orientation sur la durée de réception reste au `v2-realisme/07d`, après ce ticket.

**Status:** à faire (constantes à proposer avant le code)

**Origine (03/11/2026) :** audit de réalisme (décision Q11) : écart le plus important trouvé, il limite le rythme et les combinaisons.

**Chiffres réels :** part des passes jouées à une touche, durée moyenne de possession individuelle (valeur actuelle : 1,97 s, comparée dans `docs/INDICATEURS_V2.md`) : **non trouvées, à sourcer**.

**Point de vigilance :** le temps de calcul et le nombre de passes par minute (15 à 17 visés) bougent : remesurer le rythme, la réussite des passes, les retours au passeur et C2 (renvoyé au ticket 22).

## Acceptance criteria

- [ ] Constantes et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Scène contrôlée : à passe suivante prête et pression faible, un joueur à First Touch et Technique élevés joue de première plus souvent qu'un joueur à notes basses, jamais à 100 % ni 0 %
- [ ] Scène contrôlée : la pression adverse réduit les jeux de première
- [ ] Le contrôle orienté raccourcit le temps avant l'action suivante, mesurablement
- [ ] En match (50 matchs, graine d'audit) : part de passes à une touche, durée de possession individuelle, une-deux et troisième homme (ticket 14), comparés avant et après
- [ ] Rayon des attributs conforme à la carte, sans double comptage ; test de rayon à jour
- [ ] Indicateurs ajoutés au banc et définis dans `docs/INDICATEURS_V2.md`
- [ ] Déterminisme à graine fixée ; suite V2 verte ; V1 inchangée
