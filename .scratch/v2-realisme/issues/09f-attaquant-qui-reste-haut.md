# 09f: Un attaquant reste haut quand l'équipe défend

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (sans point d'appui, aucune contre-attaque ne démarre). **Catégorie :** placement.

**Constat vérifié :** sans ballon, le bloc entier se resserre à 32 m de long et suit la dernière ligne (`bloc.py:193-199`) ; personne ne reste devant.

**What to build:** Le rôle « avant-centre de profondeur » (et tout rôle marqué « reste haut ») garde, sans ballon, une hauteur minimale près de la ligne médiane, hors du bloc, sans jamais se placer hors-jeu au moment d'une passe.

**Attributs :** aucun

**Blocked by:** 02e (Place de référence sans ballon selon le rôle).

**Bloque :** 09g, 13e.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 35 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 30** |

Confiance : élevée. Hypothèses : réutilise le décalage sans ballon du 02e.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** équipe qui défend dans son camp : un attaquant reste au-delà de la hauteur validée
- **Statistiques (séries de matchs) :** 50 matchs : tirs de contre après récupération dans son camp

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Hauteur minimale tenue (scène)
- [ ] Contre-attaques rapportées avant / après
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
