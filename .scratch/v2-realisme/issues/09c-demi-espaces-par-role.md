# 09c: Occuper les demi-espaces selon le rôle

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (le demi-espace est la zone la plus dangereuse entre les lignes). **Catégorie :** placement.

**Constat vérifié :** voir 09a ; aucun rôle ne vise une zone particulière.

**What to build:** Les rôles « relayeur », « meneur » et « ailier intérieur » (02c) cherchent leur espace d'abord dans leur demi-espace ; les autres rôles gardent leur logique.

**Attributs :** aucun

**Blocked by:** 09b (Occuper la largeur en possession); 02c (Rôle de poste par défaut, porté par le joueur et tracé).

**Bloque :** 09h.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 40** |

Confiance : moyenne. Hypothèses : biais de choix, pas obligation.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** ailier intérieur : espace choisi dans le demi-espace de son côté
- **Statistiques (séries de matchs) :** 50 matchs : passes reçues dans les demi-espaces

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Part du temps des rôles concernés dans leur demi-espace rapportée
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
