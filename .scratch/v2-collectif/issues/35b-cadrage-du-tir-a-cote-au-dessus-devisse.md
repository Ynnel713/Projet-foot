# 35b: Cadrage du tir : à côté, au-dessus, dévissé

**Origine (05/11/2026) :** remarques du propriétaire après le ticket 28a : la façon dont le ballon et le joueur arrivent l'un vers l'autre (ballon fort ou arrêté, de face, de côté ou de dos, joueur lancé ou arrêté, bon ou mauvais pied) change la qualité, la puissance et le dosage d'un tir comme d'une passe. Découpage en petits tickets (environ 2 h chacun, mesure comprise), validé par le propriétaire.

**What to build:** Aujourd'hui un tir non converti part « à côté » dans 64 % des cas, tiré au hasard sans lien avec le tireur (`match.SHOT_WIDE_SHARE`, ticket 29). Ce ticket fait dépendre le cadrage de **l'exécution** : le tireur vise un point du but et le ballon s'en écarte selon sa note (Finishing ou Long Shots), la pression (28a), la difficulté de frappe (34b, 34c) et le pied (04a). Écart faible : cadré ; plus grand : à côté ou au-dessus ; très grand, rarement : **dévissé** (ballon lent, très écarté, parfois en touche). Le tir au-dessus ne prend sa vraie trajectoire qu'avec `v2-hauteur-ballon/02a` ; ici, issue tracée et rejouée à plat.

**Attributs :** Finishing ou Long Shots (déjà lus par le tir), aucun nouvel attribut.

**Blocked by:** 28b.

**Bloque :** 35c, 22c.

**Status:** à faire (constantes à proposer avant le code)

**Hors de ce ticket :** pied fort et pied faible (`v2-attributs-restants/04a`, qui s'applique ensuite à chacun de ces gestes) ; choix du geste (placée, enroulée, `v2-attributs-restants/10a`).

## Acceptance criteria

- [ ] Constantes et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Scène contrôlée : un tireur à note basse met plus de tirs à côté qu'un tireur à note haute, à même endroit ; la pression augmente les tirs non cadrés
- [ ] Dévissé : rare, plus fréquent à note basse et sous pression ; jamais pour 0 %
- [ ] En match : tirs cadrés 30-35 % des tirs (repère du 28b), à côté et au-dessus rapportés ; `SHOT_WIDE_SHARE` retiré
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Déterminisme à graine fixée ; suite V2 verte ; V1 inchangée
