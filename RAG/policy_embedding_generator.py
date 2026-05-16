import uuid
import pandas as pd
import os 

from pyspark.sql import SparkSession
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
TABLE_NAME = "policy_embedding"

EMBEDDING_MODEL = "databricks-gte-large-en"

POLICY_FILE = "Input/policies.txt"


# ------------------------------------------------ #
# LOAD POLICY TEXT
# ------------------------------------------------ #

with open(POLICY_FILE, "r") as f:
    policy_text = f.read()


# ------------------------------------------------ #
# CATEGORICAL CHUNKING
# (Example section-based split)
# ------------------------------------------------ #

# Assume sections separated using:
# SECTION: <title>

sections = policy_text.split("SECTION:")

categorical_chunks = []

for idx, section in enumerate(sections):

    section = section.strip()

    if not section:
        continue

    lines = section.split("\n")

    title = lines[0].strip()

    section_text = "\n".join(lines[1:]).strip()

    categorical_chunks.append({
        "policy_id": "CMS_POLICY_001",
        "chunk_id": str(uuid.uuid4()),
        "chunk_type": "categorical",
        "title": title,
        "section": title,
        "chunk_text": section_text
    })


# ------------------------------------------------ #
# SEMANTIC CHUNKING
# ------------------------------------------------ #

# splitter = RecursiveCharacterTextSplitter(
#     chunk_size=500,
#     chunk_overlap=100
# )

# semantic_text_chunks = splitter.split_text(policy_text)

# semantic_chunks = []

# for chunk in semantic_text_chunks:

#     semantic_chunks.append({
#         "policy_id": "CMS_POLICY_001",
#         "chunk_id": str(uuid.uuid4()),
#         "chunk_type": "semantic",
#         "title": "General Policy",
#         "section": "Semantic Split",
#         "chunk_text": chunk
#     })


# ------------------------------------------------ #
# MERGE ALL CHUNKS
# ------------------------------------------------ #

all_chunks = categorical_chunks #+ semantic_chunks

# print(f"Total Chunks Created: {len(all_chunks)}")


# ------------------------------------------------ #
# DATABRICKS EMBEDDING CLIENT
# ------------------------------------------------ #

os.environ["DATABRICKS_TOKEN"] = os.getenv("DATABRICKS_TOKEN_ID")
w = WorkspaceClient()


def generate_embedding(text):

    response = w.serving_endpoints.query(
        name=EMBEDDING_MODEL,
        input= [text]
    )

    embedding = response.data[0].embedding

    return embedding


# ------------------------------------------------ #
# GENERATE EMBEDDINGS
# ------------------------------------------------ #

records = []

for chunk in all_chunks:
    # embedding = generate_embedding(chunk["chunk_text"]) #add custom embedding model eg. BERT, OpenAI Embedder ...
    records.append({
            "policy_id": chunk["policy_id"],
            "chunk_id": chunk["chunk_id"],
            "chunk_type": chunk["chunk_type"],
            "title": chunk["title"],
            "section": chunk["section"],
            "chunk_text": chunk["chunk_text"],
            # "embedding": embedding #add embedding here for custom embedder 
        })

    

# ------------------------------------------------ #
# CREATE SPARK DATAFRAME
# ------------------------------------------------ #

schema = StructType([
    StructField("policy_id", StringType(), True),
    StructField("chunk_id", StringType(), True),
    StructField("chunk_type", StringType(), True),
    StructField("title", StringType(), True),
    StructField("section", StringType(), True),
    StructField("chunk_text", StringType(), True),
    # StructField("embedding", ArrayType(FloatType()), True)
])

spark_df = spark.createDataFrame(records, schema=schema)


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

print("Policy embeddings stored successfully.")