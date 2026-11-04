# 03: Résumé du match

**What to build:** Mode de visionnage qui montre tout ce qui vaut d'être vu, en environ 10 minutes.

- Chaque passage de match reçoit un **score d'intérêt** : but, grosse occasion, arrêt décisif, tacle ou faute marquants, échauffourée, belle séquence collective, célébration. Le même score sert aux Moments clés, avec un seuil plus haut.
- On garde les meilleurs passages dans l'ordre chronologique, sans enchaîner dix passages semblables.
- **Durée** : environ 10 minutes, de 8 à 12 selon l'intérêt du match. Un 0-0 fermé donne un résumé plus court, un match riche un résumé plus long.
- Sans spoiler : aucun score ni repère futur avant le passage.

**Attributs :** aucun.

**Blocked by:** `v2-collectif/28` (danger), 29 (sorties et corners), 30 (fautes), 31 (belles séquences à une touche), `v2-mise-en-scene/01`. Les célébrations (04) et les échauffourées (`v2-attributs-restants/09c`) s'y ajoutent à leur livraison.

**Status:** à faire (constantes à proposer avant le code)

**Constantes à proposer :** poids de chaque type de passage dans le score d'intérêt ; bornes de durée ; règle de non-répétition.

## Acceptance criteria

- [ ] Constantes validées par le propriétaire avant le code
- [ ] Un match très pauvre donne un résumé plus court qu'un match riche (scènes fixes)
- [ ] Le résumé n'enchaîne pas plus de N passages de même type et même issue (règle écrite et testée)
- [ ] Durée du résumé entre 8 et 12 minutes sur 50 matchs, rapportée
- [ ] Aucun score ni repère futur avant chaque passage
- [ ] Déterminisme à graine fixée ; suite V2 verte ; `npm run build` et `npm run lint` OK ; V1 inchangée
