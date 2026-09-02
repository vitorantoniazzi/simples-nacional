"""O que o DAS cobre, e o que fica de fora dele.

A alíquota efetiva é a carga do DAS, não a carga tributária. Há duas razões
distintas para um tributo ficar fora, e confundi-las leva a erro em direções
opostas:

1. **O anexo não o inclui.** O caso do Anexo IV, cujo DAS não abrange a
   contribuição previdenciária patronal: ela é recolhida à parte, sobre a
   folha. Isso *acrescenta* carga a quem compara anexos pela alíquota.

2. **A receita é segregada.** Em operações monofásicas ou com ICMS-ST, os
   percentuais dos tributos já cobrados na cadeia são desconsiderados no
   cálculo do DAS. O efeito depende da posição na cadeia: para quem revende,
   *reduz* o DAS; para quem produz, o tributo concentrado é cobrado à parte,
   com alíquota específica, e *acrescenta* carga.

Este módulo não quantifica nada. Quantificar exige a repartição do DAS por
tributo, que não está nesta versão. O que ele faz é dizer o que falta somar ou
subtrair, e citar a norma.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .tabelas import Anexo

__all__ = [
    "CPP_ALIQUOTA_FOLHA_PCT",
    "TRIBUTOS_NO_DAS",
    "Efeito",
    "ItemForaDoDAS",
    "PosicaoNaCadeia",
    "carga_fora_do_das",
]


class Efeito(Enum):
    """Direção em que um item altera a carga, comparada à alíquota do DAS."""

    ACRESCENTA = "acrescenta"
    REDUZ = "reduz"


class PosicaoNaCadeia(Enum):
    """Posição do contribuinte na cadeia, que decide a direção do efeito."""

    PRODUTOR = "produtor"
    """Industrializa ou importa: é quem recolhe o tributo concentrado."""

    REVENDEDOR = "revendedor"
    """Revende mercadoria cujo tributo já foi recolhido antes."""


# Tributos abrangidos pelo DAS em cada anexo (LC 123/2006, art. 13 e art. 18).
# O Anexo IV é a exceção que importa: não abrange a CPP.
TRIBUTOS_NO_DAS: dict[Anexo, tuple[str, ...]] = {
    Anexo.I: ("IRPJ", "CSLL", "PIS", "COFINS", "CPP", "ICMS"),
    Anexo.II: ("IRPJ", "CSLL", "PIS", "COFINS", "CPP", "IPI", "ICMS"),
    Anexo.III: ("IRPJ", "CSLL", "PIS", "COFINS", "CPP", "ISS"),
    Anexo.IV: ("IRPJ", "CSLL", "PIS", "COFINS", "ISS"),
    Anexo.V: ("IRPJ", "CSLL", "PIS", "COFINS", "CPP", "ISS"),
}

# Alíquota da contribuição patronal sobre a folha, devida à parte no Anexo IV.
CPP_ALIQUOTA_FOLHA_PCT = "20"
"""Percentual sobre a folha, ao qual se soma o RAT de 1% a 3% conforme o risco."""


@dataclass(frozen=True, slots=True)
class ItemForaDoDAS:
    """Um tributo ou encargo que a alíquota do DAS não representa."""

    tributo: str
    efeito: Efeito
    motivo: str
    base: str
    """Sobre o que incide, quando não é a receita. Ex.: "folha de salários"."""
    fundamentos: tuple[str, ...]


def carga_fora_do_das(
    anexo: Anexo,
    *,
    receita_monofasica: bool = False,
    receita_com_icms_st: bool = False,
    posicao: PosicaoNaCadeia = PosicaoNaCadeia.REVENDEDOR,
) -> tuple[ItemForaDoDAS, ...]:
    """O que a alíquota efetiva do anexo não cobre, e em que direção.

    `receita_monofasica` e `receita_com_icms_st` descrevem a operação; `posicao`
    decide a direção do efeito, porque produzir e revender o mesmo produto
    monofásico tem consequências opostas.

    >>> from simples_nacional import Anexo, carga_fora_do_das
    >>> [i.tributo for i in carga_fora_do_das(Anexo.IV)]
    ['CPP']
    >>> carga_fora_do_das(Anexo.II)
    ()
    """
    itens: list[ItemForaDoDAS] = []

    if "CPP" not in TRIBUTOS_NO_DAS[anexo]:
        itens.append(
            ItemForaDoDAS(
                tributo="CPP",
                efeito=Efeito.ACRESCENTA,
                motivo=(
                    f"O DAS do Anexo {anexo.value} não abrange a contribuição "
                    f"previdenciária patronal. Ela é recolhida à parte, a "
                    f"{CPP_ALIQUOTA_FOLHA_PCT}% sobre a folha, mais o RAT de 1% a 3%. "
                    "Comparar este anexo com outro apenas pela alíquota efetiva "
                    "subestima a carga de quem tem folha relevante."
                ),
                base="folha de salários, incluído o pró-labore",
                fundamentos=(
                    "LC 123/2006, art. 13, § 1º, VI, e art. 18, § 5º-C",
                    "Resolução CGSN nº 140/2018, art. 25, § 1º, IV",
                ),
            )
        )

    if receita_monofasica:
        produtor = posicao is PosicaoNaCadeia.PRODUTOR
        itens.append(
            ItemForaDoDAS(
                tributo="PIS/COFINS (monofásico)",
                efeito=Efeito.ACRESCENTA if produtor else Efeito.REDUZ,
                motivo=(
                    "Quem industrializa ou importa é o responsável pelo "
                    "recolhimento concentrado, com alíquotas específicas fora do "
                    "DAS: a carga real fica acima da alíquota do anexo."
                    if produtor
                    else "A contribuição já foi recolhida na origem da cadeia. A "
                    "receita deve ser segregada, e os percentuais de PIS e COFINS "
                    "são desconsiderados no cálculo do DAS: segregar reduz o DAS. "
                    "Não segregar é pagar a mais, e o indébito é recuperável."
                ),
                base="receita das operações monofásicas",
                fundamentos=(
                    "LC 123/2006, art. 18, § 4º-A, I",
                    "Resolução CGSN nº 140/2018, art. 25, § 6º",
                ),
            )
        )

    if receita_com_icms_st:
        substituto = posicao is PosicaoNaCadeia.PRODUTOR
        itens.append(
            ItemForaDoDAS(
                tributo="ICMS-ST",
                efeito=Efeito.ACRESCENTA if substituto else Efeito.REDUZ,
                motivo=(
                    "Como substituto tributário, o ICMS de toda a cadeia é "
                    "retido e recolhido à parte, fora do DAS."
                    if substituto
                    else "O ICMS foi retido pelo substituto. A receita deve ser "
                    "segregada, e o percentual de ICMS é desconsiderado no "
                    "cálculo do DAS."
                ),
                base="receita das operações com ICMS retido",
                fundamentos=(
                    "LC 123/2006, art. 13, § 1º, XIII, e art. 18, § 4º-A, IV",
                    "Resolução CGSN nº 140/2018, art. 25, § 8º",
                ),
            )
        )

    return tuple(itens)
