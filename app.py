import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- CONFIGURAÇÃO E ESTILO ---
st.set_page_config(page_title="SISTEMA MARK EVENTOS", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #000000 !important; }
    .main { background-color: #000000 !important; color: #FFFFFF !important; }
    
    /* MENU LATERAL BRANCO */
    [data-testid="stSidebar"] { background-color: #000000 !important; border-right: 2px solid #EBC92C; }
    [data-testid="stSidebar"] .stMarkdown p, [data-testid="stSidebar"] label, [data-testid="stSidebar"] .stRadio div {
        color: #FFFFFF !important; font-size: 1.1rem !important; font-weight: bold !important;
    }
    
    .titulo-mark {
        color: #EBC92C !important; text-align: center; font-family: 'Arial Black', sans-serif;
        border-bottom: 2px solid #EBC92C; padding-bottom: 15px; margin-bottom: 25px;
    }

    /* ESTILO MÉTRICAS */
    [data-testid="stMetric"] { 
        background-color: #111111 !important; border-radius: 12px; 
        border: 1px solid #333; border-left: 6px solid #EBC92C; padding: 15px;
    }
    [data-testid="stMetricValue"] { color: #FFFFFF !important; }
    [data-testid="stMetricLabel"] { color: #EBC92C !important; }
    
    /* DESTAQUE PARA CAPACIDADE */
    .capacidade-box {
        background-color: #1A1A1A; border: 2px dashed #EBC92C;
        padding: 20px; border-radius: 15px; text-align: center; margin-top: 20px;
    }

    .stButton>button {
        background-color: #EBC92C !important; color: #000000 !important;
        font-weight: 900 !important; border-radius: 10px !important; height: 3.5em;
    }
    input, select, .stSelectbox div { background-color: #1A1A1A !important; color: #FFFFFF !important; border: 1px solid #444 !important; }
    label { color: #FFFFFF !important; }
    h1, h2, h3 { color: #EBC92C !important; }
    </style>
    """, unsafe_allow_html=True)

# --- CONSTANTES TÉCNICAS ---
PESO_TUBO_METRO = 0.692
METROS_POR_GRADE = 6.12
CON_TUBO_KG = round(METROS_POR_GRADE * PESO_TUBO_METRO, 3) # 4.235 Kg
CON_BARRA_KG = 6.60 

DB_FILE = "dados_mark_v11.csv"
STOCK_FILE = "estoque_mark_v11.csv"

# --- FUNÇÕES DE DADOS ---
def registrar_log(cat, op, cli_nf, prod, status, qtd, kg):
    novo = pd.DataFrame([{
        'DATA': datetime.now().strftime("%d/%m/%Y"), 'HORA': datetime.now().strftime("%H:%M:%S"),
        'CATEGORIA': cat, 'OPERACAO': op, 'CLIENTE_NF': cli_nf,
        'PRODUTO': prod, 'STATUS/TIPO': status, 'QTD (Un)': qtd, 
        'PESO (Kg)': str(round(kg, 2)).replace('.', ',')
    }])
    novo.to_csv(DB_FILE, mode='a', header=not os.path.exists(DB_FILE), index=False, sep=';', encoding='utf-8-sig')

if 'estoque' not in st.session_state:
    if os.path.exists(STOCK_FILE):
        st.session_state.estoque = pd.read_csv(STOCK_FILE, sep=';').to_dict('records')[0]
    else:
        st.session_state.estoque = {'tubo_kg': 0.0, 'barra_kg': 0.0, 'crua_un': 0, 'pintada_un': 0, 'galva_un': 0}

def salvar():
    pd.DataFrame([st.session_state.estoque]).to_csv(STOCK_FILE, index=False, sep=';', encoding='utf-8-sig')

# --- INTERFACE ---
with st.sidebar:
