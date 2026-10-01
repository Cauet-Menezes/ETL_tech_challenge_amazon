# Especificação de regras do ETL

Regras de negócio e de tratamento de dados definidas para o pipeline. A estrutura das tabelas está no `DER.jpeg`; as regras de código e de engenharia (idempotência, validações, formato de exportação) estão no `.claude/CLAUDE.MD`.

Cada regra tem um **status**: `implementada` (existe no código e em teste), `acordada` (decidida, ainda sem código) ou `em aberto` (precisa de decisão).

## 1. Entrada

- Arquivo: `data/raw/amazon.csv` (Amazon Sales Dataset), 1465 linhas e 16 colunas, com 1351 `product_id` únicos.
- Lido com todas as colunas como texto (`extract_raw_amazon`), sem alterar valores. Caminhos configuráveis pelas variáveis de ambiente `ETL_RAW_CSV_PATH` e `ETL_OUTPUT_DIR`.

## 2. Produtos (`fato_produto`) — `src/transform_produtos.py`

### 2.1 Limpeza e tipagem — implementada
| Campo bruto | Regra | Resultado |
|---|---|---|
| `actual_price`, `discounted_price` | remove `₹` e separador de milhar (`₹1,099`) | número |
| `discount_percentage` → `discount_pct` | remove `%` (`64%`) | número (64) |
| `rating_count` | remove separador de milhar (`24,269`) | inteiro (`Int64`) |
| `rating` | converte para número; valor inválido (ex.: `\|`) vira nulo | número |
| `about_product` | quebras de linha viram um espaço | texto |

### 2.2 Duplicatas — implementada
- O bruto repete `product_id` (114 linhas repetidas). Fica **a primeira ocorrência** de cada produto.
- Para `rating_count`, que difere entre as repetições em 31 produtos, vale a primeira ocorrência. **Em aberto:** usar o maior valor.

### 2.3 Nulos — implementada
- `rating_count` nulo vira **0** (constante `MISSING_RATING_COUNT`); `receita_proxy` desses produtos fica 0.
- `rating` inválido (1 produto, `B08L12N5H1`) **permanece nulo** em `fato_produto`, mas recebe a faixa de rating **"Sem avaliação"** e o quadrante **"Sem dados"** (seção 4), para nenhum FK ficar nulo.

### 2.4 Campos derivados — implementada
| Campo | Regra |
|---|---|
| `discount_amount` | `actual_price - discounted_price` |
| `receita_proxy` | `discounted_price × rating_count` |
| `qtd_reviews_amostra` | quantidade de reviews do produto em `fato_review` (calculada em `transform_reviews`, merge no `build_gold`) |

### 2.5 Marca (`marca`) — implementada
Aplicada nesta ordem, sobre `product_name`:
1. Remove prefixos de marketing: `Amazon Brand - ` e `Newly Launched ` (ex.: `Amazon Brand - Solimo ...` → `SOLIMO`; `Newly Launched Boult ...` → `BOULT`).
2. Marca composta: se o nome começa com uma marca da lista `COMPOSITE_BRANDS` (`src/config.py`), ela inteira é a marca (ex.: `WESTERN DIGITAL`, `TATA SKY`, `EUREKA FORBES`, `HOUSE OF QUIRK`). Caso contrário, a marca é a **primeira palavra**. A lista foi montada a partir dos nomes reais do dataset; marca composta que não estiver nela continua cortada na primeira palavra, e a correção é acrescentá-la à lista.
3. Unifica grafias da mesma marca (`BRAND_ALIASES`): `AmazonBasics`, `Amazonbasics` e `Amazon Basics` → `AMAZON BASICS`; `Black + Decker` → `BLACK+DECKER`. "Amazon" no início do nome indica marca própria da Amazon (AmazonBasics, Solimo), não o site.
4. Remove `®`, `™` e pontuação no fim da palavra (`ZEBRONICS,` → `ZEBRONICS`).
5. Converte tudo para **maiúsculas** (inclui siglas: `HP`, `LG`, `JBL`).
6. Marca ausente vira **`SEM MARCA`** quando a primeira palavra é: uma palavra genérica da lista `GENERIC_BRAND_WORDS` (ex.: `PORTABLE`, `USB`, `REMOTE`, `LINT`, `UNIVERSAL`), uma letra solta (`C`, `T`) ou um número (`4`). Siglas curtas reais (`HP`, `LG`, `3M`, `MI`) são mantidas.

## 3. Reviews e usuários — `src/transform_reviews.py` (implementada)
- No bruto, `user_id`, `user_name`, `review_id`, `review_title` e `review_content` são **listas separadas por vírgula** no mesmo campo. Só `user_id`, `user_name` e `review_id` são explodidos (uma linha por review); título e texto ficam fora, como no DER.
- `user_id` e `review_id` sempre têm o mesmo número de itens, então o alinhamento é por posição.
- **Nomes:** a vírgula só separa nomes quando **não** é seguida de espaço (`Ganesh, Tamilnadu` é um nome só). Se a quantidade de nomes não bate com a de ids, descartam-se os tokens vazios (nas linhas alinhadas nunca há nome vazio, então o vazio é lixo da origem); isso resolve `B07MKMFKPG`. Os 4 produtos restantes (`B08Y1TFSP6`, `B08Y1SJVV5`, `B08Y5KXR6Z`, `B07T9FV9YP`) têm nomes a mais por causa de nomes com vírgula sem espaço (ex.: `Pradeep,Tcr`, que é o nome real da conta, vira dois tokens) e não dá para alinhar por regra; nesses casos os nomes da linha são descartados.
- **Correções manuais (`USER_NAME_CORRECTIONS` em `src/config.py`):** tabela `user_id` → nome, informada pelo usuário, que **prevalece** sobre o nome do bruto. Cobre os 8 usuários de `B07T9FV9YP` (Redgear Cloak, informados pelo usuário) e os 7 usuários dos produtos pTron (incluindo `Ibn moosa`, nome que aparece na avaliação `RFF7U7MPQFUGR`, confirmado pelo usuário) (inclui `Placeholder`, que é o nome real da conta `AF7NDY2H6JVYTSQOZP76GCATQ34Q`, confirmado pelo usuário), confirmados no perfil da Amazon (`amazon.in/gp/profile/amzn1.account.<user_id>`, título da página = nome). Ordem de resolução do nome: correção manual → nome alinhado do bruto → nome do mesmo `user_id` em outro review → **`SEM NOME`**.
- Nas linhas de `product_id` repetido, os reviews são **unidos** e depois deduplicados.
- `dim_usuario`: `id_usuario` inteiro sequencial a partir de 1, ordenado por `user_id` (estável entre execuções); `user_id` (origem) e `user_name`. 9050 usuários.
- `fato_review`: `review_id`, `id_produto`, `id_usuario`, **uma linha por `(review_id, id_produto)`** (10605 linhas). Um mesmo `review_id` aparece em até 8 produtos (761 casos, quase sempre variações do mesmo produto), então `review_id` sozinho **não é único**; a chave é composta. Decisão do usuário, para manter o review em cada produto e o `qtd_reviews_amostra` correto.
- `qtd_reviews_amostra` = reviews de `fato_review` por produto (`count_reviews_per_product`); o merge em `fato_produto` é feito no `build_gold`.

## 4. Dimensões e FKs — `src/build_gold.py` (implementada)
As dimensões são criadas primeiro e os FKs são levados à fato por merge. Ids substitutos são inteiros sequenciais a partir de 1. As constantes estão em `src/config.py`.

- **`dim_categoria`:** **uma linha por `category_path`** (211 linhas, `id_categoria` sequencial ordenado pelo caminho; `categoria_folha` não serve de chave porque 4 folhas aparecem em caminhos diferentes). `category` é separada por `|` e tem de 2 a 7 níveis. `nivel_1` a `nivel_3` recebem os três primeiros níveis; em caminhos de 2 níveis (4 caminhos, 8 produtos) **`nivel_3` repete o último nível**. `categoria_folha` é o último nível e `category_path` o caminho completo.
- **Faixas** (`dim_faixa_preco`, `dim_faixa_desconto`, `dim_faixa_rating`): colunas `faixa`, mínimo, máximo e `ordem` (o id é igual à ordem). Intervalos **[mín, máx)**; a última faixa não tem teto (máximo vazio). Nenhum produto fica fora das faixas.
  - **Preço**, sobre `discounted_price`: 0–199, 200–499, 500–999, 1.000–1.999, 2.000–4.999, 5.000+ (159, 342, 237, 262, 148, 203 produtos).
  - **Desconto**, sobre `discount_pct`: 0–9%, 10–24%, 25–39%, 40–54%, 55–69%, 70%+ (72, 156, 250, 337, 325, 211).
  - **Rating**, sobre o `rating` arredondado a 1 casa: abaixo de 3,5; 3,5 a 3,9; 4,0 a 4,1; 4,2 a 4,4; 4,5 a 5,0 (41, 299, 384, 530, 96), mais a 6ª faixa **"Sem avaliação"** (mín/máx vazios) para `rating` nulo (1 produto).
  - No Power BI, ordenar `faixa` pela coluna `ordem` ("Classificar por coluna").
- **`dim_quadrante`:** 5 linhas (decisão do usuário: a 5ª cobre o `rating` nulo). Engajamento alto quando `rating_count` > mediana (4736, calculada na execução); satisfação alta quando `rating` ≥ 4,0.

  | Quadrante | Engajamento | Satisfação | Ação sugerida | Produtos |
  |---|---|---|---|---|
  | Estrelas | Alto | Alta | Manter e destacar | 563 |
  | Promessas | Baixo | Alta | Divulgar mais | 447 |
  | Problemáticos | Alto | Baixa | Corrigir qualidade | 112 |
  | Descartáveis | Baixo | Baixa | Revisar ou descontinuar | 228 |
  | Sem dados | Indefinido | Indefinida | Coletar avaliações | 1 |
- **`fato_produto`:** recebe `id_categoria`, `id_faixa_*`, `id_quadrante` e `qtd_reviews_amostra` (0 se o produto não tem review), na ordem de colunas do DER.
- **Validações** (`validate_gold_tables`, antes de exportar; reúne todos os erros num `ValueError`): PK única em cada tabela, FK de `fato_produto` e de `fato_review` existentes no destino, nenhum nulo em `fato_produto` exceto `rating`, ids substitutos inteiros.
- **Exportação** (`export_gold_tables`): um CSV por tabela em `saida_bi/`, `utf-8-sig`, `index=False`, `decimal=","`, sobrescrevendo. O `main.py` roda o fluxo todo.

## 5. Termos e temas — (acordada, não implementada)
- `fato_termo_produto`: unigramas e bigramas extraídos de `about_product` e dos reviews, com `frequencia` por produto. PK `(id_produto, termo)`.
- `dim_tema`: mapa de palavras-chave para temas (ex.: bateria, cabo, preço); define o `id_tema` de cada termo.
- `sentimento` e `score_sentimento`: exigem um léxico. **Em aberto:** usar `vaderSentiment` (dependência nova, precisa de aprovação) ou um léxico pequeno feito à mão.

## 6. Mapa DER → código
| Tabela | Onde | Status |
|---|---|---|
| `fato_produto` (colunas de produto, `marca`, derivados) | `transform_produtos.py` | implementada |
| `fato_produto` (FKs e merge de `qtd_reviews_amostra`) | `build_gold.py` | implementada |
| `fato_review`, `dim_usuario`, contagem de reviews | `transform_reviews.py` | implementada |
| `dim_categoria`, `dim_faixa_*`, `dim_quadrante` | `build_gold.py` | implementada |
| `fato_termo_produto`, `dim_tema` | a definir | acordada |

## 7. Pendências para revisar depois
Nenhuma pendência de nomes: todos os usuários de `dim_usuario` têm nome (`SEM NOME` fica só como fallback para casos futuros).
