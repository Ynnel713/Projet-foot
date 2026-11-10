# 06: Réactions des joueurs : protestations, frustration, fair-play

**Chantier :** `v2-mise-en-scene` (audit de la roadmap du 10/11/2026, `docs/AUDIT_ROADMAP_V2.md`). **Priorité :** P3 (secondaire, mais renforce l'immersion). **Catégorie :** rendu.

**Constat vérifié :** les joueurs n'ont aucune réaction hors du jeu ; les célébrations sont prévues au ticket 04.

**What to build:** Après un but, une occasion manquée, une erreur ou une décision arbitrale : protestations autour de l'arbitre (21a), mains sur la tête, applaudissements, joueur qui aide un adversaire à se relever, capitaine qui rassemble. Déclenchées par la chaîne d'événements (19b), choisies par la situation, jamais par un tirage libre ; aucun effet sur le jeu (la contestation sanctionnée reste au `v2-attributs-restants/09a`, « Argues With Officials »).

**Attributs :** aucun attribut de réussite ; tendances d'affichage seulement.

**Blocked by:** 04 (même mécanisme d'étiquettes) ; `v2-realisme/19b`, `v2-realisme/21a`.

**Bloque :** rien.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 55 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : étiquettes et petits déplacements, comme les célébrations du ticket 04.
Temps machine, non compté : suite complète (environ 40 min) ; 50 matchs.

## Tests

- **Comportementaux :** scènes fixes : occasion manquée à la 90e à égalité contre à 3-0 : réaction plus marquée dans le premier cas
- **Statistiques (séries de matchs) :** 50 matchs : chaque type de réaction apparaît, aucun ne domine

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Réactions tracées et affichées ; résultat sportif inchangé
- [ ] Aucune réaction sans l'événement déclencheur
- [ ] `npm run build` et `npm run lint` OK (0 erreur)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
