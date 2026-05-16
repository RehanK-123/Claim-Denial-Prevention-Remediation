import uuid
import pandas as pd
import os
import re

from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    ArrayType,
    FloatType
)

from langchain_text_splitters import RecursiveCharacterTextSplitter

from databricks.sdk import WorkspaceClient

from util.dao import DAO
from util.utils import spark, logger


# ------------------------------------------------ #
# CONFIG
# ------------------------------------------------ #

CATALOG = "newcatalog"
SCHEMA = "gold"

TABLE_NAME = "fixes_embedding"

EMBEDDING_MODEL = "databricks-gte-large-en"

FIXES_FILE = "Input/fixes.txt"


# ------------------------------------------------ #
# LOAD FIXES TEXT
# ------------------------------------------------ #

with open(FIXES_FILE, "r") as f:
    fixes_text = f.read()


# ------------------------------------------------ #
# CATEGORICAL CHUNKING
# ------------------------------------------------ #
#
# Splits using:
# ISSUE:
#
# Each issue becomes a structured chunk
#
# ------------------------------------------------ #

issue_sections = re.split(r"ISSUE:", fixes_text)

categorical_chunks = []

for section in issue_sections:

    section = section.strip()

    if not section:
        continue

    lines = section.split("\n")

    issue_title = lines[0].strip()

    full_text = "\n".join(lines).strip()

    # Extract category if present above
    category_match = re.search(
        r"CATEGORY:\s*(.*?)\n",
        fixes_text
    )

    category = (
        category_match.group(1)
        if category_match
        else "GENERAL"
    )

    categorical_chunks.append({
        "fix_id": "CLAIM_FIX_001",
        "chunk_id": str(uuid.uuid4()),
        "chunk_type": "categorical",
        "category": category,
        "title": issue_title,
        "section": issue_title,
        "chunk_text": full_text
    })


# # ------------------------------------------------ #
# # SEMANTIC CHUNKING
# # ------------------------------------------------ #

# splitter = RecursiveCharacterTextSplitter(
#     chunk_size=800,
#     chunk_overlap=150
# )

# semantic_text_chunks = splitter.split_text(fixes_text)

# semantic_chunks = []

# for chunk in semantic_text_chunks:

#     semantic_chunks.append({
#         "fix_id": "CLAIM_FIX_001",
#         "chunk_id": str(uuid.uuid4()),
#         "chunk_type": "semantic",
#         "category": "SEMANTIC",
#         "title": "General Fix Guidance",
#         "section": "Semantic Split",
#         "chunk_text": chunk
#     })


# ------------------------------------------------ #
# MERGE ALL CHUNKS
# ------------------------------------------------ #

all_chunks = categorical_chunks

print(f"Total Chunks Created: {len(all_chunks)}")


# ------------------------------------------------ #
# DATABRICKS EMBEDDING CLIENT
# ------------------------------------------------ #

os.environ["DATABRICKS_TOKEN"] = os.getenv(
    "DATABRICKS_TOKEN_ID"
)

# w = WorkspaceClient()


# def generate_embedding(text):

#     response = w.serving_endpoints.query(
#         name=EMBEDDING_MODEL,
#         input=[text]
#     )

#     embedding = response.data[0].embedding

#     return embedding


# ------------------------------------------------ #
# GENERATE EMBEDDINGS
# ------------------------------------------------ #

records = []

for chunk in all_chunks:

    try:

        # embedding = generate_embedding(
        #     chunk["chunk_text"]
        # )

        records.append({
            "fix_id": chunk["fix_id"],
            "chunk_id": chunk["chunk_id"],
            "chunk_type": chunk["chunk_type"],
            "category": chunk["category"],
            "title": chunk["title"],
            "section": chunk["section"],
            "chunk_text": chunk["chunk_text"],
            # "embedding": embedding
        })

        print(
            f"Embedded chunk: {chunk['chunk_id']}"
        )

    except Exception as e:

        logger.error(
            f"Embedding failed for chunk "
            f"{chunk['chunk_id']}: {e}"
        )


# ------------------------------------------------ #
# CREATE SPARK DATAFRAME
# ------------------------------------------------ #

schema = StructType([
    StructField("fix_id", StringType(), True),
    StructField("chunk_id", StringType(), True),
    StructField("chunk_type", StringType(), True),
    StructField("category", StringType(), True),
    StructField("title", StringType(), True),
    StructField("section", StringType(), True),
    StructField("chunk_text", StringType(), True),
    # StructField(
    #     "embedding",
    #     ArrayType(FloatType()),
    #     True
    # )
])

spark_df = spark.createDataFrame(
    records,
    schema=schema
)


# ------------------------------------------------ #
# STORE USING DAO
# ------------------------------------------------ #

dao = DAO(
    spark=spark,
    catalog=CATALOG,
    schema=SCHEMA
)

dao.create_table(
    TABLE_NAME,
    spark_df
)

print("Fix embeddings stored successfully.")