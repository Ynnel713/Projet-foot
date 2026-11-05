# 36b: Passe en course

**Origine (05/11/2026) :** remarques du propriétaire après le ticket 28a : la façon dont le ballon et le joueur arrivent l'un vers l'autre (ballon fort ou arrêté, de face, de côté ou de dos, joueur lancé ou arrêté, bon ou mauvais pied) change la qualité, la puissance et le dosage d'un tir comme d'une passe. Découpage en petits tickets (environ 2 h chacun, mesure comprise), validé par le propriétaire.

**What to build:** Comme au 34c pour les tirs : un passeur **lancé** donne plus de vitesse à sa passe mais la dose moins finement ; un passeur **arrêté** dose mieux. Affecte le dosage (`possession.dosage_quality`, Passing) et la justesse, sans nouvel attribut.

**Attributs :** Aucun nouvel attribut (Passing pour le dosage, Technique pour le geste comme au 36a).

**Blocked by:** 36a, 34c (même lecture de la course).

**Bloque :** —

**Status:** à faire (constantes à proposer avant le code)

**Hors de ce ticket :** pied fort et pied faible (`v2-attributs-restants/04a`, qui s'applique ensuite à chacun de ces gestes) ; choix du geste (placée, enroulée, `v2-attributs-restants/10a`).

## Acceptance criteria

- [ ] Constantes et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Scène contrôlée : à même passe, un passeur lancé envoie plus vite et dose moins bien qu'un passeur arrêté
- [ ] En match : réussite des passes et receveur visé comparés avant / après (pas de baisse au-delà de 2 points sans explication)
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Déterminisme à graine fixée ; suite V2 verte ; V1 inchangée
