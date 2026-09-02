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

from .core import (
    Apuracao,
    aliquota_efetiva,
    anexo_por_fator_r,
    das_devido,
    fator_r,
    rbt12_proporcional,
)
from .setores import RESSALVAS, Ressalva, ressalvas_de
from .tabelas import (
    FATOR_R_MINIMO,
    LIMITE_SIMPLES,
    SUBLIMITE_ICMS_ISS,
    TABELAS,
    Anexo,
    Faixa,
)

__version__ = "0.1.0"

__all__ = [
    "FATOR_R_MINIMO",
    "LIMITE_SIMPLES",
    "RESSALVAS",
    "SUBLIMITE_ICMS_ISS",
    "TABELAS",
    "Anexo",
    "Apuracao",
    "Faixa",
    "Ressalva",
    "__version__",
    "aliquota_efetiva",
    "anexo_por_fator_r",
    "das_devido",
    "fator_r",
    "rbt12_proporcional",
    "ressalvas_de",
]
