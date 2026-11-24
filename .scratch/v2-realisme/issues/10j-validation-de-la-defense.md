# 10j: Validation de la défense collective

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (contrôle avant les styles d'équipe). **Catégorie :** validation.

**Constat vérifié :** indicateurs défensifs existants (couverture du presseur, compacité, supériorité locale) sans zones ni responsabilités.

**What to build:** Ajouter : sorties des centraux hors zone, attaquants libres dans la surface, axe devant la surface occupé, largeur selon le côté du ballon. Rapport sur 50 matchs.

**Ajout du 24/11/2026 (demande du propriétaire du 24/11/2026, éléments sur la défense, point 1 « alignement, compacité, couverture mutuelle, aspiration hors zone »).** Indicateurs ajoutés : écart entre deux défenseurs voisins de la dernière ligne (trou au-delà d'un seuil proposé), défenseur en retard sur la ligne qui remet un attaquant en jeu (« couvre l'attaquant », Teamwork, `09k`), enchaînement de sorties sans compensation (effet domino : une sortie du central suivie d'une autre dans les 3 s), défenseurs aspirés hors de leur zone sans adversaire à charge. La comparaison par niveau et par profil de défenseur, et les métriques de match (fautes, hors-jeux, relances, buts concédés par type), sont aux `40` et `41`.

**Attributs :** aucun

**Blocked by:** 10a (Choix du presseur selon la zone et la responsabilité); 10b (Le défenseur central ne quitte sa ligne que couvert); 10b2 (couverture du central sans trou) ; 10b3 (sauts de la place de référence ; mesure de stabilité de la couverture à refaire, repère 13,8 allers-retours par match) ; 10c (Couverture de la profondeur derrière la ligne) ; 10c2 (couverture de la profondeur tenue, stable et efficace) ; 10d (Protection de l'axe : le milieu récupérateur fait écran); 10e (Coulissement : côté ballon serré, côté opposé resserré vers l'axe); 10g (Marquage dans la surface : homme ou zone); 10h (Défendre le centre en retrait); 10i (Compensation d'un trou au milieu) ; `v2-realisme/28b` (ajouté le 21/11/2026, audit de réalisme du propriétaire) ; `09k` (montée de la ligne au signal, ajouté le 24/11/2026).

**Bloque :** `40`, `41` (ajoutés le 24/11/2026).

**Status:** à faire

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 55 min |
| Tests unitaires et comportementaux | 35 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h 05** (1 h 35 avant les indicateurs du 24/11/2026) |

Confiance : moyenne (élevée avant le 24/11/2026). Hypothèses : lecture de la trace ; les quatre indicateurs du 24/11/2026 (trou entre voisins, défenseur qui couvre l'attaquant, effet domino, aspiration hors zone) ont leurs seuils proposés au propriétaire avant le code. Au-dessus de 2 h de peu : découpage possible au lancement (indicateurs d'origine / indicateurs du 24/11/2026).
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Statistiques (séries de matchs) :** 50 matchs : rapport publié

## Acceptance criteria

- [ ] Indicateurs du 24/11/2026 (trou entre deux défenseurs voisins au-delà du seuil validé, défenseur en retard qui remet un attaquant en jeu, sorties enchaînées sans compensation dans les 3 s, défenseurs aspirés hors zone sans adversaire à charge) : seuils validés par le propriétaire avant le code, définis dans `docs/INDICATEURS_V2.md`, rapportés sur 50 matchs
- [ ] Indicateurs définis et ajoutés
- [ ] Rapport publié
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
