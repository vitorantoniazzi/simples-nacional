"""Lucro Presumido, para responder o que vem antes de "qual anexo?".

A pergunta que precede a escolha do anexo é se o Simples é o regime certo. Este
módulo calcula o Lucro Presumido pela parte estabelecida da lei, para que a
comparação seja possível.

O que NÃO está aqui, e por quê:

- **A majoração da LC 224/2025.** Desde 2026, receita bruta anual acima de
  R$ 5.000.000 tem os percentuais de presunção de IRPJ e CSLL acrescidos de 10%
  (32% viram 35,2%) sobre a parcela excedente. A regra é recente, foi
  regulamentada pela IN RFB 2.305/2025 com alterações da IN RFB 2.306/2026, e
  está sob litígio — há liminar suspendendo sua aplicação. Modelar norma em
  disputa como se fosse assentada produziria número confiante e errado, então
  `lucro_presumido` sinaliza quando a receita cruza o limite em vez de estimar.
- **ISS.** É municipal, varia de 2% a 5% conforme o município e a atividade, e
  não há tabela nacional. `lucro_presumido` aceita a alíquota como parâmetro e
  diz que não a arbitrou.
- **Créditos de PIS/COFINS.** No Lucro Presumido o regime é cumulativo, então
  não há crédito a considerar — mas empresa com receita mista pode ter parte no
  não cumulativo, e isso está fora daqui.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum

__all__ = [
    "ADICIONAL_IRPJ_PCT",
    "ALIQUOTA_CSLL_PCT",
    "ALIQUOTA_IRPJ_PCT",
    "COFINS_CUMULATIVO_PCT",
    "LIMITE_ADICIONAL_TRIMESTRAL",
    "LIMITE_MAJORACAO_LC224_ANUAL",
    "PIS_CUMULATIVO_PCT",
    "PRESUNCAO",
    "AtividadePresumido",
    "LucroPresumido",
    "lucro_presumido",
]

_CEM = Decimal("100")
_CENTAVO = Decimal("0.01")


def _centavos(v: Decimal) -> Decimal:
    return v.quantize(_CENTAVO, rounding=ROUND_HALF_UP)


class AtividadePresumido(Enum):
    """Atividades cujos percentuais de presunção este módulo transcreve.

    Deliberadamente curta. Transporte de passageiros (16%) e revenda de
    combustíveis (1,6%) têm presunção própria de IRPJ, mas não confirmei a de
    CSLL em fonte que me satisfizesse, e presunção arbitrada é pior que
    ausente.
    """

    COMERCIO_INDUSTRIA = "comercio_industria"
    SERVICOS = "servicos"


# Lei 9.249/1995, art. 15 (IRPJ) e art. 20 (CSLL).
PRESUNCAO: dict[AtividadePresumido, dict[str, Decimal]] = {
    AtividadePresumido.COMERCIO_INDUSTRIA: {
        "irpj": Decimal("8"),
        "csll": Decimal("12"),
    },
    AtividadePresumido.SERVICOS: {
        "irpj": Decimal("32"),
        "csll": Decimal("32"),
    },
}

ALIQUOTA_IRPJ_PCT = Decimal("15")
ADICIONAL_IRPJ_PCT = Decimal("10")
# Lei 9.430/1996: o adicional incide sobre o que exceder R$ 20.000 por mês do
# período de apuração, ou R$ 60.000 no trimestre.
LIMITE_ADICIONAL_TRIMESTRAL = Decimal("60000")
ALIQUOTA_CSLL_PCT = Decimal("9")
PIS_CUMULATIVO_PCT = Decimal("0.65")
COFINS_CUMULATIVO_PCT = Decimal("3")

# LC 224/2025: acima disto a presunção é majorada em 10% sobre o excedente.
# Não modelado — ver o docstring do módulo.
LIMITE_MAJORACAO_LC224_ANUAL = Decimal("5000000")


@dataclass(frozen=True, slots=True)
class LucroPresumido:
    """Apuração trimestral no Lucro Presumido."""

    receita_trimestral: Decimal
    atividade: AtividadePresumido
    base_irpj: Decimal
    irpj: Decimal
    adicional_irpj: Decimal
    base_csll: Decimal
    csll: Decimal
    pis: Decimal
    cofins: Decimal
    iss: Decimal
    cpp_sobre_folha: Decimal
    iss_arbitrado: bool
    """False quando a alíquota de ISS não foi informada — então `iss` é zero
    por ausência de dado, não por não incidir."""
    acima_do_limite_lc224: bool
    """True quando a receita anualizada cruza R$ 5.000.000, caso em que a
    majoração da LC 224/2025 se aplicaria e este resultado a subestima."""

    @property
    def federais(self) -> Decimal:
        return self.irpj + self.adicional_irpj + self.csll + self.pis + self.cofins

    @property
    def total(self) -> Decimal:
        return self.federais + self.iss + self.cpp_sobre_folha

    def carga_pct_da_receita(self) -> Decimal:
        if self.receita_trimestral == 0:
            return Decimal("0")
        return (self.total / self.receita_trimestral * _CEM).quantize(_CENTAVO)


def lucro_presumido(
    receita_trimestral: Decimal | int | str,
    atividade: AtividadePresumido,
    *,
    folha_trimestral: Decimal | int | str = 0,
    rat_pct: Decimal | int | str = 1,
    fap: Decimal | int | str = 1,
    iss_pct: Decimal | int | str | None = None,
) -> LucroPresumido:
    """Apura o trimestre no Lucro Presumido.

    A contribuição patronal entra sempre: no Lucro Presumido ela é devida sobre
    a folha, ao contrário do Simples, onde só o Anexo IV a deixa fora do DAS.
    Ignorá-la faria o Lucro Presumido parecer mais barato do que é.

    `iss_pct` não tem padrão porque não existe alíquota nacional de ISS. Sem
    ela o resultado traz `iss_arbitrado=False` e o ISS fica de fora,
    explicitamente.

    >>> from decimal import Decimal
    >>> from simples_nacional import AtividadePresumido, lucro_presumido
    >>> r = lucro_presumido(Decimal("240000"), AtividadePresumido.SERVICOS)
    >>> r.base_irpj
    Decimal('76800.00')
    >>> r.irpj
    Decimal('11520.00')
    >>> r.adicional_irpj
    Decimal('1680.00')
    >>> r.csll
    Decimal('6912.00')
    """
    from .comparacao import cpp_fora_do_das

    receita = Decimal(str(receita_trimestral))
    if receita < 0:
        raise ValueError(f"receita não pode ser negativa: {receita}")

    p = PRESUNCAO[atividade]
    base_irpj = _centavos(receita * p["irpj"] / _CEM)
    base_csll = _centavos(receita * p["csll"] / _CEM)

    irpj = _centavos(base_irpj * ALIQUOTA_IRPJ_PCT / _CEM)
    excedente = max(base_irpj - LIMITE_ADICIONAL_TRIMESTRAL, Decimal("0"))
    adicional = _centavos(excedente * ADICIONAL_IRPJ_PCT / _CEM)
    csll = _centavos(base_csll * ALIQUOTA_CSLL_PCT / _CEM)

    pis = _centavos(receita * PIS_CUMULATIVO_PCT / _CEM)
    cofins = _centavos(receita * COFINS_CUMULATIVO_PCT / _CEM)

    if iss_pct is None:
        iss, arbitrado = Decimal("0.00"), False
    else:
        taxa = Decimal(str(iss_pct))
        if not Decimal("0") <= taxa <= Decimal("5"):
            raise ValueError(f"iss_pct deve estar entre 0 e 5: {taxa}")
        iss, arbitrado = _centavos(receita * taxa / _CEM), True

    cpp = cpp_fora_do_das(folha_trimestral, rat_pct=rat_pct, fap=fap)

    return LucroPresumido(
        receita_trimestral=receita,
        atividade=atividade,
        base_irpj=base_irpj,
        irpj=irpj,
        adicional_irpj=adicional,
        base_csll=base_csll,
        csll=csll,
        pis=pis,
        cofins=cofins,
        iss=iss,
        cpp_sobre_folha=cpp,
        iss_arbitrado=arbitrado,
        acima_do_limite_lc224=receita * 4 > LIMITE_MAJORACAO_LC224_ANUAL,
    )
