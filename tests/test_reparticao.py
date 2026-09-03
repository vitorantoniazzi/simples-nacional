"""Repartição do DAS entre tributos.

Como as tabelas de faixa, isto é lei transcrita. A tabela abaixo é uma segunda
transcrição independente dos Anexos I a V; se ela e o pacote divergirem, é isso
que se quer descobrir.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from simples_nacional import (
    SUBLIMITE_ICMS_ISS,
    TRIBUTOS_NO_DAS,
    Anexo,
    Tributo,
    aliquota_efetiva,
    das_devido,
    das_por_tributo,
    reparticao_da_faixa,
)

# Transcrição independente. Ordem: IRPJ, CSLL, COFINS, PIS, CPP, IPI, ICMS, ISS.
# "-" significa que o tributo não consta da faixa.
LEI: dict[str, list[dict[str, str]]] = {
    "I": [
        {
            "IRPJ": "5.50",
            "CSLL": "3.50",
            "COFINS": "12.74",
            "PIS/PASEP": "2.76",
            "CPP": "41.50",
            "ICMS": "34.00",
        },
        {
            "IRPJ": "5.50",
            "CSLL": "3.50",
            "COFINS": "12.74",
            "PIS/PASEP": "2.76",
            "CPP": "41.50",
            "ICMS": "34.00",
        },
        {
            "IRPJ": "5.50",
            "CSLL": "3.50",
            "COFINS": "12.74",
            "PIS/PASEP": "2.76",
            "CPP": "42.00",
            "ICMS": "33.50",
        },
        {
            "IRPJ": "5.50",
            "CSLL": "3.50",
            "COFINS": "12.74",
            "PIS/PASEP": "2.76",
            "CPP": "42.00",
            "ICMS": "33.50",
        },
        {
            "IRPJ": "5.50",
            "CSLL": "3.50",
            "COFINS": "12.74",
            "PIS/PASEP": "2.76",
            "CPP": "42.00",
            "ICMS": "33.50",
        },
        {"IRPJ": "13.50", "CSLL": "10.00", "COFINS": "28.27", "PIS/PASEP": "6.13", "CPP": "42.10"},
    ],
    "II": [
        *[
            {
                "IRPJ": "5.50",
                "CSLL": "3.50",
                "COFINS": "11.51",
                "PIS/PASEP": "2.49",
                "CPP": "37.50",
                "IPI": "7.50",
                "ICMS": "32.00",
            }
        ]
        * 5,
        {
            "IRPJ": "8.50",
            "CSLL": "7.50",
            "COFINS": "20.96",
            "PIS/PASEP": "4.54",
            "CPP": "23.50",
            "IPI": "35.00",
        },
    ],
    "III": [
        {
            "IRPJ": "4.00",
            "CSLL": "3.50",
            "COFINS": "12.82",
            "PIS/PASEP": "2.78",
            "CPP": "43.40",
            "ISS": "33.50",
        },
        {
            "IRPJ": "4.00",
            "CSLL": "3.50",
            "COFINS": "14.05",
            "PIS/PASEP": "3.05",
            "CPP": "43.40",
            "ISS": "32.00",
        },
        {
            "IRPJ": "4.00",
            "CSLL": "3.50",
            "COFINS": "13.64",
            "PIS/PASEP": "2.96",
            "CPP": "43.40",
            "ISS": "32.50",
        },
        {
            "IRPJ": "4.00",
            "CSLL": "3.50",
            "COFINS": "13.64",
            "PIS/PASEP": "2.96",
            "CPP": "43.40",
            "ISS": "32.50",
        },
        {
            "IRPJ": "4.00",
            "CSLL": "3.50",
            "COFINS": "12.82",
            "PIS/PASEP": "2.78",
            "CPP": "43.40",
            "ISS": "33.50",
        },
        {"IRPJ": "35.00", "CSLL": "15.00", "COFINS": "16.03", "PIS/PASEP": "3.47", "CPP": "30.50"},
    ],
    "IV": [
        {"IRPJ": "18.80", "CSLL": "15.20", "COFINS": "17.67", "PIS/PASEP": "3.83", "ISS": "44.50"},
        {"IRPJ": "19.80", "CSLL": "15.20", "COFINS": "20.55", "PIS/PASEP": "4.45", "ISS": "40.00"},
        {"IRPJ": "20.80", "CSLL": "15.20", "COFINS": "19.73", "PIS/PASEP": "4.27", "ISS": "40.00"},
        {"IRPJ": "17.80", "CSLL": "19.20", "COFINS": "18.90", "PIS/PASEP": "4.10", "ISS": "40.00"},
        {"IRPJ": "18.80", "CSLL": "19.20", "COFINS": "18.08", "PIS/PASEP": "3.92", "ISS": "40.00"},
        {"IRPJ": "53.50", "CSLL": "21.50", "COFINS": "20.55", "PIS/PASEP": "4.45"},
    ],
    "V": [
        {
            "IRPJ": "25.00",
            "CSLL": "15.00",
            "COFINS": "14.10",
            "PIS/PASEP": "3.05",
            "CPP": "28.85",
            "ISS": "14.00",
        },
        {
            "IRPJ": "23.00",
            "CSLL": "15.00",
            "COFINS": "14.10",
            "PIS/PASEP": "3.05",
            "CPP": "27.85",
            "ISS": "17.00",
        },
        {
            "IRPJ": "24.00",
            "CSLL": "15.00",
            "COFINS": "14.92",
            "PIS/PASEP": "3.23",
            "CPP": "23.85",
            "ISS": "19.00",
        },
        {
            "IRPJ": "21.00",
            "CSLL": "15.00",
            "COFINS": "15.74",
            "PIS/PASEP": "3.41",
            "CPP": "23.85",
            "ISS": "21.00",
        },
        {
            "IRPJ": "23.00",
            "CSLL": "12.50",
            "COFINS": "14.10",
            "PIS/PASEP": "3.05",
            "CPP": "23.85",
            "ISS": "23.50",
        },
        {"IRPJ": "35.00", "CSLL": "15.50", "COFINS": "16.44", "PIS/PASEP": "3.56", "CPP": "29.50"},
    ],
}


@pytest.mark.parametrize(("anexo", "faixa"), [(a, f) for a in Anexo for f in range(1, 7)])
def test_bate_com_a_segunda_transcricao(anexo: Anexo, faixa: int) -> None:
    esperado = {Tributo(k): Decimal(v) for k, v in LEI[anexo.value][faixa - 1].items()}
    assert reparticao_da_faixa(anexo, faixa) == esperado


@pytest.mark.parametrize(("anexo", "faixa"), [(a, f) for a in Anexo for f in range(1, 7)])
def test_cada_faixa_soma_cem_por_cento(anexo: Anexo, faixa: int) -> None:
    # Um erro de transcrição quase sempre quebra esta soma, e é por isso que ela
    # é o teste mais valioso deste arquivo.
    assert sum(reparticao_da_faixa(anexo, faixa).values()) == Decimal("100.00")


@pytest.mark.parametrize("anexo", list(Anexo))
def test_a_sexta_faixa_nao_tem_icms_nem_iss(anexo: Anexo) -> None:
    """A ausência explica o degrau da alíquota no sublimite.

    A 6ª faixa começa em R$ 3.600.000, acima do sublimite, onde ICMS e ISS
    deixam de ser recolhidos no DAS. A alíquota da faixa cobre menos tributos,
    e por isso cai.
    """
    sexta = reparticao_da_faixa(anexo, 6)
    assert Tributo.ICMS not in sexta
    assert Tributo.ISS not in sexta


@pytest.mark.parametrize("anexo", list(Anexo))
def test_faixas_ate_a_quinta_batem_com_os_tributos_do_anexo(anexo: Anexo) -> None:
    # A repartição e TRIBUTOS_NO_DAS descrevem a mesma coisa por caminhos
    # diferentes; divergirem significaria que um dos dois está errado.
    declarados = set(TRIBUTOS_NO_DAS[anexo])
    for faixa in range(1, 6):
        na_reparticao = set(reparticao_da_faixa(anexo, faixa))
        assert na_reparticao == declarados, (anexo, faixa)


@pytest.mark.parametrize("anexo", list(Anexo))
def test_so_o_anexo_iv_nao_reparte_cpp(anexo: Anexo) -> None:
    tem = Tributo.CPP in reparticao_da_faixa(anexo, 1)
    assert tem is (anexo is not Anexo.IV)


def test_so_o_anexo_ii_reparte_ipi() -> None:
    for anexo in Anexo:
        tem = Tributo.IPI in reparticao_da_faixa(anexo, 1)
        assert tem is (anexo is Anexo.II)


@pytest.mark.parametrize("faixa", [0, 7, -1])
def test_faixa_fora_do_intervalo_e_recusada(faixa: int) -> None:
    with pytest.raises(ValueError, match="entre 1 e 6"):
        reparticao_da_faixa(Anexo.II, faixa)


def test_reparticao_devolve_copia_e_nao_a_tabela_viva() -> None:
    d = reparticao_da_faixa(Anexo.II, 1)
    d[Tributo.ICMS] = Decimal("0")
    assert reparticao_da_faixa(Anexo.II, 1)[Tributo.ICMS] == Decimal("32.00")


class TestDasPorTributo:
    def test_reparte_o_das_do_mes(self) -> None:
        ap = aliquota_efetiva(Decimal("1200000"), Anexo.II)
        partes = das_por_tributo(Decimal("100000"), ap)
        assert partes[Tributo.ICMS] == Decimal("2984.00")
        assert partes[Tributo.CPP] == Decimal("3496.88")

    def test_a_deriva_de_arredondamento_e_limitada(self) -> None:
        """Cada parcela arredonda, então a soma pode não fechar no centavo.

        A deriva é de meio centavo por tributo no pior caso. O total a recolher
        é o de das_devido, não esta soma, e o docstring diz isso.
        """
        for anexo in Anexo:
            for rbt12 in ("200000", "800000", "2000000", "4000000"):
                ap = aliquota_efetiva(Decimal(rbt12), anexo)
                total = das_devido(Decimal("100000"), ap)
                partes = das_por_tributo(Decimal("100000"), ap)
                n = len(partes)
                limite = Decimal("0.01") * n / 2
                assert abs(sum(partes.values()) - total) <= limite, (anexo, rbt12)

    def test_acima_do_sublimite_nao_ha_parcela_de_icms(self) -> None:
        ap = aliquota_efetiva(SUBLIMITE_ICMS_ISS + Decimal("1"), Anexo.II)
        assert ap.icms_iss_fora_do_das
        assert Tributo.ICMS not in das_por_tributo(Decimal("300000"), ap)

    def test_a_parcela_monofasica_e_pis_mais_cofins(self) -> None:
        # É esta soma que sai do DAS quando a receita é segregada.
        ap = aliquota_efetiva(Decimal("500000"), Anexo.I)
        partes = das_por_tributo(Decimal("50000"), ap)
        monofasico = partes[Tributo.PIS] + partes[Tributo.COFINS]
        assert monofasico > 0
        assert monofasico < das_devido(Decimal("50000"), ap)
