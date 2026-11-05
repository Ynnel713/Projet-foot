# 08c: Scan visuel avant la réception

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (avancé le 05/11/2026 sur décision du propriétaire : base du contrôle orienté et du jeu à une touche (`v2-collectif/31`)). **Catégorie :** perception.

**Constat vérifié :** aucun regard volontaire : le seul geste de « lever la tête » est l'intention textuelle pendant la réception (`cerveau.py:152`).

**What to build:** Un joueur sans ballon peut tourner brièvement la tête (scan) pour mettre à jour sa mémoire hors de son cône ; la fréquence des scans dépend d'un attribut à trancher (recommandation : Vision, qui règle déjà « quelles options il voit » ; Anticipation déjà chargée de la lecture). Un scan coûte un court instant pendant lequel il ne suit plus le ballon.

**Attributs :** Vision (fréquence des scans) ; décision du propriétaire avant le code

**Blocked by:** 08b (Mémoire de perception : positions vues, datées et vieillissantes); 07c (Réception de face, de profil ou dos au jeu).

**Bloque :** 08e, `v2-collectif/31`.

**Status:** à faire (constantes à proposer avant le code)

**Point de vigilance :** Vision règle déjà la portée des passes envisagées (`decision.visible_teammates`) : le scan ne doit pas recompter cette portée.

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : fréquences réelles de scan à sourcer.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 20 matchs.

## Tests

- **Unitaires (scène contrôlée) :** après un scan, la mémoire des joueurs dans le dos est à jour
- **Comportementaux (profils comparés) :** Vision 99 contre 11 : plus de scans par minute avant réception

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Scans tracés
- [ ] Effet de l'attribut retenu mesuré en scène A/B
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
