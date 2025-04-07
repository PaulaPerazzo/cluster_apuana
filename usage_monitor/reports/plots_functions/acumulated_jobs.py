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

def AccumulatedJobs():
    def fetch_data(query):
        cursor.execute(query)
        columns = [desc[0] for desc in cursor.description]
        data = cursor.fetchall()
        return pd.DataFrame(data, columns=columns)

    ### query accumulated jobs ###
    query_cumulative_jobs = """
        WITH unique_jobs AS (
            SELECT jobid, MIN(submit) AS submit
            FROM job_log
            GROUP BY jobid
        )
        SELECT DATE_TRUNC('month', submit) AS month,
        COUNT(*) AS jobs_in_month,
        SUM(COUNT(*)) OVER (ORDER BY DATE_TRUNC('month', submit)) AS cumulative_jobs
        FROM unique_jobs
        GROUP BY month
        ORDER BY month;
    """

    df_cumulative = fetch_data(query_cumulative_jobs)

    df_cumulative["month"] = pd.to_datetime(df_cumulative["month"])


    plt.figure(figsize=(10, 6))
    sns.set_style("whitegrid")
    plt.plot(df_cumulative["month"], df_cumulative["cumulative_jobs"], marker="o", color="green", linestyle="-")
    plt.xlabel("Mês")
    plt.ylabel("Número de Jobs")
    plt.title("Crescimento Acumulado de Jobs")
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('jobs_acumulados.png')
    plt.show()

    cursor.close()
    conn.close()

    return "Jobs acumulados ploted successfully!!"
