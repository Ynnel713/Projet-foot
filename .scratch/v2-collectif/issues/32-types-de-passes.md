# 32: Types de passes : lobée, en retrait, en profondeur

**What to build:** Toutes les passes sont au sol et de même nature (`possession.pass_aim`, `pass_velocity`). Ce ticket ajoute trois passes distinctes, choisies selon la situation :

1. **Passe lobée** : par-dessus la défense vers un joueur lancé ou un espace. Elle utilise le mode de ballon aérien du ticket 29 : un joueur au sol ne l'intercepte pas sur son trajet, seulement à son point de chute. Plus difficile qu'une passe au sol sur la même distance.
2. **Passe en retrait** : vers un défenseur ou le gardien, pour relâcher la pression ou changer de côté. Elle existe déjà comme simple passe vers un partenaire plus proche de son but (`defense.py:102`), reconnue seulement comme déclencheur de pressing ; elle devient un choix reconnu, avec son risque.
3. **Passe en profondeur** : visée vers l'espace derrière la ligne adverse pour un joueur qui appelle (ticket 16), distincte d'une passe au sol ordinaire. Le hors-jeu la rend risquée.

Le changement de jeu en diagonale et le jeu long face au pressing restent au ticket 15.

**Attributs :** Passing (exécution), Vision (voir l'espace), Decisions (choisir), Flair (options risquées), Technique pour la lobée si la carte le prévoit. Rayons à fixer dans `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage.

**Blocked by:** 33 (cadre de la décision du porteur : chaque type de passe est une option de plus), 29 (mode de ballon), 16 (appels dans le dos), `v2-hauteur-ballon/03` (la lobée passe au-dessus des joueurs selon sa vraie hauteur, et non plus selon le seul mode). À livrer avec le 15.

**Status:** découpé (04/11/2026, audit de granularité) en 32a (passes en retrait et en profondeur, démarrable) et 32b (passe lobée, après `v2-hauteur-ballon/03`). Ticket chapeau : ne pas l'implémenter tel quel ; le texte ci-dessous reste la référence de détail. Une référence à ce ticket sans lettre vaut pour tous ses morceaux.

**Origine (03/11/2026) :** audit de réalisme (décision Q12).

**Chiffres réels :** part de passes lobées, en retrait, en profondeur : **non trouvées, à sourcer**. Sans chiffre, chaque type doit apparaître au moins une fois sur 50 matchs et aucun ne domine.

## Acceptance criteria

- [ ] Constantes et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Test de cohérence (scènes fixes) : la lobée est plus fréquente quand la ligne de passe au sol est fermée et qu'il y a de l'espace derrière la défense ; la passe en retrait est plus fréquente sous pression à l'avant
- [ ] Une passe lobée n'est pas interceptée par un joueur au sol sur son trajet (test)
- [ ] Chaque type est tracé avec son mode de ballon et affiché à l'écran
- [ ] En match (50 matchs, graine d'audit) : répartition des types, réussite par type, comparées avant et après
- [ ] Rayon des attributs conforme à la carte, sans double comptage
- [ ] Déterminisme à graine fixée ; suite V2 verte ; V1 inchangée
