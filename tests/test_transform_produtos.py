import pandas as pd
import pytest

from src.transform_produtos import (
    clean_count,
    clean_percentage,
    clean_price,
    clean_rating,
    extract_brand,
    remove_duplicate_products,
    remove_line_breaks,
    transform_produtos,
)


def build_raw_row(**overrides):
    row = {
        "product_id": "P1",
        "product_name": "Wayona Cable 3FT",
        "category": "A|B|C",
        "discounted_price": "₹399",
        "actual_price": "₹1,099",
        "discount_percentage": "64%",
        "rating": "4.2",
        "rating_count": "24,269",
        "about_product": "linha 1\nlinha 2",
        "img_link": "http://img",
        "product_link": "http://link",
    }
    row.update(overrides)
    return row


def test_clean_price_remove_simbolo_e_milhar():
    result = clean_price(pd.Series(["₹1,099", "₹399", None]))
    assert result.iloc[0] == 1099
    assert result.iloc[1] == 399
    assert pd.isna(result.iloc[2])


def test_clean_percentage_remove_simbolo():
    assert clean_percentage(pd.Series(["64%"])).iloc[0] == 64


def test_clean_count_retorna_inteiro_anulavel():
    result = clean_count(pd.Series(["24,269", None]))
    assert str(result.dtype) == "Int64"
    assert result.iloc[0] == 24269
    assert pd.isna(result.iloc[1])


def test_clean_rating_invalido_vira_nulo():
    result = clean_rating(pd.Series(["4.2", "|"]))
    assert result.iloc[0] == pytest.approx(4.2)
    assert pd.isna(result.iloc[1])


def test_remove_line_breaks_troca_por_espaco():
    assert remove_line_breaks(pd.Series(["a\r\nb\nc"])).iloc[0] == "a b c"


@pytest.mark.parametrize(
    ("product_name", "expected_brand"),
    [("ZEBRONICS Speaker", "ZEBRONICS"), ("boAt Rockerz", "BOAT"), ("TP-Link Router", "TP-LINK")],
)
def test_extract_brand_converte_para_maiusculas(product_name, expected_brand):
    assert extract_brand(pd.Series([product_name])).iloc[0] == expected_brand


@pytest.mark.parametrize(
    ("product_name", "expected_brand"),
    [
        ("Western Digital WD 2TB Drive", "WESTERN DIGITAL"),
        ("TATA SKY HD Connection", "TATA SKY"),
        ("Black + Decker BD Steam Iron", "BLACK+DECKER"),
        ("House of Quirk Picker", "HOUSE OF QUIRK"),
        ("Tata Tea Gold", "TATA"),
        ("Lunagariya®, Water Bottle", "LUNAGARIYA"),
        ("Crypo™ Cable", "CRYPO"),
        ("Zebronics, Speaker", "ZEBRONICS"),
    ],
)
def test_extract_brand_compostas_simbolos_e_pontuacao(product_name, expected_brand):
    assert extract_brand(pd.Series([product_name])).iloc[0] == expected_brand


@pytest.mark.parametrize(
    ("product_name", "expected_brand"),
    [
        ("Portable Lint Remover Pet Fur", "SEM MARCA"),
        ("USB Charger Dual Port", "SEM MARCA"),
        ("4 in 1 Handheld Cutter", "SEM MARCA"),
        ("C (DEVICE) Lint Remover", "SEM MARCA"),
        ("Newly Launched Boult Dive+ Watch", "BOULT"),
        ("HP Wireless Mouse", "HP"),
        ("3M Scotch Tape", "3M"),
    ],
)
def test_extract_brand_sem_marca_e_siglas(product_name, expected_brand):
    assert extract_brand(pd.Series([product_name])).iloc[0] == expected_brand


def test_extract_brand_usa_primeira_palavra():
    assert extract_brand(pd.Series(["Wayona Cable 3FT"])).iloc[0] == "WAYONA"


@pytest.mark.parametrize(
    ("product_name", "expected_brand"),
    [
        ("AmazonBasics HDMI Cable", "AMAZON BASICS"),
        ("Amazonbasics Nylon Cable", "AMAZON BASICS"),
        ("Amazon Basics Wireless Mouse", "AMAZON BASICS"),
        ("Amazon Brand - Solimo 3A Cable", "SOLIMO"),
    ],
)
def test_extract_brand_unifica_marcas_da_amazon(product_name, expected_brand):
    assert extract_brand(pd.Series([product_name])).iloc[0] == expected_brand


def test_transform_produtos_rating_count_nulo_vira_zero():
    result = transform_produtos(pd.DataFrame([build_raw_row(rating_count=None)]))
    assert result["rating_count"].iloc[0] == 0
    assert result["receita_proxy"].iloc[0] == 0


def test_remove_duplicate_products_mantem_primeira_ocorrencia():
    raw = pd.DataFrame([build_raw_row(rating="4.2"), build_raw_row(rating="1.0")])
    result = remove_duplicate_products(raw)
    assert len(result) == 1
    assert result["rating"].iloc[0] == "4.2"


def test_transform_produtos_calcula_colunas_derivadas():
    result = transform_produtos(pd.DataFrame([build_raw_row()]))
    row = result.iloc[0]
    assert row["discount_amount"] == 700
    assert row["discount_pct"] == 64
    assert row["receita_proxy"] == 399 * 24269
    assert row["marca"] == "WAYONA"
    assert "\n" not in row["about_product"]


def test_transform_produtos_id_unico():
    raw = pd.DataFrame([build_raw_row(), build_raw_row(), build_raw_row(product_id="P2")])
    assert transform_produtos(raw)["id_produto"].is_unique
