"""O que fica fora do DAS, e em que direção."""

from __future__ import annotations

from decimal import Decimal

import pytest

from simples_nacional import (
    TRIBUTOS_NO_DAS,
    Anexo,
    Efeito,
    PosicaoNaCadeia,
    aliquota_efetiva,
    carga_fora_do_das,
)


def test_somente_o_anexo_iv_deixa_a_cpp_fora_do_das() -> None:
    for anexo in Anexo:
        tem_cpp = "CPP" in TRIBUTOS_NO_DAS[anexo]
        assert tem_cpp is (anexo is not Anexo.IV), anexo


def test_anexo_ii_e_o_unico_com_ipi_no_das() -> None:
    # Só a indústria recolhe IPI, e ela o recolhe dentro do DAS.
    for anexo in Anexo:
        assert ("IPI" in TRIBUTOS_NO_DAS[anexo]) is (anexo is Anexo.II), anexo


@pytest.mark.parametrize("anexo", [Anexo.I, Anexo.II, Anexo.III, Anexo.V])
def test_sem_segregacao_nada_fica_fora_exceto_no_anexo_iv(anexo: Anexo) -> None:
    assert carga_fora_do_das(anexo) == ()


def test_anexo_iv_acrescenta_cpp_sobre_a_folha() -> None:
    (item,) = carga_fora_do_das(Anexo.IV)
    assert item.tributo == "CPP"
    assert item.efeito is Efeito.ACRESCENTA
    assert "folha" in item.base
    assert any("5º-C" in f for f in item.fundamentos)


def test_o_degrau_do_anexo_iv_e_a_armadilha_da_comparacao() -> None:
    """Anexo IV parece mais barato que o III, e não é."""
    rbt12 = Decimal("1000000")
    iv = aliquota_efetiva(rbt12, Anexo.IV).aliquota_efetiva
    iii = aliquota_efetiva(rbt12, Anexo.III).aliquota_efetiva
    assert iv < iii  # pela alíquota, o IV engana
    assert carga_fora_do_das(Anexo.IV)  # mas tem CPP por fora
    assert carga_fora_do_das(Anexo.III) == ()  # e o III não tem


def test_monofasico_reduz_para_quem_revende() -> None:
    (item,) = carga_fora_do_das(
        Anexo.I, receita_monofasica=True, posicao=PosicaoNaCadeia.REVENDEDOR
    )
    assert item.efeito is Efeito.REDUZ
    assert "recuperável" in item.motivo


def test_monofasico_acrescenta_para_quem_produz() -> None:
    (item,) = carga_fora_do_das(Anexo.II, receita_monofasica=True, posicao=PosicaoNaCadeia.PRODUTOR)
    assert item.efeito is Efeito.ACRESCENTA


def test_a_posicao_na_cadeia_inverte_o_efeito() -> None:
    # O mesmo produto, lados opostos da cadeia, direções opostas.
    revenda = carga_fora_do_das(
        Anexo.I,
        receita_monofasica=True,
        receita_com_icms_st=True,
        posicao=PosicaoNaCadeia.REVENDEDOR,
    )
    producao = carga_fora_do_das(
        Anexo.II,
        receita_monofasica=True,
        receita_com_icms_st=True,
        posicao=PosicaoNaCadeia.PRODUTOR,
    )
    assert {i.efeito for i in revenda} == {Efeito.REDUZ}
    assert {i.efeito for i in producao} == {Efeito.ACRESCENTA}


def test_anexo_iv_com_segregacao_acumula_os_dois_motivos() -> None:
    itens = carga_fora_do_das(Anexo.IV, receita_monofasica=True, posicao=PosicaoNaCadeia.REVENDEDOR)
    assert [i.tributo for i in itens] == ["CPP", "PIS/COFINS (monofásico)"]
    # Um acrescenta e o outro reduz: por isso não se soma isso num número só.
    assert {i.efeito for i in itens} == {Efeito.ACRESCENTA, Efeito.REDUZ}


def test_todo_item_cita_fundamento_legal() -> None:
    for anexo in Anexo:
        for pos in PosicaoNaCadeia:
            for item in carga_fora_do_das(
                anexo, receita_monofasica=True, receita_com_icms_st=True, posicao=pos
            ):
                assert item.fundamentos, item.tributo
