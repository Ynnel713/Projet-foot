# 07: Mouvement des adversaires scriptés pendant la phase de construction

**What to build:** les deux adversaires scriptés de la phase "possession adverse -> perte de balle" (tickets 02/03, `_prefix_adverse_possession`) sont actuellement IMMOBILES du début à la fin du clip (choix délibéré du ticket 02). Testé en live par le propriétaire (22/10/2026) : perçu comme une vitesse qui "saute" bizarrement — figé pendant toute la construction, puis vitesse normale d'un coup sur la conclusion. Avec 5 gabarits sur 12 concernés depuis le ticket 03, c'est devenu plus visible qu'au stade du POC. À corriger avant de généraliser aux 7 gabarits restants (tickets 04/05), pour ne pas répandre le défaut avant de le régler.

**Décision à prendre avec le propriétaire avant de coder** : quel mouvement donner aux deux adversaires à la place du figement total ? Options à explorer (analyse `simulafoot-architect` recommandée avant de coder, complexe/transverse) :
- Les traiter comme des joueurs de décor normaux (`sequence_generator.enrich_with_background`) au lieu de les figer explicitement — réutilise le mécanisme de mouvement déjà existant pour le décor, à vérifier que ça reste compatible avec leurs 2 positions-clés (point de perte de balle notamment, qui ne doit pas sauter).
- Un léger mouvement idle (balancement, ajustement de position) sans déplacement réel.
- Attendre et réutiliser le mécanisme de plafond de vitesse partagé (`.scratch/plafond-vitesse-partage/`, chantier séparé piloté ailleurs) si sa portée couvre ce cas.

**Blocked by:** 03 (lot "jeu collectif ouvert") — déjà fait, c'est ce qui a rendu le défaut plus visible.

**Blocks:** 04 (lot "transition / pressing") — séquencé en premier pour ne pas répandre le défaut à 3 gabarits de plus avant de le régler.

**Status:** ready-for-agent

- [ ] Décision du propriétaire actée sur le mouvement à donner (option ci-dessus ou autre)
- [ ] Les deux adversaires scriptés ne donnent plus l'impression d'un figement total pendant la construction, sur les 5 gabarits déjà traités
- [ ] Aucun saut de position mesurable introduit aux jonctions (même garantie que les tickets 02/03)
- [ ] Déterminisme bit-à-bit vérifié
- [ ] Résultat sportif strictement identique
- [ ] Propriétaire valide visuellement sur un échantillon des 5 gabarits

**Note :** fichiers sous exception (`CLAUDE.md`) concernés selon ce qui est réellement touché — demander l'exception avant de coder.
