# Dashboard de Telemetria do Cluster Apuana (HPC)

Solução estática e desacoplada para exibição de métricas do cluster fora da VPN, substituindo o Grafana e eliminando problemas de sobrecarga de memória do Google Sheets/Looker.

---

## 🚀 Como Funciona a Arquitetura

1. **Extração e Agregação (`export_dashboard.py`)**: 
   - Roda localmente no nó manager (que tem acesso ao PostgreSQL interno e saída para a internet/GitHub).
   - Consulta apenas os dados mais recentes das tabelas (`node_state`, `gpu_log`, `queue`, `filesystem_data`, `utilization`).
   - Gera um arquivo estático leve e interativo (`dist/index.html`) e os dados em JSON (`dist/data.json`).
2. **Publicação no GitHub Pages (`deploy_gh_pages.sh`)**:
   - Faz o push periódico (via `cron`) dos arquivos estáticos para uma branch `gh-pages` (ou para um repositório dedicado).
   - Os usuários acessam via `https://<usuario-ou-org>.github.io/<repositorio>/` de qualquer lugar, celular ou computador, sem necessidade de VPN.

---

## 🛠️ Como Testar Localmente

Para visualizar o dashboard agora mesmo sem precisar estar conectado ao banco de dados interno:

```bash
# 1. Gerar com dados simulados realistas:
python3 dashboard/export_dashboard.py --mock

# 2. Abrir no navegador (no Mac):
open dashboard/dist/index.html

# Ou no Linux:
xdg-open dashboard/dist/index.html
```

Para gerar com os dados reais do PostgreSQL:
```bash
python3 dashboard/export_dashboard.py
```
*(O script utiliza automaticamente as credenciais configuradas no `.env` da raiz do projeto: `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`)*.

---

## 🌐 Configuração do GitHub Pages

### 1. Habilitar o GitHub Pages no Repositório
1. No GitHub, acesse o repositório do projeto.
2. Vá em **Settings** > **Pages** (no menu lateral esquerdo).
3. Em **Build and deployment**:
   - **Source**: `Deploy from a branch`
   - **Branch**: Selecione `gh-pages` e a pasta `/ (root)`.
   - Clique em **Save**.
4. O GitHub informará o link público (ex: `https://seu-usuario.github.io/usage_monitor/`).

### 2. Autenticação no Nó Manager
Certifique-se de que o nó manager possui uma chave SSH configurada com permissão de escrita no repositório GitHub (`ssh -T git@github.com`).

---

## ⏰ Agendamento Periódico (Crontab no Manager)

Para manter o dashboard atualizado a cada 10 minutos automaticamente:

1. No nó manager, abra o agendador:
   ```bash
   crontab -e
   ```
2. Adicione a seguinte linha (ajuste o caminho para o diretório correto):
   ```bash
   */10 * * * * /bin/bash /home/CIN/mpps/paulaperazzo/cluster_apuana/usage_monitor/dashboard/deploy_gh_pages.sh >> /tmp/apuana_dashboard.log 2>&1
   ```

---

## 💡 Dica: Repositório Dedicado de Status

Como o cron realiza commits periódicos com novas métricas, uma boa prática em HPC é criar um repositório público separado (ex: `apuana-status`):
- Mantém o repositório principal de código limpo de commits de telemetria.
- O script `deploy_gh_pages.sh` já contém as instruções comentadas para essa opção.
