# Changelog

## 0.2.0

- `carga_fora_do_das` responde o que a alíquota do anexo **não** cobre, e em que direção. O Anexo IV não abrange a CPP: ela é recolhida à parte, a 20% sobre a folha mais RAT, o que faz o anexo parecer mais barato do que é.
- `TRIBUTOS_NO_DAS` lista, por anexo, os tributos abrangidos.
- `PosicaoNaCadeia` decide a direção do efeito na segregação de receitas: produzir e revender o mesmo produto monofásico tem consequências opostas — para quem produz a carga sobe, para quem revende segregar reduz o DAS, e não segregar gera indébito recuperável.
- Ressalvas setoriais ampliadas: bebidas frias, medicamentos, cosméticos, autopeças e pneus, combustíveis. Cada uma com fundamento legal.
- `Apuracao.aliquota_arredondada` para exibição, a duas casas meio-para-cima. `aliquota_efetiva` continua exata.

Continua fora de escopo: repartição do DAS por tributo, enquadramento de CNAE e sublimites estaduais. Sem a repartição, `carga_fora_do_das` diz o que falta somar ou subtrair, mas não quantifica.

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
