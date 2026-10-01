"""Limpeza e tipagem dos produtos (base de fato_produto)."""
import re

import pandas as pd

from src.config import (
    BRAND_ALIASES,
    BRAND_NOISE_PREFIX_PATTERN,
    BRAND_SYMBOLS_PATTERN,
    BRAND_TRAILING_PUNCTUATION_PATTERN,
    COL_ABOUT_PRODUCT,
    COL_ACTUAL_PRICE,
    COL_BRAND,
    COL_CATEGORY,
    COL_DISCOUNT_AMOUNT,
    COL_DISCOUNT_PCT,
    COL_DISCOUNT_PERCENTAGE,
    COL_DISCOUNTED_PRICE,
    COL_ID_PRODUTO,
    COL_IMG_LINK,
    COL_PRODUCT_ID,
    COL_PRODUCT_LINK,
    COL_PRODUCT_NAME,
    COL_RATING,
    COL_RATING_COUNT,
    COL_REVENUE_PROXY,
    COMPOSITE_BRANDS,
    GENERIC_BRAND_WORDS,
    LINE_BREAK_PATTERN,
    LINE_BREAK_REPLACEMENT,
    MISSING_RATING_COUNT,
    NO_BRAND_JUNK_PATTERN,
    NO_BRAND_LABEL,
    PERCENT_SYMBOL,
    PRICE_NOISE_PATTERN,
    THOUSANDS_SEPARATOR,
)


def clean_price(prices: pd.Series) -> pd.Series:
    """Converte textos como '₹1,099' em número."""
    return pd.to_numeric(prices.str.replace(PRICE_NOISE_PATTERN, "", regex=True), errors="coerce")


def clean_percentage(percentages: pd.Series) -> pd.Series:
    """Converte textos como '64%' em número (64)."""
    return pd.to_numeric(percentages.str.replace(PERCENT_SYMBOL, "", regex=False), errors="coerce")


def clean_count(counts: pd.Series) -> pd.Series:
    """Converte textos como '24,269' em inteiro anulável."""
    without_separator = counts.str.replace(THOUSANDS_SEPARATOR, "", regex=False)
    return pd.to_numeric(without_separator, errors="coerce").astype("Int64")


def clean_rating(ratings: pd.Series) -> pd.Series:
    """Converte a nota em número; valores inválidos (ex.: '|') viram nulo."""
    return pd.to_numeric(ratings, errors="coerce")


def remove_line_breaks(texts: pd.Series) -> pd.Series:
    """Troca quebras de linha por um espaço."""
    return texts.str.replace(LINE_BREAK_PATTERN, LINE_BREAK_REPLACEMENT, regex=True)


def build_composite_brand_pattern(brands: tuple[str, ...]) -> str:
    """Monta o regex que reconhece qualquer marca composta no início do nome."""
    alternatives = "|".join(r"\s+".join(map(re.escape, brand.split())) for brand in brands)
    return rf"(?i)^({alternatives})(?!\w)"


COMPOSITE_BRAND_PATTERN = build_composite_brand_pattern(COMPOSITE_BRANDS)


def apply_brand_aliases(brands: pd.Series, names: pd.Series) -> pd.Series:
    """Unifica as variações de escrita de uma mesma marca."""
    for pattern, canonical_brand in BRAND_ALIASES.items():
        brands = brands.mask(names.str.match(pattern).fillna(False).astype(bool), canonical_brand)
    return brands


def clean_brand_symbols(brands: pd.Series) -> pd.Series:
    """Remove ®, ™ e pontuação no fim da marca."""
    without_symbols = brands.str.replace(BRAND_SYMBOLS_PATTERN, "", regex=True)
    return without_symbols.str.replace(BRAND_TRAILING_PUNCTUATION_PATTERN, "", regex=True)


def label_missing_brands(brands: pd.Series) -> pd.Series:
    """Troca palavras genéricas, letras soltas e números por 'SEM MARCA'."""
    is_junk = brands.str.match(NO_BRAND_JUNK_PATTERN).fillna(False).astype(bool)
    return brands.mask(is_junk | brands.isin(GENERIC_BRAND_WORDS), NO_BRAND_LABEL)


def extract_brand(product_names: pd.Series) -> pd.Series:
    """Extrai a marca em maiúsculas (composta conhecida ou 1ª palavra); sem marca vira SEM MARCA."""
    names = product_names.str.replace(BRAND_NOISE_PREFIX_PATTERN, "", regex=True)
    composite_brands = names.str.extract(COMPOSITE_BRAND_PATTERN, expand=False)
    brands = composite_brands.fillna(names.str.split().str[0])
    brands = brands.str.split().str.join(" ")
    cleaned_brands = clean_brand_symbols(apply_brand_aliases(brands, names)).str.upper()
    return label_missing_brands(cleaned_brands)


def remove_duplicate_products(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Mantém a primeira ocorrência de cada product_id."""
    return raw_df.drop_duplicates(subset=COL_PRODUCT_ID, keep="first").reset_index(drop=True)


def clean_product_columns(products: pd.DataFrame) -> pd.DataFrame:
    """Limpa e tipa as colunas de produto vindas do bruto."""
    return pd.DataFrame(
        {
            COL_ID_PRODUTO: products[COL_PRODUCT_ID],
            COL_PRODUCT_NAME: products[COL_PRODUCT_NAME],
            COL_BRAND: extract_brand(products[COL_PRODUCT_NAME]),
            COL_CATEGORY: products[COL_CATEGORY],
            COL_ABOUT_PRODUCT: remove_line_breaks(products[COL_ABOUT_PRODUCT]),
            COL_PRODUCT_LINK: products[COL_PRODUCT_LINK],
            COL_IMG_LINK: products[COL_IMG_LINK],
            COL_ACTUAL_PRICE: clean_price(products[COL_ACTUAL_PRICE]),
            COL_DISCOUNTED_PRICE: clean_price(products[COL_DISCOUNTED_PRICE]),
            COL_DISCOUNT_PCT: clean_percentage(products[COL_DISCOUNT_PERCENTAGE]),
            COL_RATING: clean_rating(products[COL_RATING]),
            COL_RATING_COUNT: clean_count(products[COL_RATING_COUNT]).fillna(MISSING_RATING_COUNT),
        }
    )


def add_derived_columns(products: pd.DataFrame) -> pd.DataFrame:
    """Calcula discount_amount e receita_proxy."""
    return products.assign(
        **{
            COL_DISCOUNT_AMOUNT: products[COL_ACTUAL_PRICE] - products[COL_DISCOUNTED_PRICE],
            COL_REVENUE_PROXY: products[COL_DISCOUNTED_PRICE] * products[COL_RATING_COUNT],
        }
    )


def transform_produtos(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Gera os produtos limpos, uma linha por id_produto (mantém category para a dimensão)."""
    unique_products = remove_duplicate_products(raw_df)
    return add_derived_columns(clean_product_columns(unique_products))
