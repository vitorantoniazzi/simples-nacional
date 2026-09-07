"""Lucro Presumido e a comparação entre regimes.

Como nas tabelas dos anexos, os números abaixo são uma transcrição
independente da lei: Lei 9.249/1995 arts. 15 e 20, Lei 9.430/1996 arts. 1º e
25. Se divergirem do pacote, é isso que se quer descobrir.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from simples_nacional import (
    ADICIONAL_IRPJ_PCT,
    ALIQUOTA_CSLL_PCT,
    ALIQUOTA_IRPJ_PCT,
    COFINS_CUMULATIVO_PCT,
    LIMITE_ADICIONAL_TRIMESTRAL,
    LIMITE_MAJORACAO_LC224_ANUAL,
    PIS_CUMULATIVO_PCT,
    PRESUNCAO,
    Anexo,
    AtividadePresumido,
    comparar_regimes,
    lucro_presumido,
)


class TestConstantesLegais:
    def test_aliquotas_transcritas(self) -> None:
        assert Decimal("15") == ALIQUOTA_IRPJ_PCT
        assert Decimal("10") == ADICIONAL_IRPJ_PCT
        assert Decimal("9") == ALIQUOTA_CSLL_PCT
        assert Decimal("0.65") == PIS_CUMULATIVO_PCT
        assert Decimal("3") == COFINS_CUMULATIVO_PCT
        assert Decimal("60000") == LIMITE_ADICIONAL_TRIMESTRAL
        assert Decimal("5000000") == LIMITE_MAJORACAO_LC224_ANUAL

    def test_a_presuncao_da_csll_difere_da_do_irpj_no_comercio(self) -> None:
        # Erro fácil: assumir 8% nos dois. A CSLL presume 12%.
        p = PRESUNCAO[AtividadePresumido.COMERCIO_INDUSTRIA]
        assert p["irpj"] == Decimal("8")
        assert p["csll"] == Decimal("12")

    def test_em_servicos_as_duas_presuncoes_coincidem(self) -> None:
        p = PRESUNCAO[AtividadePresumido.SERVICOS]
        assert p["irpj"] == p["csll"] == Decimal("32")


class TestApuracao:
    def test_servicos_no_trimestre(self) -> None:
        r = lucro_presumido(Decimal("240000"), AtividadePresumido.SERVICOS)
        assert r.base_irpj == Decimal("76800.00")
        assert r.irpj == Decimal("11520.00")
        # (76.800 - 60.000) x 10%
        assert r.adicional_irpj == Decimal("1680.00")
        assert r.base_csll == Decimal("76800.00")
        assert r.csll == Decimal("6912.00")
        assert r.pis == Decimal("1560.00")
        assert r.cofins == Decimal("7200.00")
        assert r.federais == Decimal("28872.00")

    def test_comercio_usa_as_duas_presuncoes_distintas(self) -> None:
        r = lucro_presumido(Decimal("240000"), AtividadePresumido.COMERCIO_INDUSTRIA)
        assert r.base_irpj == Decimal("19200.00")  # 8%
        assert r.base_csll == Decimal("28800.00")  # 12%
        assert r.csll == Decimal("2592.00")

    def test_sem_exceder_o_limite_nao_ha_adicional(self) -> None:
        # 8% de 240k = 19.200, abaixo de 60.000
        r = lucro_presumido(Decimal("240000"), AtividadePresumido.COMERCIO_INDUSTRIA)
        assert r.adicional_irpj == Decimal("0.00")

    def test_o_adicional_incide_so_sobre_o_excedente(self) -> None:
        # base exatamente no limite: nada de adicional
        no_limite = lucro_presumido(Decimal("187500"), AtividadePresumido.SERVICOS)
        assert no_limite.base_irpj == Decimal("60000.00")
        assert no_limite.adicional_irpj == Decimal("0.00")

    def test_a_patronal_entra_sempre_no_presumido(self) -> None:
        # Diferente do Simples, onde só o Anexo IV a deixa fora do DAS.
        r = lucro_presumido(
            Decimal("240000"),
            AtividadePresumido.SERVICOS,
            folha_trimestral=Decimal("90000"),
        )
        assert r.cpp_sobre_folha > 0
        assert r.total == r.federais + r.iss + r.cpp_sobre_folha

    def test_receita_negativa_e_recusada(self) -> None:
        with pytest.raises(ValueError, match="negativa"):
            lucro_presumido(Decimal("-1"), AtividadePresumido.SERVICOS)


class TestIssNaoArbitrado:
    def test_sem_aliquota_o_iss_fica_de_fora_e_isso_e_declarado(self) -> None:
        r = lucro_presumido(Decimal("240000"), AtividadePresumido.SERVICOS)
        assert r.iss == Decimal("0.00")
        assert r.iss_arbitrado is False

    def test_com_aliquota_o_iss_entra(self) -> None:
        r = lucro_presumido(Decimal("240000"), AtividadePresumido.SERVICOS, iss_pct=5)
        assert r.iss == Decimal("12000.00")
        assert r.iss_arbitrado is True

    @pytest.mark.parametrize("taxa", ["-1", "5.1", "10"])
    def test_aliquota_fora_da_faixa_legal_e_recusada(self, taxa: str) -> None:
        with pytest.raises(ValueError, match="iss_pct"):
            lucro_presumido(Decimal("240000"), AtividadePresumido.SERVICOS, iss_pct=taxa)


class TestLimiteLC224:
    def test_abaixo_do_limite_nao_sinaliza(self) -> None:
        r = lucro_presumido(Decimal("240000"), AtividadePresumido.SERVICOS)
        assert r.acima_do_limite_lc224 is False

    def test_acima_do_limite_sinaliza_que_subestima(self) -> None:
        # 1,3 mi no trimestre anualiza em 5,2 mi
        r = lucro_presumido(Decimal("1300000"), AtividadePresumido.SERVICOS)
        assert r.acima_do_limite_lc224 is True


class TestCompararRegimes:
    def test_sem_iss_o_presumido_parece_mais_barato_e_a_comparacao_se_marca_invalida(
        self,
    ) -> None:
        c = comparar_regimes(
            Decimal("240000"),
            Anexo.III,
            Decimal("960000"),
            AtividadePresumido.SERVICOS,
        )
        assert c.regime_mais_barato == "presumido"
        assert c.comparavel is False

    def test_com_iss_a_resposta_inverte(self) -> None:
        """O mesmo caso, com ISS informado, muda de vencedor.

        É a razão de `comparavel` existir: sem o ISS de uma prestadora, o
        Lucro Presumido sai subestimado e a comparação engana na direção dele.
        """
        c = comparar_regimes(
            Decimal("240000"),
            Anexo.III,
            Decimal("960000"),
            AtividadePresumido.SERVICOS,
            iss_pct=5,
        )
        assert c.regime_mais_barato == "simples"
        assert c.comparavel is True
        assert c.diferenca > 0

    def test_acima_do_limite_lc224_nao_e_comparavel_nem_com_iss(self) -> None:
        c = comparar_regimes(
            Decimal("1300000"),
            Anexo.III,
            Decimal("5200000"),
            AtividadePresumido.SERVICOS,
            iss_pct=5,
        )
        assert c.acima_do_limite_lc224 is True
        assert c.comparavel is False

    def test_no_anexo_iv_a_patronal_entra_dos_dois_lados(self) -> None:
        c = comparar_regimes(
            Decimal("240000"),
            Anexo.IV,
            Decimal("960000"),
            AtividadePresumido.SERVICOS,
            folha_trimestral=Decimal("90000"),
            iss_pct=5,
        )
        assert c.cpp_no_simples > 0
        assert c.total_simples == c.das_do_trimestre + c.cpp_no_simples

    def test_fora_do_anexo_iv_a_patronal_so_pesa_no_presumido(self) -> None:
        c = comparar_regimes(
            Decimal("240000"),
            Anexo.III,
            Decimal("960000"),
            AtividadePresumido.SERVICOS,
            folha_trimestral=Decimal("90000"),
            iss_pct=5,
        )
        assert c.cpp_no_simples == Decimal("0.00")

    def test_diferenca_positiva_quando_o_simples_ganha(self) -> None:
        c = comparar_regimes(
            Decimal("240000"),
            Anexo.III,
            Decimal("960000"),
            AtividadePresumido.SERVICOS,
            iss_pct=5,
        )
        assert c.diferenca == c.total_presumido - c.total_simples
        assert c.diferenca > 0
