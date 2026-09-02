"""Ressalvas setoriais: onde a alíquota efetiva não é a carga tributária total.

A alíquota efetiva do Simples Nacional cobre os tributos recolhidos no DAS.
Há setores em que tributos relevantes ficam fora dele, e nesses casos usar a
efetiva como carga total subestima o custo — às vezes por muito.

Este módulo não calcula nada. Ele registra ressalvas com a norma que as
sustenta, para que quem estiver modelando um negócio saiba o que ainda falta
somar.
"""

from __future__ import annotations

from dataclasses import dataclass

from .tabelas import Anexo

__all__ = ["RESSALVAS", "Ressalva", "ressalvas_de"]


@dataclass(frozen=True, slots=True)
class Ressalva:
    """Uma ressalva setorial sobre o alcance do DAS."""

    setor: str
    anexo: Anexo
    resumo: str
    tributos_fora_do_das: tuple[str, ...] = ()
    condicoes: tuple[str, ...] = ()
    fundamentos: tuple[str, ...] = ()


RESSALVAS: tuple[Ressalva, ...] = (
    Ressalva(
        setor="bebidas_alcoolicas",
        anexo=Anexo.II,
        resumo=(
            "Micro e pequenas cervejarias, vinícolas, destilarias e produtores de "
            "licores podem optar pelo Simples Nacional desde 2018, tributadas pelo "
            "Anexo II. A alíquota efetiva do anexo, porém, não é a carga total: "
            "cerveja sofre ICMS-ST e IPI fora do DAS."
        ),
        tributos_fora_do_das=("ICMS-ST", "IPI"),
        condicoes=(
            "Comercialização no atacado exclusivamente de produção própria.",
            "Registro no Ministério da Agricultura, Pecuária e Abastecimento (MAPA).",
            "Observância da regulamentação da ANVISA e da Receita Federal quanto à "
            "produção e comercialização de bebidas alcoólicas.",
        ),
        fundamentos=(
            'LC 123/2006, art. 17, X, "c", na redação do art. 1º da LC 155/2016',
            "Resolução CGSN nº 140/2018, art. 12",
        ),
    ),
)

_POR_SETOR: dict[str, Ressalva] = {r.setor: r for r in RESSALVAS}


def ressalvas_de(setor: str) -> tuple[Ressalva, ...]:
    """Ressalvas registradas para um setor. Tupla vazia se não houver nenhuma.

    A ausência de ressalva aqui significa apenas que este módulo não registra
    uma, não que o DAS cubra toda a carga do setor.

    >>> [r.setor for r in ressalvas_de("bebidas_alcoolicas")]
    ['bebidas_alcoolicas']
    >>> ressalvas_de("comercio_varejista")
    ()
    """
    r = _POR_SETOR.get(setor)
    return (r,) if r is not None else ()
