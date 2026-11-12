# 18g: Passe : même risque à l'évaluation et en vol

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (cohérence entre décision et résolution, comme 04a pour la conduite). **Catégorie :** exécution.

**Origine :** diagnostic du ticket 18f (11/11/2026, 12 matchs, script de diagnostic décrit dans le ticket 18f).

**Constat vérifié :** pour les passes choisies, la chance évaluée par le porteur (`possession.pass_success_probability`) vaut 0,82 en moyenne, mais le receveur visé n'a le ballon que dans 72 % des cas (premier porteur de son équipe : 74 %). L'écart vient de ce que la résolution ajoute à l'évaluation : les adversaires qui lisent la passe et courent la couper en vol (`anticipation.pass_readers`) et le contrôle raté du receveur (`possession.attempt_control`). Le couloir de passe compte déjà dans la difficulté (`_LANE_DIFFICULTY`), puis l'adversaire qui s'y trouve peut aussi couper la passe en vol : l'adversaire du couloir pèse deux fois à la résolution, une seule fois à l'évaluation. Par tranche de gêne du receveur : 0,82 évaluée pour 0,73 atteinte sans gêne ; 0,77 pour 0,58 à 0,4.

**What to build:** Faire porter à l'évaluation et à la résolution le même risque de passe, comme le 04a l'a fait pour la conduite : soit la chance évaluée inclut la coupe en vol et le contrôle, soit le couloir ne compte plus que d'une seule façon (difficulté ou coupe physique). Mesurer, par tranche de chance évaluée, la part des passes reçues par le receveur visé (calibration comme au 04c).

**Hors de ce ticket :** réglage de la réussite des passes (calibration finale `v2-collectif/22a`) ; hauteur du ballon (`v2-hauteur-ballon/03`).

**Attributs :** Passing, First Touch, Anticipation (aucun rôle nouveau ; règle anti double comptage de `docs/CARTE_ATTRIBUTS_V2.md`)

**Blocked by:** 18f (Calibration provisoire 1 bis : choix du porteur et rythme de décision).

**Bloque :** `v2-collectif/22a`.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 30 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 25 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : même démarche que 04a et 04c ; aucune nouvelle constante si le couloir ne compte plus qu'une fois.
Temps machine, non compté : série de 50 matchs, suite complète (environ 40 min).

## Tests

- **Unitaires :** une passe à travers un couloir occupé a la même chance à l'évaluation et à la résolution (scène fixe, tirages répétés)
- **Statistiques (séries de matchs) :** 50 matchs, calibration par tranche de chance évaluée (évaluée contre reçue par le receveur visé)

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Écart entre chance évaluée et passe reçue sous 3 points par tranche de chance évaluée (50 matchs)
- [ ] Aucun effet d'attribut inversé ni annulé (scènes A/B rejouées)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
