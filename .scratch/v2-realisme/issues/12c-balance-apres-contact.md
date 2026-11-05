# 12c: Balance : rester debout et continuer après un contact

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (Balance joue après le contact, Strength pendant). **Catégorie :** physique.

**Constat vérifié :** Balance n'entre que dans la résistance au tacle (moyenne avec Strength, `duel.py:58-64`) ; la carte la définit comme « continuer l'action APRÈS un contact ».

**What to build:** Après un contact perdu (collision 11b, duel d'épaule 11c, tacle sans perte), le joueur subit une perte de vitesse et un court délai avant d'agir, réduits par Balance. Balance est retirée de la résistance au tacle pour respecter son rayon (à valider : changement d'un mécanisme livré, nouveau comportement ici).

**Attributs :** Balance (après le contact)

**Lien avec l'existant :** découpe (validée le 05/11/2026) de `v2-attributs-restants/07b` : Balance, levée de la dérogation A3.

**Blocked by:** 11b (Collision asymétrique : Strength).

**Bloque :** 11e, 12g.

**Status:** à faire (constantes à proposer avant le code)

**Point de vigilance :** retirer Balance du tacle change le ticket livré `v2-socle/03` : décision explicite du propriétaire avant le code.

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 55** |

Confiance : moyenne. Hypothèses : décision du propriétaire sur le tacle.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Comportementaux (profils comparés) :** Balance 99 contre 11 après le même contact : délai plus court et moins de vitesse perdue

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Effet de Balance mesuré en scène A/B
- [ ] Décision sur le tacle consignée
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
