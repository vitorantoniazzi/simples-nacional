"""Carga total por anexo, e não apenas a alíquota do DAS.

Comparar anexos pela alíquota efetiva engana em um caso concreto: o DAS do
Anexo IV não abrange a contribuição previdenciária patronal, que é recolhida à
parte sobre a folha. Pela alíquota o Anexo IV parece mais barato que o Anexo
III; somada a CPP, frequentemente não é.

Este módulo quantifica a diferença.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import TYPE_CHECKING

from .carga import TRIBUTOS_NO_DAS
from .core import aliquota_efetiva, das_devido
from .tabelas import Anexo, Tributo

if TYPE_CHECKING:
    from .presumido import AtividadePresumido

__all__ = [
    "CPP_ALIQUOTA_PCT",
    "FAP_MAXIMO",
    "FAP_MINIMO",
    "RAT_MAXIMO_PCT",
    "RAT_MINIMO_PCT",
    "CargaDoAnexo",
    "ComparacaoDeRegimes",
    "comparar_anexos",
    "comparar_regimes",
    "cpp_fora_do_das",
]

_CEM = Decimal("100")
_CENTAVO = Decimal("0.01")

# Contribuição patronal sobre a folha, devida à parte no Anexo IV.
CPP_ALIQUOTA_PCT = Decimal("20")

# RAT conforme o grau de risco da atividade, ajustável pelo FAP.
RAT_MINIMO_PCT = Decimal("1")
RAT_MAXIMO_PCT = Decimal("3")
FAP_MINIMO = Decimal("0.5")
FAP_MAXIMO = Decimal("2.0")


def cpp_fora_do_das(
    folha: Decimal | int | str,
    *,
    rat_pct: Decimal | int | str = RAT_MINIMO_PCT,
    fap: Decimal | int | str = Decimal("1"),
) -> Decimal:
    """Contribuição patronal devida à parte, sobre a folha.

    São 20% mais o RAT do grau de risco da atividade, este último multiplicado
    pelo FAP. A folha inclui o pró-labore dos sócios.

    Só se aplica ao Anexo IV: nos outros anexos a CPP está dentro do DAS.

    >>> from decimal import Decimal
    >>> from simples_nacional import cpp_fora_do_das
    >>> cpp_fora_do_das(Decimal("50000"))
    Decimal('10500.00')
    >>> cpp_fora_do_das(Decimal("50000"), rat_pct=3, fap="1.5")
    Decimal('12250.00')
    """
    valor = Decimal(str(folha))
    rat = Decimal(str(rat_pct))
    f = Decimal(str(fap))
    if valor < 0:
        raise ValueError(f"folha não pode ser negativa: {valor}")
    if not RAT_MINIMO_PCT <= rat <= RAT_MAXIMO_PCT:
        raise ValueError(f"rat_pct deve estar entre {RAT_MINIMO_PCT} e {RAT_MAXIMO_PCT}: {rat}")
    if not FAP_MINIMO <= f <= FAP_MAXIMO:
        raise ValueError(f"fap deve estar entre {FAP_MINIMO} e {FAP_MAXIMO}: {f}")
    total_pct = CPP_ALIQUOTA_PCT + rat * f
    return (valor * total_pct / _CEM).quantize(_CENTAVO, rounding=ROUND_HALF_UP)


@dataclass(frozen=True, slots=True)
class CargaDoAnexo:
    """Carga de um anexo para uma receita e uma folha."""

    anexo: Anexo
    faixa: int
    aliquota_efetiva_pct: Decimal
    das: Decimal
    cpp_fora_do_das: Decimal
    """Zero em todos os anexos menos o IV."""

    @property
    def carga_total(self) -> Decimal:
        return self.das + self.cpp_fora_do_das

    def carga_pct_da_receita(self, receita: Decimal) -> Decimal:
        """Carga total como percentual da receita, que é o número comparável."""
        if receita == 0:
            return Decimal("0")
        return (self.carga_total / receita * _CEM).quantize(_CENTAVO)


def comparar_anexos(
    rbt12: Decimal | int | str,
    receita_do_mes: Decimal | int | str,
    *,
    folha: Decimal | int | str = 0,
    rat_pct: Decimal | int | str = RAT_MINIMO_PCT,
    fap: Decimal | int | str = Decimal("1"),
) -> tuple[CargaDoAnexo, ...]:
    """Os cinco anexos lado a lado, por carga total e não por alíquota.

    A folha só altera o Anexo IV, único em que a contribuição patronal fica
    fora do DAS. Sem informar folha, a comparação reproduz a ilusão de que o
    Anexo IV é o mais barato.

    >>> from decimal import Decimal
    >>> from simples_nacional import Anexo, comparar_anexos
    >>> linhas = {c.anexo: c for c in comparar_anexos(
    ...     Decimal("1000000"), Decimal("80000"), folha=Decimal("30000"))}
    >>> linhas[Anexo.IV].das < linhas[Anexo.III].das   # pela alíquota, o IV engana
    True
    >>> linhas[Anexo.IV].carga_total > linhas[Anexo.III].carga_total
    True
    """
    saida = []
    for anexo in Anexo:
        ap = aliquota_efetiva(rbt12, anexo)
        cpp = (
            cpp_fora_do_das(folha, rat_pct=rat_pct, fap=fap)
            if Tributo.CPP not in TRIBUTOS_NO_DAS[anexo]
            else Decimal("0.00")
        )
        saida.append(
            CargaDoAnexo(
                anexo=anexo,
                faixa=ap.faixa.numero,
                aliquota_efetiva_pct=ap.aliquota_arredondada,
                das=das_devido(receita_do_mes, ap),
                cpp_fora_do_das=cpp,
            )
        )
    return tuple(saida)


@dataclass(frozen=True, slots=True)
class ComparacaoDeRegimes:
    """Simples Nacional contra Lucro Presumido, no mesmo trimestre."""

    receita_trimestral: Decimal
    das_do_trimestre: Decimal
    cpp_no_simples: Decimal
    """Zero fora do Anexo IV, onde a patronal está dentro do DAS."""
    total_simples: Decimal
    total_presumido: Decimal
    iss_arbitrado: bool
    acima_do_limite_lc224: bool

    @property
    def diferenca(self) -> Decimal:
        """Positiva quando o Simples sai mais barato."""
        return self.total_presumido - self.total_simples

    @property
    def regime_mais_barato(self) -> str:
        if self.total_simples < self.total_presumido:
            return "simples"
        if self.total_presumido < self.total_simples:
            return "presumido"
        return "empate"

    @property
    def comparavel(self) -> bool:
        """False quando falta dado para que a comparação signifique algo.

        Sem alíquota de ISS, o Lucro Presumido de uma prestadora sai sem ISS e
        parece mais barato do que é. Acima do limite da LC 224/2025, a
        majoração não modelada o subestima do mesmo modo.
        """
        return self.iss_arbitrado and not self.acima_do_limite_lc224


def comparar_regimes(
    receita_trimestral: Decimal | int | str,
    anexo: Anexo,
    rbt12: Decimal | int | str,
    atividade: AtividadePresumido,
    *,
    folha_trimestral: Decimal | int | str = 0,
    rat_pct: Decimal | int | str = RAT_MINIMO_PCT,
    fap: Decimal | int | str = Decimal("1"),
    iss_pct: Decimal | int | str | None = None,
) -> ComparacaoDeRegimes:
    """Compara Simples e Lucro Presumido pela carga do trimestre.

    A receita do trimestre é dividida por três para o cálculo mensal do DAS,
    que é como o Simples apura; o Lucro Presumido apura o trimestre inteiro de
    uma vez.

    Leia `comparavel` antes de usar a diferença: sem alíquota de ISS informada,
    ou acima do limite da LC 224/2025, o Lucro Presumido sai subestimado e a
    comparação engana na direção dele.

    >>> from decimal import Decimal
    >>> from simples_nacional import Anexo, AtividadePresumido, comparar_regimes
    >>> c = comparar_regimes(Decimal("240000"), Anexo.III, Decimal("960000"),
    ...                      AtividadePresumido.SERVICOS, iss_pct=5)
    >>> c.regime_mais_barato
    'simples'
    >>> c.comparavel
    True
    """
    from .presumido import lucro_presumido

    receita = Decimal(str(receita_trimestral))
    ap = aliquota_efetiva(rbt12, anexo)
    mensal = receita / 3
    das = (das_devido(mensal, ap) * 3).quantize(_CENTAVO, rounding=ROUND_HALF_UP)
    cpp_simples = (
        cpp_fora_do_das(folha_trimestral, rat_pct=rat_pct, fap=fap)
        if Tributo.CPP not in TRIBUTOS_NO_DAS[anexo]
        else Decimal("0.00")
    )
    lp = lucro_presumido(
        receita,
        atividade,
        folha_trimestral=folha_trimestral,
        rat_pct=rat_pct,
        fap=fap,
        iss_pct=iss_pct,
    )
    return ComparacaoDeRegimes(
        receita_trimestral=receita,
        das_do_trimestre=das,
        cpp_no_simples=cpp_simples,
        total_simples=das + cpp_simples,
        total_presumido=lp.total,
        iss_arbitrado=lp.iss_arbitrado,
        acima_do_limite_lc224=lp.acima_do_limite_lc224,
    )
