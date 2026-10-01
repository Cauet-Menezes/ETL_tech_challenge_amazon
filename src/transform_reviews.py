"""Reviews e usuários: explode as listas do bruto e gera dim_usuario e fato_review."""
import pandas as pd

from src.config import (
    COL_ID_PRODUTO,
    COL_ID_USUARIO,
    COL_PRODUCT_ID,
    COL_REVIEW_COUNT,
    COL_REVIEW_ID,
    COL_USER_ID,
    COL_USER_NAME,
    FIRST_SURROGATE_ID,
    LIST_SEPARATOR,
    NO_USER_NAME_LABEL,
    USER_NAME_CORRECTIONS,
    USER_NAME_SEPARATOR_PATTERN,
)


def align_user_names(names: list, expected_count: int) -> list:
    """Alinha os nomes aos ids; descarta tokens vazios se preciso e usa nulos se ainda não bater."""
    if len(names) != expected_count:
        names = [name for name in names if name.strip()]
    return names if len(names) == expected_count else [None] * expected_count


def split_user_names(user_names: pd.Series, expected_counts: pd.Series) -> pd.Series:
    """Separa os nomes e os alinha à quantidade de ids de cada linha."""
    names = user_names.str.split(USER_NAME_SEPARATOR_PATTERN, regex=True)
    aligned = [align_user_names(*pair) for pair in zip(names, expected_counts)]
    return pd.Series(aligned, index=user_names.index)


def explode_reviews(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Gera uma linha por review (id_produto, review_id, user_id, user_name)."""
    with_reviews = raw_df.dropna(subset=[COL_USER_ID, COL_REVIEW_ID])
    user_ids = with_reviews[COL_USER_ID].str.split(LIST_SEPARATOR)
    reviews = pd.DataFrame(
        {
            COL_ID_PRODUTO: with_reviews[COL_PRODUCT_ID],
            COL_REVIEW_ID: with_reviews[COL_REVIEW_ID].str.split(LIST_SEPARATOR),
            COL_USER_ID: user_ids,
            COL_USER_NAME: split_user_names(with_reviews[COL_USER_NAME], user_ids.str.len()),
        }
    )
    return reviews.explode([COL_REVIEW_ID, COL_USER_ID, COL_USER_NAME], ignore_index=True)


def fill_missing_user_names(reviews: pd.DataFrame) -> pd.DataFrame:
    """Aplica as correções manuais e completa nomes vazios; sem nome em lugar nenhum, 'SEM NOME'."""
    names = reviews[COL_USER_NAME].str.strip().replace("", None)
    names = reviews[COL_USER_ID].map(USER_NAME_CORRECTIONS).fillna(names)
    known_names = reviews.assign(**{COL_USER_NAME: names}).dropna(subset=[COL_USER_NAME])
    name_by_user = known_names.drop_duplicates(COL_USER_ID).set_index(COL_USER_ID)[COL_USER_NAME]
    filled = names.fillna(reviews[COL_USER_ID].map(name_by_user)).fillna(NO_USER_NAME_LABEL)
    return reviews.assign(**{COL_USER_NAME: filled})


def build_dim_usuario(reviews: pd.DataFrame) -> pd.DataFrame:
    """Cria dim_usuario com id_usuario sequencial, ordenado por user_id (resultado estável)."""
    users = reviews[[COL_USER_ID, COL_USER_NAME]].drop_duplicates(COL_USER_ID)
    users = users.sort_values(COL_USER_ID).reset_index(drop=True)
    users.insert(0, COL_ID_USUARIO, range(FIRST_SURROGATE_ID, FIRST_SURROGATE_ID + len(users)))
    return users


def build_fato_review(reviews: pd.DataFrame, dim_usuario: pd.DataFrame) -> pd.DataFrame:
    """Cria fato_review (review_id, id_produto, id_usuario), uma linha por review e produto."""
    with_user_key = reviews.merge(dim_usuario[[COL_ID_USUARIO, COL_USER_ID]], on=COL_USER_ID)
    columns = [COL_REVIEW_ID, COL_ID_PRODUTO, COL_ID_USUARIO]
    unique_reviews = with_user_key[columns].drop_duplicates([COL_REVIEW_ID, COL_ID_PRODUTO])
    return unique_reviews.sort_values(columns).reset_index(drop=True)


def count_reviews_per_product(fato_review: pd.DataFrame) -> pd.DataFrame:
    """Conta os reviews de cada produto (qtd_reviews_amostra)."""
    counts = fato_review.groupby(COL_ID_PRODUTO).size()
    return counts.rename(COL_REVIEW_COUNT).reset_index()


def transform_reviews(raw_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Devolve (dim_usuario, fato_review) a partir do bruto."""
    reviews = fill_missing_user_names(explode_reviews(raw_df))
    dim_usuario = build_dim_usuario(reviews)
    return dim_usuario, build_fato_review(reviews, dim_usuario)
