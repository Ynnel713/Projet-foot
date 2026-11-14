# 36a: Difficulté de passe selon l'arrivée du ballon

**Origine (05/11/2026) :** remarques du propriétaire après le ticket 28a : la façon dont le ballon et le joueur arrivent l'un vers l'autre (ballon fort ou arrêté, de face, de côté ou de dos, joueur lancé ou arrêté, bon ou mauvais pied) change la qualité, la puissance et le dosage d'un tir comme d'une passe. Découpage en petits tickets (environ 2 h chacun, mesure comprise), validé par le propriétaire.

**What to build:** Même idée que le 34b pour les passes jouées sans contrôle (ticket 31) : un ballon qui arrive **fort**, **de côté** ou **de dos** rend la passe à une touche moins juste (direction), moins bien dosée (vitesse) et plus lente à déclencher ; un ballon arrêté ou contrôlé n'a pas cette difficulté. Passe par la fonction de difficulté partagée (`possession`, v2-socle/04). Technique amortit la difficulté de la passe à une touche (déjà son rôle au 31), Passing reste la précision de base.

**Attributs :** Technique (amortit), Passing inchangé.

**Blocked by:** 31, 34b (même calcul de l'angle d'arrivée) ; `v2-realisme/26a` (ajouté le 14/11/2026).

**Bloque :** 36b.

**Status:** à faire (constantes à proposer avant le code)

**Hors de ce ticket :** pied fort et pied faible (`v2-attributs-restants/04a`, qui s'applique ensuite à chacun de ces gestes) ; choix du geste (placée, enroulée, `v2-attributs-restants/10a`).

## Acceptance criteria

- [ ] Constantes et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Scènes contrôlées : passe à une touche d'un ballon de face plus réussie que de côté, elle-même plus que de dos ; ballon fort plus difficile que ballon lent
- [ ] En match : réussite des passes à une touche comparée aux passes après contrôle, rapportée
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Déterminisme à graine fixée ; suite V2 verte ; V1 inchangée
