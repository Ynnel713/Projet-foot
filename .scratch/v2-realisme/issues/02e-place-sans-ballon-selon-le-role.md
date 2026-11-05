# 02e: Place de référence sans ballon selon le rôle

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (le repli défensif dépend du rôle (ailier qui défend ou reste haut)). **Catégorie :** placement.

**Constat vérifié :** sans ballon, le bloc se cale sur la hauteur de la dernière ligne et se resserre à 32 × 40 m pour tous (`bloc.py:193-199`) ; rien ne distingue un ailier qui suit son latéral d'un ailier qui reste prêt pour la contre-attaque.

**What to build:** Décalage propre au rôle sans ballon : ailier de couloir qui redescend sur la ligne du milieu, ailier ou avant-centre qui reste haut (voir aussi 09f), milieu récupérateur devant la défense. Même mécanisme que 02d, situation sans ballon.

**Attributs :** aucun

**Blocked by:** 02b (Largeur de référence propre à chaque poste); 02c (Rôle de poste par défaut, porté par le joueur et tracé).

**Bloque :** 02h, 09d, 09f, 10a, 10d, 10f.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 50** |

Confiance : moyenne. Hypothèses : réutilise le décalage du 02d.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 20 matchs.

## Tests

- **Unitaires (scène contrôlée) :** ailier de couloir contre ailier qui reste haut : écart de hauteur sans ballon d'au moins la valeur validée
- **Statistiques (séries de matchs) :** 20 matchs : hauteur moyenne sans ballon par rôle

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Décalages sans ballon par rôle documentés
- [ ] Hauteurs moyennes sans ballon différentes selon le rôle (20 matchs)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
