"""Cálculo do Simples Nacional a partir das tabelas legais.

Reproduz os Anexos I a V da LC 123/2006 (redação da LC 155/2016) e implementa
a alíquota efetiva, o Fator R e a proporcionalização do RBT12.

Não é assessoria fiscal. Calcula o que a lei publica; enquadramento de
atividade, regime e obrigações acessórias são decisões contábeis.

    >>> from decimal import Decimal
    >>> from simples_nacional import Anexo, aliquota_efetiva, das_devido
    >>> ap = aliquota_efetiva(Decimal("1200000"), Anexo.II)
    >>> ap.faixa.numero, ap.aliquota_efetiva
    (4, Decimal('9.32500'))
    >>> das_devido(Decimal("100000"), ap)
    Decimal('9325.00')
"""

from __future__ import annotations

from .carga import (
    CPP_ALIQUOTA_FOLHA_PCT,
    TRIBUTOS_NO_DAS,
    Efeito,
    ItemForaDoDAS,
    PosicaoNaCadeia,
    carga_fora_do_das,
)
from .core import (
    Apuracao,
    aliquota_efetiva,
    anexo_por_fator_r,
    das_devido,
    fator_r,
    rbt12_proporcional,
)
from .reparticao import (
    ISS_TETO_EFETIVO_PCT,
    REPARTICAO,
    Tributo,
    das_por_tributo,
    reparticao_da_faixa,
)
from .setores import RESSALVAS, Ressalva, ressalvas_de, setores_registrados
from .tabelas import (
    FATOR_R_MINIMO,
    LIMITE_SIMPLES,
    SUBLIMITE_ICMS_ISS,
    TABELAS,
    Anexo,
    Faixa,
)

__version__ = "0.3.0"

__all__ = [
    "CPP_ALIQUOTA_FOLHA_PCT",
    "FATOR_R_MINIMO",
    "ISS_TETO_EFETIVO_PCT",
    "LIMITE_SIMPLES",
    "REPARTICAO",
    "RESSALVAS",
    "SUBLIMITE_ICMS_ISS",
    "TABELAS",
    "TRIBUTOS_NO_DAS",
    "Anexo",
    "Apuracao",
    "Efeito",
    "Faixa",
    "ItemForaDoDAS",
    "PosicaoNaCadeia",
    "Ressalva",
    "Tributo",
    "__version__",
    "aliquota_efetiva",
    "anexo_por_fator_r",
    "carga_fora_do_das",
    "das_devido",
    "das_por_tributo",
    "fator_r",
    "rbt12_proporcional",
    "reparticao_da_faixa",
    "ressalvas_de",
    "setores_registrados",
]
