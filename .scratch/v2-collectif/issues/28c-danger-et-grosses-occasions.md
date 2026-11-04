# 28c: Danger et grosses occasions, avec ou sans tir

**Découpé du ticket 28 le 04/11/2026** (audit de granularité). Détail : `28-occasion-et-issue-du-tir.md`, points 2, 6 et 7 (partie séquence).

**What to build:**

1. **Danger de la situation** : à chaque instant de la possession, la meilleure occasion potentielle parmi les attaquants (qualité du 28a), pondérée par la probabilité que le ballon leur parvienne. Une **grosse occasion** est un pic de danger au-dessus d'un seuil, **quelle que soit l'issue**.
2. **Issue d'une séquence dangereuse sans tir** : tacle ou interception salvateur, dégagement, centre non repris.
3. **Trace** : séquence dangereuse (début, pic de danger, issue), utilisée par les modes « Moments clés » et « Résumé » (`v2-mise-en-scene/02` et `03`).

**Attributs :** aucun nouveau.

**Blocked by:** 28a.

**Bloque :** `v2-mise-en-scene/02` et `03` ; 17, 19 et 22a (le 28 est « à livrer avant 17, 19 et 22 »).

**Status:** à faire (constantes à proposer avant le code)

## Acceptance criteria

- [ ] Seuil de grosse occasion proposé avec un nombre plausible par match (aucun chiffre réel pour cette définition large) et validé par le propriétaire avant le code
- [ ] Scène contrôlée : le centre qui traverse la surface et laisse un attaquant à deux doigts du but vide est une grosse occasion sans tir ; un face-à-face stoppé par un tacle salvateur aussi ; un tir de loin sans danger ne l'est pas
- [ ] Les séquences dangereuses sans tir sont tracées avec leur pic de danger, leur issue et leur origine
- [ ] Nombre de grosses occasions par match rapporté sur 50 matchs (graine d'audit) ; indicateur ajouté au banc et défini dans `docs/INDICATEURS_V2.md`
- [ ] Le calcul du danger ne change pas le jeu (mesures V2 identiques à graine fixée, hors nouveaux champs de trace)
- [ ] Déterminisme à graine fixée ; suite V2 verte ; V1 inchangée
