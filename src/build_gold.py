"""Camada gold: dimensões, FKs em fato_produto, validações e exportação dos CSVs."""
from pathlib import Path

import pandas as pd

from src.config import (
    CATEGORY_SEPARATOR,
    COL_ACAO_SUGERIDA,
    COL_CATEGORY,
    COL_CATEGORY_LEAF,
    COL_CATEGORY_LEVELS,
    COL_CATEGORY_PATH,
    COL_DISCOUNT_PCT,
    COL_DISCOUNTED_PRICE,
    COL_ENGAJAMENTO,
    COL_FAIXA,
    COL_ID_CATEGORIA,
    COL_ID_FAIXA_DESCONTO,
    COL_ID_FAIXA_PRECO,
    COL_ID_FAIXA_RATING,
    COL_ID_PRODUTO,
    COL_ID_QUADRANTE,
    COL_ORDEM,
    COL_PCT_MAX,
    COL_PCT_MIN,
    COL_PRECO_MAX,
    COL_PRECO_MIN,
    COL_QUADRANTE,
    COL_RATING,
    COL_RATING_COUNT,
    COL_RATING_MAX,
    COL_RATING_MIN,
    COL_REGRA,
    COL_REVIEW_COUNT,
    COL_SATISFACAO,
    CSV_EXTENSION,
    DISCOUNT_BANDS,
    EXPORT_CSV_ENCODING,
    EXPORT_DECIMAL_SEPARATOR,
    FATO_PRODUTO_COLUMNS,
    FIRST_SURROGATE_ID,
    FOREIGN_KEYS,
    HIGH_ENGAGEMENT,
    HIGH_SATISFACTION,
    INTEGER_ID_COLUMNS,
    LOW_ENGAGEMENT,
    LOW_SATISFACTION,
    NO_RATING_BAND_LABEL,
    NULLABLE_FATO_PRODUTO_COLUMNS,
    OUTPUT_DIR,
    PRICE_BANDS,
    PRIMARY_KEYS,
    QUADRANTS,
    RATING_BANDS,
    RATING_DECIMAL_PLACES,
    SATISFACTION_MIN_RATING,
    TABLE_DIM_CATEGORIA,
    TABLE_DIM_FAIXA_DESCONTO,
    TABLE_DIM_FAIXA_PRECO,
    TABLE_DIM_FAIXA_RATING,
    TABLE_DIM_QUADRANTE,
    TABLE_DIM_USUARIO,
    TABLE_FATO_PRODUTO,
    TABLE_FATO_REVIEW,
    UNDEFINED_ENGAGEMENT,
    UNDEFINED_SATISFACTION,
)
from src.transform_reviews import count_reviews_per_product


def build_sequential_ids(row_count: int) -> range:
    """Gera os ids substitutos sequenciais a partir de FIRST_SURROGATE_ID."""
    return range(FIRST_SURROGATE_ID, FIRST_SURROGATE_ID + row_count)


def build_band_dimension(
    bands: tuple, id_column: str, min_column: str, max_column: str, missing_label: str | None = None
) -> pd.DataFrame:
    """Monta uma dimensão de faixas (id = ordem); missing_label acrescenta a faixa sem valor."""
    rows = [{COL_FAIXA: label, min_column: low, max_column: high} for low, high, label in bands]
    if missing_label:
        rows.append({COL_FAIXA: missing_label, min_column: None, max_column: None})
    dimension = pd.DataFrame(rows)
    dimension[COL_ORDEM] = build_sequential_ids(len(dimension))
    dimension.insert(0, id_column, dimension[COL_ORDEM])
    return dimension


def assign_band_ids(
    values: pd.Series, dimension: pd.DataFrame, id_column: str, min_column: str
) -> pd.Series:
    """Devolve o id da faixa de cada valor (intervalo [mín, máx)); nulo usa a faixa sem valor."""
    bounded = dimension.dropna(subset=[min_column])
    edges = [*bounded[min_column], float("inf")]
    positions = pd.cut(values.astype(float), bins=edges, right=False, labels=False)
    ids = positions.map(dict(enumerate(bounded[id_column])))
    missing_ids = dimension.loc[dimension[min_column].isna(), id_column]
    if not missing_ids.empty:
        ids = ids.fillna(missing_ids.iloc[0])
    return ids.astype("Int64")


def build_dim_quadrante() -> pd.DataFrame:
    """Monta dim_quadrante a partir da tabela QUADRANTS."""
    columns = [COL_QUADRANTE, COL_ENGAJAMENTO, COL_SATISFACAO, COL_ACAO_SUGERIDA, COL_REGRA]
    dimension = pd.DataFrame(QUADRANTS, columns=columns)
    dimension.insert(0, COL_ID_QUADRANTE, build_sequential_ids(len(dimension)))
    return dimension


def label_engagement_and_satisfaction(products: pd.DataFrame) -> pd.DataFrame:
    """Classifica engajamento (acima da mediana) e satisfação (nota >= corte); sem nota = indefinido."""
    has_rating = products[COL_RATING].notna()
    is_engaged = (products[COL_RATING_COUNT] > products[COL_RATING_COUNT].median()).astype(bool)
    is_satisfied = (products[COL_RATING] >= SATISFACTION_MIN_RATING).astype(bool)
    engagement = is_engaged.map({True: HIGH_ENGAGEMENT, False: LOW_ENGAGEMENT})
    satisfaction = is_satisfied.map({True: HIGH_SATISFACTION, False: LOW_SATISFACTION})
    return pd.DataFrame(
        {
            COL_ENGAJAMENTO: engagement.mask(~has_rating, UNDEFINED_ENGAGEMENT),
            COL_SATISFACAO: satisfaction.mask(~has_rating, UNDEFINED_SATISFACTION),
        }
    )


def assign_quadrant_ids(products: pd.DataFrame, dimension: pd.DataFrame) -> pd.Series:
    """Devolve o id_quadrante de cada produto."""
    labels = label_engagement_and_satisfaction(products)
    keys = [COL_ENGAJAMENTO, COL_SATISFACAO]
    merged = labels.merge(dimension[[COL_ID_QUADRANTE, *keys]], on=keys, how="left")
    return pd.Series(merged[COL_ID_QUADRANTE].to_numpy(), index=products.index).astype("Int64")


def build_category_row(category_path: str) -> dict:
    """Separa o caminho em níveis; categorias rasas repetem o último nível nos níveis que faltam."""
    levels = [level.strip() for level in category_path.split(CATEGORY_SEPARATOR)]
    row = {
        column: levels[min(position, len(levels) - 1)]
        for position, column in enumerate(COL_CATEGORY_LEVELS)
    }
    row[COL_CATEGORY_LEAF] = levels[-1]
    row[COL_CATEGORY_PATH] = category_path
    return row


def build_dim_categoria(products: pd.DataFrame) -> pd.DataFrame:
    """Monta dim_categoria: uma linha por caminho de categoria, id sequencial ordenado."""
    paths = products[COL_CATEGORY].drop_duplicates().sort_values()
    dimension = pd.DataFrame([build_category_row(path) for path in paths])
    dimension.insert(0, COL_ID_CATEGORIA, build_sequential_ids(len(dimension)))
    return dimension


def build_dimensions(products: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Cria as cinco dimensões que dependem dos produtos."""
    return {
        TABLE_DIM_CATEGORIA: build_dim_categoria(products),
        TABLE_DIM_FAIXA_DESCONTO: build_band_dimension(
            DISCOUNT_BANDS, COL_ID_FAIXA_DESCONTO, COL_PCT_MIN, COL_PCT_MAX
        ),
        TABLE_DIM_FAIXA_PRECO: build_band_dimension(
            PRICE_BANDS, COL_ID_FAIXA_PRECO, COL_PRECO_MIN, COL_PRECO_MAX
        ),
        TABLE_DIM_FAIXA_RATING: build_band_dimension(
            RATING_BANDS, COL_ID_FAIXA_RATING, COL_RATING_MIN, COL_RATING_MAX, NO_RATING_BAND_LABEL
        ),
        TABLE_DIM_QUADRANTE: build_dim_quadrante(),
    }


def assign_category_ids(products: pd.DataFrame, dim_categoria: pd.DataFrame) -> pd.Series:
    """Devolve o id_categoria de cada produto pelo caminho da categoria."""
    ids_by_path = dim_categoria.set_index(COL_CATEGORY_PATH)[COL_ID_CATEGORIA]
    return products[COL_CATEGORY].map(ids_by_path).astype("Int64")


def build_fato_produto(
    products: pd.DataFrame, dimensions: dict[str, pd.DataFrame], review_counts: pd.DataFrame
) -> pd.DataFrame:
    """Leva os FKs das dimensões e qtd_reviews_amostra para fato_produto."""
    products = products.reset_index(drop=True)
    discount_dim = dimensions[TABLE_DIM_FAIXA_DESCONTO]
    price_dim = dimensions[TABLE_DIM_FAIXA_PRECO]
    rating_dim = dimensions[TABLE_DIM_FAIXA_RATING]
    rounded_rating = products[COL_RATING].round(RATING_DECIMAL_PLACES)
    with_keys = products.assign(
        **{
            COL_ID_CATEGORIA: assign_category_ids(products, dimensions[TABLE_DIM_CATEGORIA]),
            COL_ID_FAIXA_DESCONTO: assign_band_ids(
                products[COL_DISCOUNT_PCT], discount_dim, COL_ID_FAIXA_DESCONTO, COL_PCT_MIN
            ),
            COL_ID_FAIXA_PRECO: assign_band_ids(
                products[COL_DISCOUNTED_PRICE], price_dim, COL_ID_FAIXA_PRECO, COL_PRECO_MIN
            ),
            COL_ID_FAIXA_RATING: assign_band_ids(
                rounded_rating, rating_dim, COL_ID_FAIXA_RATING, COL_RATING_MIN
            ),
            COL_ID_QUADRANTE: assign_quadrant_ids(products, dimensions[TABLE_DIM_QUADRANTE]),
        }
    )
    with_counts = with_keys.merge(review_counts, on=COL_ID_PRODUTO, how="left")
    with_counts[COL_REVIEW_COUNT] = with_counts[COL_REVIEW_COUNT].fillna(0).astype(int)
    return with_counts[list(FATO_PRODUTO_COLUMNS)]


def build_gold_tables(
    products: pd.DataFrame, dim_usuario: pd.DataFrame, fato_review: pd.DataFrame
) -> dict[str, pd.DataFrame]:
    """Monta todas as tabelas do modelo (nome da tabela -> DataFrame)."""
    dimensions = build_dimensions(products)
    review_counts = count_reviews_per_product(fato_review)
    return {
        TABLE_FATO_PRODUTO: build_fato_produto(products, dimensions, review_counts),
        TABLE_FATO_REVIEW: fato_review,
        TABLE_DIM_USUARIO: dim_usuario,
        **dimensions,
    }


def find_duplicate_primary_keys(tables: dict[str, pd.DataFrame]) -> list[str]:
    """Lista as tabelas com PK repetida."""
    return [
        f"PK duplicada em {name}: {keys}"
        for name, keys in PRIMARY_KEYS.items()
        if tables[name].duplicated(subset=keys).any()
    ]


def find_missing_foreign_keys(tables: dict[str, pd.DataFrame]) -> list[str]:
    """Lista os FKs nulos ou que não existem na tabela de destino."""
    errors = []
    for table, column, target in FOREIGN_KEYS:
        valid = tables[table][column].isin(tables[target][PRIMARY_KEYS[target][0]])
        if not valid.all():
            errors.append(f"FK inválido em {table}.{column}: {int((~valid).sum())} linhas")
    return errors


def find_null_values(tables: dict[str, pd.DataFrame]) -> list[str]:
    """Lista colunas com nulos em fato_produto (exceto as permitidas) e nas PKs."""
    errors = []
    fato_produto = tables[TABLE_FATO_PRODUTO]
    required = [c for c in fato_produto.columns if c not in NULLABLE_FATO_PRODUTO_COLUMNS]
    errors.extend(f"Nulos em {TABLE_FATO_PRODUTO}.{c}" for c in required if fato_produto[c].isna().any())
    errors.extend(
        f"Nulos na PK de {name}" for name, keys in PRIMARY_KEYS.items() if tables[name][keys].isna().any().any()
    )
    return errors


def find_non_integer_ids(tables: dict[str, pd.DataFrame]) -> list[str]:
    """Lista colunas de id substituto que não são inteiras."""
    return [
        f"{name}.{column} não é inteiro"
        for name, table in tables.items()
        for column in INTEGER_ID_COLUMNS
        if column in table.columns and not pd.api.types.is_integer_dtype(table[column])
    ]


def validate_gold_tables(tables: dict[str, pd.DataFrame]) -> None:
    """Levanta ValueError com todos os problemas de PK, FK, nulos e tipos."""
    errors = [
        *find_duplicate_primary_keys(tables),
        *find_missing_foreign_keys(tables),
        *find_null_values(tables),
        *find_non_integer_ids(tables),
    ]
    if errors:
        raise ValueError("Validação falhou:\n" + "\n".join(errors))


def export_gold_tables(tables: dict[str, pd.DataFrame], output_dir: Path = OUTPUT_DIR) -> None:
    """Grava um CSV por tabela, sobrescrevendo os existentes."""
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, table in tables.items():
        table.to_csv(
            output_dir / f"{name}{CSV_EXTENSION}",
            index=False,
            encoding=EXPORT_CSV_ENCODING,
            decimal=EXPORT_DECIMAL_SEPARATOR,
        )
