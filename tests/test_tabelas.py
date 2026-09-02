"""As tabelas são lei, então o teste não verifica "o que o código faz".

A tabela abaixo é uma transcrição independente dos Anexos I a V da LC
123/2006 (redação da LC 155/2016). Se ela e o pacote divergirem, um dos dois
está errado — e é isso que se quer descobrir.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from simples_nacional import LIMITE_SIMPLES, SUBLIMITE_ICMS_ISS, TABELAS, Anexo

# (limite superior, alíquota nominal %, parcela a deduzir R$)
LEI: dict[str, list[tuple[str, str, str]]] = {
    "I": [
        ("180000.00", "4.00", "0.00"),
        ("360000.00", "7.30", "5940.00"),
        ("720000.00", "9.50", "13860.00"),
        ("1800000.00", "10.70", "22500.00"),
        ("3600000.00", "14.30", "87300.00"),
        ("4800000.00", "19.00", "378000.00"),
    ],
    "II": [
        ("180000.00", "4.50", "0.00"),
        ("360000.00", "7.80", "5940.00"),
        ("720000.00", "10.00", "13860.00"),
        ("1800000.00", "11.20", "22500.00"),
        ("3600000.00", "14.70", "85500.00"),
        ("4800000.00", "30.00", "720000.00"),
    ],
    "III": [
        ("180000.00", "6.00", "0.00"),
        ("360000.00", "11.20", "9360.00"),
        ("720000.00", "13.50", "17640.00"),
        ("1800000.00", "16.00", "35640.00"),
        ("3600000.00", "21.00", "125640.00"),
        ("4800000.00", "33.00", "648000.00"),
    ],
    "IV": [
        ("180000.00", "4.50", "0.00"),
        ("360000.00", "9.00", "8100.00"),
        ("720000.00", "10.20", "12420.00"),
        ("1800000.00", "14.00", "39780.00"),
        ("3600000.00", "22.00", "183780.00"),
        ("4800000.00", "33.00", "828000.00"),
    ],
    "V": [
        ("180000.00", "15.50", "0.00"),
        ("360000.00", "18.00", "4500.00"),
        ("720000.00", "19.50", "9900.00"),
        ("1800000.00", "20.50", "17100.00"),
        ("3600000.00", "23.00", "62100.00"),
        ("4800000.00", "30.50", "540000.00"),
    ],
}


@pytest.mark.parametrize("anexo", list(Anexo))
def test_anexo_tem_seis_faixas(anexo: Anexo) -> None:
    assert len(TABELAS[anexo]) == 6


@pytest.mark.parametrize(
    ("anexo", "indice", "esperado"),
    [(a, i, linha) for a in Anexo for i, linha in enumerate(LEI[a.value])],
)
def test_faixa_bate_com_a_lei(anexo: Anexo, indice: int, esperado: tuple[str, str, str]) -> None:
    limite, nominal, deducao = esperado
    faixa = TABELAS[anexo][indice]
    assert faixa.numero == indice + 1
    assert faixa.limite_superior == Decimal(limite)
    assert faixa.aliquota_nominal == Decimal(nominal)
    assert faixa.parcela_deduzir == Decimal(deducao)


@pytest.mark.parametrize("anexo", list(Anexo))
def test_limites_sao_crescentes(anexo: Anexo) -> None:
    limites = [f.limite_superior for f in TABELAS[anexo]]
    assert limites == sorted(limites)
    assert len(set(limites)) == len(limites)


@pytest.mark.parametrize("anexo", list(Anexo))
def test_primeira_faixa_nao_tem_deducao(anexo: Anexo) -> None:
    # Sem dedução na primeira faixa, a efetiva iguala a nominal.
    assert TABELAS[anexo][0].parcela_deduzir == Decimal("0")


@pytest.mark.parametrize("anexo", list(Anexo))
def test_ultimo_limite_e_o_limite_do_regime(anexo: Anexo) -> None:
    assert TABELAS[anexo][-1].limite_superior == LIMITE_SIMPLES


@pytest.mark.parametrize("anexo", list(Anexo))
def test_sublimite_e_limite_da_quinta_faixa(anexo: Anexo) -> None:
    # ICMS e ISS saem do DAS exatamente onde termina a 5ª faixa.
    assert TABELAS[anexo][4].limite_superior == SUBLIMITE_ICMS_ISS


def test_faixas_sao_iguais_entre_anexos() -> None:
    # Os anexos diferem em alíquota e dedução, nunca nos limites de faixa.
    por_anexo = {a: [f.limite_superior for f in TABELAS[a]] for a in Anexo}
    assert len(set(map(tuple, por_anexo.values()))) == 1
