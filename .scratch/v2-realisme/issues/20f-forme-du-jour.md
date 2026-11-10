# 20f: Forme du jour : un bon joueur peut passer à côté de son match

**Chantier :** `v2-realisme` (audit de la roadmap du 10/11/2026, `docs/AUDIT_ROADMAP_V2.md`). **Priorité :** P1 (exigence du propriétaire : un excellent joueur peut rater son match, un joueur moyen peut réussir le sien). **Catégorie :** exécution.

**Constat vérifié :** à notes égales, un joueur exprime la même note d'un match à l'autre ; seule la chance de chaque action varie, et sur un match elle se moyenne : un joueur ne « passe » jamais à côté de son match.

**What to build:** Au coup d'envoi, chaque joueur tire une forme du jour (petite, centrée sur zéro, flux nommé « forme »), appliquée par la façade (19a) aux gestes techniques et aux décisions, jamais à la vitesse. Même amplitude pour tous (la base n'a pas d'attribut de régularité) ; tracée. Aucune forme ne rend un geste impossible ni garanti (garde 19c).

**Hors de ce ticket :** moral pendant le match (17c, `v2-collectif/21`) ; forme sur une saison (branchement aux compétitions, D-V09).

**Attributs :** aucun (constante d'amplitude).

**Blocked by:** 19a, 01e.

**Bloque :** `v2-collectif/22a`.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 35 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 45** |

Confiance : moyenne. Hypothèses : une seule constante d'amplitude ; à valider par la dispersion des notes de match réelles si une source existe.
Temps machine, non compté : suite complète (environ 40 min) ; 500 matchs (01e).

## Tests

- **Statistiques (séries de matchs) :** 500 matchs : dispersion du rendement d'un même joueur entre matchs ; part des matchs où un finisseur du premier décile rend moins que la médiane
- **Statistiques (séries de matchs) :** sur 34 matchs, hiérarchie des notes conservée (corrélation note / rendement)

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Amplitude validée par le propriétaire
- [ ] Variabilité d'un match à l'autre mesurée, hiérarchie conservée sur une saison
- [ ] Forme tracée
- [ ] Toute note lue passe par la façade de la condition (`v2-realisme/19a`), jamais par `player_attribute` directement
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
