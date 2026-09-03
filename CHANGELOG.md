# Changelog

## 0.4.0

**Carga total, não alíquota.** `comparar_anexos` põe os cinco anexos lado a lado somando o que fica fora do DAS, e `cpp_fora_do_das` quantifica a contribuição patronal do Anexo IV: 20% sobre a folha mais o RAT do grau de risco, ajustado pelo FAP. Para RBT12 de R$ 1 mi, receita de R$ 80 mil e folha de R$ 30 mil, o Anexo IV mostra 10,02% de alíquota contra 12,44% do Anexo III — e carga total de 17,90% contra 12,44%. A comparação por alíquota inverte o resultado.

**Indébito acumulado.** `indebito_por_segregacao` recebe uma lista de competências e devolve, mês a mês, quanto se pagou a mais por não segregar receita monofásica ou com ICMS-ST, separando o que ainda está no prazo do art. 168 do CTN do que já prescreveu. A contagem usa o vencimento do DAS — dia 20 do mês seguinte — como referência do pagamento; quem pagou em atraso tem prazo contado da data efetiva. Pedido administrativo não interrompe o prazo (Súmula 625 do STJ).

**`percentual_segregavel` e `das_com_segregacao`** expõem a matemática da segregação, que antes vivia no servidor MCP. O cálculo pertence à biblioteca; o MCP é interface.

## 0.3.0

- `REPARTICAO` traz a segunda tabela de cada anexo, a de "Percentual de Repartição dos Tributos", que diz quanto de cada faixa pertence a cada tributo.
- `das_por_tributo` divide o DAS do mês entre IRPJ, CSLL, COFINS, PIS/PASEP, CPP, IPI, ICMS e ISS. É o que permite quantificar segregação de receita em vez de apenas apontá-la: a parcela monofásica de um DAS é a soma de PIS e COFINS, e agora ela tem número.
- `Tributo` passou a viver em `tabelas.py`, junto da lei. Antes `TRIBUTOS_NO_DAS` usava strings próprias, e dois módulos chamavam o mesmo tributo de nomes diferentes; o teste de coerência entre a repartição e os tributos por anexo pegou a divergência. Isto é uma quebra de API em relação à 0.2.0: `TRIBUTOS_NO_DAS` agora contém membros de `Tributo`, não strings.

A ausência de ICMS e de ISS na 6ª faixa de todos os anexos está fixada como propriedade esperada nos testes. Não é falha de transcrição: a 6ª faixa começa acima do sublimite, onde esses dois deixam de ser recolhidos no DAS — é a explicação estrutural da queda da alíquota ao cruzar essa linha.

As parcelas de `das_por_tributo` são arredondadas a centavos individualmente, então a soma delas pode divergir de `das_devido` em alguns centavos. A deriva é limitada, testada, e o total a recolher é o de `das_devido`.

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
