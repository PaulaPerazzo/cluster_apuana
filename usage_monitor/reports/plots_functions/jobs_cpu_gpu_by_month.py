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

def CpuGpuJobsByMonth():
    def fetch_data(query):
        cursor.execute(query)
        columns = [desc[0] for desc in cursor.description]
        data = cursor.fetchall()
        return pd.DataFrame(data, columns=columns)

    ### query to get the number of jobs executed per month with and without GPU ###
    query = """
        SELECT DATE_TRUNC('month', submit) AS month,
        COUNT(*) FILTER (WHERE reqgpu = 0) AS cpu_only,
        COUNT(*) FILTER (WHERE reqgpu > 0) AS cpu_gpu
        FROM job_log
        GROUP BY month
        ORDER BY month;
    """

    df = fetch_data(query)

    df["month"] = pd.to_datetime(df["month"])

    plt.figure(figsize=(10, 6))
    sns.set_style("whitegrid")
    plt.plot(df["month"], df["cpu_only"], marker="o", color="red", label="Apenas CPU")
    plt.plot(df["month"], df["cpu_gpu"], marker="o", color="green", label="CPU e GPU")
    plt.xlabel("Mês")
    plt.ylabel("Número de Jobs")
    plt.title("Número de Jobs: Apenas CPU vs CPU e GPU ao Longo do Tempo")
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()
    plt.savefig('jobs_cpu_gpu_by_month.png')

    cursor.close()
    conn.close()

    return "Jobs CPU e GPU por mês plotados com sucesso!"
