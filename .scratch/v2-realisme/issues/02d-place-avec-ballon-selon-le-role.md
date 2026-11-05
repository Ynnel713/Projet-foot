# 02d: Place de référence avec ballon selon le rôle

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (une équipe en possession n'est pas une copie agrandie de sa forme de départ). **Catégorie :** placement.

**Constat vérifié :** avec ballon, `Bloc.reference` (`bloc.py:186-199`) étire la forme de départ à 42 × 46 m et la monte de 8 m pour tous ; un latéral offensif et un latéral défensif ont la même place.

**What to build:** Ajouter à la place de référence avec ballon un décalage propre au rôle (profondeur et largeur) : latéral offensif haut et large, latéral défensif en retrait, milieu récupérateur sous le ballon, ailier de couloir sur la ligne, ailier intérieur rentré. Le décalage s'applique avant la mise à l'échelle du bloc et garde la forme sur le terrain.

**Attributs :** aucun

**Blocked by:** 02b (Largeur de référence propre à chaque poste); 02c (Rôle de poste par défaut, porté par le joueur et tracé).

**Bloque :** 02f, 02h, 09b, 09d, 09e.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : décalages exprimés en mètres sur la forme de départ.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 20 matchs.

## Tests

- **Unitaires (scène contrôlée) :** même équipe, latéral offensif contre défensif : place avec ballon plus haute d'au moins la valeur validée
- **Statistiques (séries de matchs) :** 20 matchs : position moyenne en possession par rôle

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Décalages par rôle documentés
- [ ] Positions moyennes en possession différentes selon le rôle, dans le sens attendu (20 matchs)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
