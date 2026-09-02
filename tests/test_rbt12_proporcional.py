"""RBT12 proporcional para empresa com menos de treze meses de atividade."""

from __future__ import annotations

from decimal import Decimal

import pytest

from simples_nacional import rbt12_proporcional


@pytest.mark.parametrize(
    ("acumulada", "meses", "esperado"),
    [
        ("10000", 1, "120000"),  # primeiro mês: receita × 12
        ("90000", 3, "360000"),  # média de 30k × 12
        ("600000", 12, "600000"),  # doze meses: a média já é o próprio RBT12
    ],
)
def test_media_mensal_vezes_doze(acumulada: str, meses: int, esperado: str) -> None:
    assert rbt12_proporcional(Decimal(acumulada), meses) == Decimal(esperado)


def test_zero_meses_e_recusado() -> None:
    with pytest.raises(ValueError, match="pelo menos 1"):
        rbt12_proporcional(Decimal("10000"), 0)


def test_acima_de_doze_meses_e_recusado() -> None:
    # Com treze meses ou mais existe RBT12 real; proporcionalizar seria errado.
    with pytest.raises(ValueError, match="acima de 12"):
        rbt12_proporcional(Decimal("600000"), 13)


def test_receita_negativa_e_recusada() -> None:
    with pytest.raises(ValueError, match="negativa"):
        rbt12_proporcional(Decimal("-1"), 3)
