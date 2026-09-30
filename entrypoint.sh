#!/bin/sh

set -e

echo "========================================"
echo " INICIANDO BACKEND PYTHON"
echo "========================================"

REPO_URL="${GITHUB_REPO_URL}"
BRANCH="${GITHUB_BRANCH:-main}"
REPO_DIR="/app/repository"

echo "Repositorio: ${REPO_URL}"
echo "Rama: ${BRANCH}"

if [ -z "${REPO_URL}" ]; then
    echo "ERROR: GITHUB_REPO_URL no está configurado."
    exit 1
fi

echo "----------------------------------------"
echo "Actualizando código desde GitHub..."
echo "----------------------------------------"

if [ ! -d "${REPO_DIR}/.git" ]; then

    echo "Repositorio no encontrado."
    echo "Clonando desde GitHub..."

    git clone \
        --branch "${BRANCH}" \
        --single-branch \
        "${REPO_URL}" \
        "${REPO_DIR}"

else

    echo "Repositorio existente."
    echo "Descargando cambios..."

    cd "${REPO_DIR}"

    git fetch origin "${BRANCH}"

    git reset --hard "origin/${BRANCH}"

    git clean -fd

fi

echo "----------------------------------------"
echo "Código actualizado."
echo "----------------------------------------"

cd "${REPO_DIR}"

echo "Commit actual:"
git log -1 --oneline

echo "----------------------------------------"
echo "Instalando dependencias..."
echo "----------------------------------------"

if [ -f requirements.txt ]; then
    pip install --no-cache-dir -r requirements.txt
fi

echo "----------------------------------------"
echo "Iniciando FastAPI..."
echo "----------------------------------------"

exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000