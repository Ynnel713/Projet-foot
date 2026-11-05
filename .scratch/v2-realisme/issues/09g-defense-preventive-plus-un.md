# 09g: Défense préventive : un défenseur de plus que les attaquants restés haut

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (la défense préventive se juge contre les attaquants adverses, pas en nombre fixe). **Catégorie :** décision.

**Constat vérifié :** `REST_DEFENDERS = 2` (`defense.py:111`) est fixe ; appliqué seulement en possession installée pour annuler un appel vers l'avant (`cerveau.py:131-139`) ; rien ne compte les attaquants adverses restés haut.

**What to build:** En possession, le nombre de joueurs gardés derrière le ballon est le nombre d'attaquants adverses restés haut plus un (borne validée), choisis parmi les rôles défensifs ; ils tiennent une position qui couvre ces attaquants (côté but). Teamwork garde son rôle (l'indiscipliné monte quand même).

**Attributs :** Teamwork (rayon existant : tenir sa place)

**Lien avec l'existant :** complète `v2-collectif/06` et `10` (livrés, non modifiés).

**Blocked by:** 02f (Tenir sa position en possession); 09f (Un attaquant reste haut quand l'équipe défend).

**Bloque :** 09h, 13c, 13d.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : « resté haut » : au-delà d'une hauteur validée.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** adversaire avec 2 attaquants restés haut : 3 joueurs derrière le ballon ; avec 1 : 2
- **Statistiques (séries de matchs) :** 50 matchs : défenseurs derrière le ballon contre attaquants adverses (repère 3,7 contre 2,0)

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Règle « plus un » tracée
- [ ] Indicateur de défense préventive rapporté
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
