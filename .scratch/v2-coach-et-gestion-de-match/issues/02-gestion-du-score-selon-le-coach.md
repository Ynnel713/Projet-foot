# 02: Gestion du score selon le style du coach

**What to build:** Moduler par le style du coach les paramètres de l'adaptation au score de v2-collectif/21 (minute de début, amplitude), **sans seconde mécanique**. L'attitude est un **dosage continu** qui dépend du style, de l'écart et de la minute, jamais un choix binaire :

- **Équipe menée** : se découvre progressivement (bloc plus haut, plus de joueurs projetés, plus de risque dans la passe et le tir). Un coach Défensif s'y résout plus tard et moins ; Offensif ou Pressing plus tôt. L'extrémité de cette courbe (fin de match, un but d'écart) est le « tout pour égaliser » du ticket 04.
- **Équipe qui mène**, trois tendances que le style dose :
  - *Protéger en reculant* (Défensif, Contre attaque) : bloc plus bas, moins de joueurs au-delà du ballon, **possession concédée**, plus de dégagements, contres en profondeur.
  - *Protéger en gardant le ballon* (Possession) : possessions plus longues, tempo plus lent, moins de passes vers l'avant, risque réduit.
  - *Continuer d'attaquer* (Offensif, Pressing) : garde son plan, baisse modérée du risque seulement en toute fin de match.
  - Sans style : comportement générique de v2-collectif/21.
- **Égalité en fin de match** : selon le style, l'équipe pousse pour gagner ou sécurise le nul (comportement générique de 21 sans style).
- La gestion du temps de l'équipe qui mène (lenteur des remises en jeu) alimente le temps additionnel (ticket 03).

**Attributs :** Determination et Leadership (déjà dans v2-collectif/21) ; aucun nouveau.

**Blocked by:** 01 ; v2-collectif/21 (qui doit exposer l'adaptation au score comme des paramètres modulables).

**Status:** à faire (constantes à proposer avant le code)

**Point de vigilance :** effet réel du score sur la possession à sourcer (Lago-Peñas et Dellal 2010 ; Bloomfield et al. 2005 : l'équipe qui mène a en moyenne moins le ballon).

- [ ] Définir dans `docs/INDICATEURS_V2.md` et ajouter à `scripts/v2_indicators.py` : part de possession par tranche de 15 min et par état du score, joueurs dans la surface adverse, dégagements
- [ ] À score et minute égaux, deux coachs de styles opposés produisent une hauteur de bloc et un nombre de joueurs projetés mesurablement différents
- [ ] Équipe menée d'un but à partir de la 75e : bloc plus haut et plus de joueurs dans la surface adverse qu'à 0-0 à la même minute
- [ ] Coach Défensif qui mène : bloc plus bas, part de possession **plus basse**, plus de dégagements qu'à égalité
- [ ] Coach Possession qui mène : possessions plus longues et moins de passes vers l'avant qu'à égalité
- [ ] Effet progressif (minute, écart), jamais une bascule à une minute fixe
- [ ] Mesure par scénarios forcés (score et minute imposés, N graines, N et intervalle fixés avant la mesure)
- [ ] Constantes produit et critères chiffrés (données réelles sourcées, ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Suite V2 verte ; V1 inchangée
