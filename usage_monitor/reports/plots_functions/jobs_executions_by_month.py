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

def JobsExecutionsByMonth():
    def fetch_data(query):
        cursor.execute(query)
        columns = [desc[0] for desc in cursor.description]
        data = cursor.fetchall()
        return pd.DataFrame(data, columns=columns)

    ### query to get the number of jobs executed per month ###
    query_qtd_jobs = """
        SELECT DATE_TRUNC('month', submit) AS month,
        COUNT(*) AS total_jobs
        FROM job_log
        GROUP BY month
        ORDER BY month;
    """

    df_qtd_jobs = fetch_data(query_qtd_jobs)

    df_qtd_jobs["month"] = pd.to_datetime(df_qtd_jobs["month"])

    plt.figure(figsize=(10, 5))
    plt.plot(df_qtd_jobs["month"], df_qtd_jobs["total_jobs"], marker="o", color="green", linestyle="-")
    plt.xlabel("Mês")
    plt.ylabel("Quantidade de Jobs")
    plt.title("Quantidade de Jobs Executados por Mês")
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.savefig('jobs_executions_by_month.png')
    plt.show()

    cursor.close()
    conn.close()

    return "Jobs Executions by Month plotted successfully!"
