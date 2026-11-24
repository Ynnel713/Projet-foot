# 21c4: Tenir un adversaire (maillot, bras)

**Chantier :** `v2-realisme`, découpage du ticket 21c (16/11/2026, validé par le propriétaire). **Priorité :** P1. **Catégorie :** arbitrage.

**Constat vérifié :** aucune faute de maintien (loi 12 : tenir un adversaire) dans le moteur.

**What to build:** Tirage de maillot ou bras retenu : (a) au marquage, quand l'attaquant marqué démarre ou fait un appel dans le dos de son défenseur (y compris dans la surface sur coup de pied arrêté) ; (b) par le défenseur battu sur un contournement. Prudence de surface du 21c1. Volet (a) faisable dès le 21c1 ; volet (b) attend le 04g.

**Ajout du 24/11/2026 (demande du propriétaire du 24/11/2026, éléments sur la défense, point 5 « tirage de maillot et obstruction »).** L'obstruction (couper la route sans jouer le ballon) et le contact léger toléré (seule une part des maintiens devient faute) sont un ticket à part, `21c8`, qui passe après celui-ci (réserve A1 de l'expert : périmètre trop large pour cette estimation). Le défenseur en retard (battu, mal placé) tient plus souvent que le défenseur bien placé : ici aussi, la fréquence suit la situation, pas un attribut de plus.

**Attributs :** Aggression (fréquence) ; Decisions (prudence de surface, 21c1).

**Blocked by:** 21c1 ; volet (b) : 04g.

**Bloque :** `21c8` (ajouté le 24/11/2026).

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 35 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 35** |

Confiance : moyenne. Hypothèses : le marquage et l'appel dans le dos sont déjà détectables ; la précision du 24/11/2026 (le défenseur en retard tient plus souvent) module la fréquence du volet existant, sans périmètre nouveau (obstruction et contact toléré au `21c8`) ; le volet (b) se branche ensuite sur le contournement du 04g.
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
