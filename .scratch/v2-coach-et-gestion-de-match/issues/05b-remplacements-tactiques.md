# 05b: Remplacements tactiques selon le score, le style, les cartons et les blessures

**Découpé du ticket 05 le 04/11/2026** (audit de granularité). Détail : `05-remplacements-v2.md`.

**What to build:** le coach choisit **qui** entre selon l'état réel du match, sur la mécanique du 05a :
- **Score et style** (dosage du ticket 02) : menée → entrée d'un profil offensif à la place d'un défensif ou d'un récupérateur ; qui mène et protège → entrée d'un défenseur ou d'un milieu défensif, éventuellement passage à 5 derrière (changement de dispositif sans téléportation) ; Offensif qui mène → poste pour poste.
- **Cartons et blessures** : réorganisation après une expulsion (`v2-attributs-restants/09a`), remplacement forcé après une blessure (`09b`) ; aucun joueur expulsé n'est remplacé.

**Attributs :** attributs seuls (table poste/attributs, D-V07).

**Blocked by:** 05a, 01, 02 ; `v2-attributs-restants/09a` et `09b` pour les cas « carton » et « blessure » (ajoutés à leur livraison, sans bloquer le reste).

**Bloque :** aucun.

**Status:** à faire (constantes à proposer avant le code)

## Acceptance criteria

- [ ] Équipe menée : part des remplacements offensifs mesurablement supérieure à celle d'une équipe qui mène
- [ ] Un passage à 5 derrière se fait sans téléportation (test)
- [ ] Après une expulsion, l'équipe ne remplace pas l'expulsé ; après une blessure, le blessé sort au prochain arrêt de jeu
- [ ] Constantes produit et critères chiffrés validés par le propriétaire avant le code
- [ ] Déterministe pour une graine donnée ; suite V2 verte ; V1 inchangée
