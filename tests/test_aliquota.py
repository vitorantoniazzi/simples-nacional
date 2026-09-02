"""Alíquota efetiva: fórmula legal, continuidade nas fronteiras e recusas."""

from __future__ import annotations

from decimal import Decimal

import pytest

from simples_nacional import (
    LIMITE_SIMPLES,
    SUBLIMITE_ICMS_ISS,
    TABELAS,
    Anexo,
    aliquota_efetiva,
    das_devido,
)


def efetiva_pela_lei(rbt12: Decimal, nominal: Decimal, deducao: Decimal) -> Decimal:
    """Art. 18, § 1º: (RBT12 × ALIQ − PD) ÷ RBT12, sem arredondar."""
    return (rbt12 * nominal / Decimal("100") - deducao) / rbt12 * Decimal("100")


@pytest.mark.parametrize("anexo", list(Anexo))
def test_no_teto_de_cada_faixa_bate_com_a_formula_legal(anexo: Anexo) -> None:
    for faixa in TABELAS[anexo]:
        r = aliquota_efetiva(faixa.limite_superior, anexo)
        assert r.faixa.numero == faixa.numero
        assert r.aliquota_efetiva == efetiva_pela_lei(
            faixa.limite_superior, faixa.aliquota_nominal, faixa.parcela_deduzir
        )


@pytest.mark.parametrize("anexo", list(Anexo))
def test_efetiva_nunca_passa_da_nominal(anexo: Anexo) -> None:
    # A parcela a deduzir só reduz, nunca aumenta.
    for rbt12 in ("1000", "180000", "500000", "1800000", "3000000", "4800000"):
        r = aliquota_efetiva(Decimal(rbt12), anexo)
        assert r.aliquota_efetiva <= r.aliquota_nominal


@pytest.mark.parametrize("anexo", list(Anexo))
def test_efetiva_cresce_ate_o_sublimite(anexo: Anexo) -> None:
    # Até o sublimite a carga do DAS cresce com o faturamento, sem quedas.
    anterior = Decimal("-1")
    for passo in range(1, 73):  # 50k .. 3,6 mi
        rbt12 = Decimal(50_000) * passo
        assert rbt12 <= SUBLIMITE_ICMS_ISS
        atual = aliquota_efetiva(rbt12, anexo).aliquota_efetiva
        assert atual >= anterior, f"caiu em {rbt12}"
        anterior = atual


@pytest.mark.parametrize("anexo", list(Anexo))
def test_efetiva_cresce_dentro_da_sexta_faixa(anexo: Anexo) -> None:
    # Depois do degrau do sublimite, a curva volta a subir monotonicamente.
    anterior = Decimal("-1")
    for passo in range(73, 97):  # 3,65 mi .. 4,8 mi
        rbt12 = Decimal(50_000) * passo
        assert rbt12 > SUBLIMITE_ICMS_ISS
        atual = aliquota_efetiva(rbt12, anexo).aliquota_efetiva
        assert atual >= anterior, f"caiu em {rbt12}"
        anterior = atual


@pytest.mark.parametrize("anexo", list(Anexo))
def test_fronteiras_ate_a_quinta_faixa_sao_continuas(anexo: Anexo) -> None:
    # As faixas 1 a 5 encaixam sem degrau: no centavo seguinte ao teto, a
    # alíquota efetiva é praticamente a mesma.
    for faixa in TABELAS[anexo][:4]:
        antes = aliquota_efetiva(faixa.limite_superior, anexo).aliquota_efetiva
        depois = aliquota_efetiva(faixa.limite_superior + Decimal("0.01"), anexo).aliquota_efetiva
        assert abs(depois - antes) <= Decimal("0.0001"), f"degrau na faixa {faixa.numero}"


@pytest.mark.parametrize("anexo", list(Anexo))
def test_sublimite_tem_degrau_para_baixo_e_isso_e_a_lei(anexo: Anexo) -> None:
    """No sublimite a efetiva do DAS CAI, e não é erro de tabela.

    Acima de R$ 3.600.000 o ICMS e o ISS deixam de ser recolhidos no DAS, então
    a alíquota da 6ª faixa cobre menos tributos que a da 5ª. A carga total não
    diminui: ela se reparte. Tratar a efetiva como carga total leva à conclusão
    falsa de que faturar mais reduz imposto.

    Este teste existe para que o degrau seja uma propriedade documentada, e
    para que ninguém o "conserte" achando que é bug.
    """
    no_teto = aliquota_efetiva(SUBLIMITE_ICMS_ISS, anexo)
    depois = aliquota_efetiva(SUBLIMITE_ICMS_ISS + Decimal("0.01"), anexo)

    assert depois.aliquota_efetiva < no_teto.aliquota_efetiva
    # E a queda vem acompanhada da sinalização que a explica.
    assert not no_teto.icms_iss_fora_do_das
    assert depois.icms_iss_fora_do_das


@pytest.mark.parametrize("anexo", list(Anexo))
def test_rbt12_zero_cai_na_primeira_faixa(anexo: Anexo) -> None:
    r = aliquota_efetiva(0, anexo)
    assert r.faixa.numero == 1
    assert r.aliquota_efetiva == TABELAS[anexo][0].aliquota_nominal


def test_sinaliza_icms_iss_fora_do_das_acima_do_sublimite() -> None:
    assert not aliquota_efetiva(SUBLIMITE_ICMS_ISS, Anexo.II).icms_iss_fora_do_das
    assert aliquota_efetiva(SUBLIMITE_ICMS_ISS + Decimal("0.01"), Anexo.II).icms_iss_fora_do_das


def test_sinaliza_saida_do_regime_acima_do_limite() -> None:
    assert not aliquota_efetiva(LIMITE_SIMPLES, Anexo.II).acima_do_limite
    r = aliquota_efetiva(LIMITE_SIMPLES + Decimal("0.01"), Anexo.II)
    assert r.acima_do_limite
    assert r.faixa.numero == 6  # última faixa serve de referência


def test_das_devido_aplica_a_efetiva_sobre_a_receita_do_mes() -> None:
    ap = aliquota_efetiva(Decimal("1200000"), Anexo.II)
    # 9,325 exato: um empate, que o dinheiro resolve meio-para-cima.
    assert ap.aliquota_efetiva == Decimal("9.32500")
    assert das_devido(Decimal("100000"), ap) == Decimal("9325.00")


def test_float_e_recusado_em_vez_de_arredondar_em_silencio() -> None:
    with pytest.raises(TypeError, match="float"):
        # float deliberado: e exatamente o que a funcao deve recusar.
        aliquota_efetiva(180000.0, Anexo.II)  # type: ignore[arg-type]


@pytest.mark.parametrize("valor", ["-1", "-0.01"])
def test_rbt12_negativo_e_recusado(valor: str) -> None:
    with pytest.raises(ValueError, match="negativo"):
        aliquota_efetiva(Decimal(valor), Anexo.II)


def test_rbt12_nao_numerico_e_recusado() -> None:
    with pytest.raises(ValueError, match="não é um número"):
        aliquota_efetiva("mil reais", Anexo.II)
