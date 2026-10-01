"""Constantes, caminhos e nomes de colunas do pipeline."""
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

ENV_RAW_CSV_PATH = "ETL_RAW_CSV_PATH"
ENV_OUTPUT_DIR = "ETL_OUTPUT_DIR"

RAW_CSV_PATH = Path(os.environ.get(ENV_RAW_CSV_PATH, PROJECT_ROOT / "data" / "raw" / "amazon.csv"))
OUTPUT_DIR = Path(os.environ.get(ENV_OUTPUT_DIR, PROJECT_ROOT / "saida_bi"))

RAW_CSV_ENCODING = "utf-8"
EXPORT_CSV_ENCODING = "utf-8-sig"
EXPORT_DECIMAL_SEPARATOR = ","

# Colunas do arquivo bruto
COL_PRODUCT_ID = "product_id"
COL_PRODUCT_NAME = "product_name"
COL_CATEGORY = "category"
COL_DISCOUNTED_PRICE = "discounted_price"
COL_ACTUAL_PRICE = "actual_price"
COL_DISCOUNT_PERCENTAGE = "discount_percentage"
COL_RATING = "rating"
COL_RATING_COUNT = "rating_count"
COL_ABOUT_PRODUCT = "about_product"
COL_IMG_LINK = "img_link"
COL_PRODUCT_LINK = "product_link"

# Colunas de fato_produto (nomes do DER)
COL_ID_PRODUTO = "id_produto"
COL_BRAND = "marca"
COL_DISCOUNT_AMOUNT = "discount_amount"
COL_DISCOUNT_PCT = "discount_pct"
COL_REVENUE_PROXY = "receita_proxy"

# Limpeza dos valores textuais
PRICE_NOISE_PATTERN = r"[₹,]"
PERCENT_SYMBOL = "%"
THOUSANDS_SEPARATOR = ","
LINE_BREAK_PATTERN = r"\s*[\r\n]+\s*"
LINE_BREAK_REPLACEMENT = " "

# Marca e contagem
MISSING_RATING_COUNT = 0
BRAND_NOISE_PREFIX_PATTERN = r"(?i)^(?:amazon\s*brand\s*-\s*|newly\s+launched\s+)"
NO_BRAND_LABEL = "SEM MARCA"
NO_BRAND_JUNK_PATTERN = r"^(?:\w|\d+)$"
BRAND_SYMBOLS_PATTERN = r"[®™]"
BRAND_TRAILING_PUNCTUATION_PATTERN = r"[^\w\s]+$"

# Primeiras palavras que descrevem o produto, não a marca (em maiúsculas)
GENERIC_BRAND_WORDS = (
    "BRAND",
    "EMPTY",
    "FIRESTICK",
    "GENERIC",
    "LINT",
    "MILK",
    "MONITOR",
    "MULTIFUNCTIONAL",
    "PERSONAL",
    "PORTABLE",
    "REMOTE",
    "ROOM",
    "SILICONE",
    "TIME",
    "UNIVERSAL",
    "USB",
)

# Variações de escrita que devem virar uma única marca: {regex do início do nome: marca}
BRAND_ALIASES = {
    r"(?i)^amazon\s*basics": "Amazon Basics",
    r"(?i)^black\s*\+\s*decker": "Black+Decker",
}

# Marcas de mais de uma palavra (a extração usa só a 1ª palavra para as demais)
COMPOSITE_BRANDS = (
    "Ant Esports",
    "Ao Smith",
    "American Micronic",
    "Cafe Jei",
    "Csi International",
    "Dr Trust",
    "En Ligne",
    "Eureka Forbes",
    "Green Tales",
    "Heart Home",
    "House Of Quirk",
    "Instant Pot",
    "King Shine",
    "Kitchen Kit",
    "Kitchen Mart",
    "Kuber Industries",
    "Maharaja Whiteline",
    "Morphy Richards",
    "Mr. Brand",
    "Orient Electric",
    "Pc Square",
    "Pick Ur Needs",
    "R B Nova",
    "Rc Print",
    "Royal Step",
    "Shakti Technology",
    "Sure From Aquaguard",
    "Swiss Military",
    "Table Magic",
    "Tata Sky",
    "Western Digital",
    "White Feather",
)

# Reviews e usuários
COL_USER_ID = "user_id"
COL_USER_NAME = "user_name"
COL_REVIEW_ID = "review_id"
COL_ID_USUARIO = "id_usuario"
COL_REVIEW_COUNT = "qtd_reviews_amostra"
LIST_SEPARATOR = ","
USER_NAME_SEPARATOR_PATTERN = r",(?!\s)"  # vírgula seguida de espaço faz parte do nome
NO_USER_NAME_LABEL = "SEM NOME"
FIRST_SURROGATE_ID = 1
# Correções manuais de nome (user_id -> nome), informadas pelo usuário ou confirmadas no perfil da Amazon; valem sobre o nome do bruto.
USER_NAME_CORRECTIONS = {
    "AFZ7BSWDEUCVHARR4CX2UCO5VZEA": "RUPESH BISHT",
    "AHFKTS4EHCDCYQS425TALOSRSNHQ": "Sinoj Mullangath",
    "AF65MIICMJTPBXOMJVXMRXJO564A": "Charles",
    "AEUDRXQAIOQFAJMC2HXHA5I726VA": "Sanjeev Khurana",
    "AGHNUCRUYQXMP4652XV7ZVK5DPMQ": "Dhruvil",
    "AFJQ6LWTWGENRRJXZLWWX27YREJA": "Pradeep,Tcr",
    "AFWKRJGICXU2EXDCHLR5AXVCMQEA": "JULFIKKAR MONDAL",
    "AHFOGTDIQHP3LINYF4EQOBZ6GKZQ": "CM",
    "AEQ2YMXSZWEOHK2EHTNLOS56YTZQ": "Jayesh",
    "AGRVINWECNY7323CWFXZYYIZOFTQ": "Rajesh k.",
    "AHFAAPSY2MJ5HYOU2VQDJ7AQY4NQ": "dinesh",
    "AH2WGV2PEBUTICRPBEEVKF24G5LA": "Chitra",
    "AEP4MK3EKOBDKTGPJTRN5RBDIODA": "Ajaybabu.O.M",
    "AF7NDY2H6JVYTSQOZP76GCATQ34Q": "Placeholder",
    "AHBAT6VLOXWGYDL57KHCNCLPXAKA": "Ibn moosa",
}

# Tabelas de saída (nome do CSV = nome da tabela no DER)
TABLE_FATO_PRODUTO = "fato_produto"
TABLE_FATO_REVIEW = "fato_review"
TABLE_DIM_USUARIO = "dim_usuario"
TABLE_DIM_CATEGORIA = "dim_categoria"
TABLE_DIM_FAIXA_DESCONTO = "dim_faixa_desconto"
TABLE_DIM_FAIXA_PRECO = "dim_faixa_preco"
TABLE_DIM_FAIXA_RATING = "dim_faixa_rating"
TABLE_DIM_QUADRANTE = "dim_quadrante"
CSV_EXTENSION = ".csv"

# Chaves substitutas e colunas das dimensões
COL_ID_CATEGORIA = "id_categoria"
COL_ID_FAIXA_DESCONTO = "id_faixa_desconto"
COL_ID_FAIXA_PRECO = "id_faixa_preco"
COL_ID_FAIXA_RATING = "id_faixa_rating"
COL_ID_QUADRANTE = "id_quadrante"
COL_FAIXA = "faixa"
COL_ORDEM = "ordem"
COL_PCT_MIN = "pct_min"
COL_PCT_MAX = "pct_max"
COL_PRECO_MIN = "preco_min"
COL_PRECO_MAX = "preco_max"
COL_RATING_MIN = "rating_min"
COL_RATING_MAX = "rating_max"
COL_QUADRANTE = "quadrante"
COL_ENGAJAMENTO = "engajamento"
COL_SATISFACAO = "satisfacao"
COL_ACAO_SUGERIDA = "acao_sugerida"
COL_REGRA = "regra"
COL_CATEGORY_LEVELS = ("nivel_1", "nivel_2", "nivel_3")
COL_CATEGORY_LEAF = "categoria_folha"
COL_CATEGORY_PATH = "category_path"
CATEGORY_SEPARATOR = "|"

# Faixas: (mínimo, máximo, rótulo) em intervalos [mínimo, máximo); máximo None = sem teto
PRICE_BANDS = (
    (0, 200, "₹0–199"),
    (200, 500, "₹200–499"),
    (500, 1000, "₹500–999"),
    (1000, 2000, "₹1.000–1.999"),
    (2000, 5000, "₹2.000–4.999"),
    (5000, None, "₹5.000+"),
)
DISCOUNT_BANDS = (
    (0, 10, "0–9%"),
    (10, 25, "10–24%"),
    (25, 40, "25–39%"),
    (40, 55, "40–54%"),
    (55, 70, "55–69%"),
    (70, None, "70%+"),
)
RATING_BANDS = (
    (0, 3.5, "Abaixo de 3,5"),
    (3.5, 4.0, "3,5 a 3,9"),
    (4.0, 4.2, "4,0 a 4,1"),
    (4.2, 4.5, "4,2 a 4,4"),
    (4.5, None, "4,5 a 5,0"),
)
NO_RATING_BAND_LABEL = "Sem avaliação"
RATING_DECIMAL_PLACES = 1

# Quadrantes: engajamento alto = rating_count > mediana; satisfação alta = rating >= mínimo
SATISFACTION_MIN_RATING = 4.0
HIGH_ENGAGEMENT = "Alto"
LOW_ENGAGEMENT = "Baixo"
UNDEFINED_ENGAGEMENT = "Indefinido"
HIGH_SATISFACTION = "Alta"
LOW_SATISFACTION = "Baixa"
UNDEFINED_SATISFACTION = "Indefinida"
QUADRANTS = (
    ("Estrelas", HIGH_ENGAGEMENT, HIGH_SATISFACTION, "Manter e destacar",
     "rating_count > mediana e rating >= 4,0"),
    ("Promessas", LOW_ENGAGEMENT, HIGH_SATISFACTION, "Divulgar mais",
     "rating_count <= mediana e rating >= 4,0"),
    ("Problemáticos", HIGH_ENGAGEMENT, LOW_SATISFACTION, "Corrigir qualidade",
     "rating_count > mediana e rating < 4,0"),
    ("Descartáveis", LOW_ENGAGEMENT, LOW_SATISFACTION, "Revisar ou descontinuar",
     "rating_count <= mediana e rating < 4,0"),
    ("Sem dados", UNDEFINED_ENGAGEMENT, UNDEFINED_SATISFACTION, "Coletar avaliações",
     "rating ausente"),
)

# Colunas de fato_produto na ordem do DER
FATO_PRODUTO_COLUMNS = (
    COL_ID_PRODUTO, COL_ID_CATEGORIA, COL_ID_FAIXA_DESCONTO, COL_ID_FAIXA_PRECO,
    COL_ID_FAIXA_RATING, COL_ID_QUADRANTE, COL_PRODUCT_NAME, COL_BRAND, COL_ABOUT_PRODUCT,
    COL_PRODUCT_LINK, COL_IMG_LINK, COL_ACTUAL_PRICE, COL_DISCOUNTED_PRICE,
    COL_DISCOUNT_AMOUNT, COL_DISCOUNT_PCT, COL_RATING, COL_RATING_COUNT, COL_REVENUE_PROXY,
    COL_REVIEW_COUNT,
)
NULLABLE_FATO_PRODUTO_COLUMNS = (COL_RATING,)  # produto sem nota segue nulo, mas tem faixa e quadrante

# Validações antes de exportar
PRIMARY_KEYS = {
    TABLE_FATO_PRODUTO: [COL_ID_PRODUTO],
    TABLE_FATO_REVIEW: [COL_REVIEW_ID, COL_ID_PRODUTO],
    TABLE_DIM_USUARIO: [COL_ID_USUARIO],
    TABLE_DIM_CATEGORIA: [COL_ID_CATEGORIA],
    TABLE_DIM_FAIXA_DESCONTO: [COL_ID_FAIXA_DESCONTO],
    TABLE_DIM_FAIXA_PRECO: [COL_ID_FAIXA_PRECO],
    TABLE_DIM_FAIXA_RATING: [COL_ID_FAIXA_RATING],
    TABLE_DIM_QUADRANTE: [COL_ID_QUADRANTE],
}
# (tabela, coluna do FK, tabela de destino)
FOREIGN_KEYS = (
    (TABLE_FATO_PRODUTO, COL_ID_CATEGORIA, TABLE_DIM_CATEGORIA),
    (TABLE_FATO_PRODUTO, COL_ID_FAIXA_DESCONTO, TABLE_DIM_FAIXA_DESCONTO),
    (TABLE_FATO_PRODUTO, COL_ID_FAIXA_PRECO, TABLE_DIM_FAIXA_PRECO),
    (TABLE_FATO_PRODUTO, COL_ID_FAIXA_RATING, TABLE_DIM_FAIXA_RATING),
    (TABLE_FATO_PRODUTO, COL_ID_QUADRANTE, TABLE_DIM_QUADRANTE),
    (TABLE_FATO_REVIEW, COL_ID_PRODUTO, TABLE_FATO_PRODUTO),
    (TABLE_FATO_REVIEW, COL_ID_USUARIO, TABLE_DIM_USUARIO),
)
INTEGER_ID_COLUMNS = (
    COL_ID_CATEGORIA, COL_ID_FAIXA_DESCONTO, COL_ID_FAIXA_PRECO, COL_ID_FAIXA_RATING,
    COL_ID_QUADRANTE, COL_ID_USUARIO,
)
