import streamlit as st
import pandas as pd
from datetime import datetime
import os
from PIL import Image

# --- CONFIGURAÇÃO BÁSICA ---
st.set_page_config(page_title="TESTE MARK EVENTOS", layout="wide")

# Estilo Visual Mark Eventos
st.markdown("""
    <style>
    .main { background-color: #0A0A0A; color: #FFFFFF; }
    [data-testid="stSidebar"] { background-color: #000000; border-right: 2px solid #EBC92C; }
    [data-testid="stMetric"] { 
        background-color: #161616; border-radius: 10px; 
        border-left: 5px solid #EBC92C; padding: 20px; 
    }
    .stButton>button {
        width: 100%; background-color: #EBC92C; color: black;
        font-weight: bold; height: 3em;
    }
    </style>
    """, unsafe_allow_html=True)

# --- ARQUIVOS DE DADOS ---
DB_FILE = "log_mark_teste.csv"
STOCK_FILE = "estoque_mark_teste.csv"

# Constantes de Consumo
CON_TUBO = 6.162
CON_BARRA = 6.60

def registrar_log(cat, op, cli, prod, qtd, kg):
    agora = datetime.now()
    novo = pd.DataFrame([{
        'DATA': agora.strftime("%d/%m/%Y"),
        'HORA': agora.strftime("%H:%M:%S"),
        'CATEGORIA': cat,
        'OPERACAO': op,
        'CLIENTE_NF': cli,
        'PRODUTO': prod,
        'QTD': qtd,
        'KG': str(round(kg, 2)).replace('.', ',')
    }])
    header = not os.path.exists(DB_FILE)
    novo.to_csv(DB_FILE, mode='a', header=header, index=False, sep=';', encoding='utf-8-sig')

# Inicialização Segura de Estoque
if 'estoque' not in st.session_state:
    if os.path.exists(STOCK_FILE):
        try:
            st.session_state.estoque = pd.read_csv(STOCK_FILE, sep=';').to_dict('records')[0]
        except:
            st.session_state.estoque = {'tubo': 0.0, 'barra': 0.0, 'prontas': 0}
    else:
        st.session_state.estoque = {'tubo': 0.0, 'barra': 0.0, 'prontas': 0}

def salvar_estoque():
    pd.DataFrame([st.session_state.estoque]).to_csv(STOCK_FILE, index=False, sep=';', encoding='utf-8-sig')

# --- INTERFACE ---
with st.sidebar:
    if os.path.exists("logo.png"):
        st.image(Image.open("logo.png"))
    else:
        st.title("MARK EVENTOS")
    st.divider()
    menu = st.radio("MENU", ["PAINEL", "PRODUÇÃO", "VENDAS", "CARGA", "RELATÓRIO"])

if menu == "PAINEL":
    st.header("📊 Painel de Testes")
    c1, c2, c3 = st.columns(3)
    c1.metric("Grades Prontas", f"{int(st.session_state.estoque['prontas'])} un")
    c2.metric("Tubo (Kg)", f"{st.session_state.estoque['tubo']:.1f}")
    c3.metric("Barra (Kg)", f"{st.session_state.estoque['barra']:.1f}")

elif menu == "PRODUÇÃO":
    st.header("🔨 Registrar Fabricação")
    qtd = st.number_input("Qtd produzida:", min_value=1, step=1)
    if st.button("Confirmar"):
        g_t, g_b = qtd * CON_TUBO, qtd * CON_BARRA
        if st.session_state.estoque['tubo'] >= g_t:
            st.session_state.estoque['tubo'] -= g_t
            st.session_state.estoque['barra'] -= g_b
            st.session_state.estoque['prontas'] += qtd
            registrar_log("PRODUCAO", "FABRICAÇÃO", "INTERNO", "GRADE", qtd, g_t+g_b)
            salvar_estoque()
            st.success("Produção registrada!")
        else: st.error("Sem material!")

elif menu == "VENDAS":
    st.header("🤝 Registrar Venda")
    cli = st.text_input("Cliente:")
    qtd = st.number_input("Qtd vendida:", min_value=1, step=1)
    if st.button("Vender"):
        if st.session_state.estoque['prontas'] >= qtd and cli:
            st.session_state.estoque['prontas'] -= qtd
            registrar_log("VENDA", "VENDA", cli.upper(), "GRADE", qtd, 0)
            salvar_estoque()
            st.success("Venda feita!")
        else: st.error("Verifique estoque/cliente.")

elif menu == "CARGA":
    st.header("🚚 Entrada de Aço")
    mat = st.selectbox("Material:", ["tubo", "barra"])
    peso = st.number_input("Peso (Kg):", min_value=0.0)
    if st.button("Adicionar"):
        st.session_state.estoque[mat] += peso
        registrar_log("CARGA", "ENTRADA", "FORNECEDOR", mat, 0, peso)
        salvar_estoque()
        st.success("Estoque abastecido!")

elif menu == "RELATÓRIO":
    st.header("📋 Relatório Excel")
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE, sep=';', encoding='utf-8-sig')
            st.dataframe(df, use_container_width=True)
            csv = df.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
            st.download_button("📥 Baixar Excel", csv, "Relatorio_Mark.csv", "text/csv")
        except:
            st.error("Erro no arquivo. Por favor, delete os arquivos CSV na pasta e tente de novo.")
