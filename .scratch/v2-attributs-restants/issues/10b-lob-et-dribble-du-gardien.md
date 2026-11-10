# 10b: Lob et dribble du gardien

**Découpé du ticket 10 le 04/11/2026** (audit de granularité). Détail : `10-types-de-finition.md`, point 4.

**What to build:** deux finitions de plus, ouvertes quand le gardien sort (Rushing Out, ticket 03b) : le **lob** (par-dessus le gardien avancé) et le **dribble du gardien**, résolu par Dribbling contre One on Ones dans le duel un contre un du ticket 07a (pas de second duel en double). Gestes « Likes To Lob Keeper » et « Likes To Round Keeper » en penchants.

**Attributs :** Dribbling, One on Ones (gardien) ; Decisions, Flair.

**Blocked by:** 10a, 03b, 07a ; `v2-realisme/21b` (gravité de la faute), `v2-realisme/03l` (gardien qui part tôt) ; `v2-hauteur-ballon/02a` (trajectoire en cloche) (ajouté le 10/11/2026, audit de la roadmap).

**Bloque :** aucun.

**Status:** à faire (constantes à proposer avant le code)

## Acceptance criteria

- [ ] Constantes produit validées par le propriétaire avant le code
- [ ] Test de cohérence (scènes fixes) : la part de lobs est nettement plus forte gardien avancé que gardien sur sa ligne
- [ ] Repris du ticket 03 (critère Rushing Out, troisième volet) : à situation égale, plus de buts lobés face à un gardien à Rushing Out élevé
- [ ] Le dribble du gardien passe par le duel du 07a (test)
- [ ] Lobs et dribbles du gardien apparaissent au moins une fois sur 50 matchs, sans dominer
- [ ] Tracés et rejoués par le rendu, sans changer l'issue
- [ ] Déterminisme à graine fixée ; suite V2 verte ; V1 inchangée

## Complément de l'audit de la roadmap (10/11/2026)

Source : `docs/AUDIT_ROADMAP_V2.md` §13 (question du propriétaire : dribbler le gardien en face-à-face, avec une faute possible du gardien). État vérifié : le dribble du gardien n'existe que comme une conduite ordinaire ; le gardien, s'il est à portée du porteur, intervient avec le tacle des joueurs de champ (`match.py`, candidats au tacle sans exclusion du gardien ; tentative selon Aggression, réussite selon Tackling, faute environ 30 % des tacles) : attributs hors de son rayon, et une faute dans la surface donne déjà un penalty, mais sans carton. Précisions pour ce ticket :

1. L'intervention du gardien dans les pieds du porteur passe par One on Ones (et Bravery pour plonger, `v2-realisme/17b`), plus par Tackling ni Aggression.
2. Faute du gardien sur le dribbleur : penalty dans la surface, coup franc direct hors de la surface ; sanction selon `v2-realisme/21b` (occasion manifeste annulée : jaune dans la surface s'il tente de jouer le ballon, rouge sinon ; rouge hors de la surface).
3. Après le gardien éliminé, la finition reste incertaine : but vide, angle fermé, défenseur revenu sur la ligne.

- [ ] Le gardien n'utilise plus Tackling ni Aggression pour intervenir sur le porteur
- [ ] Scènes : dribble réussi puis but vide marqué ou manqué ; faute du gardien dans la surface : penalty et carton selon 21b ; hors de la surface : coup franc et rouge

**Le piqué par-dessus le gardien** (demande du propriétaire, 10/11/2026) : une variante du lob, fréquente en face-à-face, à traiter ici comme **une option de plus** dans l'arsenal du tireur, jamais un geste imposé.

4. **Quand il devient intéressant** : le gardien sort au-devant du tireur ou se couche tôt (anticipation et départ anticipé du `v2-realisme/03l`, sortie du 03e) ; il est rarement le bon choix face à un gardien resté debout sur sa ligne. Le piqué entre dans le choix de la finition (10a) avec sa valeur réelle, perçue via Decisions, comme les autres options : pas de part fixe.
5. **Qui le tente et qui le réussit** : la réussite dépend de Technique (geste difficile, rayon de la carte) et de Composure sous la pression du face-à-face ; Flair et le geste préféré « Likes To Lob Keeper » ne changent que la fréquence du choix, pas la réussite. Un joueur modeste peut le réussir, un très bon peut le manquer (garde `v2-realisme/19c`).
6. **Ses ratés sont physiques** : trop long (au-dessus de la barre), trop court ou pas assez haut (le gardien le touche en se relevant), à côté ; trajectoire en cloche avec la hauteur du ballon (`v2-hauteur-ballon/02a`), résolue par la portée du gardien (05b).
7. **Fréquence** : rare à l'échelle d'un match ; repère sourcé à chercher (part des buts marqués en piqué parmi les face-à-face), sinon « non trouvé » et fréquence rapportée sans réglage.

- [ ] Scènes : gardien qui sort et se couche tôt contre gardien debout sur sa ligne : piqué nettement plus souvent choisi dans le premier cas
- [ ] Technique 90 contre 50, même situation : réussite du piqué plus haute, jamais garantie ; ratés trop long, trop court et à côté tous présents
- [ ] « Likes To Lob Keeper » et Flair : plus de piqués tentés, réussite inchangée à notes égales
- [ ] Fréquence rapportée sur 500 matchs (rare, sans dominer les autres finitions)
