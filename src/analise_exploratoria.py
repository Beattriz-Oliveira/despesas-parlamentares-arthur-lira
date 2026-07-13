import sqlite3
import pandas as pd

def analise_dados (caminho_bd):
    conexao = sqlite3.connect(caminho_bd)
    df = pd.read_sql_query('SELECT* FROM tb_despesas', conexao)
    print("=== ANÁLISE EXPLORATÓRIA DOS DADOS ===")
    print(f"Total de registros analisados: {len(df)}\n")
    
    # Estatística Descritiva
    print("--- Resumo Estatístico dos Valores ---")
    print(df['valorDocumento'].describe())
    print('-' * 40)
    
    # Ranking de despesas que mais consomem dinheiro
    print("\n--- Top 5 Categorias Mais Caras (Soma Total) ---")
    gastos_tipo = df.groupby('tipoDespesa')['valorDocumento'].sum().sort_values(ascending= False)
    print(gastos_tipo.head(5))
    print('-' * 40)
    
    # Faixa de Valores
    print("\n--- Distribuição por Faixa de Valor ---")
    print(df['faixaValor'].value_counts(normalize= True) * 100)
    print('-' * 40)
    
    # Ponto fora da curva e o saldo negativo
    print("\n--- Ponto Fora da Curva ---")
    print(df[df['valorDocumento'] == df['valorDocumento'].max()][['tipoDespesa', 'nomeFornecedor', 'valorDocumento']])
    print("\n--- Justificativa do Valor Negativo ---")
    print(df[df['valorDocumento'] == df['valorDocumento'].min()][['tipoDespesa', 'nomeFornecedor', 'valorDocumento']])
    print('-' * 40)
    
    # Ranking dos fornecedores que mais receberam dinheiro
    top_fornecedor = df.groupby('nomeFornecedor')['valorDocumento'].sum().sort_values(ascending= False).head(3)
    print("\n--- Top 3 Empresas que mais Recebem ---")
    print(top_fornecedor)
    print('-' * 40)
    
    # Verificação de fidelidade
    locacoes = df[df['tipoDespesa'] == 'LOCAÇÃO OU FRETAMENTO DE VEÍCULOS AUTOMOTORES']
    print("\n--- Frequência de Locadoras Utilizadas ---")
    print(locacoes['nomeFornecedor'].value_counts())
    print('-' * 40)
    
    # Evolução temporal dos gastos
    gastos_anuais = df.groupby('ano')['valorDocumento'].sum().sort_values(ascending= False).head
    print("\n--- Gastos Totais por Ano ---")
    print(gastos_anuais)
    print('-' * 40)
    
    # Gastos do ano de 2026 - ano de eleição de deputados
    dados_2026 = df[df['ano'] == 2026]
    gastos_mes_2026 = dados_2026.groupby('mes')['valorDocumento'].sum().sort_index()
    print("\n--- Evolução de Gastos Mês a Mês em 2026 ---")
    print(gastos_mes_2026)
    media_mensal = gastos_mes_2026.mean()
    print(f"\nMédia de gasto mensal atual: R$ {media_mensal:.2f}")
    
    # Gastos do ano de 2024 -- ano de eleição de prefeitos
    dados_2024 = df[df['ano'] == 2024]
    gastos_mes_2024 = dados_2024.groupby('mes')['valorDocumento'].sum().sort_index()
    print("\n--- Evolução de Gastos Mês a Mês em 2024 ---")
    print(gastos_mes_2024)
    media_mensal = gastos_mes_2024.mean()
    print(f"\nMédia de gasto mensal atual: R$ {media_mensal:.2f}")
    
if __name__ == '__main__':
    analise_dados("data/camara_dados.db")