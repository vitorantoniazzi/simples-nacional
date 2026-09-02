"""Cálculo da alíquota efetiva, do Fator R e do RBT12 proporcional."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from .tabelas import (
    FATOR_R_MINIMO,
    LIMITE_SIMPLES,
    SUBLIMITE_ICMS_ISS,
    TABELAS,
    Anexo,
    Faixa,
)

__all__ = [
    "Apuracao",
    "aliquota_efetiva",
    "anexo_por_fator_r",
    "das_devido",
    "fator_r",
    "rbt12_proporcional",
]

_CEM = Decimal("100")


def _para_decimal(valor: Decimal | int | str, nome: str) -> Decimal:
    """Converte para Decimal recusando float, que não é exato para dinheiro."""
    if isinstance(valor, float):
        raise TypeError(
            f"{nome} recebeu float, que não representa dinheiro exatamente. "
            f"Use Decimal, int ou str: Decimal({valor!r})"
        )
    try:
        return Decimal(valor)
    except InvalidOperation as exc:
        raise ValueError(f"{nome} não é um número válido: {valor!r}") from exc


@dataclass(frozen=True, slots=True)
class Apuracao:
    """Resultado de uma apuração de alíquota efetiva."""

    anexo: Anexo
    faixa: Faixa
    rbt12: Decimal
    aliquota_efetiva: Decimal
    """Percentual exato a aplicar sobre a receita do mês, sem arredondamento.

    Mantido exato de propósito: a alíquota é valor intermediário, e arredondá-la
    aqui quebraria a continuidade nas fronteiras de faixa e escolheria por você
    uma política de arredondamento que a lei não impõe à alíquota. Arredonde na
    apresentação (``.quantize(Decimal("0.01"))``); o dinheiro é arredondado em
    :func:`das_devido`.
    """
    acima_do_limite: bool
    """RBT12 acima de R$ 4.800.000: a empresa está fora do Simples Nacional."""
    icms_iss_fora_do_das: bool
    """RBT12 acima do sublimite: ICMS e ISS são apurados fora do DAS."""

    @property
    def aliquota_nominal(self) -> Decimal:
        return self.faixa.aliquota_nominal

    @property
    def parcela_deduzir(self) -> Decimal:
        return self.faixa.parcela_deduzir


def _faixa_de(rbt12: Decimal, anexo: Anexo) -> Faixa:
    faixas = TABELAS[anexo]
    for faixa in faixas:
        if rbt12 <= faixa.limite_superior:
            return faixa
    return faixas[-1]


def aliquota_efetiva(rbt12: Decimal | int | str, anexo: Anexo) -> Apuracao:
    """Alíquota efetiva do Simples Nacional para um RBT12 e um anexo.

    A fórmula é a do art. 18, § 1º da LC 123/2006:

        efetiva = (RBT12 × alíquota_nominal − parcela_a_deduzir) ÷ RBT12

    `rbt12` é a receita bruta acumulada dos doze meses anteriores ao período
    de apuração. Para empresas com menos de treze meses de atividade, use
    :func:`rbt12_proporcional` para obtê-lo.

    Um RBT12 igual a zero cai na primeira faixa, cuja parcela a deduzir é
    zero, de modo que a efetiva iguala a nominal.

    >>> from decimal import Decimal
    >>> from simples_nacional import Anexo, aliquota_efetiva
    >>> r = aliquota_efetiva(Decimal("500000"), Anexo.II)
    >>> r.faixa.numero
    3
    >>> r.aliquota_efetiva
    Decimal('7.22800')
    """
    valor = _para_decimal(rbt12, "rbt12")
    if valor < 0:
        raise ValueError(f"rbt12 não pode ser negativo: {valor}")

    faixa = _faixa_de(valor, anexo)

    if valor == 0:
        efetiva = faixa.aliquota_nominal
    else:
        bruto = (valor * faixa.aliquota_nominal / _CEM) - faixa.parcela_deduzir
        efetiva = bruto / valor * _CEM
        if efetiva < 0:
            efetiva = Decimal("0")

    return Apuracao(
        anexo=anexo,
        faixa=faixa,
        rbt12=valor,
        aliquota_efetiva=efetiva,
        acima_do_limite=valor > LIMITE_SIMPLES,
        icms_iss_fora_do_das=valor > SUBLIMITE_ICMS_ISS,
    )


def das_devido(receita_do_mes: Decimal | int | str, apuracao: Apuracao) -> Decimal:
    """Valor do DAS do mês: receita do mês × alíquota efetiva.

    Arredondado a centavos meio-para-cima, que é a convenção para dinheiro no
    Brasil, e não o meio-para-par que o :mod:`decimal` usa por omissão.

    >>> from decimal import Decimal
    >>> from simples_nacional import Anexo, aliquota_efetiva
    >>> das_devido(Decimal("100000"), aliquota_efetiva(Decimal("1200000"), Anexo.II))
    Decimal('9325.00')
    """
    receita = _para_decimal(receita_do_mes, "receita_do_mes")
    if receita < 0:
        raise ValueError(f"receita_do_mes não pode ser negativa: {receita}")
    bruto = receita * apuracao.aliquota_efetiva / _CEM
    return bruto.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def fator_r(folha_12m: Decimal | int | str, rbt12: Decimal | int | str) -> Decimal:
    """Razão entre folha de salários e receita bruta, ambas em doze meses.

    Definido nos §§ 5º-J e 5º-M do art. 18 da LC 123/2006. Retorna uma razão,
    não um percentual: 0.28 significa 28%.

    Receita zero com folha positiva devolve 1 (100%), porque a razão diverge e
    o enquadramento resultante é o mais favorável, pelo Anexo III. Receita zero
    e folha zero devolve 0.
    """
    folha = _para_decimal(folha_12m, "folha_12m")
    receita = _para_decimal(rbt12, "rbt12")
    if folha < 0:
        raise ValueError(f"folha_12m não pode ser negativa: {folha}")
    if receita < 0:
        raise ValueError(f"rbt12 não pode ser negativo: {receita}")
    if receita == 0:
        return Decimal("1") if folha > 0 else Decimal("0")
    return folha / receita


def anexo_por_fator_r(folha_12m: Decimal | int | str, rbt12: Decimal | int | str) -> Anexo:
    """Anexo aplicável a atividade do § 5º-I, decidido pelo Fator R.

    Fator R de 28% ou mais leva ao Anexo III; abaixo disso, ao Anexo V. O
    limite é inclusivo no Anexo III, conforme a redação do § 5º-M ("igual ou
    superior a 28%").
    """
    return Anexo.III if fator_r(folha_12m, rbt12) >= FATOR_R_MINIMO else Anexo.V


def rbt12_proporcional(receita_acumulada: Decimal | int | str, meses_de_atividade: int) -> Decimal:
    """RBT12 proporcionalizado para empresa com menos de treze meses.

    Regra do art. 18, § 2º da LC 123/2006: nos primeiros doze meses, a receita
    bruta acumulada é convertida em base anual pela média mensal vezes doze.

    >>> from decimal import Decimal
    >>> rbt12_proporcional(Decimal("90000"), 3)
    Decimal('360000')
    """
    receita = _para_decimal(receita_acumulada, "receita_acumulada")
    if receita < 0:
        raise ValueError(f"receita_acumulada não pode ser negativa: {receita}")
    if meses_de_atividade < 1:
        raise ValueError(f"meses_de_atividade deve ser pelo menos 1: {meses_de_atividade}")
    if meses_de_atividade > 12:
        raise ValueError(
            "meses_de_atividade acima de 12 não é proporcionalização: "
            f"use o RBT12 real. Recebido: {meses_de_atividade}"
        )
    return receita / Decimal(meses_de_atividade) * Decimal("12")
