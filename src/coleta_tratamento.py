import os
import requests
import json
import sqlite3
import sys
import time
import pandas as pd
from dotenv import load_dotenv
from tabulate import tabulate
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

if datetime.now() > datetime(2027, 1, 1):
    print("Prazo do projeto encerrado. Automação desativada.")
    sys.exit(0)

load_dotenv()

# API
url_camara = os.getenv("URL_CAMARA_DESPESAS")

def coleta_dados(deputado_id, anos):
    lista_completa = []

    # Configura sessão com retry automático
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=2)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)

    print("Iniciando a coleta de dados de múltiplos anos ...")

    for ano in anos:
        url = f"https://dadosabertos.camara.leg.br/api/v2/deputados/{deputado_id}/despesas?ano={ano}&itens=1000"
        try:
            resposta = session.get(url, timeout=30)
            if resposta.status_code == 200:
                dados = resposta.json().get("dados", [])
                if dados:
                    lista_completa.extend(dados)
                    print(f"Coletado ano {ano}: {len(dados)} registros.")
                else:
                    print(f"Ano {ano}: sem registros, pulando.")
            else:
                print(f"Erro no ano {ano}: {resposta.status_code}")
        except requests.exceptions.ConnectTimeout:
            print(f"Timeout no ano {ano}, pulando.")
        except requests.exceptions.RequestException as e:
            print(f"Erro no ano {ano}: {e}")

        time.sleep(1)  # Pausa entre requisições para respeitar a API

    return lista_completa

def salvar_dados_brutos(dados, caminho_arquivo):
    with open(caminho_arquivo, 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)
    print(f"Dado bruto salvo em: {caminho_arquivo}")

def tratamento_dados(dados_lista):
    print("Iniciando a limpeza e tratamento dos dados ...")

    df = pd.DataFrame(dados_lista)

    # Retirando colunas desnecessarias
    colunas_remover = [
        'codDocumento', 'codTipoDocumento', 'numDocumento',
        'urlDocumento', 'codLote', 'numRessarcimento'
    ]
    df = df.drop(columns=colunas_remover, errors='ignore')

    # Tratando colunas
    df['valorDocumento'] = pd.to_numeric(df['valorDocumento'], errors='coerce')
    df['dataDocumento'] = pd.to_datetime(df['dataDocumento'], errors='coerce').dt.date

    # Remove a linha se não tiver a data
    df = df.dropna(subset=['dataDocumento'])

    df['nomeFornecedor'] = df['nomeFornecedor'].replace('Gol Linhas Aéreas', 'GOL')

    # Salvando as alterações
    df.to_csv("data/despesas_tratadas.csv", index=False, encoding='utf-8')
    print("Limpeza concluída! Dados salvos em: data/despesas_tratadas.csv")
    print(f"Volume final de dados: {len(df)} registros.")

    return df

def enriquecimento_dados(df):
    print("Enriquecendo dados...")

    # Faixa de Valor
    def categorizar_valor(valor):
        if valor <= 500: return 'pequeno'
        elif valor <= 2000: return 'médio'
        else: return 'grande'

    df['faixaValor'] = df['valorDocumento'].apply(categorizar_valor)

    # Métricas de tempo
    df['dataDocumento'] = pd.to_datetime(df['dataDocumento'])
    df['trimestre'] = df['dataDocumento'].dt.quarter

    meses = {
        1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
        5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
        9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
    }
    df['nomeMes'] = df['mes'].map(meses)

    df.to_csv("data/despesas_enriquecidas.csv", index=False, encoding='utf-8')
    print("Enriquecimento concluído! Salvo em: data/despesas_enriquecidas.csv")

    return df

def amazenamento_dado(df, caminho_bd):
    print("Salvando os dados no banco de dados ...")

    conexao = sqlite3.connect(caminho_bd)
    df.to_sql('tb_despesas', conexao, if_exists='replace', index=False)
    conexao.close()

    print(f"Dados armazenados com sucesso no banco: {caminho_bd} na tabela 'tb_despesas'!")

if __name__ == "__main__":

    deputado_id = 160541
    anos = range(2023, 2027)  # Apenas anos com dados reais

    # Coleta
    dados_brutos = coleta_dados(deputado_id, anos)

    if dados_brutos:
        caminho_destino = "data/despesas.json"
        salvar_dados_brutos(dados_brutos, caminho_destino)

        dados_limpos = tratamento_dados(dados_brutos)
        dados_finais = enriquecimento_dados(dados_limpos)
        amazenamento_dado(dados_finais, "data/camara_dados.db")