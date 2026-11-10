# 19e: Lecture de la chaîne d'un but et origine des buts

**Chantier :** `v2-realisme` (découpé du `19b` le 10/11/2026, recommandation de l'architecte validée par délégation du propriétaire). **Priorité :** P0 (avant 18a). **Catégorie :** mesure.

**What to build:** Outil `scripts/v2_chain.py` : remonter la chaîne d'un but ou d'une occasion dans `MatchTrace.events` (19b) et l'afficher. Classement de l'origine d'un but : en remontant depuis le but, premier événement qui donne le ballon à l'équipe qui marque : remise en jeu (coup de pied arrêté), perte sur contrôle raté ou touche trop longue (erreur), tacle, interception ou conduite perdue au contact (récupération), engagement (jeu placé). Statistiques sur 20 matchs : part des buts par origine. Lecture seule.

**Reprise de la réserve A1 de l'expert sur le 19b (10/11/2026), à faire en premier :** la faute avec avantage est écrite au moment où l'avantage se règle (`match._settle_advantage`), avec la minute de la faute : les minutes du journal ne sont pas toujours croissantes, et une faute réglée après un but a ce but pour cause. Correctif recommandé : écrire « faute (avantage) » dans `_foul` au moment où l'avantage est accordé, rien au règlement. Test : sur 20 matchs, minutes du journal croissantes et aucune faute causée par un but. (+ 15 min à l'estimation.)

**Constante à proposer avant le code :** ce qui compte comme coup de pied arrêté (touche ? coup franc indirect de hors-jeu, qui n'a pas d'événement de remise ?) et une éventuelle limite de temps (un but 3 minutes après une touche n'en est plus un).

**Attributs :** aucun

**Blocked by:** 19b.

**Bloque :** 18a.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 10 min |
| Développement | 25 min |
| Tests unitaires et comportementaux | 15 min |
| Intégration et vérifications | 10 min |
| **Total (travail effectif)** | **1 h 00** |

Confiance : moyenne. Hypothèses : journal du 19b livré.
Temps machine, non compté : 20 matchs (environ 8 min en parallèle) ; suite complète (environ 25 min).

## Tests

- **Unitaires :** chaîne artificielle (corner → tête → but ; tacle → passe → but ; contrôle raté → tir → but) classée dans la bonne origine
- **Statistiques (séries de matchs) :** 20 matchs : part des buts par origine, comparée à l'ordre de grandeur réel (sourcé ou « non trouvé »)

## Acceptance criteria

- [ ] Constante produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] `scripts/v2_chain.py` affiche la chaîne d'un but choisi
- [ ] Origine classée pour chaque but de 20 matchs ; aucun but « inclassable » non expliqué
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes résultats sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
