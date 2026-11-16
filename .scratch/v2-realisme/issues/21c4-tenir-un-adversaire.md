# 21c4: Tenir un adversaire (maillot, bras)

**Chantier :** `v2-realisme`, découpage du ticket 21c (16/11/2026, validé par le propriétaire). **Priorité :** P1. **Catégorie :** arbitrage.

**Constat vérifié :** aucune faute de maintien (loi 12 : tenir un adversaire) dans le moteur.

**What to build:** Tirage de maillot ou bras retenu : (a) au marquage, quand l'attaquant marqué démarre ou fait un appel dans le dos de son défenseur (y compris dans la surface sur coup de pied arrêté) ; (b) par le défenseur battu sur un contournement. Prudence de surface du 21c1. Volet (a) faisable dès le 21c1 ; volet (b) attend le 04g.

**Attributs :** Aggression (fréquence) ; Decisions (prudence de surface, 21c1).

**Blocked by:** 21c1 ; volet (b) : 04g.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 35 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 35** |

Confiance : moyenne. Hypothèses : le marquage et l'appel dans le dos sont déjà détectables ; le volet (b) se branche ensuite sur le contournement du 04g.
Temps machine, non compté : suite complète (environ 10 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** appel dans le dos du défenseur : maillot tiré possible ; même scène dans sa surface : plus rare, jamais nul ; défenseur battu sur contournement (après le 04g)
- **Statistiques :** 50 matchs : maintiens par match

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Source tracée (« tenir un adversaire », maillot ou bras)
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md` ; test de rayon à jour
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
