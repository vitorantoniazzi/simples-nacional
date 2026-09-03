"""Repartição do DAS entre os tributos que ele abrange.

Cada anexo tem uma segunda tabela, "Percentual de Repartição dos Tributos",
que diz quanto de cada faixa pertence a cada tributo. Ela é o que permite
responder "quanto do meu DAS é ICMS?" — e, com isso, quantificar segregação de
receita em vez de apenas apontá-la.

Como as tabelas de faixa, isto é a lei transcrita, não valores calculados. Os
percentuais somam exatamente 100% em cada faixa, e o teste verifica isso: uma
transcrição errada quase sempre quebra a soma.

Note a ausência de ICMS e de ISS na 6ª faixa de todos os anexos. Não é falha de
transcrição: a 6ª faixa começa em R$ 3.600.000, acima do sublimite, onde esses
dois tributos deixam de ser recolhidos no DAS. É a explicação estrutural da
queda da alíquota efetiva ao cruzar essa linha.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from typing import TYPE_CHECKING

from .tabelas import Anexo, Tributo

if TYPE_CHECKING:
    from .core import Apuracao

__all__ = [
    "ISS_TETO_EFETIVO_PCT",
    "REPARTICAO",
    "Tributo",
    "das_por_tributo",
    "reparticao_da_faixa",
]

_CEM = Decimal("100")


# Teto do percentual efetivo devido ao ISS nos Anexos III e V. Acima dele, a
# diferença é transferida proporcionalmente aos tributos federais.
ISS_TETO_EFETIVO_PCT = Decimal("5")

T = Tributo


def _linhas(
    tributos: tuple[Tributo, ...], faixas: list[tuple[str, ...]]
) -> tuple[dict[Tributo, Decimal], ...]:
    saida = []
    for valores in faixas:
        assert len(valores) == len(tributos)
        saida.append({t: Decimal(v) for t, v in zip(tributos, valores, strict=True) if v != "-"})
    return tuple(saida)


# Anexos I a V da LC 123/2006, redação da LC 155/2016, tabela de repartição.
REPARTICAO: dict[Anexo, tuple[dict[Tributo, Decimal], ...]] = {
    Anexo.I: _linhas(
        (T.IRPJ, T.CSLL, T.COFINS, T.PIS, T.CPP, T.ICMS),
        [
            ("5.50", "3.50", "12.74", "2.76", "41.50", "34.00"),
            ("5.50", "3.50", "12.74", "2.76", "41.50", "34.00"),
            ("5.50", "3.50", "12.74", "2.76", "42.00", "33.50"),
            ("5.50", "3.50", "12.74", "2.76", "42.00", "33.50"),
            ("5.50", "3.50", "12.74", "2.76", "42.00", "33.50"),
            ("13.50", "10.00", "28.27", "6.13", "42.10", "-"),
        ],
    ),
    Anexo.II: _linhas(
        (T.IRPJ, T.CSLL, T.COFINS, T.PIS, T.CPP, T.IPI, T.ICMS),
        [
            ("5.50", "3.50", "11.51", "2.49", "37.50", "7.50", "32.00"),
            ("5.50", "3.50", "11.51", "2.49", "37.50", "7.50", "32.00"),
            ("5.50", "3.50", "11.51", "2.49", "37.50", "7.50", "32.00"),
            ("5.50", "3.50", "11.51", "2.49", "37.50", "7.50", "32.00"),
            ("5.50", "3.50", "11.51", "2.49", "37.50", "7.50", "32.00"),
            ("8.50", "7.50", "20.96", "4.54", "23.50", "35.00", "-"),
        ],
    ),
    Anexo.III: _linhas(
        (T.IRPJ, T.CSLL, T.COFINS, T.PIS, T.CPP, T.ISS),
        [
            ("4.00", "3.50", "12.82", "2.78", "43.40", "33.50"),
            ("4.00", "3.50", "14.05", "3.05", "43.40", "32.00"),
            ("4.00", "3.50", "13.64", "2.96", "43.40", "32.50"),
            ("4.00", "3.50", "13.64", "2.96", "43.40", "32.50"),
            ("4.00", "3.50", "12.82", "2.78", "43.40", "33.50"),
            ("35.00", "15.00", "16.03", "3.47", "30.50", "-"),
        ],
    ),
    Anexo.IV: _linhas(
        (T.IRPJ, T.CSLL, T.COFINS, T.PIS, T.ISS),
        [
            ("18.80", "15.20", "17.67", "3.83", "44.50"),
            ("19.80", "15.20", "20.55", "4.45", "40.00"),
            ("20.80", "15.20", "19.73", "4.27", "40.00"),
            ("17.80", "19.20", "18.90", "4.10", "40.00"),
            ("18.80", "19.20", "18.08", "3.92", "40.00"),
            ("53.50", "21.50", "20.55", "4.45", "-"),
        ],
    ),
    Anexo.V: _linhas(
        (T.IRPJ, T.CSLL, T.COFINS, T.PIS, T.CPP, T.ISS),
        [
            ("25.00", "15.00", "14.10", "3.05", "28.85", "14.00"),
            ("23.00", "15.00", "14.10", "3.05", "27.85", "17.00"),
            ("24.00", "15.00", "14.92", "3.23", "23.85", "19.00"),
            ("21.00", "15.00", "15.74", "3.41", "23.85", "21.00"),
            ("23.00", "12.50", "14.10", "3.05", "23.85", "23.50"),
            ("35.00", "15.50", "16.44", "3.56", "29.50", "-"),
        ],
    ),
}


def reparticao_da_faixa(anexo: Anexo, faixa: int) -> dict[Tributo, Decimal]:
    """Percentuais de repartição de uma faixa, por tributo.

    Os valores somam 100% e representam a fatia de cada tributo dentro do DAS,
    não alíquotas sobre a receita.

    >>> from simples_nacional import Anexo, Tributo, reparticao_da_faixa
    >>> reparticao_da_faixa(Anexo.II, 4)[Tributo.ICMS]
    Decimal('32.00')
    >>> Tributo.ICMS in reparticao_da_faixa(Anexo.II, 6)
    False
    """
    if not 1 <= faixa <= 6:
        raise ValueError(f"faixa deve estar entre 1 e 6: {faixa}")
    return dict(REPARTICAO[anexo][faixa - 1])


def das_por_tributo(
    receita_do_mes: Decimal | int | str,
    apuracao: Apuracao,
) -> dict[Tributo, Decimal]:
    """Divide o DAS do mês entre os tributos que ele abrange.

    É esta divisão que permite quantificar segregação de receita: para uma
    operação monofásica, é a soma das parcelas de PIS e COFINS que sai do DAS;
    para uma com ICMS-ST, a parcela do ICMS.

    Cada parcela é arredondada a centavos, então a soma delas pode divergir do
    valor devolvido por :func:`~simples_nacional.das_devido` em alguns centavos.
    A deriva é limitada a meio centavo por tributo, e o total a recolher é o de
    ``das_devido``, não esta soma. Use estas parcelas para atribuição e
    relatório, não para apurar a guia.

    >>> from decimal import Decimal
    >>> from simples_nacional import Anexo, aliquota_efetiva, das_devido, das_por_tributo
    >>> ap = aliquota_efetiva(Decimal("1200000"), Anexo.II)
    >>> partes = das_por_tributo(Decimal("100000"), ap)
    >>> partes[Tributo.ICMS]
    Decimal('2984.00')
    >>> das_devido(Decimal("100000"), ap)
    Decimal('9325.00')
    >>> sum(partes.values()) - das_devido(Decimal("100000"), ap)
    Decimal('0.02')
    """
    from .core import das_devido

    total = das_devido(receita_do_mes, apuracao)
    pesos = reparticao_da_faixa(apuracao.anexo, apuracao.faixa.numero)
    return {
        tributo: (total * peso / _CEM).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        for tributo, peso in pesos.items()
    }
