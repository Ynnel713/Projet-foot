# 07d: Temps de contrôle et enchaînement selon l'orientation

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (dos au jeu, il faut se retourner avant d'attaquer). **Catégorie :** exécution.

**Constat vérifié :** `possession.reception_delay_s` (`possession.py:170`) ne dépend que de First Touch et de la pression.

**What to build:** Le temps avant la première décision augmente pour une réception dos au jeu (rotation nécessaire) et baisse de profil ; dos au jeu, les options vers l'avant ne sont accessibles qu'après la rotation (le porteur peut jouer en remise avant).

**Attributs :** aucun

**Lien avec l'existant :** à coordonner avec `v2-collectif/31` (contrôle orienté, à faire) : 31 règle la durée par First Touch et Technique, ce ticket ajoute l'orientation, sans toucher à 31.

**Blocked by:** 07c (Réception de face, de profil ou dos au jeu); `v2-collectif/31`.

**Bloque :** 07g.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 55** |

Confiance : moyenne. Hypothèses : 31 livré avant ; sinon dépendance à rediscuter.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** même joueur, même ballon : dos au jeu plus lent que de profil
- **Statistiques (séries de matchs) :** 50 matchs : temps de possession individuelle par type de réception

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Effet de l'orientation mesuré en scène
- [ ] Temps de possession individuelle rapporté (repère 2-3 s)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
