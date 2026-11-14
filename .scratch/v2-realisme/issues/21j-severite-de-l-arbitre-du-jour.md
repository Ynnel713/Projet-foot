# 21j: Sévérité de l'arbitre du jour

**Chantier :** `v2-realisme` (suggestions du propriétaire du 14/11/2026, axe « arbitrage multi-étages » : tolérance variable aux contacts). **Priorité :** P2. **Catégorie :** arbitrage.

**Constat vérifié (14/11/2026) :** l'arbitre n'existe pas encore (21a, à faire) ; le 21a prévoit une décision selon ce que l'arbitre voit (distance, angle, masquage), mais un seul seuil de sévérité, le même pour tous les matchs. Dans le football réel, le nombre de fautes sifflées et de cartons par match varie nettement d'un arbitre à l'autre (chiffres à sourcer).

**What to build:** au coup d'envoi, l'arbitre du match reçoit une sévérité tirée dans une distribution validée (sans nom ni réputation : aucun arbitre réel). Elle déplace son seuil d'intervention sur un contact (21a, 21b) et son seuil de carton, dans les deux sens. Elle est constante pendant le match. Les joueurs ne la connaissent pas : aucun effet sur leurs décisions dans ce ticket (pas de lecture de l'arbitre, qui serait du faux réalisme sans donnée).

**Hors de ce ticket :** réactions des joueurs et du banc, mise en scène (`v2-mise-en-scene/06`) ; VAR (21g, 21h), qui corrige sur les faits, pas selon la sévérité.

**Attributs :** aucun.

**Blocked by:** 21a, 21b.

**Bloque :** rien.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 25 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 20** |

Confiance : moyenne. Hypothèses : 21a et 21b exposent un seuil unique à décaler.
Temps machine, non compté : suite complète ; mesure 100 matchs.

## Tests

- **Scènes :** même contact, arbitre sévère et arbitre tolérant : probabilité de coup de sifflet ordonnée.
- **Statistiques (100 matchs) :** dispersion des fautes sifflées et des cartons par match, comparée au repère réel.

## Acceptance criteria

- [ ] Constantes produit (distribution de la sévérité) et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Dispersion des cartons par match plus large qu'avec un seuil unique, moyenne inchangée dans la marge validée
- [ ] Sévérité tracée au coup d'envoi
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
