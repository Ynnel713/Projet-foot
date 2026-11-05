# 34d: Volée et demi-volée

**Origine (05/11/2026) :** remarques du propriétaire après le ticket 28a : la façon dont le ballon et le joueur arrivent l'un vers l'autre (ballon fort ou arrêté, de face, de côté ou de dos, joueur lancé ou arrêté, bon ou mauvais pied) change la qualité, la puissance et le dosage d'un tir comme d'une passe. Découpage en petits tickets (environ 2 h chacun, mesure comprise), validé par le propriétaire.

**What to build:** Avec la hauteur du ballon (`v2-hauteur-ballon/02a`), un ballon qui arrive en l'air à hauteur de pied peut être repris de volée (avant le rebond) ou de demi-volée (juste après). Plus difficile qu'un tir au sol (34b), surtout de côté ; Technique amortit. Au-dessus de la hauteur de pied, c'est une tête (`v2-attributs-restants/01`). Un centre au second poteau repris de volée devient possible.

**Attributs :** Technique (amortit), Finishing ou Long Shots inchangés.

**Blocked by:** 34b, `v2-hauteur-ballon/02a`.

**Bloque :** 10a.

**Status:** à faire (constantes à proposer avant le code)

**Hors de ce ticket :** pied fort et pied faible (`v2-attributs-restants/04a`, qui s'applique ensuite à chacun de ces gestes) ; choix du geste (placée, enroulée, `v2-attributs-restants/10a`).

## Acceptance criteria

- [ ] Constantes et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Scène contrôlée : un centre à hauteur de pied est repris de volée ; plus haut, il ne l'est pas (tête, ticket 01)
- [ ] Scène contrôlée : à même endroit, volée de côté moins réussie que tir de première au sol de face ; Technique élevée réduit l'écart
- [ ] En match : part des volées parmi les tirs rapportée (réel à sourcer)
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Déterminisme à graine fixée ; suite V2 verte ; V1 inchangée
