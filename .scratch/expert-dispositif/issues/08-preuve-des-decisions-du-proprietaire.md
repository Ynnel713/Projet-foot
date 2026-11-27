# 08: Preuve des décisions du propriétaire pour le contrôle qualité

**Ouvert le 27/11/2026** (décision du propriétaire, « Ok avec ta recommandation », à la clôture de `v2-ecran-match/22b`).

**Constat :** le contrôle qualité (`.claude/agents/controle-qualite.md`) ne juge pas de la même façon une même forme de preuve d'une décision du propriétaire.
- `v2-hauteur-ballon/02b2` (journal, sous-étape `v2-hauteur-ballon/02b2`, 27/11/2026) : VALIDÉ avec un critère de fluidité non tenu, accepté par le propriétaire (« ok »), sur la seule foi du ticket.
- `v2-ecran-match/22b` (journal, passages 1 et 2) : BLOQUÉ deux fois, sur le même type de critère et la même forme de preuve (« J'accepte », cité dans le ticket avec la question posée). Le QC objectait que la section Comments est rédigée par la session : ni la conversation ni aucune pièce indépendante ne lui sont accessibles.
- Passage 3 : VALIDÉ, après qu'on lui a soumis la règle (le ticket est le support des décisions du propriétaire) et le précédent.

Les deux lectures se défendent : le dispositif ne dit pas explicitement quelle preuve d'une décision du propriétaire le QC doit accepter, et toute trace dans le dépôt est écrite par la session.

**What to build:**
1. Écrire la règle dans `docs/agents/validation-tickets.md` et dans la consigne du sous-agent `controle-qualite` : une décision ou une acceptation du propriétaire est recevable si le ticket cite la question posée et ses mots exacts, avec la date ; le QC n'a pas à en exiger d'autre preuve, il vérifie la forme (question, mots, date, objet précis).
2. Examiner (proposition au propriétaire, sans coder sans son accord) un support plus robuste : par exemple, un fichier de décisions append-only alimenté par un mécanisme que la session ne peut pas forger. Préciser ce qui est possible dans une session cloud, et ce qui ne l'est pas.
3. Banc : un cas de test du QC (contenu fourni) avec une acceptation citée dans la bonne forme, et un cas sans les mots du propriétaire.

**Blocked by:** aucun.

**Bloque :** aucun.

**Estimation** (27/11/2026) : analyse 20 min, développement (règle et consigne) 20 min, tests 20 min, intégration 15 min ; total 1 h 15 ; confiance moyenne.

**Status:** à faire

## Acceptance criteria

- [ ] Règle écrite dans `docs/agents/validation-tickets.md` et dans la consigne du QC (forme recevable d'une décision du propriétaire)
- [ ] Proposition chiffrée au propriétaire sur un support plus robuste (point 2), décision consignée
- [ ] Deux cas de test du QC (acceptation recevable, acceptation absente) rendus comme attendu

## Comments
