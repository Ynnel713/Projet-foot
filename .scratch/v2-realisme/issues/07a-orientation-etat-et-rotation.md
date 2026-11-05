# 07a: Orientation du corps : état propre et rotation bornée

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (avancé le 05/11/2026 sur décision du propriétaire : base du contrôle orienté et du jeu à une touche (`v2-collectif/31`)). **Catégorie :** physique.

**Constat vérifié :** `PlayerState` (`movement.py:72`) n'a aucun champ d'orientation ; la direction du corps n'existe nulle part dans `v2engine/` (recherche « orient », « facing », « heading » : seul `decision.free_point` emploie `heading`, pour une direction de conduite).

**What to build:** Ajouter à chaque joueur un cap (direction du corps), distinct de sa vitesse, qui tourne vers une direction voulue (intention) à une vitesse angulaire maximale commune (valeur sourcée ou « non trouvé »). Par défaut il regarde le ballon ; en course rapide il regarde dans le sens de course. Tracé et transmis à l'écran.

**Hors de ce ticket :** effet sur le déplacement (07b), Agility (07f).

**Attributs :** aucun

**Blocked by:** 01f (Fabrique de scènes de test partagée).

**Bloque :** 04h, 07b, 07c, 07e, 07f, 08a, 11d, `v2-collectif/31`.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 25 min |
| **Total (travail effectif)** | **2 h 10** |

Confiance : moyenne. Hypothèses : champ ajouté à `PlayerState` et à la trace ; rendu : simple trait d'orientation.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 20 matchs (temps de calcul).

## Tests

- **Unitaires (scène contrôlée) :** demi-tour demandé : durée égale à 180° divisé par la vitesse angulaire, à un pas près
- **Intégration :** trace et API : cap présent

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Cap tracé et affiché
- [ ] Aucun effet sur le jeu (mesures identiques à graine fixée, hors nouveaux champs)
- [ ] Temps de calcul rapporté
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
