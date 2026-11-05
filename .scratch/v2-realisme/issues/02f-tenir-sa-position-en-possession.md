# 02f: Tenir sa position en possession

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (cause directe des volumes d'appels et de course artificiels). **Catégorie :** décision.

**Constat vérifié :** `cerveau.py:102-103` donne le rôle `APPEL` à tout joueur de champ dont l'équipe a le ballon : chacun cherche en permanence un espace libre (`off_ball.choose_space`) ; il n'existe aucun rôle « tenir sa place » en possession.

**What to build:** Nouveau rôle `TENIR` en possession : le joueur rejoint et garde sa place de référence (02d), avec le seuil de Teamwork déjà utilisé sans ballon (`Bloc.replacement`), et ne fait plus d'appel. Dans ce ticket, seuls le porteur, le receveur visé et les joueurs choisis par une règle provisoire simple (les deux plus proches devant le ballon) gardent `APPEL` ; la vraie sélection vient au 02g.

**Hors de ce ticket :** sélection des appelants (02g) ; intensité de course (12d).

**Attributs :** aucun

**Blocked by:** 02d (Place de référence avec ballon selon le rôle).

**Bloque :** 02g, 09g, 12d.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : le Teamwork garde son rayon (tenir et reprendre sa place) : pas de double comptage.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** possession installée au milieu : au plus le nombre provisoire d'appelants ; les autres restent à moins de leur tolérance de leur place
- **Comportementaux (profils comparés) :** Teamwork 99 contre 11 : écart moyen à la place plus faible
- **Statistiques (séries de matchs) :** 50 matchs : appels par joueur et km par joueur avant / après (indicateurs du 01d)

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Rôle `TENIR` tracé et visible dans l'intention
- [ ] Appels par joueur et km en baisse mesurée (50 matchs), sans viser encore les valeurs réelles
- [ ] Solutions de passe ouvertes rapportées (pas de chute non expliquée)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
