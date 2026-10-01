"""engine/minhash.py : signature MinHash via hashlib, deterministe."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from engine import minhash

TEXTE = "Kylian Mbappé efface le gardien d'un crochet et pousse tranquillement le ballon au fond des filets !"


def _jaccard_exact(a: str, b: str) -> float:
    sa, sb = minhash.shingles(a), minhash.shingles(b)
    return len(sa & sb) / len(sa | sb)


class TestShingles:
    def test_trois_mots_consecutifs_en_minuscules_sans_ponctuation(self):
        assert minhash.shingles("Quel but, mes amis !") == {"quel but mes", "but mes amis"}

    def test_les_apostrophes_separent_les_mots(self):
        assert "l ailier file" in minhash.shingles("L'ailier file")

    def test_moins_de_trois_mots_donne_un_seul_shingle(self):
        assert minhash.shingles("Quel but") == {"quel but"}

    def test_texte_sans_mot_donne_aucun_shingle(self):
        assert minhash.shingles("  !!! ... ") == frozenset()

    def test_forme_composee_et_decomposee_sont_equivalentes(self):
        assert minhash.shingles("Mbappé marque un but") == minhash.shingles("Mbappé marque un but")


class TestSignature:
    def test_formule_exacte_sha256_par_permutation(self):
        sig = minhash.signature("un deux trois quatre", permutations=4)
        attendu = tuple(
            min(
                int.from_bytes(hashlib.sha256(f"{i}|{s}".encode()).digest()[:8], "big")
                for s in ("un deux trois", "deux trois quatre")
            )
            for i in range(4)
        )
        assert sig == attendu

    def test_longueur_par_defaut_et_determinisme(self):
        assert len(minhash.signature(TEXTE)) == minhash.NB_PERMUTATIONS == 64
        assert minhash.signature(TEXTE) == minhash.signature(TEXTE)

    def test_un_texte_vide_a_une_signature_constante(self):
        assert set(minhash.signature("")) == {2**64 - 1}
        assert minhash.similarite(minhash.signature(""), minhash.signature("...")) == 1.0

    def test_signature_identique_quelle_que_soit_la_graine_de_hachage_de_python(self):
        """sha256, pas hash() : PYTHONHASHSEED ne doit rien changer."""
        code = (
            "import json; from engine.minhash import signature;"
            f"print(json.dumps(signature({TEXTE!r})))"
        )
        sorties = set()
        for graine in ("1", "2", "random"):
            resultat = subprocess.run(
                [sys.executable, "-c", code],
                capture_output=True,
                text=True,
                check=True,
                env={**os.environ, "PYTHONHASHSEED": graine, "PYTHONIOENCODING": "utf-8"},
                cwd=str(Path(__file__).resolve().parent.parent),
            )
            sorties.add(resultat.stdout.strip())
        assert len(sorties) == 1
        assert json.loads(sorties.pop()) == list(minhash.signature(TEXTE))


class TestSimilarite:
    def test_identique_donne_1_et_disjoint_donne_presque_0(self):
        autre = "Le gardien repousse du bout des doigts une frappe lointaine puis capte le rebond sans trembler."
        assert minhash.similarite(minhash.signature(TEXTE), minhash.signature(TEXTE)) == 1.0
        assert minhash.similarite(minhash.signature(TEXTE), minhash.signature(autre)) < 0.1

    def test_insensible_a_la_casse_et_a_la_ponctuation(self):
        assert minhash.similarite(minhash.signature(TEXTE), minhash.signature(TEXTE.upper().replace("!", "."))) == 1.0

    def test_estime_la_similarite_de_jaccard_exacte(self):
        voisin = TEXTE.replace("tranquillement", "calmement")
        estimation = minhash.similarite(minhash.signature(TEXTE), minhash.signature(voisin))
        assert abs(estimation - _jaccard_exact(TEXTE, voisin)) < 0.2

    def test_longueurs_differentes_ou_signatures_vides_sont_refusees(self):
        with pytest.raises(ValueError, match="incomparables"):
            minhash.similarite((1, 2), (1,))
        with pytest.raises(ValueError, match="incomparables"):
            minhash.similarite((), ())


def test_serialisation_aller_retour():
    sig = minhash.signature(TEXTE)
    assert minhash.deserialiser(minhash.serialiser(sig)) == sig
