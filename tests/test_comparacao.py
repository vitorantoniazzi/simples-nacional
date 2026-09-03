"""Carga total por anexo, e a CPP que o Anexo IV deixa de fora."""

from __future__ import annotations

from decimal import Decimal

import pytest

from simples_nacional import (
    CPP_ALIQUOTA_PCT,
    FAP_MAXIMO,
    RAT_MAXIMO_PCT,
    RAT_MINIMO_PCT,
    Anexo,
    comparar_anexos,
    cpp_fora_do_das,
)


class TestCppForaDoDas:
    def test_vinte_por_cento_mais_rat_minimo(self) -> None:
        # 20% + 1% de RAT com FAP neutro = 21%
        assert cpp_fora_do_das(Decimal("50000")) == Decimal("10500.00")

    def test_rat_maximo_com_fap_agravado(self) -> None:
        # 20% + 3% x 1.5 = 24,5%
        assert cpp_fora_do_das(Decimal("50000"), rat_pct=3, fap="1.5") == Decimal("12250.00")

    def test_fap_reduzido_diminui_a_contribuicao(self) -> None:
        cheio = cpp_fora_do_das(Decimal("50000"), rat_pct=3, fap=1)
        reduzido = cpp_fora_do_das(Decimal("50000"), rat_pct=3, fap="0.5")
        assert reduzido < cheio

    def test_folha_zero_devolve_zero(self) -> None:
        assert cpp_fora_do_das(0) == Decimal("0.00")

    @pytest.mark.parametrize("rat", ["0.9", "3.1", "0", "5"])
    def test_rat_fora_da_faixa_legal_e_recusado(self, rat: str) -> None:
        with pytest.raises(ValueError, match="rat_pct"):
            cpp_fora_do_das(Decimal("50000"), rat_pct=rat)

    @pytest.mark.parametrize("fap", ["0.4", "2.1"])
    def test_fap_fora_da_faixa_e_recusado(self, fap: str) -> None:
        with pytest.raises(ValueError, match="fap"):
            cpp_fora_do_das(Decimal("50000"), fap=fap)

    def test_folha_negativa_e_recusada(self) -> None:
        with pytest.raises(ValueError, match="negativa"):
            cpp_fora_do_das(Decimal("-1"))

    def test_os_limites_legais_sao_os_declarados(self) -> None:
        assert Decimal("20") == CPP_ALIQUOTA_PCT
        assert Decimal("1") == RAT_MINIMO_PCT
        assert Decimal("3") == RAT_MAXIMO_PCT
        assert Decimal("2.0") == FAP_MAXIMO


class TestCompararAnexos:
    def test_devolve_os_cinco_anexos(self) -> None:
        linhas = comparar_anexos(Decimal("1000000"), Decimal("80000"))
        assert [c.anexo for c in linhas] == list(Anexo)

    def test_so_o_anexo_iv_tem_cpp_fora_do_das(self) -> None:
        linhas = comparar_anexos(Decimal("1000000"), Decimal("80000"), folha=Decimal("30000"))
        for c in linhas:
            tem = c.cpp_fora_do_das > 0
            assert tem is (c.anexo is Anexo.IV), c.anexo

    def test_a_armadilha_do_anexo_iv_se_inverte_com_a_folha(self) -> None:
        """Pela alíquota o IV é mais barato que o III; pela carga, não é."""
        por_anexo = {
            c.anexo: c
            for c in comparar_anexos(Decimal("1000000"), Decimal("80000"), folha=Decimal("30000"))
        }
        iv, iii = por_anexo[Anexo.IV], por_anexo[Anexo.III]
        assert iv.das < iii.das
        assert iv.carga_total > iii.carga_total

    def test_sem_folha_a_ilusao_permanece(self) -> None:
        # Sem folha informada não há CPP a somar, e o IV segue parecendo barato.
        por_anexo = {c.anexo: c for c in comparar_anexos(Decimal("1000000"), Decimal("80000"))}
        assert por_anexo[Anexo.IV].carga_total < por_anexo[Anexo.III].carga_total

    def test_carga_como_percentual_da_receita(self) -> None:
        receita = Decimal("80000")
        por_anexo = {
            c.anexo: c for c in comparar_anexos(Decimal("1000000"), receita, folha=Decimal("30000"))
        }
        # Nos anexos sem CPP por fora, a carga percentual é a própria alíquota.
        assert (
            por_anexo[Anexo.III].carga_pct_da_receita(receita)
            == por_anexo[Anexo.III].aliquota_efetiva_pct
        )
        # No IV, é maior.
        assert (
            por_anexo[Anexo.IV].carga_pct_da_receita(receita)
            > por_anexo[Anexo.IV].aliquota_efetiva_pct
        )

    def test_receita_zero_nao_divide_por_zero(self) -> None:
        (c,) = [x for x in comparar_anexos(Decimal("1000000"), Decimal("0")) if x.anexo is Anexo.I]
        assert c.carga_pct_da_receita(Decimal("0")) == Decimal("0")
