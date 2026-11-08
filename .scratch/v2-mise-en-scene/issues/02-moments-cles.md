# 02: Moments clés

**What to build:** Mode de visionnage qui ne montre que les **grosses occasions, les buts et les cartons rouges**.

- **Grosse occasion** : séquence dont le pic de danger dépasse un seuil, quelle que soit l'issue (définition et seuil du ticket `v2-collectif/28`). Le moment couvre la séquence jusqu'à son issue : but, arrêt, tir à côté ou contré, tacle ou interception salvateur, centre non repris, dégagement.
- **Carton rouge** : ajouté quand les cartons existent (`v2-attributs-restants/09a`).
- Les moments qui se chevauchent sont fusionnés (par exemple un tir repoussé qui devient un but).
- Chaque moment porte son type, son issue et son score d'intérêt (le même qui servira au résumé).

**Attributs :** aucun.

**Blocked by:** `v2-collectif/28` (28c livré le 08/11/2026 ; avant de lire `MatchTrace.chances`, traiter ses réserves A1, séquence coupée en deux, et A2, origine « récupération » ambiguë : voir le ticket 28c, Comments), `v2-mise-en-scene/01`. Les cartons rouges viennent avec `v2-attributs-restants/09a`.

**Status:** à faire (constantes à proposer avant le code)

**Constantes à proposer :** marges avant et après une séquence ; règle de fusion ; nombre maximal de moments par mode.

**Chiffres réels :** grosses occasions par équipe et par match selon cette définition large : **non trouvé**. Le seuil est proposé avec un nombre plausible par match, justifié.

## Acceptance criteria

- [ ] Constantes validées par le propriétaire avant le code
- [ ] Scène contrôlée : le centre qui traverse la surface et laisse un attaquant à deux doigts du but vide est un moment clé ; un face-à-face conclu par un tacle salvateur aussi ; un tir de loin sans danger ne l'est pas
- [ ] Les moments fusionnés sont testés (tir repoussé puis but : un seul moment)
- [ ] Le mode ne montre que ces moments, sans score ni repère futur avant chacun
- [ ] En match (50 matchs, graine d'audit) : nombre de moments clés par match et leur répartition par issue, rapportés
- [ ] Déterminisme à graine fixée ; suite V2 verte ; `npm run build` et `npm run lint` OK ; V1 inchangée
