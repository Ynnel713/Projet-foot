# 04: Célébrations

**What to build:** Après un but, les joueurs célèbrent de façon **variée et cohérente**, pendant le ballon mort du ticket `v2-collectif/29` (avant l'engagement).

- **Intentions de joueurs** affichées par le rendu existant avec une étiquette : course vers le coin ou les supporters, regroupement avec le passeur, glissade, geste individuel, retour calme.
- **La situation décide**, jamais un tirage libre : importance du but (ouverture du score, égalisation, but vainqueur, dernière minute, but qui scelle), score, minute, buteur (personnalité, geste préféré « Gets Crowd Going »), passeur.
- **Temps réel** : le ballon mort de la célébration est compté dans le temps additionnel (`v2-coach-et-gestion-de-match/03`).
- **Aucun effet sur le résultat sportif.** La célébration est tracée (type, joueurs, minute).
- **« Gets Crowd Going »** (81 joueurs environ) est rattaché ici : il augmente la fréquence et l'ampleur de la célébration. Décision de propriétaire du ticket `v2-attributs-restants/05` résolue.

**Attributs :** aucun attribut de réussite ; geste préféré « Gets Crowd Going » en penchant (fréquence seulement).

**Blocked by:** `v2-collectif/29`, `v2-mise-en-scene/01` (buteur et passeur dans la trace).

**Status:** à faire (constantes à proposer avant le code)

**Constantes à proposer :** durée de chaque type de célébration ; poids des facteurs dans le choix.

## Acceptance criteria

- [ ] Constantes validées par le propriétaire avant le code
- [ ] Test de cohérence (scènes fixes) : le but de la dernière minute ou de l'égalisation donne plus souvent une célébration ample et collective qu'un but en début de match avec trois buts d'avance
- [ ] « Gets Crowd Going » augmente la fréquence de la célébration, sans effet sur le jeu
- [ ] Chaque type apparaît au moins une fois sur 50 matchs et aucun ne domine
- [ ] La durée de célébration est comptée dans le temps additionnel
- [ ] Célébration tracée et affichée (étiquette) ; résultat sportif inchangé
- [ ] Déterminisme à graine fixée ; suite V2 verte ; `npm run build` et `npm run lint` OK ; V1 inchangée
