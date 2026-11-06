#!/usr/bin/env bash
# ==============================================================================
# Apuana HPC - Script de Publicação Automática no GitHub Pages
# ==============================================================================
# Este script:
# 1. Executa o export_dashboard.py para consultar o PostgreSQL e gerar o dist/
# 2. Faz o deploy dos arquivos estáticos para o GitHub Pages
#
# Pode ser agendado no crontab do nó manager:
# */10 * * * * /bin/bash /caminho/cluster_apuana/usage_monitor/dashboard/deploy_gh_pages.sh >> /var/log/apuana_dashboard.log 2>&1
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DIST_DIR="$SCRIPT_DIR/dist"

cd "$PROJECT_ROOT"

echo "=================================================="
echo "Sincronização Iniciada: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=================================================="

# 1. Executar gerador de dashboard
if python3 "$SCRIPT_DIR/export_dashboard.py"; then
    echo "[✓] Métricas extraídas e HTML compilado com sucesso."
else
    echo "[!] Falha ao extrair do PostgreSQL. Verifique a conexão com o banco."
    exit 1
fi

# ==============================================================================
# OPÇÃO A: Deploy para Repositório Separado (Recomendado para não poluir o histórico)
# ==============================================================================
# Caso você tenha um repositório dedicado (ex: https://github.com/seu-lab/apuana-status):
# Descomente e ajuste as linhas abaixo:
#
# STATUS_REPO_DIR="/home/usuario/apuana-status"
# if [ -d "$STATUS_REPO_DIR" ]; then
#     echo "[i] Copiando arquivos para o repositório de status..."
#     cp -r "$DIST_DIR"/* "$STATUS_REPO_DIR/"
#     cd "$STATUS_REPO_DIR"
#     git add -A
#     # Só comita se houver mudanças reais
#     if ! git diff-index --quiet HEAD --; then
#         git commit -m "Auto-update telemetry: $(date '+%Y-%m-%d %H:%M:%S') [skip ci]"
#         git push origin main
#         echo "[✓] Publicado com sucesso no GitHub Pages!"
#     else
#         echo "[i] Nenhuma alteração nas métricas desde a última execução."
#     fi
#     exit 0
# fi

# ==============================================================================
# OPÇÃO B: Deploy via branch 'gh-pages' no repositório local atual
# ==============================================================================
echo "[i] Preparando envio para branch gh-pages..."

# Cria um repositório git temporário dentro de dist/ para push órfão limpo
TEMP_DEPLOY_DIR=$(mktemp -d)
cp -r "$DIST_DIR"/* "$TEMP_DEPLOY_DIR/"

cd "$TEMP_DEPLOY_DIR"
git init -q
git config user.name "Apuana Monitor Bot"
git config user.email "bot@apuana.local"
git checkout -b gh-pages -q
git add -A
git commit -m "Cluster telemetry update: $(date '+%Y-%m-%d %H:%M:%S') [skip ci]" -q

# Pega o remote origin do repositório principal
REMOTE_URL=$(git -C "$PROJECT_ROOT" remote get-url origin 2>/dev/null || echo "")

if [ -n "$REMOTE_URL" ]; then
    echo "[i] Enviando para $REMOTE_URL (branch: gh-pages)..."
    git push --force "$REMOTE_URL" gh-pages:gh-pages
    echo "[✓] GitHub Pages atualizado com sucesso!"
else
    echo "[!] Repositório remoto 'origin' não configurado. Verifique com 'git remote -v'."
fi

# Limpeza
rm -rf "$TEMP_DEPLOY_DIR"

echo "Sincronização Finalizada: $(date '+%Y-%m-%d %H:%M:%S')"
