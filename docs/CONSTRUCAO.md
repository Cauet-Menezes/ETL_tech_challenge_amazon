# Histórico de construção do ETL

Registro das decisões e etapas da construção do pipeline, na ordem em que aconteceram. As regras vigentes estão em `.claude/spec/ESPECIFICACAO.md`; aqui ficam o porquê e o caminho percorrido.

## 1. Preparação do projeto
- Criado o `CLAUDE.md` (contexto, modelo estrela, estilo de código, engenharia de dados, o que não fazer, fluxo).
- **Decisão:** sem banco de dados. Removidos `src/db.py` e o `.mcp.json` (Supabase); a saída são só CSVs para o Power BI.
- O `DER.jpeg` foi adotado como fonte da estrutura das tabelas.
- Criada a especificação de regras em `.claude/spec/ESPECIFICACAO.md`, apontada pelo CLAUDE.md. Em conflito: a especificação vale para dados; o CLAUDE.md, para estilo e engenharia. (A pasta `.claude` está no `.gitignore`; o usuário optou por não alterá-lo.)
- Fluxo combinado: compactar a conversa perto de 300K tokens e reler CLAUDE.md, DER e especificação depois. Foi configurada uma status line que mostra a janela de contexto e avisa em 300K.
- Stack e versões fixadas: Python 3.13, pandas 3.0.6, pytest 9.1.1, ruff 0.16.9 (`.venv`).

## 2. Extração e produtos (`config.py`, `extract.py`, `transform_produtos.py`)
- Leitura com todas as colunas como texto, para não alterar valores.
- Limpeza: `₹1,099` → número; `64%` → 64; `24,269` → inteiro anulável; `rating` inválido (`|`) → nulo; quebras de linha de `about_product` → espaço.
- Dados brutos: 1465 linhas, 1351 `product_id` únicos. **Decisão:** manter a primeira ocorrência (em aberto: usar o maior `rating_count`, que difere em 31 produtos).
- **Decisão:** `rating_count` nulo vira 0.
- Derivados: `discount_amount = actual_price - discounted_price`; `receita_proxy = discounted_price × rating_count`.

### Marca
Validou-se que "Amazon" no início do nome indica marca própria (AmazonBasics, Solimo), não o site. Regras, em ordem:
1. remove prefixos de marketing (`Amazon Brand - `, `Newly Launched `);
2. marca composta se estiver na lista `COMPOSITE_BRANDS` (32 marcas, montada a partir dos nomes reais); senão, a primeira palavra;
3. unifica grafias (`AmazonBasics`/`Amazonbasics` → AMAZON BASICS; `Black + Decker` → BLACK+DECKER);
4. remove `®`, `™` e pontuação no fim;
5. tudo em **maiúsculas** (decisão do usuário, em vez de capitalizar);
6. palavra genérica, letra solta ou número → **SEM MARCA**.

Erros corrigidos no caminho: contagens iniciais de marcas da Amazon que estavam erradas (corrigidas para 19 AmazonBasics + 4 Solimo, 48 no total depois de normalizar) e um teste que ainda esperava a marca em caixa mista.

## 3. Reviews e usuários (`transform_reviews.py`)
- No bruto, `user_id`, `user_name` e `review_id` são listas separadas por vírgula no mesmo campo; são explodidas por posição.
- Nomes com vírgula: a vírgula só separa nomes quando não é seguida de espaço.
- **Decisão:** `fato_review` tem **uma linha por `(review_id, id_produto)`**, porque um mesmo `review_id` aparece em até 8 produtos (761 casos).
- Em 5 produtos os nomes ficaram desalinhados com os ids (23 usuários afetados). A causa eram nomes com vírgula sem espaço (ex.: `Pradeep,Tcr`) e um nome vazio no `B07MKMFKPG`.
  - O usuário levantou os nomes manualmente; os perfis públicos da Amazon foram conferidos pelo navegador (título da página = nome) e o que não deu para ver foi informado pelo usuário.
  - Uma suposição minha estava errada: tratei `CM` como token sobrante, mas é o nome real de uma conta. A lista de tokens ignorados foi removida e substituída pela tabela `USER_NAME_CORRECTIONS` (15 entradas), que prevalece sobre o nome do bruto.
  - Ordem de resolução: correção manual → nome alinhado → nome do mesmo `user_id` em outro review → `SEM NOME`.
- Resultado: `dim_usuario` com 9050 usuários, nenhum `SEM NOME`; `fato_review` com 10605 linhas; todos os FKs válidos.

## 4. Camada gold (`build_gold.py`, `main.py`)
Antes de codar, a distribuição real foi analisada e a proposta foi **revisada por dois subagentes**: o primeiro criticou, o segundo recalculou os números do zero. O resultado mudou a proposta em quatro pontos:
1. **Erro corrigido:** os Descartáveis eram 228, não 229. O produto sem nota (`NaN >= 4.0` é falso) tinha sido contado como "satisfação baixa".
2. **`rating` nulo:** em vez de FK nulo com exceção na validação, o produto recebe a faixa "Sem avaliação" e o quadrante "Sem dados". Consequência aprovada pelo usuário: `dim_quadrante` com 5 linhas e `dim_faixa_rating` com 6.
3. **`dim_categoria`:** uma linha por `category_path` (211), não por folha: 4 folhas repetem em caminhos diferentes. Nos 4 caminhos de 2 níveis (8 produtos), `nivel_3` repete o último nível.
4. **Rótulos das faixas** sem ambiguidade para o Power BI (`₹0–199` em vez de `0-200`), e rating comparado já arredondado a 1 casa.

Decisões aprovadas pelo usuário ("faça"):
| Item | Decisão |
|---|---|
| Preço | sobre `discounted_price`: 0–199, 200–499, 500–999, 1.000–1.999, 2.000–4.999, 5.000+ |
| Desconto | 0–9%, 10–24%, 25–39%, 40–54%, 55–69%, 70%+ |
| Rating | <3,5; 3,5–3,9; 4,0–4,1; 4,2–4,4; 4,5–5,0; Sem avaliação |
| Quadrantes | engajamento alto = `rating_count` > mediana (4736); satisfação alta = `rating` ≥ 4,0 |

Implementação:
- Funções pequenas por dimensão, `assign_band_ids` (via `pd.cut`, intervalos `[mín, máx)`), `assign_quadrant_ids` e `assign_category_ids`; constantes nomeadas em `config.py`.
- Validações antes de exportar: PK única, FK existente, sem nulos fora de `rating`, ids inteiros; todos os erros reunidos num `ValueError`.
- Exportação de um CSV por tabela, `utf-8-sig`, `decimal=","`, sobrescrevendo (idempotente).
- Distribuição final conferida contra a proposta: faixas e quadrantes com as mesmas contagens; `qtd_reviews_amostra` soma 10605.
- Um teste meu errou o id da faixa "Sem avaliação" (6, não 5) e foi corrigido.

## 5. Qualidade
56 testes (`tests/test_transform_produtos.py`, `test_transform_reviews.py`, `test_build_gold.py`) e `ruff` sem alertas.

## 6. Versionamento
Feitos 10 commits na `main` (padrão `chore`/`docs`/`feat`), incluindo `data/raw/amazon.csv`, `DER.jpeg` e `saida_bi/`. `.idea/` e `.claude/settings.local.json` ficam de fora. O push desses commits para o remoto já foi feito.

## 7. O que falta construir

### 7.1 `fato_termo_produto` e `dim_tema` (seção 5 da especificação)
Única parte do DER ainda sem código. O que já está acordado:
- `fato_termo_produto`: unigramas e bigramas de `about_product` (e do texto das reviews, por produto), com `tipo_termo` (uni/bigrama), `frequencia`, `sentimento`, `score_sentimento` e `id_tema`. PK `(id_produto, termo)`.
- `dim_tema`: mapa de palavras-chave para temas (ex.: bateria, cabo, preço), com `id_tema`, `tema` e `descricao`.

Decisões a tomar antes de codar (propor o plano e esperar aprovação, como manda o CLAUDE.md):
1. **Texto das reviews:** o bruto traz `review_title` e `review_content` como listas por vírgula, e o texto tem vírgulas próprias (até 125 num campo). Recomendado: usar o texto **por produto** (sem separar por review). Alternativa: avaliar a viabilidade de separar em reviews individuais (risco de associar o texto à review errada). A `fato_review` não ganha colunas sem pedido, porque isso altera o DER.
2. **Sentimento:** precisa de um léxico. Opções: `vaderSentiment` (dependência nova, **exige aprovação**) ou um léxico pequeno feito à mão (sem dependência, menos preciso).
3. **Limpeza do texto:** stopwords, minúsculas, remoção de números e símbolos, e como tratar a frequência mínima para o bigrama não explodir o tamanho do CSV.
4. **Lista de temas e palavras-chave** para `dim_tema`, e o que fazer com termos sem tema (FK nulo ou tema "Outros", seguindo a lição do `rating` nulo).

Entregáveis desse bloco: módulo (ex.: `src/transform_termos.py`) com testes, tabelas incluídas no `build_gold_tables`, PK e FK validadas (`(id_produto, termo)` único e `id_tema` existente), atualização da especificação, do README e deste arquivo.

### 7.2 Pendências de regra
- **`rating_count` de duplicatas:** hoje vale a primeira ocorrência; decidir se passa a valer o maior valor (difere em 31 produtos).
- **Marcas compostas fora da lista:** continuam cortadas na primeira palavra; a correção é acrescentar a marca em `COMPOSITE_BRANDS`.
- **`fato_review`:** decisão sobre o texto das reviews (item 7.1.1), registrada no CLAUDE.md para revisão.

### 7.3 Integração com o Power BI (fora do Python)
- Importar os CSVs de `saida_bi/` (UTF-8, vírgula decimal) e criar os relacionamentos PK/FK do DER.
- Ordenar `faixa` por `ordem` nas dimensões de faixa.
- Construir os visuais da pergunta Preço → Desconto → Engajamento → Satisfação e as recomendações por quadrante.

### 7.4 Engenharia
- Se o repositório for compartilhado, avaliar uma checagem automática (testes e lint) na integração contínua.
