# 25f: Dézoner de temps en temps, et compenser la place laissée

**Chantier :** `v2-realisme` (demande du propriétaire du 14/11/2026 : jeu sans ballon et placement dynamique comme cœur du jeu ; audit de la roadmap du même jour). **Priorité :** P1. **Catégorie :** décision.

**Constat vérifié (14/11/2026) :** en possession, un joueur ne quitte durablement sa zone que pour un appel ; aucune permutation (ailier qui rentre, milieu qui occupe le couloir laissé). La compensation existe seulement sans ballon (`v2-collectif/09`, rôle `COMPENSATION`).

**What to build:** un joueur peut prendre pour un temps la zone d'un coéquipier ou une zone vide (dézonage) quand elle est exploitable (candidats du 25a, couloir vide du 09b) ; un coéquipier proche prend alors la place laissée, ou la structure se réajuste (règle du `v2-collectif/09` appliquée en possession). Le dézonage dure tant que l'action le justifie, puis chacun revient (Teamwork). Rare et motivé : fréquence par match bornée (valeur validée), jamais un tirage au hasard.

**Attributs :** Flair (tendance à dézoner ; rayon de la carte : « tenter l'inattendu », à étendre et justifier), Teamwork (compenser, revenir ; rayon existant). Le style du coach (`13d`) pourra moduler plus tard.

**Blocked by:** 25a, 25d, 09b.

**Bloque :** 25h, `v2-collectif/17`, `v2-collectif/19`.

**Ticket 24 en cours :** toute courbe d'attribut de ce ticket passe par `success_probability` / `duel_probability`, dont la forme change au 24 ; les constantes de niveau sont proposées après la livraison du 24.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **2 h** |

Confiance : faible. Hypothèses : réutilisation du mécanisme de compensation du 09 ; un dézonage à la fois par équipe.
Temps machine, non compté : suite complète ; mesure 50 matchs.

## Tests

- **Comportementaux :** Flair 99 contre 11 : dézonages par match ; couloir laissé vide moins de la durée validée après un dézonage.
- **Statistiques (50 matchs) :** dézonages et permutations par match, couloirs vides en possession installée (09a), regroupement.

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Toute place laissée par un dézonage est reprise ou la structure réajustée dans le délai validé (test)
- [ ] Dézonages par match dans la fourchette validée ; Flair haut en fait plus que Flair bas
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
