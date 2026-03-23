import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="SISTEMA MARK EVENTOS", layout="wide")

# --- CSS PERSONALIZADO (ALTO CONTRASTE) ---
st.markdown("""
    <style>
    /* 1. FUNDO E TEXTOS GERAIS */
    .main { background-color: #000000 !important; color: #FFFFFF !important; }
    
    /* 2. BARRA LATERAL */
    [data-testid="stSidebar"] { 
        background-color: #000000 !important; 
        border-right: 2px solid #EBC92C; 
    }
    [data-testid="stSidebar"] .stMarkdown p, [data-testid="stSidebar"] label {
        color: #FFFFFF !important;
        font-weight: bold;
    }

    /* 3. TÍTULO DA MARCA */
    .titulo-mark {
        color: #EBC92C !important;
        text-align: center;
        font-family: 'Arial Black', sans-serif;
        border-bottom: 2px solid #EBC92C;
        padding-bottom: 10px;
        margin-bottom: 20px;
    }

    /* 4. MÉTRICAS (NÚMEROS GRANDES) */
    [data-testid="stMetricValue"] { color: #FFFFFF !important; font-weight: bold !important; }
    [data-testid="stMetricLabel"] { color: #EBC92C !important; font-size: 1.1rem !important; }
    [data-testid="stMetric"] { 
        background-color: #1A1A1A !important; 
        border-radius: 10px; 
        border-left: 5px solid #EBC92C;
        padding: 15px;
    }

    /* 5. BOTÕES */
    .stButton>button {
        background-color: #EBC92C !important;
        color: #000000 !important;
        font-weight: bold !important;
        border-radius: 8px !important;
        height: 3.5em;
        border: none !important;
    }
    .stButton>button:hover {
        background-color: #FFFFFF !important;
        color: #000000 !important;
    }

    /* 6. CAMPOS DE ENTRADA (ESCRITA) */
    input, select, textarea {
        background-color: #262626 !important;
        color: #FFFFFF !important;
        border: 1px solid #EBC92C !important;
    }
    label { color: #FFFFFF !important; } /* Cor dos nomes dos campos */

    /* 7. TABELA (RELATÓRIO) */
    .stDataFrame { background-color: #1A1A1A !important; }
    
    /* Títulos e Subtítulos */
    h1, h2, h3 { color: #EBC92C !important; }
    </style>
    """, unsafe_allow_html=True)

# --- CONFIGURAÇÃO DE DADOS ---
DB_FILE = "dados_mark_v7.csv"
STOCK_FILE = "estoque_mark_v7.csv"
CON_TUBO, CON_BARRA = 6.162, 6.60

def registrar_log(cat, op, cli, prod, qtd, kg):
    agora = datetime.now()
    novo = pd.DataFrame([{
        'DATA': agora.strftime("%d/%m/%Y"), 'HORA': agora.strftime("%H:%M:%S"),
        'CATEGORIA': cat, 'OPERACAO': op, 'CLIENTE_NF': cli,
        'PRODUTO': prod, 'QTD': qtd, 'KG': str(round(kg, 2)).replace('.', ',')
    }])
    header = not os.path.exists(DB_FILE)
    novo.to_csv(DB_FILE, mode='a', header=header, index=False, sep=';', encoding='utf-8-sig')

if 'estoque' not in st.session_state:
    if os.path.exists(STOCK_FILE):
        try: st.session_state.estoque = pd.read_csv(STOCK_FILE, sep=';').to_dict('records')[0]
        except: st.session_state.estoque = {'tubo': 0.0, 'barra': 0.0, 'prontas': 0}
    else: st.session_state.estoque = {'tubo': 0.0, 'barra': 0.0, 'prontas': 0}

def salvar_estoque():
    pd.DataFrame([st.session_state.estoque]).to_csv(STOCK_FILE, index=False, sep=';', encoding='utf-8-sig')

# --- MENU LATERAL ---
with st.sidebar:
    st.markdown("<h1 class='titulo-mark'>MARK<br>EVENTOS</h1>", unsafe_allow_html=True)
    menu = st.radio("NAVEGAÇÃO", ["🏠 PAINEL", "🔨 PRODUÇÃO", "🤝 VENDAS", "🚚 CARGA", "📊 RELATÓRIO"])

# --- PÁGINAS ---
if menu == "🏠 PAINEL":
    st.header("📊 Painel Geral de Estoque")
    c1, c2, c3 = st.columns(3)
    c1.metric("GRADES PRONTAS", f"{int(st.session_state.estoque['prontas'])} un")
    c2.metric("TUBO 1.1/4 (Kg)", f"{st.session_state.estoque['tubo']:.1f}")
    c3.metric("BARRA 3/8 (Kg)", f"{st.session_state.estoque['barra']:.1f}")

elif menu == "🔨 PRODUÇÃO":
    st.header("🔨 Registrar Fabricação")
    qtd = st.number_input("Quantidade produzida:", min_value=1, step=1)
    if st.button("CONFIRMAR PRODUÇÃO"):
        g_t, g_b = qtd * CON_TUBO, qtd * CON_BARRA
        if st.session_state.estoque['tubo'] >= g_t:
            st.session_state.estoque['tubo'] -= g_t
            st.session_state.estoque['barra'] -= g_b
            st.session_state.estoque['prontas'] += qtd
            registrar_log("PRODUCAO", "FABRICAÇÃO", "INTERNO", "GRADE", qtd, g_t+g_b)
            salvar_estoque()
            st.success("Estoque atualizado!")
        else: st.error("Massa de aço insuficiente!")

elif menu == "🤝 VENDAS":
    st.header("🤝 Registrar Venda")
    cli = st.text_input("Nome do Cliente:")
    qtd = st.number_input("Quantidade vendida:", min_value=1, step=1)
    if st.button("FINALIZAR VENDA"):
        if st.session_state.estoque['prontas'] >= qtd and cli:
            st.session_state.estoque['prontas'] -= qtd
            registrar_log("VENDA", "SAÍDA", cli.upper(), "GRADE", qtd, 0)
            salvar_estoque()
            st.success("Venda registrada!")
        else: st.error("Verifique estoque ou nome do cliente.")

elif menu == "🚚 CARGA":
    st.header("🚚 Entrada de Material")
    mat = st.selectbox("Tipo:", ["tubo", "barra"])
    nf = st.text_input("Nota Fiscal:")
    peso = st.number_input("Peso (Kg):", min_value=0.0)
    if st.button("ADICIONAR AO ESTOQUE"):
        st.session_state.estoque[mat] += peso
        registrar_log("CARGA", "ENTRADA", f"NF: {nf}", mat, 0, peso)
        salvar_estoque()
        st.success("Carga adicionada!")

elif menu == "RELATÓRIO":
    st.header("📋 Histórico Completo")
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE, sep=';', encoding='utf-8-sig')
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
        st.download_button("📥 Baixar Planilha", csv, "Relatorio_Mark.csv", "text/csv")
