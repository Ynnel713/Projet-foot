# 34a: Tir de première intention

**Origine (05/11/2026) :** remarques du propriétaire après le ticket 28a : la façon dont le ballon et le joueur arrivent l'un vers l'autre (ballon fort ou arrêté, de face, de côté ou de dos, joueur lancé ou arrêté, bon ou mauvais pied) change la qualité, la puissance et le dosage d'un tir comme d'une passe. Découpage en petits tickets (environ 2 h chacun, mesure comprise), validé par le propriétaire.

**What to build:** Aujourd'hui tout tir part d'un ballon contrôlé (réception de 1,7 à 2,9 s) : il n'existe ni reprise, ni tir sans contrôle. Ce ticket ouvre le **tir sans contrôle** d'un ballon qui arrive au sol, sur le mécanisme de jeu à une touche du ticket 31 : le receveur peut tirer de première quand la qualité de l'occasion (28a) le justifie. Decisions choisit entre tirer de première et contrôler (le contrôle laisse revenir un défenseur, la première intention est plus difficile). Exécution : la chance du 28a, avec une difficulté de première intention amortie par Technique (Finishing ou Long Shots restent l'exécution de base). La difficulté selon l'arrivée du ballon vient au 34b.

**Attributs :** Decisions, Technique (amortit la difficulté de première intention), Finishing ou Long Shots inchangés.

**Blocked by:** 31 (jeu à une touche), 28b.

**Bloque :** 34b, 34d, 10a.

**Status:** à faire (constantes à proposer avant le code)

**Hors de ce ticket :** pied fort et pied faible (`v2-attributs-restants/04a`, qui s'applique ensuite à chacun de ces gestes) ; choix du geste (placée, enroulée, `v2-attributs-restants/10a`).

## Acceptance criteria

- [ ] Constantes et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Scène contrôlée : passe au sol vers un attaquant démarqué dans la surface, il tire de première une partie du temps, jamais 0 % ni 100 % ; un défenseur proche augmente la part de première intention (pas le temps de contrôler)
- [ ] Scène contrôlée : à situation égale, Technique élevée réussit mieux la première intention que Technique basse ; sans première intention, Technique ne change rien au tir
- [ ] En match (50 matchs, graine d'audit) : part des tirs de première intention rapportée (réel à sourcer), tirs et buts par match comparés avant / après
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Déterminisme à graine fixée ; suite V2 verte ; V1 inchangée
