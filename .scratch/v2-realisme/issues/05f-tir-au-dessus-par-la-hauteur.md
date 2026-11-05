# 05f: Tir au-dessus de la barre par la vraie hauteur

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (la moitié des tirs non cadrés partent au-dessus). **Catégorie :** exécution.

**Constat vérifié :** le moteur est à plat ; le ticket `v2-collectif/35b` trace l'issue « au-dessus » sans trajectoire en hauteur ; `v2-hauteur-ballon/02a` (à faire) apporte la hauteur.

**What to build:** Le tir reçoit une hauteur de départ et un angle d'élévation issus de l'exécution (35b) ; avec la gravité de 02a, il passe sous ou au-dessus de la barre ; l'arrêt du 05b tient compte de la hauteur atteignable par le gardien.

**Attributs :** aucun

**Blocked by:** 05b (Arrêt : le gardien atteint ou non le ballon); `v2-hauteur-ballon/02a`; `v2-collectif/35b`.

**Bloque :** rien.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : hauteur de la barre et portée verticale du gardien : valeurs proposées.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** tir avec élévation excessive : au-dessus ; tir tendu : sous la barre
- **Statistiques (séries de matchs) :** 50 matchs : part des tirs au-dessus

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Tirs au-dessus tracés avec leur hauteur au franchissement
- [ ] Arrêts tenant compte de la hauteur (scène)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
