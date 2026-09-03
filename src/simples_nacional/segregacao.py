"""Segregação de receitas e o indébito de quem não segrega.

Receita de operação monofásica de PIS/COFINS ou com ICMS já retido por
substituição tributária deve ser segregada: no cálculo do DAS, os percentuais
dos tributos já cobrados na cadeia são desconsiderados. Quem revende e não
segrega paga a mais, e o excesso é indébito.

O módulo calcula esse excesso, por competência e acumulado, e separa o que
ainda está dentro do prazo prescricional do que já prescreveu.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from .core import aliquota_efetiva
from .reparticao import reparticao_da_faixa
from .tabelas import Anexo, Tributo

__all__ = [
    "ANOS_DE_PRESCRICAO",
    "Competencia",
    "Indebito",
    "IndebitoDaCompetencia",
    "das_com_segregacao",
    "indebito_por_segregacao",
    "percentual_segregavel",
]

_CEM = Decimal("100")
_CENTAVO = Decimal("0.01")

# CTN, art. 168, com a contagem do art. 3º da LC 118/2005.
ANOS_DE_PRESCRICAO = 5

# O DAS de uma competência vence no dia 20 do mês seguinte.
DIA_DE_VENCIMENTO = 20


def _centavos(valor: Decimal) -> Decimal:
    return valor.quantize(_CENTAVO, rounding=ROUND_HALF_UP)


def percentual_segregavel(
    anexo: Anexo,
    faixa: int,
    *,
    monofasica: bool = False,
    com_icms_st: bool = False,
) -> Decimal:
    """Percentual da alíquota que é desconsiderado ao segregar a receita.

    Soma as fatias dos tributos já cobrados na cadeia: PIS e COFINS para
    operação monofásica, ICMS para operação com substituição tributária.

    Devolve zero quando o tributo não integra a faixa — o que acontece com o
    ICMS acima do sublimite, onde segregar ICMS-ST não altera nada.

    >>> from simples_nacional import Anexo, percentual_segregavel
    >>> percentual_segregavel(Anexo.I, 4, monofasica=True, com_icms_st=True)
    Decimal('49.00')
    >>> percentual_segregavel(Anexo.I, 6, com_icms_st=True)
    Decimal('0')
    """
    pesos = reparticao_da_faixa(anexo, faixa)
    zero = Decimal("0")
    total = zero
    if monofasica:
        total += pesos.get(Tributo.PIS, zero) + pesos.get(Tributo.COFINS, zero)
    if com_icms_st:
        total += pesos.get(Tributo.ICMS, zero)
    return total


def das_com_segregacao(
    receita: Decimal | int | str,
    anexo: Anexo,
    rbt12: Decimal | int | str,
    *,
    monofasica: bool = False,
    com_icms_st: bool = False,
) -> Decimal:
    """DAS de uma parcela de receita, com a segregação aplicada.

    >>> from decimal import Decimal
    >>> from simples_nacional import Anexo, das_com_segregacao
    >>> das_com_segregacao(Decimal("60000"), Anexo.I, Decimal("900000"),
    ...                    monofasica=True, com_icms_st=True)
    Decimal('2509.20')
    """
    ap = aliquota_efetiva(rbt12, anexo)
    fora = percentual_segregavel(
        anexo, ap.faixa.numero, monofasica=monofasica, com_icms_st=com_icms_st
    )
    valor = Decimal(str(receita)) if not isinstance(receita, Decimal) else receita
    if valor < 0:
        raise ValueError(f"receita não pode ser negativa: {valor}")
    return _centavos(valor * ap.aliquota_efetiva / _CEM * (_CEM - fora) / _CEM)


@dataclass(frozen=True, slots=True)
class Competencia:
    """Uma competência mensal, com a receita repartida por regime."""

    ano: int
    mes: int
    rbt12: Decimal
    receita_sem_regime_especial: Decimal = Decimal("0")
    receita_monofasica: Decimal = Decimal("0")
    receita_com_icms_st: Decimal = Decimal("0")
    receita_monofasica_e_com_icms_st: Decimal = Decimal("0")

    def __post_init__(self) -> None:
        if not 1 <= self.mes <= 12:
            raise ValueError(f"mês inválido: {self.mes}")

    @property
    def vencimento(self) -> date:
        """Dia 20 do mês seguinte, quando o DAS da competência vence."""
        ano, mes = (self.ano + 1, 1) if self.mes == 12 else (self.ano, self.mes + 1)
        return date(ano, mes, DIA_DE_VENCIMENTO)

    @property
    def receita_total(self) -> Decimal:
        return (
            self.receita_sem_regime_especial
            + self.receita_monofasica
            + self.receita_com_icms_st
            + self.receita_monofasica_e_com_icms_st
        )


@dataclass(frozen=True, slots=True)
class IndebitoDaCompetencia:
    """Quanto uma competência pagou a mais por não segregar."""

    competencia: Competencia
    faixa: int
    das_sem_segregar: Decimal
    das_segregado: Decimal
    prescrito: bool

    @property
    def indebito(self) -> Decimal:
        return self.das_sem_segregar - self.das_segregado


@dataclass(frozen=True, slots=True)
class Indebito:
    """Indébito acumulado, separado pelo prazo prescricional."""

    competencias: tuple[IndebitoDaCompetencia, ...] = field(default_factory=tuple)
    data_de_corte: date = date.min
    """Vencimentos anteriores a esta data estão prescritos."""

    @property
    def recuperavel(self) -> Decimal:
        return sum((c.indebito for c in self.competencias if not c.prescrito), Decimal("0"))

    @property
    def prescrito(self) -> Decimal:
        return sum((c.indebito for c in self.competencias if c.prescrito), Decimal("0"))

    @property
    def total(self) -> Decimal:
        return self.recuperavel + self.prescrito


def indebito_por_segregacao(
    competencias: list[Competencia],
    anexo: Anexo,
    *,
    hoje: date | None = None,
) -> Indebito:
    """Indébito de quem revendeu sem segregar, competência a competência.

    O prazo do art. 168 do CTN é de cinco anos contados do pagamento indevido.
    Aqui a contagem usa o vencimento do DAS — dia 20 do mês seguinte — como
    referência, porque é a data que se conhece a partir da competência. Quem
    pagou em atraso tem prazo contado da data efetiva do pagamento, que só o
    contribuinte conhece.

    Um pedido administrativo não interrompe o prazo (Súmula 625 do STJ), então
    a data de corte não se move por ter havido protocolo.

    >>> from datetime import date
    >>> from decimal import Decimal
    >>> from simples_nacional import Anexo, Competencia, indebito_por_segregacao
    >>> c = Competencia(2026, 1, Decimal("900000"),
    ...                 receita_monofasica_e_com_icms_st=Decimal("60000"))
    >>> r = indebito_por_segregacao([c], Anexo.I, hoje=date(2026, 9, 3))
    >>> r.recuperavel
    Decimal('2410.80')
    >>> r.prescrito
    Decimal('0')
    """
    referencia = hoje or date.today()
    corte = date(referencia.year - ANOS_DE_PRESCRICAO, referencia.month, referencia.day)

    linhas = []
    for c in competencias:
        ap = aliquota_efetiva(c.rbt12, anexo)
        sem = _centavos(c.receita_total * ap.aliquota_efetiva / _CEM)
        com = (
            das_com_segregacao(c.receita_sem_regime_especial, anexo, c.rbt12)
            + das_com_segregacao(c.receita_monofasica, anexo, c.rbt12, monofasica=True)
            + das_com_segregacao(c.receita_com_icms_st, anexo, c.rbt12, com_icms_st=True)
            + das_com_segregacao(
                c.receita_monofasica_e_com_icms_st,
                anexo,
                c.rbt12,
                monofasica=True,
                com_icms_st=True,
            )
        )
        linhas.append(
            IndebitoDaCompetencia(
                competencia=c,
                faixa=ap.faixa.numero,
                das_sem_segregar=sem,
                das_segregado=com,
                prescrito=c.vencimento < corte,
            )
        )

    return Indebito(competencias=tuple(linhas), data_de_corte=corte)
