# 07: Mouvement des adversaires scriptés pendant la phase de construction

**What to build:** les deux adversaires scriptés de la phase "possession adverse -> perte de balle" (tickets 02/03, `_prefix_adverse_possession`) sont actuellement IMMOBILES du début à la fin du clip (choix délibéré du ticket 02). Testé en live par le propriétaire (22/10/2026) : perçu comme une vitesse qui "saute" bizarrement — figé pendant toute la construction, puis vitesse normale d'un coup sur la conclusion. Avec 5 gabarits sur 12 concernés depuis le ticket 03, c'est devenu plus visible qu'au stade du POC. À corriger avant de généraliser aux 7 gabarits restants (tickets 04/05), pour ne pas répandre le défaut avant de le régler.

**Décision prise avec le propriétaire (22/10/2026)**, après analyse `simulafoot-architect` :
- **Option retenue** : léger balancement borné (idle sway), codé directement dans `_prefix_adverse_possession` (`templates.py`) via un keyframe intermédiaire au milieu de la construction — pas de réutilisation de `enrich_with_background` (incompatible avec le point de jonction exact, aurait réintroduit le bug de "téléportation" du ticket 02) ni d'attente du plafond de vitesse partagé (chantier externe pas encore codé, pas un prérequis réel).
- **Amplitude validée** : 0,5 m (`_SWAY_AMPLITUDE_M`), constante produit.
- **Périmètre étendu** : pas seulement les 2 adversaires scriptés — aussi le(s) rôle(s) actif(s) du camp qui marque (ex. le récupérateur), eux aussi totalement figés pendant la construction (constat de l'architecte, confirmé par le propriétaire).
- Les deux points de jonction (début du préfixe, et la vraie jonction "perte_balle" -> conclusion) restent bit-à-bit identiques à l'ancrage — seul le keyframe intermédiaire s'écarte, jamais au-delà de l'amplitude validée.

**Blocked by:** 03 (lot "jeu collectif ouvert") — déjà fait, c'est ce qui a rendu le défaut plus visible.

**Blocks:** 04 (lot "transition / pressing") — séquencé en premier pour ne pas répandre le défaut à 3 gabarits de plus avant de le régler.

**Status:** livré (23/10/2026, `9610f61`) ; statut mis à jour le 04/11/2026 d'après `git log` (l'ancien statut n'avait pas été reporté)

- [ ] Décision du propriétaire actée sur le mouvement à donner (option ci-dessus ou autre)
- [ ] Les deux adversaires scriptés ne donnent plus l'impression d'un figement total pendant la construction, sur les 5 gabarits déjà traités
- [ ] Aucun saut de position mesurable introduit aux jonctions (même garantie que les tickets 02/03)
- [ ] Déterminisme bit-à-bit vérifié
- [ ] Résultat sportif strictement identique
- [ ] Propriétaire valide visuellement sur un échantillon des 5 gabarits

**Note :** fichiers sous exception (`CLAUDE.md`) concernés selon ce qui est réellement touché — demander l'exception avant de coder.
