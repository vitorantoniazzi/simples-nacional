"""Ressalvas setoriais."""

from __future__ import annotations

from simples_nacional import RESSALVAS, Anexo, ressalvas_de


def test_bebidas_alcoolicas_esta_registrada_no_anexo_ii() -> None:
    (r,) = ressalvas_de("bebidas_alcoolicas")
    assert r.anexo is Anexo.II


def test_bebidas_alcoolicas_aponta_icms_st_e_ipi_fora_do_das() -> None:
    (r,) = ressalvas_de("bebidas_alcoolicas")
    assert set(r.tributos_fora_do_das) == {"ICMS-ST", "IPI"}


def test_bebidas_alcoolicas_exige_mapa_e_producao_propria() -> None:
    (r,) = ressalvas_de("bebidas_alcoolicas")
    condicoes = " ".join(r.condicoes)
    assert "MAPA" in condicoes
    assert "produção própria" in condicoes


def test_setor_desconhecido_devolve_tupla_vazia() -> None:
    assert ressalvas_de("comercio_varejista") == ()


def test_toda_ressalva_cita_o_fundamento_legal() -> None:
    # Uma ressalva sem norma que a sustente é opinião, não referência.
    for r in RESSALVAS:
        assert r.fundamentos, f"{r.setor} não cita fundamento"
        assert any("LC" in f for f in r.fundamentos)
