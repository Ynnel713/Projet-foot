# 25b: Placement de construction quand le gardien ou un central a le ballon

**Chantier :** `v2-realisme` (demande du propriétaire du 14/11/2026 : jeu sans ballon et placement dynamique comme cœur du jeu ; audit de la roadmap du même jour). **Priorité :** P1 (la sortie de balle n'existe pas : `v2-collectif/15` et `v2-attributs-restants/03c` choisiraient entre des solutions que personne ne crée). **Catégorie :** placement.

**Constat vérifié (14/11/2026) :** la place avec ballon est un décalage fixe par rôle (`bloc.ROLE_PLACE_WITH_BALL` : défenseur central (0, 0), sentinelle −4 m), identique que le ballon soit chez le gardien ou dans le dernier tiers. Sur une sortie de but, `restart.place` n'éloigne que les adversaires. Les centraux et les milieux défensifs ne sont jamais appelants (`cerveau.CALLER_ROLES`, `_call_rank` : seuls les joueurs devant le ballon).

**What to build:** une phase « construction » (ballon au gardien ou à un défenseur dans son propre tiers, sortie de but comprise) avec sa propre table de décalages par rôle : centraux qui s'écartent vers les angles de la surface, sentinelle ou regista qui décroche dans l'axe entre eux ou devant eux, latéraux qui montent et s'ouvrent, milieux relayeurs qui se placent dans les demi-espaces. La table s'ajoute à `ROLE_PLACE_WITH_BALL` comme la table sans ballon du 02e ; la place reste ensuite corrigée par l'espace libre (25a) et par Teamwork. Sous pressing haut adverse, les mêmes joueurs restent plus proches du porteur (distance validée) ; sans pressing, ils s'écartent au maximum.

**Hors de ce ticket :** choix du porteur entre court et long (`v2-collectif/15`) ; qualité de la relance du gardien (`v2-attributs-restants/03c`).

**Attributs :** aucun (structure collective ; Teamwork garde son rayon de tolérance).

**Blocked by:** 02d (livré), 02e (livré). Indépendant du 25a.

**Bloque :** `v2-collectif/15`, `v2-attributs-restants/03c`, 25d, 25h.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 45** |

Confiance : moyenne. Hypothèses : détection de la phase sur la situation existante (`situation.py`) plus la position du ballon ; décalages tactiques sans chiffre réel (ordres de grandeur, « non trouvé » probable).
Temps machine, non compté : suite complète ; mesure 50 matchs.

## Tests

- **Scènes :** sortie de but sans pressing : écart entre les deux centraux au moins égal à la valeur validée, sentinelle à moins de la distance validée du gardien ; même scène sous pressing haut : centraux plus proches.
- **Statistiques (50 matchs) :** part des relances courtes du gardien, pertes dans son propre tiers, solutions de passe du gardien.

## Acceptance criteria

- [ ] Constantes produit (décalages par rôle, seuil de pressing) et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Gardien porteur sans pressing : au moins deux solutions de passe ouvertes en moyenne (valeur à valider)
- [ ] Décalages visibles dans la trace (phase et place de référence)
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
