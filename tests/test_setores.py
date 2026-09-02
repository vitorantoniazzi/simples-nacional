"""Ressalvas setoriais."""

from __future__ import annotations

from simples_nacional import RESSALVAS, Anexo, ressalvas_de, setores_registrados


def test_bebidas_alcoolicas_e_monofasica_e_tem_icms_st() -> None:
    (r,) = ressalvas_de("bebidas_alcoolicas")
    assert r.monofasico
    assert r.icms_st
    assert r.anexo_tipico is Anexo.II


def test_bebidas_alcoolicas_exige_mapa_e_producao_propria() -> None:
    (r,) = ressalvas_de("bebidas_alcoolicas")
    condicoes = " ".join(r.condicoes)
    assert "MAPA" in condicoes
    assert "produção própria" in condicoes


def test_setor_desconhecido_devolve_tupla_vazia() -> None:
    assert ressalvas_de("consultoria") == ()


def test_setores_registrados_bate_com_as_ressalvas() -> None:
    assert set(setores_registrados()) == {r.setor for r in RESSALVAS}


def test_todo_setor_registrado_tem_ao_menos_um_regime_especial() -> None:
    # Um setor sem monofásico nem ST não tem por que estar aqui.
    for r in RESSALVAS:
        assert r.monofasico or r.icms_st, r.setor


def test_toda_ressalva_cita_o_fundamento_legal() -> None:
    for r in RESSALVAS:
        assert r.fundamentos, r.setor
        assert any("Lei" in f or "LC" in f or "Resolução" in f for f in r.fundamentos)
