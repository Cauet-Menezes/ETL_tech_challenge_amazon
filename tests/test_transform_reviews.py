import pandas as pd

from src.transform_reviews import (
    build_dim_usuario,
    count_reviews_per_product,
    explode_reviews,
    fill_missing_user_names,
    split_user_names,
    transform_reviews,
)


def build_raw_row(product_id, user_ids, user_names, review_ids):
    return {
        "product_id": product_id,
        "user_id": user_ids,
        "user_name": user_names,
        "review_id": review_ids,
    }


def test_split_user_names_mantem_virgula_seguida_de_espaco():
    names = pd.Series(["Ana,Ganesh, Tamilnadu,Rui"])
    result = split_user_names(names, pd.Series([3]))
    assert result.iloc[0] == ["Ana", "Ganesh, Tamilnadu", "Rui"]


def test_split_user_names_desalinhado_vira_nulos():
    result = split_user_names(pd.Series(["Ana,Bia,Caio"]), pd.Series([2]))
    assert result.iloc[0] == [None, None]


def test_split_user_names_descarta_token_vazio_que_sobra():
    result = split_user_names(pd.Series(["Ana,,Bia"]), pd.Series([2]))
    assert result.iloc[0] == ["Ana", "Bia"]


def test_explode_reviews_gera_uma_linha_por_review():
    raw = pd.DataFrame([build_raw_row("P1", "U1,U2", "Ana,Bia", "R1,R2")])
    result = explode_reviews(raw)
    assert result[["review_id", "user_id", "user_name"]].values.tolist() == [
        ["R1", "U1", "Ana"],
        ["R2", "U2", "Bia"],
    ]


def test_explode_reviews_ignora_produto_sem_review():
    raw = pd.DataFrame([build_raw_row("P1", None, None, None)])
    assert explode_reviews(raw).empty


def test_fill_missing_user_names_usa_outra_ocorrencia_ou_sem_nome():
    reviews = pd.DataFrame(
        {
            "user_id": ["U1", "U1", "U2"],
            "user_name": ["Ana", None, ""],
        }
    )
    result = fill_missing_user_names(reviews)
    assert result["user_name"].tolist() == ["Ana", "Ana", "SEM NOME"]


def test_fill_missing_user_names_correcao_manual_prevalece(monkeypatch):
    monkeypatch.setattr("src.transform_reviews.USER_NAME_CORRECTIONS", {"U1": "Pradeep, TCR"})
    reviews = pd.DataFrame({"user_id": ["U1", "U2"], "user_name": ["Pradeep", "Bia"]})
    result = fill_missing_user_names(reviews)
    assert result["user_name"].tolist() == ["Pradeep, TCR", "Bia"]


def test_build_dim_usuario_ids_sequenciais_e_estaveis():
    reviews = pd.DataFrame({"user_id": ["U2", "U1", "U2"], "user_name": ["B", "A", "B"]})
    result = build_dim_usuario(reviews)
    assert result[["id_usuario", "user_id"]].values.tolist() == [[1, "U1"], [2, "U2"]]


def test_transform_reviews_review_compartilhado_fica_em_cada_produto():
    raw = pd.DataFrame(
        [
            build_raw_row("P1", "U1,U2", "Ana,Bia", "R1,R2"),
            build_raw_row("P2", "U1", "Ana", "R1"),
            build_raw_row("P1", "U1,U2", "Ana,Bia", "R1,R2"),
        ]
    )
    dim_usuario, fato_review = transform_reviews(raw)
    assert len(dim_usuario) == 2
    assert fato_review[["review_id", "id_produto"]].values.tolist() == [
        ["R1", "P1"],
        ["R1", "P2"],
        ["R2", "P1"],
    ]
    assert not fato_review.duplicated(["review_id", "id_produto"]).any()


def test_count_reviews_per_product():
    fato_review = pd.DataFrame({"review_id": ["R1", "R2", "R1"], "id_produto": ["P1", "P1", "P2"]})
    result = count_reviews_per_product(fato_review)
    assert result.values.tolist() == [["P1", 2], ["P2", 1]]
