# 09a: Couloirs et demi-espaces : définition et mesure

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (base commune de l'occupation tactique). **Catégorie :** mesure.

**Constat vérifié :** aucune notion de couloir dans `v2engine/` ni dans le banc (recherche « couloir », « demi-espace » : seulement des commentaires).

**What to build:** Définir cinq couloirs (deux extérieurs, deux demi-espaces, l'axe) dans un module partagé, et ajouter au banc l'occupation de chaque couloir par équipe et par phase (joueurs présents, part du temps avec au moins un joueur dans chaque couloir extérieur).

**Attributs :** aucun

**Blocked by:** 01d (Banc : distance par poste, temps et distance à haute intensité, appels selon la définition sourcée).

**Bloque :** 09b.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 35** |

Confiance : élevée. Hypothèses : largeurs des couloirs : convention à valider (bords de la surface et du petit rectangle).
Temps machine, non compté : suite complète (environ 40 min) ; mesure 20 matchs.

## Tests

- **Unitaires (scène contrôlée) :** joueur en y donné : couloir attendu
- **Statistiques (séries de matchs) :** 20 matchs : occupation de référence

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Module et indicateur ajoutés
- [ ] Référence publiée
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
