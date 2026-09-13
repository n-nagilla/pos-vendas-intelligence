import sqlite3
import pandas as pd
from datetime import datetime
import os

DB_PATH = "data/garantias.db"

def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ordens_servico (
            Numero INTEGER PRIMARY KEY,
            Tipo TEXT,
            Cliente TEXT,
            Modelo TEXT,
            Serie TEXT,
            Recep TEXT,
            Chassi TEXT,
            Emissao TEXT,
            Prometida TEXT,
            Itens_Liquido REAL DEFAULT 0,
            Serv_Liquido REAL DEFAULT 0,
            Valor_Liquido REAL DEFAULT 0,
            Operacao TEXT,
            Marca TEXT DEFAULT '',
            Consultor_Responsavel TEXT DEFAULT '',
            Dono_OS TEXT DEFAULT '',
            Descricao_Servico TEXT DEFAULT '',
            Necessita_Peca TEXT DEFAULT 'Não',
            Pedido_Peca TEXT DEFAULT '',
            Data_Pedido_Peca TEXT DEFAULT '',
            Previsao_Peca TEXT DEFAULT '',
            Peca_BO TEXT DEFAULT 'Não',
            Codigo_Descricao_Peca TEXT DEFAULT '',
            Data_Atendimento TEXT DEFAULT '',
            Servico_Concluido TEXT DEFAULT 'Não',
            Gargalo_Atual TEXT DEFAULT '',
            Status_Garantia TEXT DEFAULT 'Aberta na Oficina',
            AOL_Protocolo TEXT DEFAULT '',
            Processo_Fabrica TEXT DEFAULT '',
            Data_Submissao TEXT DEFAULT '',
            Data_Aprovacao TEXT DEFAULT '',
            Data_Rejeicao TEXT DEFAULT '',
            Motivo_Rejeicao TEXT DEFAULT '',
            Valor_Solicitado REAL DEFAULT 0,
            Valor_Aprovado REAL DEFAULT 0,
            Data_Faturamento TEXT DEFAULT '',
            Valor_Faturado REAL DEFAULT 0,
            Processo_Encerrado TEXT DEFAULT 'Não',
            Responsavel TEXT DEFAULT '',
            Proxima_Acao TEXT DEFAULT '',
            Prazo_Acao TEXT DEFAULT '',
            Observacoes TEXT DEFAULT '',
            Atualizado_Em TEXT
        )
    """)
    conn.commit()
    conn.close()

def sincronizar_excel_com_db(caminho_excel="data/raw/GARANTIAS EM ABERTO - MARDISA AGRO.xlsx"):
    init_db()
    if not os.path.exists(caminho_excel):
        return

    df_raw = pd.read_excel(caminho_excel, sheet_name=0)
    idx_header = 1
    df = df_raw.iloc[idx_header + 1:].copy()
    df.columns = [str(c).strip() for c in df_raw.iloc[idx_header].tolist()]

    df["Numero"] = pd.to_numeric(df["Numero"], errors="coerce").fillna(0).astype(int)
    df = df[df["Numero"] > 0]

    for col in ["Itens Liquido", "Serv. Liquido", "Valor Liquido"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    def mapear_filial(cod):
        s = str(cod).upper()
        if "223" in s: return "Imperatriz"
        elif "225" in s: return "Alto Alegre"
        elif "221" in s: return "Fendt Balsas"
        elif "222" in s: return "Valtra Balsas"
        return "Regional"

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    agora = datetime.now().strftime("%Y-%m-%d %H:%M")

    for _, row in df.iterrows():
        num = int(row["Numero"])
        tipo = str(row.get("Tipo", ""))
        cliente = str(row.get("Cliente", ""))
        modelo = str(row.get("Modelo", ""))
        recep = str(row.get("Recep.", ""))
        chassi = str(row.get("Chassi", ""))
        emissao = str(row.get("Emissao", ""))
        prometida = str(row.get("Prometida", ""))
        itens = float(row.get("Itens Liquido", 0))
        serv = float(row.get("Serv. Liquido", 0))
        valor = float(row.get("Valor Liquido", 0))
        operacao = mapear_filial(recep)

        cursor.execute("SELECT Numero FROM ordens_servico WHERE Numero = ?", (num,))
        existe = cursor.fetchone()

        if not existe:
            cursor.execute("""
                INSERT INTO ordens_servico (
                    Numero, Tipo, Cliente, Modelo, Recep, Chassi, Emissao, Prometida,
                    Itens_Liquido, Serv_Liquido, Valor_Liquido, Operacao, Atualizado_Em
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (num, tipo, cliente, modelo, recep, chassi, emissao, prometida, itens, serv, valor, operacao, agora))
        else:
            cursor.execute("""
                UPDATE ordens_servico
                SET Itens_Liquido = ?, Serv_Liquido = ?, Valor_Liquido = ?, Operacao = ?
                WHERE Numero = ?
            """, (itens, serv, valor, operacao, num))

    conn.commit()
    conn.close()

def carregar_dados_gestao():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM ordens_servico", conn)
    conn.close()

    if df.empty:
        return df

    df["Emissao_dt"] = pd.to_datetime(df["Emissao"], format="%d/%m/%Y", errors="coerce")
    hoje = datetime.now()
    df["Dias_Aberto"] = (hoje - df["Emissao_dt"]).dt.days.fillna(0).astype(int)
    return df

def atualizar_os_completa(num_os, dados_dict):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    agora = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    campos = ", ".join([f"{k} = ?" for k in dados_dict.keys()])
    valores = list(dados_dict.values())
    valores.extend([agora, num_os])

    query = f"UPDATE ordens_servico SET {campos}, Atualizado_Em = ? WHERE Numero = ?"
    cursor.execute(query, valores)
    conn.commit()
    conn.close()
