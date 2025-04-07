import os
import psycopg2
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv('DB_HOST'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME')
)
cursor = conn.cursor()

def GpusMemory():
    def fetch_data(query):
        cursor.execute(query)
        cols = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        return pd.DataFrame(rows, columns=cols)

    ### get gpu memory usage from the database ###
    query_gpu_mem = """
    WITH recent_gpus AS (
        SELECT
            CONCAT(hostname, ':', name) AS gpu_id,
            memory_used
        FROM gpu_log
        WHERE time >= NOW() - INTERVAL '2 months'
    )
    SELECT
        gpu_id,
        AVG(memory_used::numeric) AS avg_mem_usage
    FROM recent_gpus
    GROUP BY gpu_id
    ORDER BY avg_mem_usage DESC;
    """

    df = fetch_data(query_gpu_mem)

    plt.figure(figsize=(12, 6))
    sns.set_style("whitegrid")
    sns.barplot(x="gpu_id", y="avg_mem_usage", data=df, palette="viridis")
    plt.xlabel("GPU (hostname:name)")
    plt.ylabel("Média de Memória Utilizada (MiB)")
    plt.title("Uso Médio de Memória das GPUs (Últimos 2 meses)")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig('gpus_memory.png')
    plt.show()

    cursor.close()
    conn.close()

    return "Gpus Memory plotted successfully!"
