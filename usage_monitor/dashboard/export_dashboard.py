#!/usr/bin/env python3
"""
Apuana HPC Cluster - Dashboard Data Extractor & HTML Generator
Queries telemetry from PostgreSQL and compiles a standalone, responsive
dashboard with GPU thermal/power telemetry, job activity history, and cluster state.
Ready for GitHub Pages export.
"""

import os
import sys
import json
import argparse
from datetime import datetime, date, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

try:
    from database import DatabaseConnection
except ImportError:
    DatabaseConnection = None

try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    env_file = BASE_DIR / ".env"
    if env_file.exists():
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


def custom_json_serializer(obj):
    """Serializes date and datetime objects for JSON output."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def generate_mock_data():
    """Generates realistic mock data with full power, temp, and jobs history."""
    now = datetime.now()
    days_labels = [(now - timedelta(days=6 - i)).strftime("%d/%m") for i in range(7)]
    
    total_watts = 0
    gpu_count = 0
    temp_sum = 0
    
    nodes = []
    for i in range(1, 11):
        is_alloc = i in [1, 2, 3, 5, 6, 7]
        is_idle = i in [4, 8, 9]
        is_down = i == 10
        
        state = "alloc" if is_alloc else ("idle" if is_idle else "down")
        label = "Alocado" if is_alloc else ("Livre" if is_idle else "Inativo")
        color = "blue" if is_alloc else ("emerald" if is_idle else "rose")
        
        node_gpus = []
        if not is_down:
            for g in range(4):
                temp = 48 + ((i * 3 + g * 7) % 32)
                p_watts = int(240 + ((i * 15 + g * 20) % 90)) if is_alloc else int(32 + ((g * 5) % 15))
                mem_used = int(40960 * (0.82 if is_alloc else 0.04))
                
                total_watts += p_watts
                temp_sum += temp
                gpu_count += 1
                
                node_gpus.append({
                    "name": f"NVIDIA A100-SXM4-40GB #{g}",
                    "temperature": temp,
                    "memory_used": mem_used,
                    "memory_total": 40960,
                    "memory_percent": int(82 if is_alloc else 4),
                    "power_watts": p_watts,
                    "power_limit_watts": 400
                })
        
        nodes.append({
            "hostname": f"cluster-node{i}",
            "state": state,
            "status_label": label,
            "status_color": color,
            "last_updated": now.strftime("%Y-%m-%d %H:%M:%S"),
            "gpus": node_gpus
        })

    avg_temp = round(temp_sum / gpu_count, 1) if gpu_count else 0
    avg_power_per_gpu = round(total_watts / gpu_count, 1) if gpu_count else 0

    return {
        "generated_at": now.strftime("%d/%m/%Y %H:%M:%S"),
        "cluster_name": "Apuana HPC Cluster",
        "summary": {
            "total_nodes": 10,
            "active_nodes": 9,
            "down_nodes": 1,
            "total_gpus": 36,
            "active_gpus": 24,
            "running_jobs": 14,
            "pending_jobs": 4,
            "total_power_kw": round(total_watts / 1000.0, 2),
            "avg_power_gpu_w": avg_power_per_gpu,
            "avg_temp_gpu_c": avg_temp,
            "jobs_today": 42,
            "overall_status": "operational"
        },
        "nodes": nodes,
        "queue": [
            {"jobid": 10421, "name": "train_bert_large", "user": "mpps", "state": "RUNNING", "state_badge": "R", "time": "12:45:10", "nodelist": "cluster-node[1-2]"},
            {"jobid": 10422, "name": "deep_rl_sim", "user": "lucasf", "state": "RUNNING", "state_badge": "R", "time": "08:12:00", "nodelist": "cluster-node3"},
            {"jobid": 10423, "name": "docking_screening", "user": "carla_bio", "state": "RUNNING", "state_badge": "R", "time": "04:30:15", "nodelist": "cluster-node5"},
            {"jobid": 10424, "name": "vit_inference", "user": "andre_cv", "state": "RUNNING", "state_badge": "R", "time": "01:15:40", "nodelist": "cluster-node6"},
            {"jobid": 10425, "name": "llama3_fine_tune", "user": "rodrigo_nlp", "state": "PENDING", "state_badge": "PD", "time": "00:00:00", "nodelist": "None (Resources)"},
            {"jobid": 10426, "name": "quantum_chem_opt", "user": "juliana_qc", "state": "PENDING", "state_badge": "PD", "time": "00:00:00", "nodelist": "None (Priority)"}
        ],
        "filesystem": [
            {"mounted": "/home", "filesystem": "/dev/sda1", "size": "10TB", "used": "7.2TB", "avail": "2.8TB", "usepercent": 72},
            {"mounted": "/data", "filesystem": "/dev/sdb1", "size": "48TB", "used": "31TB", "avail": "17TB", "usepercent": 65},
            {"mounted": "/scratch", "filesystem": "/dev/nvme0n1", "size": "8TB", "used": "3.1TB", "avail": "4.9TB", "usepercent": 39}
        ],
        "utilization_history": {
            "labels": days_labels,
            "occupation": [78.5, 82.1, 74.3, 89.0, 91.2, 85.4, 88.0],
            "idle": [18.2, 14.5, 22.0, 8.5, 6.1, 11.2, 9.5],
            "unavailability": [3.3, 3.4, 3.7, 2.5, 2.7, 3.4, 2.5]
        },
        "daily_jobs_history": {
            "labels": [(now - timedelta(days=13 - i)).strftime("%d/%m") for i in range(14)],
            "cpu_jobs": [18, 22, 15, 28, 30, 24, 19, 25, 34, 40, 31, 28, 33, 26],
            "gpu_jobs": [12, 16, 14, 20, 25, 18, 15, 21, 28, 32, 27, 22, 29, 21],
            "total_jobs": [30, 38, 29, 48, 55, 42, 34, 46, 62, 72, 58, 50, 62, 47]
        },
        "nodes_power_temp": {
            "labels": [f"node{i}" for i in range(1, 11)],
            "power_watts": [950, 980, 920, 140, 990, 940, 960, 150, 145, 0],
            "avg_temp": [68, 71, 66, 38, 73, 69, 70, 39, 37, 0]
        }
    }


def fetch_cluster_data(db_conn):
    """Queries real cluster telemetry from PostgreSQL tables with thermal, power, and daily jobs."""
    cur = db_conn.cursor()

    # 1. Obter nós e seus últimos status
    query_nodes = """
        SELECT DISTINCT ON (hostname) hostname, state, last_updated
        FROM node_state
        ORDER BY hostname, last_updated DESC;
    """
    cur.execute(query_nodes)
    nodes_raw = cur.fetchall()

    # 2. Obter GPUs mais recentes por nó (incluindo temperatura e power_watts se existir)
    # Detecta se a coluna power_watts existe na tabela gpu_log
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='gpu_log' AND column_name='power_watts';
    """)
    has_power_col = cur.fetchone() is not None

    if has_power_col:
        query_gpus = """
            SELECT DISTINCT ON (hostname, name) hostname, name, temperature_gpu, memory_used, power_watts, time
            FROM gpu_log
            ORDER BY hostname, name, time DESC;
        """
    else:
        query_gpus = """
            SELECT DISTINCT ON (hostname, name) hostname, name, temperature_gpu, memory_used, NULL as power_watts, time
            FROM gpu_log
            ORDER BY hostname, name, time DESC;
        """
    cur.execute(query_gpus)
    gpus_raw = cur.fetchall()

    gpus_by_node = {}
    total_gpus = 0
    active_gpus = 0
    total_cluster_watts = 0
    sum_temp = 0
    count_temp = 0

    node_power_map = {}
    node_temp_map = {}

    for row in gpus_raw:
        h_name, gpu_name, temp, mem_used, p_watts, _ = row
        try:
            mem_used_int = int(mem_used)
        except (ValueError, TypeError):
            mem_used_int = 0

        try:
            temp_int = int(temp) if temp is not None else 0
        except (ValueError, TypeError):
            temp_int = 0

        try:
            power_float = float(p_watts) if p_watts is not None else 0.0
        except (ValueError, TypeError):
            power_float = 0.0

        mem_total = 40960
        if "80GB" in gpu_name:
            mem_total = 81920
        elif "24GB" in gpu_name or "3090" in gpu_name or "4090" in gpu_name:
            mem_total = 24576

        mem_percent = min(100, int((mem_used_int / mem_total) * 100)) if mem_total else 0

        total_gpus += 1
        if mem_used_int > 1000 or power_float > 80:
            active_gpus += 1

        total_cluster_watts += power_float
        if temp_int > 0:
            sum_temp += temp_int
            count_temp += 1

        node_power_map[h_name] = node_power_map.get(h_name, 0.0) + power_float
        node_temp_map.setdefault(h_name, []).append(temp_int)

        gpu_item = {
            "name": gpu_name,
            "temperature": temp_int,
            "memory_used": mem_used_int,
            "memory_total": mem_total,
            "memory_percent": mem_percent,
            "power_watts": round(power_float, 1),
            "power_limit_watts": 400
        }
        gpus_by_node.setdefault(h_name, []).append(gpu_item)

    avg_gpu_temp = round(sum_temp / count_temp, 1) if count_temp > 0 else 0
    avg_gpu_power = round(total_cluster_watts / total_gpus, 1) if total_gpus > 0 else 0

    # Montar estrutura dos nós
    nodes_list = []
    total_nodes = len(nodes_raw)
    active_nodes = 0
    down_nodes = 0

    status_map = {
        "idle": ("Livre", "emerald"),
        "alloc": ("Alocado", "blue"),
        "allocated": ("Alocado", "blue"),
        "mix": ("Misto", "amber"),
        "mixed": ("Misto", "amber"),
        "down": ("Inativo", "rose"),
        "drain": ("Drenando", "purple"),
        "drained": ("Drenado", "purple"),
        "maint": ("Manutenção", "amber"),
    }

    for row in nodes_raw:
        hostname, state, last_updated = row
        state_lower = str(state).strip().lower().replace("*", "").replace("~", "")
        label, color = status_map.get(state_lower, (state, "gray"))

        if color in ["emerald", "blue", "amber"]:
            active_nodes += 1
        else:
            down_nodes += 1

        ts_str = last_updated.strftime("%Y-%m-%d %H:%M:%S") if isinstance(last_updated, (datetime, date)) else str(last_updated)
        node_gpus = gpus_by_node.get(hostname, [])

        nodes_list.append({
            "hostname": hostname,
            "state": state,
            "status_label": label,
            "status_color": color,
            "last_updated": ts_str,
            "gpus": node_gpus
        })

    def node_sort_key(n):
        digits = "".join(filter(str.isdigit, n["hostname"]))
        return int(digits) if digits else 999
    nodes_list.sort(key=node_sort_key)

    # 3. Métricas de Consumo e Temperatura agregadas por nó
    nodes_power_temp = {
        "labels": [n["hostname"].replace("cluster-", "") for n in nodes_list],
        "power_watts": [round(node_power_map.get(n["hostname"], 0.0), 1) for n in nodes_list],
        "avg_temp": [
            round(sum(node_temp_map.get(n["hostname"], [0])) / max(1, len(node_temp_map.get(n["hostname"], []))), 1)
            for n in nodes_list
        ]
    }

    # 4. Fila de Jobs (Queue)
    query_queue = """
        SELECT jobid, name, "USER", state, time, nodelist, last_updated
        FROM queue
        WHERE last_updated >= (SELECT COALESCE(MAX(last_updated) - INTERVAL '15 minutes', NOW() - INTERVAL '1 day') FROM queue)
        ORDER BY state, jobid DESC
        LIMIT 100;
    """
    try:
        cur.execute(query_queue)
        queue_raw = cur.fetchall()
    except Exception as e:
        print(f"Warning reading queue: {e}")
        db_conn.rollback()
        queue_raw = []

    queue_list = []
    running_jobs = 0
    pending_jobs = 0

    for q in queue_raw:
        jobid, name, user, state, time_val, nodelist, _ = q
        st_clean = str(state).strip()
        if st_clean in ("R", "RUNNING"):
            running_jobs += 1
            badge = "R"
            full_st = "RUNNING"
        elif st_clean in ("PD", "PENDING"):
            pending_jobs += 1
            badge = "PD"
            full_st = "PENDING"
        else:
            badge = st_clean[:2]
            full_st = st_clean

        queue_list.append({
            "jobid": jobid,
            "name": name,
            "user": user,
            "state": full_st,
            "state_badge": badge,
            "time": str(time_val),
            "nodelist": nodelist or "-"
        })

    # 5. Histórico Diário de Jobs Lançados (Últimos 14 dias a partir de job_log)
    query_daily_jobs = """
        WITH recent_days AS (
            SELECT
                DATE_TRUNC('day', submit)::date AS day_ref,
                CASE WHEN reqgpu IS NOT NULL AND reqgpu::numeric > 0 THEN 1 ELSE 0 END AS is_gpu
            FROM job_log
            WHERE submit >= NOW() - INTERVAL '14 days'
        )
        SELECT
            day_ref,
            SUM(CASE WHEN is_gpu = 0 THEN 1 ELSE 0 END) AS cpu_jobs,
            SUM(CASE WHEN is_gpu = 1 THEN 1 ELSE 0 END) AS gpu_jobs,
            COUNT(*) AS total_jobs
        FROM recent_days
        GROUP BY day_ref
        ORDER BY day_ref ASC;
    """
    daily_jobs_labels = []
    daily_cpu_jobs = []
    daily_gpu_jobs = []
    daily_total_jobs = []
    jobs_today = 0

    try:
        cur.execute(query_daily_jobs)
        daily_rows = cur.fetchall()
        for r in daily_rows:
            d_ref, c_jobs, g_jobs, t_jobs = r
            daily_jobs_labels.append(d_ref.strftime("%d/%m") if isinstance(d_ref, (date, datetime)) else str(d_ref))
            daily_cpu_jobs.append(int(c_jobs or 0))
            daily_gpu_jobs.append(int(g_jobs or 0))
            daily_total_jobs.append(int(t_jobs or 0))
        if daily_total_jobs:
            jobs_today = daily_total_jobs[-1]
    except Exception as e:
        print(f"Warning reading daily jobs from job_log: {e}")
        db_conn.rollback()

    daily_jobs_history = {
        "labels": daily_jobs_labels,
        "cpu_jobs": daily_cpu_jobs,
        "gpu_jobs": daily_gpu_jobs,
        "total_jobs": daily_total_jobs
    }

    # 6. Filesystem
    query_fs = """
        SELECT DISTINCT ON (mounted) filesystem, size, used, avail, usepercent, mounted, time
        FROM filesystem_data
        ORDER BY mounted, time DESC;
    """
    try:
        cur.execute(query_fs)
        fs_raw = cur.fetchall()
    except Exception as e:
        print(f"Warning reading filesystem_data: {e}")
        db_conn.rollback()
        fs_raw = []

    filesystem_list = []
    for fs in fs_raw:
        filesystem, size, used, avail, usepercent, mounted, _ = fs
        try:
            pct = int(str(usepercent).replace("%", ""))
        except (ValueError, TypeError):
            pct = 0

        filesystem_list.append({
            "mounted": mounted,
            "filesystem": filesystem,
            "size": size,
            "used": used,
            "avail": avail,
            "usepercent": pct
        })

    # 7. Histórico de Utilização (30 dias)
    query_util = """
        SELECT last_update, ocupation, idle, indisponibility
        FROM utilization
        ORDER BY last_update ASC
        LIMIT 30;
    """
    try:
        cur.execute(query_util)
        util_raw = cur.fetchall()
    except Exception as e:
        print(f"Warning reading utilization: {e}")
        db_conn.rollback()
        util_raw = []

    labels = []
    occupation = []
    idle = []
    unavail = []

    for u in util_raw:
        dt, ocp, idl, ind = u
        labels.append(dt.strftime("%d/%m") if isinstance(dt, (date, datetime)) else str(dt))
        occupation.append(float(ocp or 0))
        idle.append(float(idl or 0))
        unavail.append(float(ind or 0))

    util_history = {
        "labels": labels,
        "occupation": occupation,
        "idle": idle,
        "unavailability": unavail
    }

    cur.close()

    return {
        "generated_at": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "cluster_name": "Apuana HPC Cluster",
        "summary": {
            "total_nodes": total_nodes,
            "active_nodes": active_nodes,
            "down_nodes": down_nodes,
            "total_gpus": total_gpus,
            "active_gpus": active_gpus,
            "running_jobs": running_jobs,
            "pending_jobs": pending_jobs,
            "total_power_kw": round(total_cluster_watts / 1000.0, 2),
            "avg_power_gpu_w": avg_gpu_power,
            "avg_temp_gpu_c": avg_gpu_temp,
            "jobs_today": jobs_today,
            "overall_status": "operational" if down_nodes <= 1 else "degraded"
        },
        "nodes": nodes_list,
        "queue": queue_list,
        "filesystem": filesystem_list,
        "utilization_history": util_history,
        "daily_jobs_history": daily_jobs_history,
        "nodes_power_temp": nodes_power_temp
    }


def render_html_dashboard(data, output_path):
    """Renders the HTML file with all interactive widgets and telemetry embedded."""
    data_json_str = json.dumps(data, default=custom_json_serializer, ensure_ascii=False)

    html_content = f"""<!DOCTYPE html>
<html lang="pt-BR" class="dark">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Apuana HPC Cluster | Monitoramento & Telemetria</title>
  
  <!-- Tailwind CSS & Lucide Icons -->
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://unpkg.com/lucide@latest"></script>
  <!-- Chart.js para gráficos -->
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

  <script>
    tailwind.config = {{
      darkMode: 'class',
      theme: {{
        extend: {{
          colors: {{
            brand: {{
              50: '#eef2ff',
              500: '#6366f1',
              600: '#4f46e5',
              700: '#4338ca',
              900: '#312e81',
            }}
          }}
        }}
      }}
    }}
  </script>
  <style>
    .glass {{
      background: rgba(30, 41, 59, 0.7);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border: 1px solid rgba(255, 255, 255, 0.08);
    }}
    .light .glass {{
      background: rgba(255, 255, 255, 0.85);
      border: 1px solid rgba(0, 0, 0, 0.08);
    }}
  </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen transition-colors duration-200 selection:bg-indigo-500 selection:text-white">

  <!-- Dados embutidos diretamente no HTML para carregamento instantâneo offline/GitHub Pages -->
  <script id="cluster-raw-data" type="application/json">
    {data_json_str}
  </script>

  <!-- Top Navigation Bar -->
  <header class="sticky top-0 z-50 glass border-b border-slate-800/80 px-4 lg:px-8 py-3">
    <div class="max-w-7xl mx-auto flex items-center justify-between">
      <div class="flex items-center space-x-3">
        <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
          <i data-lucide="cpu" class="w-6 h-6 text-white"></i>
        </div>
        <div>
          <div class="flex items-center gap-2">
            <h1 class="font-bold text-lg tracking-tight">Cluster Apuana</h1>
            <span id="badge-cluster-status" class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
              Operacional
            </span>
          </div>
          <p class="text-xs text-slate-400">Telemetria de Alta Performance (HPC & AI)</p>
        </div>
      </div>

      <div class="flex items-center space-x-4">
        <!-- Timestamp da Sincronização -->
        <div class="hidden sm:flex items-center space-x-1.5 text-xs text-slate-400 bg-slate-900/60 px-3 py-1.5 rounded-lg border border-slate-800">
          <i data-lucide="clock" class="w-3.5 h-3.5 text-indigo-400"></i>
          <span>Atualizado em: <strong id="timestamp-updated" class="text-slate-200">--:--</strong></span>
        </div>

        <!-- Modo Escuro / Claro -->
        <button id="theme-toggle" class="p-2 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 transition-colors" title="Alternar tema">
          <i data-lucide="sun" id="theme-icon-sun" class="w-4 h-4 hidden"></i>
          <i data-lucide="moon" id="theme-icon-moon" class="w-4 h-4"></i>
        </button>
      </div>
    </div>
  </header>

  <main class="max-w-7xl mx-auto px-4 lg:px-8 py-8 space-y-8">

    <!-- KPI Summary Cards (6 métricas essenciais incluindo Energia e Temperatura) -->
    <section class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
      
      <!-- Card Nós -->
      <div class="glass p-4 rounded-2xl relative overflow-hidden group">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-[11px] font-medium text-slate-400 uppercase tracking-wider">Nós do Cluster</p>
            <h3 id="kpi-nodes" class="text-xl font-bold mt-1 text-slate-100">-- / --</h3>
            <p id="kpi-nodes-sub" class="text-[11px] text-emerald-400 mt-1 flex items-center gap-1">
              <i data-lucide="check-circle" class="w-3 h-3"></i> nós online
            </p>
          </div>
          <div class="w-10 h-10 rounded-xl bg-indigo-500/10 text-indigo-400 flex items-center justify-center">
            <i data-lucide="server" class="w-5 h-5"></i>
          </div>
        </div>
        <div class="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-indigo-500 to-violet-500"></div>
      </div>

      <!-- Card GPUs -->
      <div class="glass p-4 rounded-2xl relative overflow-hidden group">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-[11px] font-medium text-slate-400 uppercase tracking-wider">GPUs em Carga</p>
            <h3 id="kpi-gpus" class="text-xl font-bold mt-1 text-slate-100">-- / --</h3>
            <p id="kpi-gpus-sub" class="text-[11px] text-violet-400 mt-1 flex items-center gap-1">
              <i data-lucide="zap" class="w-3 h-3"></i> aceleradores
            </p>
          </div>
          <div class="w-10 h-10 rounded-xl bg-violet-500/10 text-violet-400 flex items-center justify-center">
            <i data-lucide="circuit-board" class="w-5 h-5"></i>
          </div>
        </div>
        <div class="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-violet-500 to-pink-500"></div>
      </div>

      <!-- Card Energia Total (Potência) -->
      <div class="glass p-4 rounded-2xl relative overflow-hidden group">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-[11px] font-medium text-slate-400 uppercase tracking-wider">Uso Energético</p>
            <h3 id="kpi-power" class="text-xl font-bold mt-1 text-amber-400">-- kW</h3>
            <p id="kpi-power-sub" class="text-[11px] text-slate-400 mt-1 flex items-center gap-1">
              <i data-lucide="activity" class="w-3 h-3 text-amber-400"></i> ~-- W / GPU
            </p>
          </div>
          <div class="w-10 h-10 rounded-xl bg-amber-500/10 text-amber-400 flex items-center justify-center">
            <i data-lucide="zap" class="w-5 h-5"></i>
          </div>
        </div>
        <div class="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-amber-500 to-yellow-500"></div>
      </div>

      <!-- Card Temperatura Média -->
      <div class="glass p-4 rounded-2xl relative overflow-hidden group">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-[11px] font-medium text-slate-400 uppercase tracking-wider">Temperatura Média</p>
            <h3 id="kpi-temp" class="text-xl font-bold mt-1 text-slate-100">-- °C</h3>
            <p id="kpi-temp-sub" class="text-[11px] text-emerald-400 mt-1 flex items-center gap-1">
              <i data-lucide="thermometer" class="w-3 h-3"></i> Térmica estável
            </p>
          </div>
          <div class="w-10 h-10 rounded-xl bg-rose-500/10 text-rose-400 flex items-center justify-center">
            <i data-lucide="thermometer" class="w-5 h-5"></i>
          </div>
        </div>
        <div class="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-rose-500 to-red-500"></div>
      </div>

      <!-- Card Fila Slurm -->
      <div class="glass p-4 rounded-2xl relative overflow-hidden group">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-[11px] font-medium text-slate-400 uppercase tracking-wider">Fila Slurm</p>
            <h3 id="kpi-jobs" class="text-xl font-bold mt-1 text-slate-100">-- rodando</h3>
            <p id="kpi-jobs-pending" class="text-[11px] text-amber-400 mt-1 flex items-center gap-1">
              <i data-lucide="hourglass" class="w-3 h-3"></i> -- pendentes
            </p>
          </div>
          <div class="w-10 h-10 rounded-xl bg-blue-500/10 text-blue-400 flex items-center justify-center">
            <i data-lucide="list-ordered" class="w-5 h-5"></i>
          </div>
        </div>
        <div class="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-500 to-indigo-500"></div>
      </div>

      <!-- Card Jobs Lançados Hoje -->
      <div class="glass p-4 rounded-2xl relative overflow-hidden group">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-[11px] font-medium text-slate-400 uppercase tracking-wider">Lançados Hoje</p>
            <h3 id="kpi-jobs-today" class="text-xl font-bold mt-1 text-slate-100">-- jobs</h3>
            <p class="text-[11px] text-indigo-400 mt-1 flex items-center gap-1">
              <i data-lucide="calendar" class="w-3 h-3"></i> jobs submetidos
            </p>
          </div>
          <div class="w-10 h-10 rounded-xl bg-teal-500/10 text-teal-400 flex items-center justify-center">
            <i data-lucide="bar-chart-2" class="w-5 h-5"></i>
          </div>
        </div>
        <div class="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-teal-500 to-emerald-500"></div>
      </div>

    </section>

    <!-- Seção de Análise Gráfica: Jobs Diários + Energia & Temperatura por Nó -->
    <section class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      
      <!-- Gráfico 1: Jobs Lançados por Dia (CPU vs GPU) -->
      <div class="glass rounded-2xl p-6 space-y-3">
        <div class="flex items-center justify-between">
          <div>
            <h3 class="text-base font-bold tracking-tight flex items-center gap-2">
              <i data-lucide="calendar" class="w-4 h-4 text-indigo-400"></i>
              Jobs Lançados por Dia (Últimos 14 dias)
            </h3>
            <p class="text-xs text-slate-400">Distribuição diária de submissões divididas entre tarefas com CPU e GPU</p>
          </div>
          <span class="text-xs px-2.5 py-1 rounded-md bg-indigo-500/10 text-indigo-400 font-mono">Slurm sacct</span>
        </div>
        <div class="h-60 relative">
          <canvas id="dailyJobsChart"></canvas>
        </div>
      </div>

      <!-- Gráfico 2: Energia (Watts) & Temperatura (°C) por Nodo -->
      <div class="glass rounded-2xl p-6 space-y-3">
        <div class="flex items-center justify-between">
          <div>
            <h3 class="text-base font-bold tracking-tight flex items-center gap-2">
              <i data-lucide="flame" class="w-4 h-4 text-amber-400"></i>
              Perfil Térmico e Energético por Nodo
            </h3>
            <p class="text-xs text-slate-400">Potência total consumida (W) e temperatura média das GPUs (°C)</p>
          </div>
          <span class="text-xs px-2.5 py-1 rounded-md bg-amber-500/10 text-amber-400 font-mono">nvidia-smi</span>
        </div>
        <div class="h-60 relative">
          <canvas id="nodeThermalPowerChart"></canvas>
        </div>
      </div>

    </section>

    <!-- Seção de Nós (Matriz de Computação) -->
    <section class="space-y-4">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 class="text-xl font-bold tracking-tight flex items-center gap-2">
            <i data-lucide="server" class="w-5 h-5 text-indigo-400"></i>
            Estado dos Nodos de Computação
          </h2>
          <p class="text-xs text-slate-400">Status no Slurm, GPUs instaladas, telemetria térmica (°C) e potência (W)</p>
        </div>

        <!-- Filtros Rápidos -->
        <div class="flex items-center gap-2">
          <button onclick="filterNodes('all')" class="node-filter-btn px-3 py-1.5 rounded-lg text-xs font-medium bg-indigo-600 text-white" data-filter="all">Todos</button>
          <button onclick="filterNodes('alloc')" class="node-filter-btn px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800 text-slate-300 hover:bg-slate-700" data-filter="alloc">Alocados</button>
          <button onclick="filterNodes('idle')" class="node-filter-btn px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800 text-slate-300 hover:bg-slate-700" data-filter="idle">Livres</button>
          <button onclick="filterNodes('down')" class="node-filter-btn px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800 text-slate-300 hover:bg-slate-700" data-filter="down">Inativos</button>
        </div>
      </div>

      <!-- Grid dos Nós -->
      <div id="nodes-grid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        <!-- Renderizado dinamicamente via JS -->
      </div>
    </section>

    <!-- Fila de Jobs Slurm, Armazenamento & Utilização -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
      
      <!-- Tabela da Fila do Slurm (2 colunas) -->
      <div class="lg:col-span-2 glass rounded-2xl p-6 space-y-4">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h2 class="text-lg font-bold tracking-tight flex items-center gap-2">
              <i data-lucide="list-ordered" class="w-5 h-5 text-indigo-400"></i>
              Fila de Execução do Slurm
            </h2>
            <p class="text-xs text-slate-400">Tarefas rodando e em espera pelos recursos do cluster</p>
          </div>
          <!-- Campo de Busca de Job / Usuário -->
          <div class="relative">
            <i data-lucide="search" class="w-4 h-4 absolute left-3 top-2.5 text-slate-400"></i>
            <input type="text" id="job-search" placeholder="Buscar job ou usuário..." 
                   class="bg-slate-900 border border-slate-700 text-xs rounded-lg pl-9 pr-3 py-2 text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 w-full sm:w-56" />
          </div>
        </div>

        <div class="overflow-x-auto rounded-xl border border-slate-800">
          <table class="w-full text-left text-xs text-slate-300">
            <thead class="bg-slate-900/80 text-slate-400 uppercase tracking-wider text-[10px] border-b border-slate-800">
              <tr>
                <th class="py-3 px-4">Job ID</th>
                <th class="py-3 px-4">Nome</th>
                <th class="py-3 px-4">Usuário</th>
                <th class="py-3 px-4">Estado</th>
                <th class="py-3 px-4">Tempo</th>
                <th class="py-3 px-4">Nós Alocados</th>
              </tr>
            </thead>
            <tbody id="queue-table-body" class="divide-y divide-slate-800/60 font-mono">
              <!-- Renderizado dinamicamente -->
            </tbody>
          </table>
        </div>
      </div>

      <!-- Armazenamento & Utilização Mensal (1 coluna) -->
      <div class="space-y-6">
        
        <!-- Filesystem Disks -->
        <div class="glass rounded-2xl p-6 space-y-4">
          <h2 class="text-lg font-bold tracking-tight flex items-center gap-2">
            <i data-lucide="hard-drive" class="w-5 h-5 text-indigo-400"></i>
            Espaço em Disco
          </h2>
          <div id="filesystem-list" class="space-y-4">
            <!-- Renderizado dinamicamente -->
          </div>
        </div>

        <!-- Tendência de Utilização (Chart.js) -->
        <div class="glass rounded-2xl p-6 space-y-3">
          <h2 class="text-lg font-bold tracking-tight flex items-center gap-2">
            <i data-lucide="trending-up" class="w-5 h-5 text-indigo-400"></i>
            Utilização Geral (%)
          </h2>
          <p class="text-xs text-slate-400">Ocupação vs ociosidade média do cluster</p>
          <div class="h-44 relative">
            <canvas id="utilizationChart"></canvas>
          </div>
        </div>

      </div>

    </div>

  </main>

  <!-- Footer -->
  <footer class="border-t border-slate-800/80 mt-16 py-6 text-center text-xs text-slate-500">
    <p>Cluster Apuana • Telemetria de Uso, Energia & Monitoramento de Nós • Exportado automaticamente para GitHub Pages</p>
  </footer>

  <!-- Lógica da Aplicação Web em Vanilla JS -->
  <script>
    let clusterData = {{}};
    try {{
      const rawScript = document.getElementById('cluster-raw-data');
      clusterData = JSON.parse(rawScript.textContent);
    }} catch (e) {{
      console.error("Erro ao carregar dados do cluster:", e);
    }}

    let currentFilter = 'all';

    document.addEventListener("DOMContentLoaded", () => {{
      renderSummary(clusterData);
      renderNodes(clusterData.nodes, currentFilter);
      renderQueue(clusterData.queue);
      renderFilesystem(clusterData.filesystem);
      renderCharts(clusterData);
      
      lucide.createIcons();
      setupSearch();
      setupThemeToggle();
    }});

    function renderSummary(data) {{
      if (!data || !data.summary) return;
      const s = data.summary;

      document.getElementById('timestamp-updated').textContent = data.generated_at || 'Agora';
      document.getElementById('kpi-nodes').textContent = `${{s.active_nodes}} / ${{s.total_nodes}}`;
      document.getElementById('kpi-nodes-sub').innerHTML = s.down_nodes === 0
        ? `<i data-lucide="check-circle" class="w-3 h-3 text-emerald-400"></i> Todos nós operacionais`
        : `<i data-lucide="alert-triangle" class="w-3 h-3 text-amber-400"></i> ${{s.down_nodes}} nó(s) com atenção`;

      document.getElementById('kpi-gpus').textContent = `${{s.active_gpus}} / ${{s.total_gpus}}`;
      
      // Energia e Temperatura
      if (document.getElementById('kpi-power')) {{
        document.getElementById('kpi-power').textContent = `${{s.total_power_kw || 0}} kW`;
        document.getElementById('kpi-power-sub').innerHTML = `<i data-lucide="activity" class="w-3 h-3 text-amber-400"></i> ~${{s.avg_power_gpu_w || 0}} W / GPU`;
      }}

      if (document.getElementById('kpi-temp')) {{
        document.getElementById('kpi-temp').textContent = `${{s.avg_temp_gpu_c || 0}} °C`;
        const tempColor = (s.avg_temp_gpu_c > 75) ? 'text-rose-400' : 'text-emerald-400';
        document.getElementById('kpi-temp-sub').className = `text-[11px] ${{tempColor}} mt-1 flex items-center gap-1`;
      }}

      document.getElementById('kpi-jobs').textContent = `${{s.running_jobs}} rodando`;
      document.getElementById('kpi-jobs-pending').textContent = `${{s.pending_jobs}} na fila (pendentes)`;

      if (document.getElementById('kpi-jobs-today')) {{
        document.getElementById('kpi-jobs-today').textContent = `${{s.jobs_today || 0}} jobs`;
      }}
    }}

    function renderNodes(nodes, filter) {{
      const container = document.getElementById('nodes-grid');
      container.innerHTML = '';

      if (!nodes || nodes.length === 0) {{
        container.innerHTML = '<div class="col-span-full text-center py-8 text-slate-500">Nenhum nó registrado.</div>';
        return;
      }}

      nodes.forEach(node => {{
        const isAlloc = node.status_color === 'blue';
        const isIdle = node.status_color === 'emerald';
        const isDown = node.status_color === 'rose';

        if (filter === 'alloc' && !isAlloc) return;
        if (filter === 'idle' && !isIdle) return;
        if (filter === 'down' && !isDown) return;

        let badgeBg = 'bg-slate-800 text-slate-300';
        let dotColor = 'bg-slate-400';
        if (isIdle) {{ badgeBg = 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'; dotColor = 'bg-emerald-400'; }}
        if (isAlloc) {{ badgeBg = 'bg-blue-500/10 text-blue-400 border border-blue-500/20'; dotColor = 'bg-blue-400'; }}
        if (isDown) {{ badgeBg = 'bg-rose-500/10 text-rose-400 border border-rose-500/20'; dotColor = 'bg-rose-400'; }}

        // GPUs do nó com indicação clara de VRAM, Temperatura e Watts
        let gpusHtml = '';
        if (node.gpus && node.gpus.length > 0) {{
          gpusHtml = `
            <div class="mt-4 pt-3 border-t border-slate-800/80 space-y-2">
              <div class="text-[11px] font-medium text-slate-400 flex items-center justify-between">
                <span>GPUs (${{node.gpus.length}})</span>
                <span class="text-[10px] text-slate-500">VRAM • Temp • Watts</span>
              </div>
              <div class="space-y-1.5">
                ${{node.gpus.map((gpu, idx) => {{
                  const tempBadge = gpu.temperature > 75 
                    ? 'text-rose-400 font-semibold' 
                    : (gpu.temperature > 60 ? 'text-amber-400' : 'text-emerald-400');
                  const powerBadge = gpu.power_watts ? `${{Math.round(gpu.power_watts)}}W` : '';
                  return `
                  <div class="bg-slate-900/80 p-2 rounded-lg border border-slate-800 text-[11px]">
                    <div class="flex justify-between items-center mb-1">
                      <span class="font-medium text-slate-300 truncate max-w-[110px]" title="${{gpu.name}}">GPU ${{idx}}</span>
                      <span class="text-slate-400 flex items-center gap-1 font-mono text-[10px]">
                        <span class="${{tempBadge}}">${{gpu.temperature}}°C</span>
                        ${{powerBadge ? `<span class="text-slate-600">•</span><span class="text-amber-400/90">${{powerBadge}}</span>` : ''}}
                        <span class="text-slate-600">•</span>
                        <span>${{Math.round(gpu.memory_used / 1024)}}GB</span>
                      </span>
                    </div>
                    <div class="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                      <div class="h-full rounded-full ${{gpu.memory_percent > 85 ? 'bg-amber-500' : 'bg-indigo-500'}}" style="width: ${{gpu.memory_percent}}%"></div>
                    </div>
                  </div>
                  `;
                }}).join('')}}
              </div>
            </div>
          `;
        }} else {{
          gpusHtml = `
            <div class="mt-4 pt-3 border-t border-slate-800/80 text-[11px] text-slate-500 flex items-center gap-1">
              <i data-lucide="info" class="w-3.5 h-3.5"></i> Sem GPUs ou nó offline
            </div>
          `;
        }}

        const card = document.createElement('div');
        card.className = "glass p-4 rounded-xl border border-slate-800/80 hover:border-slate-700 transition-all flex flex-col justify-between";
        card.innerHTML = `
          <div>
            <div class="flex items-center justify-between">
              <span class="font-semibold text-sm tracking-tight text-slate-200">${{node.hostname}}</span>
              <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-medium ${{badgeBg}}">
                <span class="w-1.5 h-1.5 rounded-full ${{dotColor}}"></span>
                ${{node.status_label}}
              </span>
            </div>
            ${{gpusHtml}}
          </div>
          <div class="mt-3 pt-2 text-[10px] text-slate-500 flex items-center justify-between">
            <span>Último sync:</span>
            <span>${{node.last_updated.split(' ')[1] || node.last_updated}}</span>
          </div>
        `;
        container.appendChild(card);
      }});

      lucide.createIcons();
    }}

    function filterNodes(type) {{
      currentFilter = type;
      document.querySelectorAll('.node-filter-btn').forEach(btn => {{
        if (btn.dataset.filter === type) {{
          btn.className = "node-filter-btn px-3 py-1.5 rounded-lg text-xs font-medium bg-indigo-600 text-white";
        }} else {{
          btn.className = "node-filter-btn px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800 text-slate-300 hover:bg-slate-700";
        }}
      }});
      renderNodes(clusterData.nodes, currentFilter);
    }}

    function renderQueue(queue, searchQuery = '') {{
      const tbody = document.getElementById('queue-table-body');
      tbody.innerHTML = '';

      if (!queue || queue.length === 0) {{
        tbody.innerHTML = '<tr><td colspan="6" class="text-center py-6 text-slate-500">Nenhum job na fila no momento.</td></tr>';
        return;
      }}

      const filtered = queue.filter(job => {{
        if (!searchQuery) return true;
        const q = searchQuery.toLowerCase();
        return (
          String(job.jobid).includes(q) ||
          (job.user && job.user.toLowerCase().includes(q)) ||
          (job.name && job.name.toLowerCase().includes(q))
        );
      }});

      if (filtered.length === 0) {{
        tbody.innerHTML = '<tr><td colspan="6" class="text-center py-6 text-slate-500">Nenhum job corresponde à busca.</td></tr>';
        return;
      }}

      filtered.forEach(job => {{
        const isRunning = job.state === 'RUNNING';
        const badgeColor = isRunning 
          ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20' 
          : 'bg-amber-500/10 text-amber-400 border border-amber-500/20';

        const tr = document.createElement('tr');
        tr.className = "hover:bg-slate-900/50 transition-colors";
        tr.innerHTML = `
          <td class="py-3 px-4 font-semibold text-slate-200">${{job.jobid}}</td>
          <td class="py-3 px-4 text-slate-300 max-w-[160px] truncate" title="${{job.name}}">${{job.name}}</td>
          <td class="py-3 px-4 text-indigo-300 font-medium">${{job.user}}</td>
          <td class="py-3 px-4">
            <span class="inline-block px-2 py-0.5 rounded text-[10px] font-medium ${{badgeColor}}">
              ${{job.state}}
            </span>
          </td>
          <td class="py-3 px-4 text-slate-400">${{job.time}}</td>
          <td class="py-3 px-4 text-slate-400">${{job.nodelist}}</td>
        `;
        tbody.appendChild(tr);
      }});
    }}

    function renderFilesystem(fsList) {{
      const container = document.getElementById('filesystem-list');
      container.innerHTML = '';

      if (!fsList || fsList.length === 0) {{
        container.innerHTML = '<p class="text-xs text-slate-500">Sem dados de disco disponíveis.</p>';
        return;
      }}

      fsList.forEach(fs => {{
        let barColor = 'bg-indigo-500';
        if (fs.usepercent > 85) barColor = 'bg-amber-500';
        if (fs.usepercent > 95) barColor = 'bg-rose-500';

        const item = document.createElement('div');
        item.className = "space-y-1.5";
        item.innerHTML = `
          <div class="flex justify-between text-xs">
            <span class="font-medium text-slate-300 font-mono">${{fs.mounted}}</span>
            <span class="text-slate-400">${{fs.used}} / ${{fs.size}} (${{fs.usepercent}}%)</span>
          </div>
          <div class="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
            <div class="h-full ${{barColor}} rounded-full transition-all duration-500" style="width: ${{fs.usepercent}}%"></div>
          </div>
        `;
        container.appendChild(item);
      }});
    }}

    function renderCharts(data) {{
      // 1. Gráfico de Jobs Diários (CPU vs GPU)
      if (data.daily_jobs_history && data.daily_jobs_history.labels && data.daily_jobs_history.labels.length > 0) {{
        const dj = data.daily_jobs_history;
        const ctxDaily = document.getElementById('dailyJobsChart').getContext('2d');
        new Chart(ctxDaily, {{
          type: 'bar',
          data: {{
            labels: dj.labels,
            datasets: [
              {{
                label: 'Jobs GPU',
                data: dj.gpu_jobs,
                backgroundColor: '#8b5cf6',
                borderRadius: 4
              }},
              {{
                label: 'Jobs CPU',
                data: dj.cpu_jobs,
                backgroundColor: '#38bdf8',
                borderRadius: 4
              }}
            ]
          }},
          options: {{
            responsive: true,
            maintainAspectRatio: false,
            scales: {{
              x: {{ stacked: true, grid: {{ display: false }}, ticks: {{ color: '#64748b', font: {{ size: 10 }} }} }},
              y: {{ stacked: true, beginAtZero: true, grid: {{ color: 'rgba(255, 255, 255, 0.05)' }}, ticks: {{ color: '#64748b', font: {{ size: 10 }} }} }}
            }},
            plugins: {{
              legend: {{ position: 'top', labels: {{ color: '#94a3b8', font: {{ size: 10 }} }} }}
            }}
          }}
        }});
      }}

      // 2. Gráfico de Perfil Térmico e Energético por Nodo
      if (data.nodes_power_temp && data.nodes_power_temp.labels && data.nodes_power_temp.labels.length > 0) {{
        const npt = data.nodes_power_temp;
        const ctxThermal = document.getElementById('nodeThermalPowerChart').getContext('2d');
        new Chart(ctxThermal, {{
          data: {{
            labels: npt.labels,
            datasets: [
              {{
                type: 'bar',
                label: 'Potência Total (Watts)',
                data: npt.power_watts,
                backgroundColor: 'rgba(245, 158, 11, 0.8)',
                yAxisID: 'yPower',
                borderRadius: 4
              }},
              {{
                type: 'line',
                label: 'Temp. Média (°C)',
                data: npt.avg_temp,
                borderColor: '#f43f5e',
                backgroundColor: '#f43f5e',
                borderWidth: 2,
                pointRadius: 3,
                yAxisID: 'yTemp'
              }}
            ]
          }},
          options: {{
            responsive: true,
            maintainAspectRatio: false,
            scales: {{
              x: {{ grid: {{ display: false }}, ticks: {{ color: '#64748b', font: {{ size: 10 }} }} }},
              yPower: {{
                type: 'linear',
                position: 'left',
                beginAtZero: true,
                grid: {{ color: 'rgba(255, 255, 255, 0.05)' }},
                ticks: {{ color: '#f59e0b', font: {{ size: 10 }} }},
                title: {{ display: true, text: 'Watts (W)', color: '#f59e0b', font: {{ size: 10 }} }}
              }},
              yTemp: {{
                type: 'linear',
                position: 'right',
                beginAtZero: true,
                max: 100,
                grid: {{ display: false }},
                ticks: {{ color: '#f43f5e', font: {{ size: 10 }} }},
                title: {{ display: true, text: 'Temp (°C)', color: '#f43f5e', font: {{ size: 10 }} }}
              }}
            }},
            plugins: {{
              legend: {{ position: 'top', labels: {{ color: '#94a3b8', font: {{ size: 10 }} }} }}
            }}
          }}
        }});
      }}

      // 3. Gráfico de Histórico de Ocupação/Ociosidade
      if (data.utilization_history && data.utilization_history.labels && data.utilization_history.labels.length > 0) {{
        const ctxUtil = document.getElementById('utilizationChart').getContext('2d');
        new Chart(ctxUtil, {{
          type: 'line',
          data: {{
            labels: data.utilization_history.labels,
            datasets: [
              {{
                label: 'Ocupação (%)',
                data: data.utilization_history.occupation,
                borderColor: '#6366f1',
                backgroundColor: 'rgba(99, 102, 241, 0.1)',
                tension: 0.3,
                fill: true,
                borderWidth: 2
              }},
              {{
                label: 'Ociosidade (%)',
                data: data.utilization_history.idle,
                borderColor: '#38bdf8',
                backgroundColor: 'transparent',
                tension: 0.3,
                borderWidth: 2,
                borderDash: [4, 4]
              }}
            ]
          }},
          options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
              legend: {{ display: true, position: 'top', labels: {{ color: '#94a3b8', font: {{ size: 10 }} }} }}
            }},
            scales: {{
              y: {{ beginAtZero: true, max: 100, grid: {{ color: 'rgba(255, 255, 255, 0.05)' }}, ticks: {{ color: '#64748b', font: {{ size: 10 }} }} }},
              x: {{ grid: {{ display: false }}, ticks: {{ color: '#64748b', font: {{ size: 10 }} }} }}
            }}
          }}
        }});
      }}
    }}

    function setupSearch() {{
      const input = document.getElementById('job-search');
      input.addEventListener('input', (e) => {{
        renderQueue(clusterData.queue, e.target.value);
      }});
    }}

    function setupThemeToggle() {{
      const toggle = document.getElementById('theme-toggle');
      const sun = document.getElementById('theme-icon-sun');
      const moon = document.getElementById('theme-icon-moon');

      toggle.addEventListener('click', () => {{
        const html = document.documentElement;
        if (html.classList.contains('dark')) {{
          html.classList.remove('dark');
          html.classList.add('light');
          sun.classList.remove('hidden');
          moon.classList.add('hidden');
        }} else {{
          html.classList.remove('light');
          html.classList.add('dark');
          sun.classList.add('hidden');
          moon.classList.remove('hidden');
        }}
      }});
    }}
  </script>
</body>
</html>
"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"[✓] Dashboard HTML renderizado em: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Export Apuana Cluster status to HTML dashboard")
    parser.add_argument("--mock", action="store_true", help="Gera dados mock simulados para testes locais")
    parser.add_argument("--output-dir", default=str(BASE_DIR / "dashboard" / "dist"), help="Diretório de saída")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    data = None

    if args.mock:
        print("[i] Modo Mock ativado: Gerando dados de demonstração com telemetria completa...")
        data = generate_mock_data()
    else:
        try:
            if DatabaseConnection is not None:
                db = DatabaseConnection()
                conn = db.connect(
                    host=os.getenv("DB_HOST", "localhost"),
                    user=os.getenv("DB_USER", "postgres"),
                    password=os.getenv("DB_PASSWORD", ""),
                    database=os.getenv("DB_NAME", "cluster"),
                )
                if conn:
                    print("[i] Conectado ao PostgreSQL. Consultando telemetria em tempo real...")
                    data = fetch_cluster_data(conn)
                    conn.close()
                else:
                    print("[!] Conexão falhou. Usando dados mock para renderizar...")
                    data = generate_mock_data()
            else:
                print("[!] DatabaseConnection indisponível. Usando mock...")
                data = generate_mock_data()
        except Exception as e:
            print(f"[!] Erro ao consultar banco: {e}")
            print("[i] Usando dados mock de demonstração...")
            data = generate_mock_data()

    # 1. Salvar JSON estruturado
    json_path = out_dir / "data.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, default=custom_json_serializer, indent=2, ensure_ascii=False)
    print(f"[✓] Dados JSON salvos em: {json_path}")

    # 2. Renderizar HTML autônomo
    html_path = out_dir / "index.html"
    render_html_dashboard(data, html_path)


if __name__ == "__main__":
    main()
