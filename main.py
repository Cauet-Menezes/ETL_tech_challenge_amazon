"""Executa o pipeline: extração, transformações, validações e exportação dos CSVs."""
from src.build_gold import build_gold_tables, export_gold_tables, validate_gold_tables
from src.config import OUTPUT_DIR
from src.extract import extract_raw_amazon
from src.transform_produtos import transform_produtos
from src.transform_reviews import transform_reviews


def run_pipeline() -> None:
    """Roda o ETL completo e grava os CSVs em OUTPUT_DIR."""
    raw_df = extract_raw_amazon()
    products = transform_produtos(raw_df)
    dim_usuario, fato_review = transform_reviews(raw_df)
    tables = build_gold_tables(products, dim_usuario, fato_review)
    validate_gold_tables(tables)
    export_gold_tables(tables)
    for name, table in tables.items():
        print(f"{name}: {len(table)} linhas")
    print(f"CSVs gravados em {OUTPUT_DIR}")


if __name__ == "__main__":
    run_pipeline()
