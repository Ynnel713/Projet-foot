import random
from collections import Counter

import pytest

from ligue1sim.animation.templates import (
    ANCHOR_STATIC,
    BUILDERS,
    TEMPLATES,
    TemplateContext,
    _urgency_factor,
    build_from_template,
    pick_template,
)
from ligue1sim.events import GoalEvent
from ligue1sim.lineup import Lineup
from ligue1sim.pitch_geometry import GRID_COLUMNS, GRID_ROWS, PITCH_LENGTH_M, PitchPoint, Zone, center_of
from ligue1sim.players import Player

_SCORER_ZONE = Zone(col=10, row=4)
_ASSIST_ZONE = Zone(col=7, row=3)


def _chi_square_homogeneity(counts_a: Counter, counts_b: Counter) -> float:
    """Statistique du chi² pour un test d'homogénéité entre deux
    échantillons catégoriels indépendants (table de contingence 2xK) --
    implémentation directe (pas de scipy dans ce projet), formule standard :
    somme sur chaque cellule de (observé - attendu)² / attendu, attendu =
    (total ligne * total colonne) / total général."""
    categories = set(counts_a) | set(counts_b)
    total_a = sum(counts_a.values())
    total_b = sum(counts_b.values())
    grand_total = total_a + total_b
    chi2 = 0.0
    for category in categories:
        col_total = counts_a.get(category, 0) + counts_b.get(category, 0)
        for observed, row_total in ((counts_a.get(category, 0), total_a), (counts_b.get(category, 0), total_b)):
            expected = row_total * col_total / grand_total
            if expected > 0:
                chi2 += (observed - expected) ** 2 / expected
    return chi2


def _player(poste: str, note: float, name: str, player_id: int) -> Player:
    return Player(
        prenom=name, nom="", nationalite="France", age=25, poste=poste, note=note,
        club="Test FC", championnat="TEST", id=player_id,
    )


def _lineup() -> Lineup:
    players = [
        _player("GK", 70.0, "gk", 1),
        _player("DC", 70.0, "cb0", 2),
        _player("DC", 70.0, "cb1", 3),
        _player("LB", 70.0, "lb", 4),
        _player("RB", 70.0, "rb", 5),
        _player("MDC", 70.0, "mdc", 6),
        _player("MC", 70.0, "mc0", 7),
        _player("MC", 70.0, "mc1", 8),
        _player("AG", 70.0, "ag", 9),
        _player("AD", 70.0, "ad", 10),
        _player("BU", 70.0, "bu", 11),
    ]
    return Lineup(club_name="Test FC", formation="4-3-3", players=players, rating=70.0)


def _start_positions(lineup: Lineup) -> dict[int, PitchPoint]:
    return {p.id: PitchPoint(x=0.15 + 0.06 * i, y=0.1 + 0.07 * i) for i, p in enumerate(lineup.players)}


def _goal_event(*, scorer: str = "bu", assist: str | None = "mc0", minute: int = 34, penalty: bool = False) -> GoalEvent:
    return GoalEvent(
        club_name="Test FC",
        scorer=scorer,
        assist=assist,
        minute=minute,
        penalty=penalty,
        zone=_SCORER_ZONE,
        assist_zone=_ASSIST_ZONE if assist else None,
    )


class TestTemplateRichness:
    """Critère minimal de richesse (23/09/2026, suite à l'audit visuel de
    scripts/preview_templates.py) : chaque gabarit doit avoir au moins 3
    keyframes ET une phase de préparation visible (un `tag` avant la
    conclusion) -- universellement, un gabarit à 2 points (départ/arrivée)
    ne raconte rien. Le nombre de RÔLES, en revanche, n'est exigé qu'aux 4
    gabarits identifiés comme pauvres par l'audit (`corner`, `penalty`,
    `but_gag`, `recuperation_haute`, tous enrichis à 3 rôles ce jour) : un
    "une_deux" ou un "coup_franc" n'ont légitimement besoin que de peu
    d'acteurs, leur imposer un 3e rôle serait artificiel plutôt que
    réaliste."""

    _FORMERLY_POOR_TEMPLATES = {"corner", "penalty", "but_gag", "recuperation_haute"}

    def _nb_keyframes(self, template) -> int:
        return len({frame.t_ratio for role in template.roles for frame in role.frames})

    def test_every_template_has_at_least_three_keyframes(self):
        for name, template in TEMPLATES.items():
            assert self._nb_keyframes(template) >= 3, f"{name} n'a que {self._nb_keyframes(template)} keyframes"

    def test_every_template_has_a_visible_preparation_phase_before_the_conclusion(self):
        # Un tag non vide avant le dernier point -- pas juste "départ" puis
        # "tir" sans rien entre les deux.
        for name, template in TEMPLATES.items():
            tags_before_last = [tag for t_ratio, tag in template.tags if t_ratio < 1.0]
            assert any(tags_before_last), f"{name} n'a aucune phase de préparation étiquetée avant t=1.0"

    def test_formerly_poor_templates_now_have_at_least_three_named_roles(self):
        for name in self._FORMERLY_POOR_TEMPLATES:
            assert len(TEMPLATES[name].roles) >= 3, f"{name} a encore moins de 3 rôles"


class TestRegistryIntegrity:
    def test_at_least_eight_templates_are_registered(self):
        assert len(TEMPLATES) >= 8

    def test_twelve_templates_are_registered(self):
        assert len(TEMPLATES) == 12

    def test_every_template_has_a_matching_builder(self):
        assert set(TEMPLATES) == set(BUILDERS)

    def test_every_template_key_matches_its_own_name(self):
        for key, template in TEMPLATES.items():
            assert key == template.name

    def test_every_template_has_a_positive_weight_and_duration(self):
        for template in TEMPLATES.values():
            assert template.weight > 0
            assert template.duration > 0


class TestEveryTemplateProducesAValidSequence:
    """"Chaque template produit une Sequence valide pour un event synthétique"
    -- la validité (t croissant, même ensemble de joueurs à chaque keyframe)
    est déjà vérifiée par Sequence.__post_init__ : un template buggé lève
    une exception ici plutôt que produire un objet invalide en silence."""

    @pytest.mark.parametrize("name", sorted(BUILDERS))
    def test_builds_a_sequence_with_assisted_goal(self, name):
        lineup = _lineup()
        sequence = BUILDERS[name](_goal_event(), lineup, _start_positions(lineup))

        assert sequence.keyframes
        assert sequence.duration == TEMPLATES[name].duration
        assert sequence.meta["template"] == name

    @pytest.mark.parametrize("name", sorted(BUILDERS))
    def test_builds_a_sequence_with_an_unassisted_goal(self, name):
        # Les gabarits qui utilisent un rôle "assist" doivent continuer à
        # fonctionner sans passeur réel (event.assist=None) -- le rôle est
        # simplement absent, pas une erreur (voir _resolve_roles).
        lineup = _lineup()
        sequence = BUILDERS[name](_goal_event(assist=None), lineup, _start_positions(lineup))
        assert sequence.keyframes

    @pytest.mark.parametrize("name", sorted(BUILDERS))
    def test_produced_sequence_serializes_to_json(self, name):
        lineup = _lineup()
        sequence = BUILDERS[name](_goal_event(), lineup, _start_positions(lineup))
        payload = sequence.to_json()
        assert payload["keyframes"]


class TestPenaltyIsSpecialCased:
    def test_penalty_template_places_the_scorer_at_the_penalty_spot_zone(self):
        lineup = _lineup()
        event = _goal_event(assist=None, penalty=True, minute=70)
        sequence = BUILDERS["penalty"](event, lineup, _start_positions(lineup))

        expected = center_of(event.zone)
        scorer_final_x, scorer_final_y = sequence.keyframes[-1].players[11]  # id du "bu"
        assert scorer_final_x == pytest.approx(expected.x)
        assert scorer_final_y == pytest.approx(expected.y)


class TestBuildFromTemplateIsPure:
    def test_same_inputs_produce_an_identical_sequence(self):
        lineup = _lineup()
        start = _start_positions(lineup)
        event = _goal_event()

        first = build_from_template(TEMPLATES["contre_attaque"], event, lineup, start)
        second = build_from_template(TEMPLATES["contre_attaque"], event, lineup, start)

        assert first.to_json() == second.to_json()


class TestScorerReachesTheEventZone:
    def test_the_scorers_final_position_matches_the_event_zone_centre(self):
        lineup = _lineup()
        event = _goal_event()
        sequence = build_from_template(TEMPLATES["debordement_centre_tete"], event, lineup, _start_positions(lineup))

        expected = center_of(event.zone)
        last = sequence.keyframes[-1]
        scorer_x, scorer_y = last.players[11]  # "bu"
        assert scorer_x == pytest.approx(expected.x)
        assert scorer_y == pytest.approx(expected.y)


class TestPickTemplateHardConstraints:
    def _context(self, **overrides) -> TemplateContext:
        base = dict(
            minute=50, goal_diff_before=0, scorer_poste="BU", assist_poste="MC", penalty=False,
            competition_type="league",
        )
        base.update(overrides)
        return TemplateContext(**base)

    def test_a_penalty_context_always_picks_the_penalty_template(self):
        context = self._context(penalty=True, assist_poste=None)
        picks = {pick_template(context) for _ in range(30)}
        assert picks == {"penalty"}

    def test_a_non_penalty_context_never_picks_the_penalty_template(self):
        context = self._context(penalty=False)
        picks = {pick_template(context) for _ in range(60)}
        assert "penalty" not in picks


class TestPickTemplateContextScoring:
    def test_wide_scorer_with_no_assist_favors_the_individual_run_template(self):
        context = TemplateContext(
            minute=60, goal_diff_before=0, scorer_poste="AG", assist_poste=None, penalty=False,
            competition_type="league",
        )
        percee = TEMPLATES["percee_individuelle"]
        recuperation = TEMPLATES["coup_franc"]
        assert percee.weight * percee.context_score(context) > recuperation.weight * recuperation.context_score(context)

    def test_aerial_scorer_with_wide_assist_favors_the_header_from_a_cross_template(self):
        favorable = TemplateContext(
            minute=60, goal_diff_before=0, scorer_poste="DC", assist_poste="AG", penalty=False,
            competition_type="league",
        )
        neutral = TemplateContext(
            minute=60, goal_diff_before=0, scorer_poste="MC", assist_poste="MC", penalty=False,
            competition_type="league",
        )
        debordement = TEMPLATES["debordement_centre_tete"]
        assert debordement.context_score(favorable) > debordement.context_score(neutral)

    def test_picking_many_times_over_varied_contexts_yields_more_than_one_template(self):
        # La diversité doit venir des gabarits eux-mêmes (voir objectif du
        # module), pas d'un seul gabarit qui écraserait tous les autres.
        contexts = [
            TemplateContext(
                minute=m, goal_diff_before=0, scorer_poste=poste, assist_poste=assist, penalty=False,
                competition_type="league",
            )
            for m in (5, 30, 60, 85)
            for poste in ("BU", "AG", "AD", "DC", "MOC")
            for assist in (None, "MC", "AG", "MDC")
        ]
        picks = {pick_template(context) for context in contexts}
        assert len(picks) > 3


class TestPickTemplateReactsToScore:
    """Vérifie que `TemplateContext.goal_diff_before` a un effet RÉEL sur la
    distribution des gabarits -- avant le 23/09/2026, ce champ existait mais
    n'était lu par AUCUNE fonction `context_score`, donc `pick_template`
    "pondérait à vide" quel que soit l'écart au score transmis."""

    _URGENT_TEMPLATES = {"contre_attaque", "recuperation_haute", "percee_individuelle"}

    def _bucket(self, name: str) -> str:
        if name == "construction_placee":
            return "construction_placee"
        return name if name in self._URGENT_TEMPLATES else "autres"

    def _context(self, goal_diff_before: int) -> TemplateContext:
        return TemplateContext(
            minute=60, goal_diff_before=goal_diff_before, scorer_poste="BU", assist_poste="MC",
            penalty=False, competition_type="league",
        )

    def test_urgency_factor_is_higher_when_trailing_and_lower_when_leading_comfortably(self):
        assert _urgency_factor(-2) > _urgency_factor(-1) > _urgency_factor(0) > _urgency_factor(1) > _urgency_factor(2)

    def test_construction_placee_is_favored_over_contre_attaque_when_comfortably_ahead(self):
        context = self._context(goal_diff_before=3)
        construction = TEMPLATES["construction_placee"]
        contre_attaque = TEMPLATES["contre_attaque"]
        assert (
            construction.weight * construction.context_score(context)
            > contre_attaque.weight * contre_attaque.context_score(context)
        )

    def test_contre_attaque_is_favored_over_construction_placee_when_level(self):
        context = self._context(goal_diff_before=0)
        construction = TEMPLATES["construction_placee"]
        contre_attaque = TEMPLATES["contre_attaque"]
        assert (
            contre_attaque.weight * contre_attaque.context_score(context)
            > construction.weight * construction.context_score(context)
        )

    def test_template_distribution_differs_significantly_between_a_level_and_a_blowout_score(self):
        """Test statistique (chi² d'homogénéité, sans dépendance à scipy --
        non installé dans ce projet, voir valeur critique documentée) sur
        500 tirages par contexte : la distribution des gabarits (regroupés
        en 4 catégories pour garantir des effectifs attendus suffisants,
        voir `_bucket`) doit différer significativement entre un but à 0-0
        (goal_diff_before=0) et un but à 3-0 (goal_diff_before=3), même
        minute et mêmes postes."""
        context_level = self._context(goal_diff_before=0)
        context_blowout = self._context(goal_diff_before=3)

        counts_level = Counter(self._bucket(pick_template(context_level, rng=random.Random(seed))) for seed in range(500))
        counts_blowout = Counter(
            self._bucket(pick_template(context_blowout, rng=random.Random(seed + 1_000_000))) for seed in range(500)
        )

        chi2 = _chi_square_homogeneity(counts_level, counts_blowout)
        # Table du chi², df=3 (4 catégories - 1), alpha=1% -> 11.345 (valeur
        # standard, aucune dépendance à scipy nécessaire pour ce seuil fixe).
        assert chi2 > 11.345, f"chi2={chi2:.2f} ne dépasse pas le seuil de significativité (df=3, alpha=1%)"

        # Le sens de l'effet compte autant que son existence : une équipe
        # menée à 0-0 presse/contre plus, une équipe qui mène 3-0 construit.
        assert counts_level["recuperation_haute"] / 500 > counts_blowout["recuperation_haute"] / 500
        assert counts_blowout["construction_placee"] / 500 > counts_level["construction_placee"] / 500


class TestSegmentSpeedHeadroom:
    """"Point B" du brief du 23/09/2026 : un segment de gabarit qui exige
    RÉELLEMENT plus que v_max en moyenne ne peut pas être rattrapé par le
    repli linéaire de motion.py (voir sa docstring de module, "Limite connue
    et non corrigée" -- saut de position/vitesse à la transition). Aucun des
    12 gabarits actuels n'atteint ce seuil (`une_deux` est le plus proche,
    ~76% de v_max) -- ce test fige cette marge pour qu'une future édition
    d'un gabarit (nouveaux RoleFrame plus exigeants) ne la fasse pas
    silencieusement basculer en territoire "impossible"."""

    def _worst_ratio(self, name: str, lineup: Lineup) -> float:
        from ligue1sim.animation.motion import _real_distance_m, max_speed_normalized

        sequence = BUILDERS[name](_goal_event(), lineup, _start_positions(lineup))
        worst = 0.0
        for player_id, entry in sequence.roster.items():
            if entry.role is None:
                continue
            v_max = max_speed_normalized(entry.poste)
            for kf_a, kf_b in zip(sequence.keyframes, sequence.keyframes[1:]):
                duration = kf_b.t - kf_a.t
                if duration <= 0:
                    continue
                dist_m = _real_distance_m(kf_a.players[player_id], kf_b.players[player_id])
                required_avg_speed = (dist_m / 105.0) / duration
                worst = max(worst, required_avg_speed / v_max)
        return worst

    @pytest.mark.parametrize("name", sorted(BUILDERS))
    def test_no_template_ever_demands_more_than_v_max(self, name):
        ratio = self._worst_ratio(name, _lineup())
        assert ratio < 1.0, f"{name} exige {ratio:.2f}x v_max sur son segment le plus dur -- devient \"impossible\""

    def test_une_deux_is_the_closest_to_the_critical_threshold(self):
        # Constat du 23/09/2026 (voir docs/simulation_physique_archi.md,
        # "Point B") -- si ce n'est plus vrai, la table a changé et mérite
        # d'être revérifiée, pas seulement ce test corrigé en silence.
        lineup = _lineup()
        ratios = {name: self._worst_ratio(name, lineup) for name in BUILDERS}
        assert max(ratios, key=ratios.get) == "une_deux"


class TestContreAttaqueSupport1Carries:
    """Fix du 23/09/2026 (brief "contre_attaque carrier movement") :
    `support1` récupère le ballon à t=0, le conduit vers l'avant (ANCHOR_SCORER,
    plus ANCHOR_STATIC), puis le relâche à `assist` au ratio prévu -- voir le
    commentaire sur le rôle dans templates.py pour le raisonnement complet.

    Fix "suite 2" (même jour, brief "carrier continuation") : support1 ne
    s'arrête plus net après la passe (0.3 -> 0.3, figé) mais continue
    d'avancer en décélérant jusqu'à la fin (0.3 -> 0.4) -- voir
    `test_contre_attaque_support1_continues_after_the_relay`."""

    def _sequence(self):
        lineup = _lineup()
        return BUILDERS["contre_attaque"](_goal_event(), lineup, _start_positions(lineup))

    def test_contre_attaque_support1_moves(self):
        from ligue1sim.animation.motion import _real_distance_m

        sequence = self._sequence()
        support_id = next(pid for pid, entry in sequence.roster.items() if entry.role == "support1")
        first = sequence.keyframes[0].players[support_id]
        last = sequence.keyframes[-1].players[support_id]
        delta_m = _real_distance_m(first, last)
        assert delta_m > 0.05 * PITCH_LENGTH_M, f"delta={delta_m:.2f}m, attendu > {0.05 * PITCH_LENGTH_M:.2f}m"

    def test_contre_attaque_support1_continues_after_the_relay(self):
        # Brief "carrier continuation" du 23/09/2026 : un arrêt net juste
        # après la passe (t_ratio=0.4) lisait comme "il a débranché" -- il
        # doit continuer d'avancer, même modestement, jusqu'à la fin.
        from ligue1sim.animation.motion import _real_distance_m

        sequence = self._sequence()
        support_id = next(pid for pid, entry in sequence.roster.items() if entry.role == "support1")
        at_relay = next(kf.players[support_id] for kf in sequence.keyframes if kf.t == pytest.approx(0.4 * sequence.duration))
        at_end = sequence.keyframes[-1].players[support_id]
        delta_m = _real_distance_m(at_relay, at_end)
        assert delta_m > 1.5, f"delta post-relais={delta_m:.2f}m, attendu > 1.5m (pas un arrêt net)"

    def test_contre_attaque_ball_follows_carrier(self):
        from ligue1sim.animation.motion import _real_distance_m

        sequence = self._sequence()
        support_id = next(pid for pid, entry in sequence.roster.items() if entry.role == "support1")
        carried_keyframes = [kf for kf in sequence.keyframes if kf.ball.owner_id == support_id]
        assert carried_keyframes, "aucun keyframe où support1 porte le ballon -- ball_owner mal câblé"
        for kf in carried_keyframes:
            dist_m = _real_distance_m((kf.ball.x, kf.ball.y), kf.players[support_id])
            assert dist_m < 2.0, f"t={kf.t}: ballon à {dist_m:.2f}m de support1 (tolérance 2m)"

    def test_contre_attaque_ball_transfers_to_assist(self):
        from ligue1sim.animation.motion import _real_distance_m

        sequence = self._sequence()
        assist_id = next(pid for pid, entry in sequence.roster.items() if entry.role == "assist")
        transfer_ratio = next(ratio for ratio, role in TEMPLATES["contre_attaque"].ball_owner if role == "assist")
        transfer_kf = next(kf for kf in sequence.keyframes if kf.t == pytest.approx(transfer_ratio * sequence.duration))

        assert transfer_kf.ball.owner_id == assist_id
        dist_m = _real_distance_m((transfer_kf.ball.x, transfer_kf.ball.y), transfer_kf.players[assist_id])
        assert dist_m < 2.0, f"transfert : ballon à {dist_m:.2f}m de assist (tolérance 2m)"


class TestNoDeadProgressOnStaticAnchor:
    """Tâche 2 du brief du 23/09/2026 : un ANCHOR_STATIC fige la cible = le
    départ (voir `_anchor_point`) -- tout `RoleFrame.progress` non nul à
    côté est donc du code mort, exactement le bug qui rendait `support1`
    immobile dans `contre_attaque` (voir `TestContreAttaqueSupport1Carries`).

    Exclusion au niveau du RÔLE, PAS du gabarit (voir brief du 23/09/2026,
    "suite 2" : un frozenset de noms de gabarits sautait le gabarit ENTIER,
    masquant tout futur rôle mort ajouté ailleurs dans ce même gabarit --
    angle mort démontré par modification temporaire + revert, voir
    docs/simulation_physique_archi.md pour la preuve). Les 8 cas trouvés le
    23/09/2026 ont tous été corrigés le jour même : cette liste est donc
    vide -- elle ne le reste que si un futur cas est délibérément laissé
    statique ET documenté comme tel, jamais par défaut."""

    _KNOWN_DEAD_PROGRESS_OFFENDERS: frozenset[tuple[str, str]] = frozenset()
    _EPSILON = 0.01

    def test_no_dead_progress_on_static_anchor(self):
        violations = []
        for name, template in TEMPLATES.items():
            for role in template.roles:
                if (name, role.name) in self._KNOWN_DEAD_PROGRESS_OFFENDERS:
                    continue
                if role.end_anchor != ANCHOR_STATIC:
                    continue
                for frame in role.frames:
                    if frame.progress is not None and frame.progress > self._EPSILON:
                        violations.append(f"{name}.{role.name} @ t_ratio={frame.t_ratio} progress={frame.progress}")

        assert not violations, "progress non nul sur ANCHOR_STATIC (code mort) : " + "; ".join(violations)

    def test_the_known_offenders_list_is_not_stale(self):
        # Contre-vérification : si un (gabarit, rôle) de la liste ne viole
        # plus rien (corrigé sans mettre à jour cette liste), on veut le
        # savoir -- sinon la liste se fige et masque un futur vrai fix.
        # Vide aujourd'hui (voir docstring de classe) -- cette boucle ne
        # s'exécute donc sur rien, elle redevient utile dès qu'une entrée y
        # est réintroduite.
        for name, role_name in self._KNOWN_DEAD_PROGRESS_OFFENDERS:
            template = TEMPLATES[name]
            role = next(r for r in template.roles if r.name == role_name)
            found = (
                role.end_anchor == ANCHOR_STATIC
                and any(f.progress is not None and f.progress > self._EPSILON for f in role.frames)
            )
            assert found, f"{name}.{role_name} est listé comme dette connue mais ne viole plus rien -- retire-le"
