# =========================================================
# BASE IMAGE
# =========================================================
FROM python:3.11-slim

# =========================================================
# ENVIRONMENT VARIABLES
# =========================================================
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    NUMBA_DISABLE_CUDA=1 \
    PIP_NO_CACHE_DIR=1 \

WORKDIR /app

# =========================================================
# SYSTEM DEPENDENCIES
# =========================================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    cmake \
    python3-dev \
    libgomp1 \
    llvm \
    llvm-dev \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# =========================================================
# COPY REQUIREMENTS
# =========================================================
COPY requirements.txt .

# =========================================================
# PYTHON PACKAGE INSTALLATION
# =========================================================

RUN pip install --upgrade pip setuptools wheel

# Remove incompatible packages if resolver added them
RUN pip uninstall -y \
    shap \
    numba \
    llvmlite \
    nvidia-nccl-cu12 \
    || true

# Stable scientific stack
RUN pip install \
    numpy==1.26.4 \
    scipy==1.12.0 \
    scikit-learn==1.4.2

# Stable SHAP stack
RUN pip install \
    numba==0.59.1 \
    llvmlite==0.42.0 \
    shap==0.45.1

# Install remaining dependencies
RUN pip install -r requirements.txt

# Databricks SDKs
RUN pip install \
    databricks-vectorsearch \
    databricks-sdk

# =========================================================
# VERIFY IMPORTS
# =========================================================
RUN python -c "import numba; print('NUMBA OK')" && \
    python -c "import llvmlite; print('LLVM OK')" && \
    python -c "import xgboost; print('XGBOOST OK')"

# =========================================================
# COPY APPLICATION FILES
# =========================================================
COPY artifacts/ ./artifacts/
COPY LLM/ ./LLM/
COPY ML/ ./ML/
COPY RAG/ ./RAG/
COPY Rule_Engine/ ./Rule_Engine/
COPY util/ ./util/
COPY logs/ ./logs/

COPY config.py .
COPY app.py .
COPY transformations.py .

# =========================================================
# EXPOSE PORT
# =========================================================
EXPOSE 8080

# =========================================================
# START APPLICATION
# =========================================================
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
