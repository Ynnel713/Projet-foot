# 35a: Puissance de frappe

**Origine (05/11/2026) :** remarques du propriétaire après le ticket 28a : la façon dont le ballon et le joueur arrivent l'un vers l'autre (ballon fort ou arrêté, de face, de côté ou de dos, joueur lancé ou arrêté, bon ou mauvais pied) change la qualité, la puissance et le dosage d'un tir comme d'une passe. Découpage en petits tickets (environ 2 h chacun, mesure comprise), validé par le propriétaire.

**What to build:** Aujourd'hui tout tir part à 30 m/s, quel que soit le tireur. Ce ticket donne à chaque tir une **vitesse** qui dépend de **Long Shots** (capacité de frappe : un joueur à 18/20 frappe très fort, un joueur à 7-8 ne peut pas frapper très fort ; la carte des attributs définit déjà Long Shots comme « précision et puissance ») et, après 34c, de l'élan. La vitesse compte : moins de temps de réaction pour le gardien (arrêts du 28b, notes au `v2-attributs-restants/03b`) et ballon contré ou repoussé qui part plus loin. **Point à trancher avant le code** (recommandation du porteur) : la puissance vient de Long Shots pour tous les tirs, y compris dans la surface, où Finishing garde la précision ; ce sont deux effets distincts (vitesse et précision), pas un mélange de notes dans un même calcul, donc pas de double comptage. À inscrire dans la carte.

**Attributs :** Long Shots (puissance, partout), Finishing inchangé (précision dans la surface).

**Blocked by:** 28b.

**Bloque :** 34c, 10a (frappe puissante).

**Status:** à faire (constantes à proposer avant le code)

**Hors de ce ticket :** pied fort et pied faible (`v2-attributs-restants/04a`, qui s'applique ensuite à chacun de ces gestes) ; choix du geste (placée, enroulée, `v2-attributs-restants/10a`).

## Acceptance criteria

- [ ] Constantes et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Scène contrôlée : vitesse du tir croissante avec Long Shots, jamais au-dessus du maximum réel (à sourcer)
- [ ] Scène contrôlée : à même endroit, un tir plus rapide est moins souvent capté (28b)
- [ ] Carte des attributs : Long Shots porte la puissance de tous les tirs, Finishing la précision dans la surface ; test de rayon à jour
- [ ] En match : distribution des vitesses de tir rapportée
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Déterminisme à graine fixée ; suite V2 verte ; V1 inchangée
