"""Tabelas legais do Simples Nacional.

Os valores desta módulo são reproduções das tabelas dos Anexos I a V da
Lei Complementar nº 123/2006, na redação dada pela Lei Complementar nº
155/2016 (vigente desde 01/01/2018).

Não são estimativas nem valores calculados: são a lei transcrita. Qualquer
alteração aqui deve citar a norma que a motivou.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

__all__ = ["FATOR_R_MINIMO", "LIMITE_SIMPLES", "SUBLIMITE_ICMS_ISS", "TABELAS", "Anexo", "Faixa"]


class Anexo(Enum):
    """Anexos da LC 123/2006 que definem alíquota nominal e parcela a deduzir."""

    I = "I"
    II = "II"
    III = "III"
    IV = "IV"
    V = "V"

    @property
    def descricao(self) -> str:
        return _DESCRICOES[self]


_DESCRICOES: dict[Anexo, str] = {
    Anexo.I: "Comércio",
    Anexo.II: "Indústria",
    Anexo.III: "Locação de bens móveis e serviços em geral",
    Anexo.IV: "Serviços do § 5º-C (construção, advocacia, vigilância, limpeza)",
    Anexo.V: "Serviços do § 5º-I (intelectuais), quando o Fator R for inferior ao mínimo",
}


@dataclass(frozen=True, slots=True)
class Faixa:
    """Uma das seis faixas de receita bruta de um anexo."""

    numero: int
    limite_superior: Decimal
    aliquota_nominal: Decimal
    parcela_deduzir: Decimal


def _faixas(linhas: list[tuple[str, str, str]]) -> tuple[Faixa, ...]:
    return tuple(
        Faixa(
            numero=i,
            limite_superior=Decimal(limite),
            aliquota_nominal=Decimal(aliquota),
            parcela_deduzir=Decimal(deducao),
        )
        for i, (limite, aliquota, deducao) in enumerate(linhas, start=1)
    )


# Limite geral de receita bruta anual para permanência no Simples Nacional.
LIMITE_SIMPLES = Decimal("4800000.00")

# Acima deste sublimite, ICMS e ISS deixam de ser recolhidos no DAS e passam
# a ser apurados fora do regime (LC 123/2006, art. 19 e art. 20).
SUBLIMITE_ICMS_ISS = Decimal("3600000.00")

# Razão mínima entre folha de salários e receita bruta (ambas em 12 meses)
# para que atividades do § 5º-I sejam tributadas pelo Anexo III (§ 5º-M).
FATOR_R_MINIMO = Decimal("0.28")


TABELAS: dict[Anexo, tuple[Faixa, ...]] = {
    Anexo.I: _faixas(
        [
            ("180000.00", "4.00", "0.00"),
            ("360000.00", "7.30", "5940.00"),
            ("720000.00", "9.50", "13860.00"),
            ("1800000.00", "10.70", "22500.00"),
            ("3600000.00", "14.30", "87300.00"),
            ("4800000.00", "19.00", "378000.00"),
        ]
    ),
    Anexo.II: _faixas(
        [
            ("180000.00", "4.50", "0.00"),
            ("360000.00", "7.80", "5940.00"),
            ("720000.00", "10.00", "13860.00"),
            ("1800000.00", "11.20", "22500.00"),
            ("3600000.00", "14.70", "85500.00"),
            ("4800000.00", "30.00", "720000.00"),
        ]
    ),
    Anexo.III: _faixas(
        [
            ("180000.00", "6.00", "0.00"),
            ("360000.00", "11.20", "9360.00"),
            ("720000.00", "13.50", "17640.00"),
            ("1800000.00", "16.00", "35640.00"),
            ("3600000.00", "21.00", "125640.00"),
            ("4800000.00", "33.00", "648000.00"),
        ]
    ),
    Anexo.IV: _faixas(
        [
            ("180000.00", "4.50", "0.00"),
            ("360000.00", "9.00", "8100.00"),
            ("720000.00", "10.20", "12420.00"),
            ("1800000.00", "14.00", "39780.00"),
            ("3600000.00", "22.00", "183780.00"),
            ("4800000.00", "33.00", "828000.00"),
        ]
    ),
    Anexo.V: _faixas(
        [
            ("180000.00", "15.50", "0.00"),
            ("360000.00", "18.00", "4500.00"),
            ("720000.00", "19.50", "9900.00"),
            ("1800000.00", "20.50", "17100.00"),
            ("3600000.00", "23.00", "62100.00"),
            ("4800000.00", "30.50", "540000.00"),
        ]
    ),
}
