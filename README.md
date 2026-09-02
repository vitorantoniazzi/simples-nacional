# simples-nacional

Cálculo do Simples Nacional a partir das tabelas legais. Sem dependências, tipado, e testado contra a lei em vez de contra si mesmo.

```bash
pip install simples-nacional-complexo
```

O pacote se instala como `simples-nacional-complexo` e se importa como `simples_nacional`. O sufixo existe porque `simplesnacional` no PyPI já pertence a [outro projeto](https://pypi.org/project/simplesnacional/), de propósito diferente — e porque o nome diz a tese: a alíquota do Simples não conta a história toda.

## Por que existe

A fórmula da alíquota efetiva é uma linha. O que dá errado está em volta dela: usar `float` para dinheiro, esquecer que o Fator R decide entre dois anexos com quase 10 pontos de diferença, tratar o RBT12 de uma empresa de três meses como se fosse anual, e assumir que a efetiva é a carga tributária total quando o setor recolhe ICMS-ST e IPI fora do DAS.

Esta biblioteca cuida dessas quatro coisas e recusa entrada ambígua em vez de arredondar em silêncio.

## Uso

```python
from decimal import Decimal
from simples_nacional import Anexo, aliquota_efetiva, das_devido

ap = aliquota_efetiva(Decimal("1200000"), Anexo.II)

ap.faixa.numero  # 4
ap.aliquota_nominal  # Decimal('11.20')
ap.aliquota_efetiva  # Decimal('9.33')

das_devido(Decimal("100000"), ap)  # Decimal('9330.00')
```

### Fator R

Atividades do § 5º-I são tributadas pelo Anexo III quando a folha de doze meses representa 28% ou mais da receita, e pelo Anexo V abaixo disso. O limite é inclusivo no Anexo III.

```python
from simples_nacional import anexo_por_fator_r, fator_r

fator_r(Decimal("28000"), Decimal("100000"))  # Decimal('0.28')
anexo_por_fator_r(Decimal("28000"), Decimal("100000"))  # Anexo.III
anexo_por_fator_r(Decimal("27999"), Decimal("100000"))  # Anexo.V
```

Para uma empresa de serviços na faixa 3, isso é a diferença entre 13,5% e 19,5% nominais. Errar o Fator R custa mais que errar a fórmula.

### Empresa com menos de treze meses

Não existe RBT12 real antes de doze meses fechados. O art. 18, § 2º manda proporcionalizar:

```python
from simples_nacional import rbt12_proporcional

rbt12 = rbt12_proporcional(Decimal("90000"), meses_de_atividade=3)  # Decimal('360000')
aliquota_efetiva(rbt12, Anexo.I).faixa.numero  # 2
```

### Quando o DAS não é a carga total

```python
from simples_nacional import ressalvas_de

(r,) = ressalvas_de("bebidas_alcoolicas")
r.tributos_fora_do_das  # ('ICMS-ST', 'IPI')
r.condicoes  # produção própria no atacado, registro no MAPA, ...
r.fundamentos  # ('LC 123/2006, art. 17, X, "c", ...', 'Resolução CGSN nº 140/2018, art. 12')
```

Uma microcervejaria no Anexo II com efetiva de 9% não tem carga de 9%: ICMS-ST e IPI são recolhidos fora do DAS. Modelar o negócio pela efetiva subestima o custo.

## O degrau do sublimite

Atravessar R$ 3.600.000 **reduz** a alíquota efetiva do DAS. Em todos os cinco anexos:

| Anexo | No teto da 5ª faixa | Centavo seguinte |
| --- | --- | --- |
| I | 11,875% | 8,500% |
| II | 12,325% | 10,000% |
| III | 17,510% | 15,000% |
| IV | 16,895% | 10,000% |
| V | 21,275% | 15,500% |

Não é erro de tabela. Acima do sublimite, ICMS e ISS deixam de ser recolhidos no DAS, então a alíquota da 6ª faixa cobre menos tributos que a da 5ª. A carga total não cai — ela se reparte, e o que sai do DAS passa a ser apurado fora.

Quem usa a efetiva como carga total conclui que faturar mais barateia o imposto. É por isso que `Apuracao` carrega `icms_iss_fora_do_das`: a queda vem sempre acompanhada da bandeira que a explica.

`tests/test_aliquota.py` fixa esse degrau como propriedade esperada, para que ninguém o "conserte" achando que é bug.

## A armadilha do Anexo IV

```python
from simples_nacional import Anexo, aliquota_efetiva, carga_fora_do_das

rbt12 = Decimal("1000000")

aliquota_efetiva(rbt12, Anexo.III).aliquota_arredondada   # Decimal('12.44')
aliquota_efetiva(rbt12, Anexo.IV).aliquota_arredondada    # Decimal('10.02')  parece melhor

carga_fora_do_das(Anexo.III)   # ()
carga_fora_do_das(Anexo.IV)    # (ItemForaDoDAS(tributo='CPP', efeito=ACRESCENTA, ...),)
```

O DAS do Anexo IV não abrange a contribuição patronal: são 20% sobre a folha, mais RAT de 1% a 3%, recolhidos à parte. Comparar anexos pela alíquota efetiva subestima a carga de quem tem folha.

## Segregação de receitas: a direção depende da cadeia

```python
from simples_nacional import PosicaoNaCadeia, carga_fora_do_das

# cervejaria: é ela quem recolhe o concentrado
carga_fora_do_das(Anexo.II, receita_monofasica=True, receita_com_icms_st=True,
                  posicao=PosicaoNaCadeia.PRODUTOR)
# PIS/COFINS: ACRESCENTA · ICMS-ST: ACRESCENTA

# bar que revende a mesma cerveja: já foi tributada antes
carga_fora_do_das(Anexo.I, receita_monofasica=True, receita_com_icms_st=True,
                  posicao=PosicaoNaCadeia.REVENDEDOR)
# PIS/COFINS: REDUZ · ICMS-ST: REDUZ
```

Mesmo produto, lados opostos da cadeia, efeitos opostos. Para quem revende, não segregar é pagar a mais — e o indébito é recuperável. É essa a razão de existir a indústria de recuperação de PIS/COFINS monofásico.

## Sinalizações

`Apuracao` marca as duas fronteiras que mudam o regime, em vez de deixar passar:

| Campo | Significado |
| --- | --- |
| `icms_iss_fora_do_das` | RBT12 acima de R$ 3.600.000: ICMS e ISS saem do DAS |
| `acima_do_limite` | RBT12 acima de R$ 4.800.000: a empresa está fora do Simples |

## `Decimal`, não `float`

Passar `float` levanta `TypeError`. Isso é deliberado:

```python
aliquota_efetiva(180000.0, Anexo.II)
# TypeError: rbt12 recebeu float, que não representa dinheiro exatamente.
```

Aceite `Decimal`, `int` ou `str`.

## O que não faz

- **Repartição por tributo.** Os anexos quebram o DAS em IRPJ, CSLL, PIS, COFINS, CPP, ICMS e ISS. Não está aqui ainda, porque são 210 percentuais e publicar tabela fiscal meio conferida é pior que não publicar. Planejado para a 0.2.
- **Enquadramento de atividade.** Descobrir o anexo de um CNAE é decisão contábil, não aritmética.
- **Sublimite estadual.** Alguns estados adotam sublimite próprio; aqui só o federal de R$ 3,6 mi.

## Fonte das tabelas

Anexos I a V da [LC 123/2006](https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp123.htm), na redação da [LC 155/2016](https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp155.htm), vigente desde 01/01/2018. As tabelas estão em `tabelas.py` como transcrição da lei, e `tests/test_tabelas.py` as compara com uma segunda transcrição independente — se divergirem, o teste quebra.

## Não é assessoria fiscal

Calcula o que a lei publica. Enquadramento, regime, obrigações acessórias e planejamento são decisões de contador.

## Licença

MIT
