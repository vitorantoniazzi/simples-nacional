"""Segregação de receitas e o indébito de quem não segrega."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from simples_nacional import (
    ANOS_DE_PRESCRICAO,
    SUBLIMITE_ICMS_ISS,
    Anexo,
    Competencia,
    das_com_segregacao,
    indebito_por_segregacao,
    percentual_segregavel,
)


class TestPercentualSegregavel:
    def test_monofasico_e_pis_mais_cofins(self) -> None:
        # Anexo I faixa 4: PIS 2,76 + COFINS 12,74 = 15,50
        assert percentual_segregavel(Anexo.I, 4, monofasica=True) == Decimal("15.50")

    def test_icms_st_e_a_fatia_do_icms(self) -> None:
        assert percentual_segregavel(Anexo.I, 4, com_icms_st=True) == Decimal("33.50")

    def test_os_dois_juntos_somam(self) -> None:
        assert percentual_segregavel(Anexo.I, 4, monofasica=True, com_icms_st=True) == Decimal(
            "49.00"
        )

    def test_sem_regime_especial_nao_segrega_nada(self) -> None:
        assert percentual_segregavel(Anexo.I, 4) == Decimal("0")

    def test_acima_do_sublimite_o_icms_st_nao_tem_efeito(self) -> None:
        # Na 6ª faixa o ICMS já não integra o DAS: não há o que desconsiderar.
        assert percentual_segregavel(Anexo.I, 6, com_icms_st=True) == Decimal("0")

    def test_anexo_iv_nao_tem_icms_para_segregar(self) -> None:
        # Serviços não recolhem ICMS; segregar ICMS-ST ali é inócuo.
        assert percentual_segregavel(Anexo.IV, 3, com_icms_st=True) == Decimal("0")


class TestDasComSegregacao:
    def test_reduz_proporcionalmente_ao_percentual_desconsiderado(self) -> None:
        args = (Decimal("60000"), Anexo.I, Decimal("900000"))
        cheio = das_com_segregacao(*args)
        segregado = das_com_segregacao(*args, monofasica=True, com_icms_st=True)
        assert segregado == Decimal("2509.20")
        assert segregado < cheio

    def test_receita_negativa_e_recusada(self) -> None:
        with pytest.raises(ValueError, match="negativa"):
            das_com_segregacao(Decimal("-1"), Anexo.I, Decimal("900000"))


class TestCompetencia:
    def test_vencimento_e_dia_20_do_mes_seguinte(self) -> None:
        assert Competencia(2026, 1, Decimal("0")).vencimento == date(2026, 2, 20)

    def test_dezembro_vence_em_janeiro_do_ano_seguinte(self) -> None:
        assert Competencia(2026, 12, Decimal("0")).vencimento == date(2027, 1, 20)

    @pytest.mark.parametrize("mes", [0, 13, -1])
    def test_mes_invalido_e_recusado(self, mes: int) -> None:
        with pytest.raises(ValueError, match="mês inválido"):
            Competencia(2026, mes, Decimal("0"))

    def test_receita_total_soma_as_categorias(self) -> None:
        c = Competencia(
            2026,
            1,
            Decimal("900000"),
            receita_sem_regime_especial=Decimal("20000"),
            receita_monofasica_e_com_icms_st=Decimal("60000"),
        )
        assert c.receita_total == Decimal("80000")


class TestIndebito:
    def bar(self, ano: int, mes: int) -> Competencia:
        return Competencia(
            ano,
            mes,
            Decimal("900000"),
            receita_sem_regime_especial=Decimal("20000"),
            receita_monofasica_e_com_icms_st=Decimal("60000"),
        )

    def test_uma_competencia(self) -> None:
        r = indebito_por_segregacao([self.bar(2026, 1)], Anexo.I, hoje=date(2026, 9, 3))
        assert r.recuperavel == Decimal("2410.80")
        assert r.prescrito == Decimal("0")

    def test_doze_competencias_acumulam(self) -> None:
        meses = [self.bar(2026, m) for m in range(1, 13)]
        r = indebito_por_segregacao(meses, Anexo.I, hoje=date(2027, 2, 1))
        assert r.recuperavel == Decimal("2410.80") * 12
        assert r.total == r.recuperavel

    def test_competencia_antiga_prescreve(self) -> None:
        # Vencimento em 2018 está fora dos cinco anos contados de 2026.
        r = indebito_por_segregacao(
            [self.bar(2018, 1), self.bar(2026, 1)], Anexo.I, hoje=date(2026, 9, 3)
        )
        assert r.prescrito == Decimal("2410.80")
        assert r.recuperavel == Decimal("2410.80")
        assert r.total == Decimal("2410.80") * 2

    def test_a_data_de_corte_e_cinco_anos_atras(self) -> None:
        r = indebito_por_segregacao([], Anexo.I, hoje=date(2026, 9, 3))
        assert r.data_de_corte == date(2026 - ANOS_DE_PRESCRICAO, 9, 3)

    def test_sem_regime_especial_nao_ha_indebito(self) -> None:
        c = Competencia(2026, 1, Decimal("900000"), receita_sem_regime_especial=Decimal("80000"))
        r = indebito_por_segregacao([c], Anexo.I, hoje=date(2026, 9, 3))
        assert r.total == Decimal("0")

    def test_acima_do_sublimite_o_icms_st_nao_gera_indebito(self) -> None:
        c = Competencia(
            2026,
            1,
            SUBLIMITE_ICMS_ISS + Decimal("1"),
            receita_com_icms_st=Decimal("100000"),
        )
        r = indebito_por_segregacao([c], Anexo.I, hoje=date(2026, 9, 3))
        assert r.total == Decimal("0")

    def test_lista_vazia_devolve_zeros(self) -> None:
        r = indebito_por_segregacao([], Anexo.I, hoje=date(2026, 9, 3))
        assert r.total == Decimal("0")
        assert r.competencias == ()
