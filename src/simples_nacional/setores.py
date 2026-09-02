"""Setores em que a alíquota do DAS não representa a carga tributária.

Cada registro diz se a receita do setor é monofásica de PIS/COFINS, se sofre
ICMS-ST, e cita a norma. O efeito na carga depende da posição na cadeia, e é
:func:`simples_nacional.carga_fora_do_das` que resolve isso.

Este módulo não calcula nada. A ausência de um setor aqui significa apenas que
ele não está registrado, não que o DAS cubra toda a sua carga.
"""

from __future__ import annotations

from dataclasses import dataclass

from .tabelas import Anexo

__all__ = ["RESSALVAS", "Ressalva", "ressalvas_de", "setores_registrados"]


@dataclass(frozen=True, slots=True)
class Ressalva:
    """Uma ressalva setorial sobre o alcance do DAS."""

    setor: str
    resumo: str
    monofasico: bool = False
    """Receita sujeita a PIS/COFINS concentrado numa etapa da cadeia."""
    icms_st: bool = False
    """Receita sujeita a substituição tributária do ICMS."""
    anexo_tipico: Anexo | None = None
    condicoes: tuple[str, ...] = ()
    fundamentos: tuple[str, ...] = ()


_MONOFASICO = (
    "Lei 10.147/2000 (medicamentos e cosméticos)",
    "Lei 10.485/2002 (autopeças e pneus)",
    "Lei 10.865/2004 e Lei 13.097/2015 (bebidas frias)",
    "LC 123/2006, art. 18, § 4º-A, I",
)

RESSALVAS: tuple[Ressalva, ...] = (
    Ressalva(
        setor="bebidas_alcoolicas",
        resumo=(
            "Micro e pequenas cervejarias, vinícolas, destilarias e produtores de "
            "licores podem optar pelo Simples desde 2018, no Anexo II. Cerveja é "
            "bebida fria: PIS/COFINS são concentrados e há ICMS-ST. Quem produz "
            "recolhe à parte e tem carga acima da alíquota; quem revende segrega "
            "a receita e reduz o DAS."
        ),
        monofasico=True,
        icms_st=True,
        anexo_tipico=Anexo.II,
        condicoes=(
            "Comercialização no atacado exclusivamente de produção própria.",
            "Registro no Ministério da Agricultura, Pecuária e Abastecimento (MAPA).",
            "Observância da regulamentação da ANVISA e da Receita Federal quanto à "
            "produção e comercialização de bebidas alcoólicas.",
        ),
        fundamentos=(
            'LC 123/2006, art. 17, X, "c", na redação do art. 1º da LC 155/2016',
            "Resolução CGSN nº 140/2018, art. 12",
            *_MONOFASICO,
        ),
    ),
    Ressalva(
        setor="bebidas_frias_nao_alcoolicas",
        resumo=(
            "Refrigerante, água mineral e demais bebidas frias seguem o mesmo "
            "regime concentrado de PIS/COFINS das cervejas."
        ),
        monofasico=True,
        icms_st=True,
        anexo_tipico=Anexo.II,
        fundamentos=_MONOFASICO,
    ),
    Ressalva(
        setor="medicamentos",
        resumo=(
            "Medicamentos têm PIS/COFINS concentrados na indústria e no importador. "
            "Farmácia que revende deve segregar a receita, sob pena de pagar a mais."
        ),
        monofasico=True,
        anexo_tipico=Anexo.I,
        fundamentos=("Lei 10.147/2000", "LC 123/2006, art. 18, § 4º-A, I"),
    ),
    Ressalva(
        setor="cosmeticos_perfumaria",
        resumo=(
            "Cosméticos, produtos de perfumaria e de higiene pessoal listados na "
            "Lei 10.147/2000 são monofásicos de PIS/COFINS."
        ),
        monofasico=True,
        anexo_tipico=Anexo.I,
        fundamentos=("Lei 10.147/2000", "LC 123/2006, art. 18, § 4º-A, I"),
    ),
    Ressalva(
        setor="autopecas_pneus",
        resumo="Autopeças e pneus têm PIS/COFINS concentrados na cadeia.",
        monofasico=True,
        anexo_tipico=Anexo.I,
        fundamentos=("Lei 10.485/2002", "LC 123/2006, art. 18, § 4º-A, I"),
    ),
    Ressalva(
        setor="combustiveis",
        resumo=(
            "Combustíveis são o caso clássico de tributação concentrada, com "
            "PIS/COFINS na refinaria ou no importador e ICMS-ST na cadeia."
        ),
        monofasico=True,
        icms_st=True,
        anexo_tipico=Anexo.I,
        fundamentos=("Lei 9.718/1998", "LC 123/2006, art. 18, § 4º-A, I"),
    ),
)

_POR_SETOR: dict[str, Ressalva] = {r.setor: r for r in RESSALVAS}


def setores_registrados() -> tuple[str, ...]:
    """Nomes dos setores com ressalva registrada."""
    return tuple(_POR_SETOR)


def ressalvas_de(setor: str) -> tuple[Ressalva, ...]:
    """Ressalvas de um setor. Tupla vazia se não houver registro.

    >>> [r.setor for r in ressalvas_de("medicamentos")]
    ['medicamentos']
    >>> ressalvas_de("consultoria")
    ()
    """
    r = _POR_SETOR.get(setor)
    return (r,) if r is not None else ()
