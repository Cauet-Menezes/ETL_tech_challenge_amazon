# CLAUDE.md

## Contexto
Projeto de engenharia de dados: ETL em Python que trata os dados e gera CSVs para uso no Power BI, onde serão construídos os visuais.
Não há carga em banco de dados: a saída do pipeline são apenas arquivos CSV.
Stack: Python (mais atual), pandas (mais atual).

## Modelo de dados (star schema)
Cada tabela do DER vira um CSV. Os relacionamentos (PK/FK) são criados no Power BI.
- Fatos: `fato_produto`, `fato_termo_produto`, `fato_review`
- Dimensões: `dim_categoria`, `dim_faixa_desconto`, `dim_faixa_preco`, `dim_faixa_rating`, `dim_quadrante`, `dim_tema`, `dim_usuario`
- As chaves substitutas (`id_categoria`, `id_faixa_*`, `id_quadrante`, `id_tema`) são geradas no Python: criar a dimensão primeiro e depois fazer o merge para levar o FK à fato.
- Saída dos CSVs em `saida_bi/`.

## Especificação de regras
As regras de negócio e de tratamento de dados (limpeza, duplicatas, nulos, marca, reviews, dimensões, termos) estão em `.claude/spec/ESPECIFICACAO.md`, com o status de cada uma (implementada, acordada ou em aberto). Ler antes de mexer nas transformações e **atualizar o arquivo sempre que uma regra mudar ou for implementada**. Em conflito, a especificação vale para regras de dado; este arquivo vale para estilo e engenharia.

## Estilo de código
- Nomes de funções e variáveis descritivos, começando com verbo nas funções.
- Uma função faz uma única coisa; se passar de ~30 linhas, dividir.
- Preferir a solução mais simples: funções antes de classes, sem abstrações desnecessárias.
- Sem números ou strings mágicas: usar constantes nomeadas.
- Docstring curta (1 linha) em funções públicas.

## Engenharia de dados
- Execução idempotente: rodar o pipeline duas vezes gera os mesmos CSVs (sobrescrever os arquivos, nunca acrescentar).
- Credenciais e caminhos sensíveis apenas via variável de ambiente, nunca no código.
- Validar antes de exportar:
  - nulos e tipos das colunas;
  - PK sem duplicatas em cada dimensão e em `(id_produto, termo)` de `fato_termo_produto`;
  - todo FK de `fato_produto` existe na dimensão correspondente.
- Exportar CSV com `encoding="utf-8-sig"` e `index=False`.
- Decimais: usar `decimal=","` na exportação.
- Remover quebras de linha dos campos de texto longos (ex.: `about_product`) antes de exportar.
- IDs são inteiros ou texto, nunca decimais.
- Se houver SQL longo, ele fica em arquivos `.sql`, não dentro do Python.
- subir o amazon.csv e a  saida_bi ao versionamento no git.

## O que NÃO fazer
- Não refatorar código fora do escopo da tarefa.
- Não alterar a estrutura (colunas/tabelas) do modelo de dados sem eu pedir.
- Não adicionar dependências novas sem avisar.

## Fluxo
1. Ler os arquivos relevantes antes de editar.
2. Em mudanças grandes, propor o plano antes de codar.
3. Rodar testes e lint antes de dizer que terminou.
4. Ao atingir ~300K tokens de contexto, compactar a conversa. Depois de compactar (e no início de cada sessão), reler `.claude/CLAUDE.MD`, `DER.jpeg` e `.claude/spec/ESPECIFICACAO.md` antes de continuar.

## Estado atual do repositório
- Comandos (usar o `.venv`): `.venv/Scripts/python -m pytest -q` (testes), `.venv/Scripts/python -m ruff check .` (lint), `.venv/Scripts/python -m pytest tests/test_transform_produtos.py::nome_do_teste` (um teste). Dependências com versão fixada em `requirements.txt` (pandas, pytest, ruff).
- Implementado: `src/config.py` (constantes e caminhos), `src/extract.py`, `src/transform_produtos.py`, `src/transform_reviews.py`, `src/build_gold.py` (dimensões, FKs, validações, export) e `main.py` (`.venv/Scripts/python main.py` gera os CSVs), com testes em `tests/`.
- Pendente: `fato_termo_produto` e `dim_tema` (termos, temas, sentimento; ver seção 5 da especificação).
- Entrada: `data/raw/amazon.csv`. Ele e `saida_bi/` devem ser versionados no git (ainda não commitados; `saida_bi/` já é gerada pelo `main.py`). `.env` está ignorado e vazio.
- **Para revisão (`fato_review`):** o bruto não tem nota nem data por review; só `review_id`, `user_id`, `user_name`, `review_title` e `review_content`. Por isso a `fato_review` fica só com `review_id`, `id_produto` e `id_usuario` (quem avaliou o quê; o `rating` de satisfação continua o do produto). Título e texto também vêm como lista separada por vírgula, mas o texto tem vírgulas próprias (até 125 num campo), então não dá para separar as reviews por posição sem heurística (risco de associar o texto à review errada). Decisão pendente: manter assim e usar o texto por produto em `fato_termo_produto`/`dim_tema` (recomendado), ou avaliar a viabilidade de separar o texto em reviews individuais. Mudar colunas da `fato_review` altera o DER e só com pedido do usuário.
- O pipeline não usa banco (`src/db.py` e o MCP do Supabase foram removidos): a saída é só CSV.
- Layout: `extract` → `transform_produtos` / `transform_reviews` → `build_gold` (dimensões, depois fatos, validações e export em `saida_bi/`), orquestrado por `main.py`.
