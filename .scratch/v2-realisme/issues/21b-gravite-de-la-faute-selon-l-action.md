# 21b: Gravité de la faute selon l'action (loi 12)

**Chantier :** `v2-realisme` (audit de la roadmap du 10/11/2026, `docs/AUDIT_ROADMAP_V2.md`). **Priorité :** P1 (un tacle par derrière à pleine vitesse n'a pas la même gravité qu'un accrochage). **Catégorie :** arbitrage.

**Constat vérifié :** la gravité est tirée dans des parts fixes (inconsidérée 12 %, excès d'engagement 0,5 %), indépendantes de l'action (`duel.foul_severity`) ; ni l'angle, ni la vitesse, ni le tacle glissé, ni l'occasion manifeste annulée ne la changent.

**What to build:** Gravité déduite de l'action réelle : angle d'approche (11d), vitesse relative, tacle glissé (04j), ballon jouable ou non, contact par derrière. Sanctions disciplinaires de la loi 12 : occasion de but manifeste annulée (danger du 28c, distance au but, défenseurs restants) : rouge hors de la surface, jaune dans la surface s'il y a tentative de jouer le ballon ; attaque prometteuse arrêtée : jaune ; faute tactique : jaune. Aggression garde la fréquence (pas de double comptage).

**Attributs :** aucun nouveau (Aggression : fréquence, inchangé).

**Blocked by:** 11d, 04j.

**Bloque :** `v2-attributs-restants/09a` ; 21c ; 21h ; `v2-attributs-restants/10b` (ajouté le 10/11/2026, audit de la roadmap) ; 21j (ajouté le 14/11/2026).

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : gravité calculée à partir de grandeurs déjà présentes dans le moteur.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** tacle glissé par derrière à pleine vitesse contre tacle de face à l'arrêt : gravité ordonnée
- **Unitaires (scène contrôlée) :** occasion manifeste annulée dans et hors de la surface : jaune et rouge
- **Statistiques (séries de matchs) :** 50 matchs : gravités par match, comparées aux cartons réels (repère du 09a)

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Plus aucune part fixe : gravité expliquée par l'action
- [ ] Cas de la loi 12 couverts par des scènes
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
