import pandas as pd
import pytest

from src.build_gold import (
    assign_band_ids,
    assign_quadrant_ids,
    build_band_dimension,
    build_category_row,
    build_dim_categoria,
    build_dim_quadrante,
    build_gold_tables,
    export_gold_tables,
    validate_gold_tables,
)
from src.config import (
    COL_ID_FAIXA_PRECO,
    COL_ID_FAIXA_RATING,
    COL_PRECO_MAX,
    COL_PRECO_MIN,
    COL_RATING_MAX,
    COL_RATING_MIN,
    NO_RATING_BAND_LABEL,
    PRICE_BANDS,
    RATING_BANDS,
)

PATH_DEEP = "A|B|C|D"
PATH_SHALLOW = "A|B"


def build_products(**columns):
    base = {
        "id_produto": ["P1", "P2", "P3", "P4"],
        "product_name": ["n1", "n2", "n3", "n4"],
        "marca": ["X", "X", "Y", "Y"],
        "category": [PATH_DEEP, PATH_SHALLOW, PATH_DEEP, PATH_DEEP],
        "about_product": ["a"] * 4,
        "product_link": ["l"] * 4,
        "img_link": ["i"] * 4,
        "actual_price": [300.0, 600.0, 7000.0, 100.0],
        "discounted_price": [199.0, 200.0, 5000.0, 100.0],
        "discount_amount": [101.0, 400.0, 2000.0, 0.0],
        "discount_pct": [9.0, 10.0, 70.0, 0.0],
        "rating": [4.0, 3.9, 4.5, None],
        "rating_count": pd.array([100, 10, 5000, 7], dtype="Int64"),
        "receita_proxy": [1.0, 1.0, 1.0, 1.0],
    }
    base.update(columns)
    return pd.DataFrame(base)


def build_reviews():
    dim_usuario = pd.DataFrame({"id_usuario": [1, 2], "user_id": ["U1", "U2"], "user_name": ["a", "b"]})
    fato_review = pd.DataFrame(
        {"review_id": ["R1", "R2", "R3"], "id_produto": ["P1", "P1", "P3"], "id_usuario": [1, 2, 1]}
    )
    return dim_usuario, fato_review


@pytest.fixture
def tables():
    dim_usuario, fato_review = build_reviews()
    return build_gold_tables(build_products(), dim_usuario, fato_review)


def test_assign_band_ids_usa_intervalo_fechado_na_esquerda():
    dimension = build_band_dimension(PRICE_BANDS, COL_ID_FAIXA_PRECO, COL_PRECO_MIN, COL_PRECO_MAX)
    ids = assign_band_ids(pd.Series([0.0, 199.0, 200.0, 5000.0, 77990.0]), dimension,
                          COL_ID_FAIXA_PRECO, COL_PRECO_MIN)
    assert ids.tolist() == [1, 1, 2, 6, 6]


def test_assign_band_ids_rating_nulo_vai_para_sem_avaliacao():
    dimension = build_band_dimension(
        RATING_BANDS, COL_ID_FAIXA_RATING, COL_RATING_MIN, COL_RATING_MAX, NO_RATING_BAND_LABEL
    )
    ids = assign_band_ids(pd.Series([3.4, 3.5, 4.0, 5.0, None]), dimension,
                          COL_ID_FAIXA_RATING, COL_RATING_MIN)
    assert ids.tolist() == [1, 2, 3, 5, 6]
    assert dimension["faixa"].iloc[-1] == NO_RATING_BAND_LABEL


def test_build_band_dimension_ultima_faixa_sem_teto():
    dimension = build_band_dimension(PRICE_BANDS, COL_ID_FAIXA_PRECO, COL_PRECO_MIN, COL_PRECO_MAX)
    assert dimension["ordem"].tolist() == [1, 2, 3, 4, 5, 6]
    assert pd.isna(dimension[COL_PRECO_MAX].iloc[-1])


def test_dim_quadrante_tem_cinco_linhas_com_id_sequencial():
    dimension = build_dim_quadrante()
    assert dimension["id_quadrante"].tolist() == [1, 2, 3, 4, 5]
    assert dimension["quadrante"].iloc[-1] == "Sem dados"


def test_assign_quadrant_ids_cobre_os_quatro_quadrantes_e_sem_nota():
    products = build_products(
        rating=[4.0, 4.5, 3.9, 3.0, None],
        rating_count=pd.array([10, 300, 300, 10, 100], dtype="Int64"),
        id_produto=["a", "b", "c", "d", "e"],
        product_name=["n"] * 5, marca=["x"] * 5, category=[PATH_DEEP] * 5,
        about_product=["a"] * 5, product_link=["l"] * 5, img_link=["i"] * 5,
        actual_price=[1.0] * 5, discounted_price=[1.0] * 5, discount_amount=[0.0] * 5,
        discount_pct=[0.0] * 5, receita_proxy=[1.0] * 5,
    )
    ids = assign_quadrant_ids(products, build_dim_quadrante())
    # mediana = 100: engajamento alto só acima dela (produtos b e c)
    assert ids.tolist() == [2, 1, 3, 4, 5]


def test_build_category_row_repete_ultimo_nivel_em_categoria_rasa():
    row = build_category_row(PATH_SHALLOW)
    assert (row["nivel_1"], row["nivel_2"], row["nivel_3"]) == ("A", "B", "B")
    assert row["categoria_folha"] == "B"
    assert row["category_path"] == PATH_SHALLOW


def test_build_dim_categoria_uma_linha_por_caminho_ordenada():
    dimension = build_dim_categoria(build_products())
    assert dimension["category_path"].tolist() == [PATH_SHALLOW, PATH_DEEP]
    assert dimension["id_categoria"].tolist() == [1, 2]


def test_fato_produto_tem_fks_contagem_de_reviews_e_ordem_do_der(tables):
    fato = tables["fato_produto"]
    assert list(fato.columns[:6]) == [
        "id_produto", "id_categoria", "id_faixa_desconto", "id_faixa_preco",
        "id_faixa_rating", "id_quadrante",
    ]
    assert fato["qtd_reviews_amostra"].tolist() == [2, 0, 1, 0]
    assert fato["id_faixa_rating"].iloc[3] == 6  # sem nota
    assert fato["id_quadrante"].iloc[3] == 5


def test_validate_gold_tables_aceita_tabelas_validas(tables):
    validate_gold_tables(tables)


def test_validate_gold_tables_detecta_fk_inexistente(tables):
    tables["fato_produto"].loc[0, "id_faixa_preco"] = 99
    with pytest.raises(ValueError, match="id_faixa_preco"):
        validate_gold_tables(tables)


def test_validate_gold_tables_detecta_pk_duplicada(tables):
    tables["fato_produto"].loc[1, "id_produto"] = "P1"
    with pytest.raises(ValueError, match="PK duplicada em fato_produto"):
        validate_gold_tables(tables)


def test_validate_gold_tables_detecta_nulo_fora_do_rating(tables):
    tables["fato_produto"].loc[0, "marca"] = None
    with pytest.raises(ValueError, match="marca"):
        validate_gold_tables(tables)


def test_export_gold_tables_grava_csv_idempotente(tables, tmp_path):
    export_gold_tables(tables, tmp_path)
    first = (tmp_path / "fato_produto.csv").read_bytes()
    export_gold_tables(tables, tmp_path)
    assert (tmp_path / "fato_produto.csv").read_bytes() == first
    assert first.startswith(b"\xef\xbb\xbf")  # utf-8-sig
    assert len(list(tmp_path.glob("*.csv"))) == len(tables)


def test_export_gold_tables_usa_virgula_decimal(tables, tmp_path):
    export_gold_tables(tables, tmp_path)
    text = (tmp_path / "fato_produto.csv").read_text(encoding="utf-8-sig")
    assert '"4,5"' in text
