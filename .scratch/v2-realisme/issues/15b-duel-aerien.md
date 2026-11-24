# 15b: Duel aérien : taille, Jumping Reach, Strength au contact

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P2 (le duel aérien dépend de la hauteur atteinte et du contact). **Catégorie :** exécution.

**Constat vérifié :** Jumping Reach, Heading et la taille ne sont lus nulle part dans `v2engine/`.

**What to build:** Entre les joueurs sélectionnés (15a), le duel est gagné selon la hauteur atteinte (taille plus Jumping Reach), le placement au contact (Strength) et l'élan ; jamais 0 ni 100 %.

**Attributs :** Jumping Reach, taille, Strength (contact) ; Bravery au 17b

**Lien avec l'existant :** découpe (validée le 05/11/2026) de `v2-attributs-restants/01` : duel.

**Blocked by:** 15a (Qui attaque la trajectoire aérienne); 11b (Collision asymétrique : Strength).

**Bloque :** 15c, 15f.

**Status:** découpé (chapeau, 24/11/2026) en `15b1` (duel loyal et retombée), `15b2` (fautes du duel aérien), `15b3` (jeu dangereux, pied haut) ; découpe et constantes validées par le propriétaire le 24/11/2026 (« oui je valide »)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : avantage de taille à sourcer (point de vigilance du ticket 01).
Temps machine, non compté : suite complète (environ 40 min).

## Tests

- **Comportementaux (profils comparés) :** 1,95 m contre 1,70 m, autres notes égales : le grand gagne plus souvent ; Jumping Reach 99 réduit l'écart

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Effets mesurés en scène A/B
- [ ] Joueur sans taille : taille moyenne du poste
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Comments

- 23/11/2026 (réserve A1 du `v2-attributs-restants/03c1`) : une fois le duel aérien livré, refaire la mesure de la part des longs ballons du gardien gardés par son équipe selon Kicking (séries forcées à 40 et 80, `.scratch/v2-attributs-restants/mesures/03c-serie.py`) ; sans duel, 85 % quelle que soit la précision.
- 24/11/2026 : périmètre élargi par le propriétaire (faute de celui qui ne saute pas et fait la bascule, charge sans jouer le ballon, jeu à l'épaule, déséquilibre à la retombée, toute situation de ces duels). Découpe validée le même jour : `15b1`, `15b2`, `15b3`. Renvoyés : ne pas sauter par crainte du contact (Bravery, `17b`) ; tête contre tête (blessures, `v2-attributs-restants/09b`) ; charge sur le gardien (`v2-attributs-restants/03a`) ; tirage de maillot sur corner (`16b`) ; ballon dévié par le duel (`15e`, `05d`) ; main dans le duel (aucun système de main : ticket à créer si voulu). Chiffres trouvés : StatsBomb HOPS (la taille explique 22 % de la variation de la capacité aérienne) ; Kim et Kim 2025 (taux brut trompeur sans la taille de l'adversaire) ; Stats Perform (114 063 duels : 31 % aériens loyaux, 19,9 % de fautes, tous duels confondus).
