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

def Utilization():
    def fetch_data(query):
        cursor.execute(query)
        columns = [desc[0] for desc in cursor.description]
        data = cursor.fetchall()
        return pd.DataFrame(data, columns=columns)

    ### query to get the utilization of the cluster by month for 2024 and 2025 ###
    query_utilization = """
        SELECT 
            DATE_TRUNC('month', last_update) AS month,
            AVG(ocupation) AS avg_occupation,
            AVG(idle) AS avg_idle,
            AVG(indisponibility) AS avg_unavailability
        FROM utilization
        WHERE EXTRACT(YEAR FROM last_update) IN (2024, 2025)
        GROUP BY DATE_TRUNC('month', last_update)
        ORDER BY DATE_TRUNC('month', last_update);
    """

    df_util = fetch_data(query_utilization)
    df_util["month"] = pd.to_datetime(df_util["month"])

    plt.figure(figsize=(10, 6))
    sns.set_style("whitegrid")
    plt.plot(df_util["month"], df_util["avg_occupation"], marker="o", color="red", label="Ocupação")
    plt.plot(df_util["month"], df_util["avg_idle"], marker="o", color="blue", label="Ociosidade")
    plt.plot(df_util["month"], df_util["avg_unavailability"], marker="o", color="green", label="Indisponibilidade")
    plt.xlabel("Mês")
    plt.ylabel("Utilização (%)")
    plt.title("Utilização Média")
    plt.legend()
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("utilization.png")
    plt.show()

    cursor.close()
    conn.close()

    return "utilization plot created"
