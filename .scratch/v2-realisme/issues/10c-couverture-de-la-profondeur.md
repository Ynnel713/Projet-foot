# 10c: Couverture de la profondeur derrière la ligne

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (l'espace dans le dos est le premier danger d'une ligne haute). **Catégorie :** placement.

**Constat vérifié :** un seul couvreur, placé 6 m derrière le porteur sur l'axe porteur-but (`COVER_DEPTH_M`), seulement dans la moitié défendue.

**What to build:** Quand une passe en profondeur est possible (attaquant dans le dos possible, espace derrière la ligne), le défenseur le plus éloigné du ballon de la dernière ligne se place légèrement plus bas que la ligne (décalage validé) côté opposé au ballon, sans casser le piège du hors-jeu au moment des passes.

**Attributs :** aucun

**Blocked by:** 10b (Le défenseur central ne quitte sa ligne que couvert).

**Bloque :** 10j.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : conflit possible avec le piège du hors-jeu (ticket 23) : mesure du hors-jeu obligatoire.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** ligne haute, ballon à droite : le défenseur gauche est en retrait de la valeur validée
- **Statistiques (séries de matchs) :** 50 matchs : passes en profondeur réussies et hors-jeu

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Couverture tracée
- [ ] Hors-jeu par match rapporté (pas de chute non expliquée)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
