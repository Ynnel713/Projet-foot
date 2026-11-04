# 32a: Passes en retrait et en profondeur

**Découpé du ticket 32 le 04/11/2026** (audit de granularité) : ces deux passes sont au sol et ne dépendent pas de la hauteur du ballon. Détail : `32-types-de-passes.md`, points 2 et 3.

**What to build:**

1. **Passe en retrait** : vers un défenseur ou le gardien, pour relâcher la pression ou changer de côté. Elle existe comme simple passe vers un partenaire plus proche de son but (`defense.py:102`), reconnue seulement comme déclencheur de pressing ; elle devient un choix reconnu, avec son risque.
2. **Passe en profondeur** : visée vers l'espace derrière la ligne adverse pour un joueur qui appelle (ticket 16), distincte d'une passe au sol ordinaire. Le hors-jeu la rend risquée.

Le changement de jeu en diagonale et le jeu long face au pressing restent au ticket 15.

**Attributs :** Passing (exécution), Vision (voir l'espace), Decisions (choisir), Flair (options risquées). Rayons à fixer dans `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage.

**Blocked by:** 33, 29, 16 (tous livrés) : démarrable. À livrer avec le 15.

**Bloque :** 32b ; 22a.

**Status:** à faire (constantes à proposer avant le code)

**Chiffres réels :** part de passes en retrait et en profondeur : **non trouvées, à sourcer**. Sans chiffre, chaque type apparaît au moins une fois sur 50 matchs et aucun ne domine. Rappel (ticket 22, base du 01/11/2026) : passes en profondeur à 0,2 %, cause principale du déficit de hors-jeu.

## Acceptance criteria

- [ ] Constantes et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Test de cohérence (scènes fixes) : la passe en retrait est plus fréquente sous pression à l'avant ; la passe en profondeur suit un appel dans le dos avec de l'espace derrière la ligne
- [ ] Chaque type est tracé et affiché à l'écran
- [ ] En match (50 matchs, graine d'audit) : répartition des types, réussite par type, hors-jeu par match, comparés avant et après
- [ ] Rayon des attributs conforme à la carte, sans double comptage
- [ ] Déterminisme à graine fixée ; suite V2 verte ; V1 inchangée
