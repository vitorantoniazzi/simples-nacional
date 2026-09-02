"""Fator R: a razão que decide entre Anexo III e Anexo V."""

from __future__ import annotations

from decimal import Decimal

import pytest

from simples_nacional import FATOR_R_MINIMO, Anexo, anexo_por_fator_r, fator_r


def test_razao_e_folha_sobre_receita() -> None:
    assert fator_r(Decimal("28000"), Decimal("100000")) == Decimal("0.28")


def test_limite_de_28_por_cento_e_inclusivo_no_anexo_iii() -> None:
    # § 5º-M fala em "igual ou superior a 28%", então o empate vai ao III.
    assert Decimal("0.28") == FATOR_R_MINIMO
    assert anexo_por_fator_r(Decimal("28000"), Decimal("100000")) is Anexo.III


def test_abaixo_do_limite_vai_ao_anexo_v() -> None:
    assert anexo_por_fator_r(Decimal("27999.99"), Decimal("100000")) is Anexo.V


def test_acima_do_limite_vai_ao_anexo_iii() -> None:
    assert anexo_por_fator_r(Decimal("40000"), Decimal("100000")) is Anexo.III


def test_receita_zero_com_folha_positiva_vai_ao_anexo_iii() -> None:
    # A razão diverge; o enquadramento resultante é o mais favorável.
    assert fator_r(Decimal("1000"), Decimal("0")) == Decimal("1")
    assert anexo_por_fator_r(Decimal("1000"), Decimal("0")) is Anexo.III


def test_receita_e_folha_zero_vao_ao_anexo_v() -> None:
    assert fator_r(Decimal("0"), Decimal("0")) == Decimal("0")
    assert anexo_por_fator_r(Decimal("0"), Decimal("0")) is Anexo.V


@pytest.mark.parametrize(
    ("folha", "receita", "erro"),
    [("-1", "100000", "folha_12m"), ("1000", "-1", "rbt12")],
)
def test_valores_negativos_sao_recusados(folha: str, receita: str, erro: str) -> None:
    with pytest.raises(ValueError, match=erro):
        fator_r(Decimal(folha), Decimal(receita))


def test_float_e_recusado() -> None:
    with pytest.raises(TypeError, match="float"):
        # float deliberado: e exatamente o que a funcao deve recusar.
        fator_r(28000.0, Decimal("100000"))  # type: ignore[arg-type]
