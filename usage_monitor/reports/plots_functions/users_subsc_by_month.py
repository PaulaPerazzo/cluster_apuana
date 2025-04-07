import pandas as pd
import matplotlib.pyplot as plt

def UserSubscByMonth():
    file_path = "/Users/paulaperazzo/Documents/apuana/cluster_apuana/usage_monitor/reports/user_files/user_forms_12-03-25.csv"
    df = pd.read_csv(file_path)

    df['Carimbo de data/hora'] = pd.to_datetime(df['Carimbo de data/hora'], dayfirst=True, errors='coerce')

    df_unique = df.drop_duplicates(subset=['Endereço de e-mail'])
    df_unique['month'] = df_unique['Carimbo de data/hora'].dt.to_period('M').dt.to_timestamp()

    monthly_counts = df_unique.groupby('month').size().reset_index(name='registrations')
    print(monthly_counts)

    plt.figure(figsize=(10,6))
    plt.plot(monthly_counts['month'], monthly_counts['registrations'], marker='o', linestyle='-', color='green')
    plt.xlabel('Mês')
    plt.ylabel('Número Acumulado de Usuários')
    plt.title('Crescimento Acumulado de Usuários Registrados no Cluster')
    plt.xticks(rotation=45)
    plt.grid(True)

    for idx, row in monthly_counts.iterrows():
        plt.text(row['month'], row['registrations'], str(row['registrations']), fontsize=9, ha='center', va='bottom')

    plt.tight_layout()
    plt.savefig('user_subs_by_month.png')
    plt.show()

    return "User Subscriptions by Month plotted successfully!"
