# 04h: Duel un contre un : le crochet

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (le crochet exploite un défenseur lent à se retourner). **Catégorie :** exécution.

**Constat vérifié :** voir 04g ; aucune notion de défenseur « lancé du mauvais côté » sans orientation.

**What to build:** Changement de direction brusque face à un défenseur proche : réussite par Dribbling contre le temps de rotation du défenseur (orientation 07a, Agility 07f) ; un crochet réussi crée un écart temporaire.

**Attributs :** Dribbling (porteur) ; Agility du défenseur via 07f (pas de nouvel effet)

**Lien avec l'existant :** découpe (validée le 05/11/2026) de `v2-attributs-restants/07a` : crochet.

**Blocked by:** 04g (Duel un contre un : le contournement); 07a (Orientation du corps : état propre et rotation bornée); 07f (Agility : vitesse de rotation du corps).

**Bloque :** rien.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : orientation et vitesse de rotation disponibles.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** défenseur proche et lent à se retourner : crochet plus fréquent qu'avec un défenseur loin

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Geste tracé et affiché
- [ ] Crochet plus fréquent face à un défenseur proche et lent (scène)
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
