# Changelog

## 0.1.0

Primeira versão.

- Tabelas dos Anexos I a V da LC 123/2006 (redação da LC 155/2016), transcritas da lei e verificadas contra uma segunda transcrição independente em `tests/test_tabelas.py`.
- `aliquota_efetiva` pela fórmula do art. 18, § 1º, em `Decimal` exato e sem arredondamento.
- `das_devido`, com arredondamento a centavos meio-para-cima.
- `fator_r` e `anexo_por_fator_r`, com o limite de 28% inclusivo no Anexo III conforme o § 5º-M.
- `rbt12_proporcional` para empresa com menos de treze meses (art. 18, § 2º).
- Sinalização de `icms_iss_fora_do_das` e `acima_do_limite`.
- Ressalvas setoriais para bebidas alcoólicas, com fundamento legal.
- `float` é recusado com `TypeError` em vez de arredondado em silêncio.

Não incluído: repartição do DAS por tributo, enquadramento de CNAE, sublimites estaduais.
