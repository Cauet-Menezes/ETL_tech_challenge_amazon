# ETL_tech_challenge_amazon
Dashboard em Power BI que analisa produtos, preços, descontos e avaliações de clientes na Amazon Sales Dataset, investigando a relação Preço → Desconto → Engajamento → Satisfação e gerando recomendações para o negócio.

Este repositório contém o **ETL em Python (pandas)** que trata o dataset bruto e gera os CSVs de um modelo estrela (`saida_bi/`), que são carregados no Power BI. Não há carga em banco de dados.

## Como executar
```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt   # Windows; no Linux/macOS: .venv/bin/python
.venv/Scripts/python main.py          # gera os CSVs em saida_bi/
.venv/Scripts/python -m pytest -q     # testes
.venv/Scripts/python -m ruff check .  # lint
```
Variáveis de ambiente opcionais: `ETL_RAW_CSV_PATH` (padrão `data/raw/amazon.csv`) e `ETL_OUTPUT_DIR` (padrão `saida_bi/`). A execução é idempotente: rodar duas vezes sobrescreve os mesmos arquivos.

## Pipeline
```
data/raw/amazon.csv
   └─ extract.py ──► transform_produtos.py ──┐
                 └─► transform_reviews.py ───┼─► build_gold.py ──► validações ──► saida_bi/*.csv
                                             │   (dimensões, FKs)
                                      main.py orquestra
```
| Módulo | Função |
|---|---|
| `src/config.py` | constantes, caminhos, nomes de colunas, faixas, quadrantes e correções manuais |
| `src/extract.py` | lê o CSV bruto com todas as colunas como texto |
| `src/transform_produtos.py` | limpeza, tipagem, duplicatas, marca e campos derivados |
| `src/transform_reviews.py` | explode as listas de usuários/reviews e gera `dim_usuario` e `fato_review` |
| `src/build_gold.py` | dimensões, FKs em `fato_produto`, validações e exportação |
| `main.py` | executa o fluxo completo |

## Modelo de dados (`saida_bi/`)
Definido no `DER.jpeg`. Os relacionamentos (PK/FK) são criados no Power BI.

| Tabela | Linhas | Status |
|---|---|---|
| `fato_produto` | 1351 | pronta |
| `fato_review` | 10605 | pronta |
| `dim_usuario` | 9050 | pronta |
| `dim_categoria` | 211 | pronta |
| `dim_faixa_preco`, `dim_faixa_desconto` | 6 cada | pronta |
| `dim_faixa_rating` | 6 | pronta |
| `dim_quadrante` | 5 | pronta |
| `fato_termo_produto`, `dim_tema` | — | pendente |

Formato dos CSVs: `utf-8-sig`, separador decimal `,`, sem índice. No Power BI, ordene `faixa` pela coluna `ordem` nas dimensões de faixa.

## Regras de negócio resumidas
Detalhes e status de cada regra em `.claude/spec/ESPECIFICACAO.md` (pasta ignorada pelo git) e no histórico em [`docs/CONSTRUCAO.md`](docs/CONSTRUCAO.md).
- **Duplicatas:** o bruto repete `product_id` (1465 linhas, 1351 únicos); fica a primeira ocorrência.
- **Nulos:** `rating_count` nulo vira 0; `rating` inválido (1 produto) segue nulo, com faixa "Sem avaliação" e quadrante "Sem dados".
- **Marca:** extraída do nome do produto, em maiúsculas, com marcas compostas, aliases e `SEM MARCA`.
- **Faixas** (intervalos `[mín, máx)`): preço sobre `discounted_price`; desconto sobre `discount_pct`; rating arredondado a 1 casa.
- **Quadrantes:** engajamento alto = `rating_count` acima da mediana; satisfação alta = `rating` ≥ 4,0 (Estrelas, Promessas, Problemáticos, Descartáveis, Sem dados).
- **Reviews:** `fato_review` tem chave composta `(review_id, id_produto)`.

## Pendências
- `fato_termo_produto` e `dim_tema` (unigramas/bigramas, temas e sentimento). O sentimento exige um léxico; usar `vaderSentiment` depende de aprovação (dependência nova).
- Versionar `data/raw/amazon.csv` e `saida_bi/` no git.
- Em aberto: usar o maior `rating_count` entre produtos duplicados (hoje vale a primeira ocorrência); marcas compostas fora da lista `COMPOSITE_BRANDS` são cortadas na primeira palavra.
