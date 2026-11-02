# 05: Remplacements en V2

**What to build:** Le moteur V2 ne fait aujourd'hui aucun remplacement. Ajouter un banc et jusqu'à 5 remplacements en 3 fenêtres (la mi-temps ne compte pas comme fenêtre), décidés par le coach à partir de l'état réel :

- **Fatigue** (réserve d'énergie de v2-collectif/12) : le joueur le plus épuisé à son poste sort en priorité.
- **Score et style** (dosage du ticket 02) : menée → entrée d'un profil offensif à la place d'un défensif ou d'un récupérateur ; qui mène et protège → entrée d'un défenseur ou d'un milieu défensif, éventuellement passage à 5 derrière ; Offensif qui mène → poste pour poste.
- **Cartons et blessures** quand le moteur les modélise (v2-attributs-restants/09).
- **Exécution physique** : le changement n'a lieu que sur un arrêt de jeu (ballon sorti, faute, but) ou à la mi-temps ; le sortant quitte le terrain, l'entrant entre par la ligne médiane, puis rejoint sa position ; un éventuel changement de dispositif se fait sans téléportation. Un entrant hors de son poste naturel subit la pénalité de v2-attributs-restants/04.

Les remplacements sont enregistrés dans la trace (minute, sortant, entrant) et nourrissent le temps additionnel (ticket 03).

**Attributs :** Stamina (via la fatigue) ; attributs seuls (table poste/attributs, D-V07) pour le choix de l'entrant ; Postes naturels (via v2-attributs-restants/04).

**Blocked by:** 01, 02, 03 (mi-temps) ; v2-collectif/12 ; v2-attributs-restants/02 (arrêts de jeu) et 04.

**Status:** à faire (constantes à proposer avant le code)

**Point de vigilance :** la sélection des remplaçants réutilise `ligue1sim.lineup` en lecture seule (D-V02). Aucun joueur expulsé ne peut être remplacé. Choix de l'entrant par les attributs seuls (table poste/attributs, D-V07), jamais par la Moyenne FM : décision du propriétaire du 02/11/2026.

- [ ] Nombre de remplacements et minutes dans des fourchettes réelles sourcées (ou « non trouvé ») ; aucun avant la mi-temps sauf blessure
- [ ] Aucun remplacement pendant que le ballon est en jeu
- [ ] Équipe menée : part des remplacements offensifs mesurablement supérieure à celle d'une équipe qui mène
- [ ] Les sortants sont en moyenne plus fatigués que les joueurs restés sur le terrain au même poste
- [ ] Un entrant frais court mesurablement plus que le sortant
- [ ] Remplacements visibles dans la trace et l'UI V2
- [ ] Déterministe pour une graine donnée
- [ ] Suite V2 verte ; V1 inchangée
