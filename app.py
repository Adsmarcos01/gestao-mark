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
    [data-testid="stSidebar"] { background-color: #000000 !important; border-right: 2px solid #EBC92C; }
    [data-testid="stSidebar"] .stMarkdown p, [data-testid="stSidebar"] label {
        color: #FFFFFF !important; font-size: 1.1rem !important; font-weight: bold !important;
    }
    .titulo-mark {
        color: #EBC92C !important; text-align: center; font-family: 'Arial Black', sans-serif;
        border-bottom: 2px solid #EBC92C; padding-bottom: 15px; margin-bottom: 25px;
    }
    [data-testid="stMetric"] { 
        background-color: #111111 !important; border-radius: 12px; 
        border: 1px solid #333; border-left: 6px solid #EBC92C; padding: 15px;
    }
    [data-testid="stMetricValue"] { color: #FFFFFF !important; }
    [data-testid="stMetricLabel"] { color: #EBC92C !important; }
    .stButton>button {
        background-color: #EBC92C !important; color: #000000 !important;
        font-weight: 900 !important; border-radius: 10px !important; height: 3.5em;
    }
    input, select, .stSelectbox div { background-color: #1A1A1A !important; color: #FFFFFF !important; border: 1px solid #444 !important; }
    label { color: #FFFFFF !important; }
    h1, h2, h3 { color: #EBC92C !important; }
    </style>
    """, unsafe_allow_html=True)

# --- BANCO DE DADOS ---
DB_FILE = "dados_mark_v9.csv"
STOCK_FILE = "estoque_mark_v9.csv"
CON_TUBO, CON_BARRA = 6.162, 6.60

def registrar_log(cat, op, cli_nf, prod, status, qtd, kg):
    agora = datetime.now()
    novo = pd.DataFrame([{
        'DATA': agora.strftime("%d/%m/%Y"), 'HORA': agora.strftime("%H:%M:%S"),
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

# --- MENU ---
with st.sidebar:
    st.markdown("<h1 class='titulo-mark'>MARK<br>EVENTOS</h1>", unsafe_allow_html=True)
    menu = st.radio("NAVEGAÇÃO", ["🏠 PAINEL", "🔨 PRODUÇÃO CRUA", "🎨 ACABAMENTO", "🤝 VENDAS", "🚚 CARGA", "📊 RELATÓRIO"])

# --- PÁGINAS ---
if menu == "🏠 PAINEL":
    st.header("📊 Resumo de Estoque")
    c1, c2, c3 = st.columns(3)
    c1.metric("GRADES CRUAS", f"{int(st.session_state.estoque['crua_un'])} Un")
    c2.metric("GRADES PINTADAS", f"{int(st.session_state.estoque['pintada_un'])} Un")
    c3.metric("GRADES GALVA.", f"{int(st.session_state.estoque['galva_un'])} Un")
    st.divider()
    ca, cb = st.columns(2)
    ca.metric("TUBO 1.1/4", f"{st.session_state.estoque['tubo_kg']:.1f} Kg")
    cb.metric("BARRA 3/8", f"{st.session_state.estoque['barra_kg']:.1f} Kg")

elif menu == "🔨 PRODUÇÃO CRUA":
    st.header("🔨 Fabricação de Grades Cruas")
    qtd = st.number_input("Quantidade de grades soldadas:", min_value=1, step=1)
    if st.button("REGISTRAR PRODUÇÃO"):
        g_t, g_b = qtd * CON_TUBO, qtd * CON_BARRA
        if st.session_state.estoque['tubo_kg'] >= g_t:
            st.session_state.estoque['tubo_kg'] -= g_t
            st.session_state.estoque['barra_kg'] -= g_b
            st.session_state.estoque['crua_un'] += qtd
            registrar_log("PRODUCAO", "SOLDA", "INTERNO", "GRADE", "CRUA", qtd, g_t+g_b)
            salvar(); st.success("Grades cruas adicionadas ao estoque!")
        else: st.error("Falta aço no galpão!")

elif menu == "🎨 ACABAMENTO":
    st.header("🎨 Enviar para Acabamento")
    st.info(f"Saldo disponível de grades cruas: {int(st.session_state.estoque['crua_un'])} Un")
    tipo = st.selectbox("Destino do acabamento:", ["Pintura", "Galvanização"])
    qtd = st.number_input("Quantidade para processar:", min_value=1, step=1)
    if st.button("CONFIRMAR ACABAMENTO"):
        if st.session_state.estoque['crua_un'] >= qtd:
            st.session_state.estoque['crua_un'] -= qtd
            chave = 'pintada_un' if tipo == "Pintura" else 'galva_un'
            st.session_state.estoque[chave] += qtd
            registrar_log("ACABAMENTO", "PROCESSO", "INTERNO", "GRADE", tipo.upper(), qtd, 0)
            salvar(); st.success(f"Grades movidas para {tipo}!")
        else: st.error("Não há grades cruas suficientes!")

elif menu == "🤝 VENDAS":
    st.header("🤝 Registrar Venda")
    tipo = st.selectbox("Tipo de Grade:", ["Pintada", "Galvanizada"])
    cli = st.text_input("Cliente:")
    qtd = st.number_input("Quantidade:", min_value=1, step=1)
    if st.button("FINALIZAR VENDA"):
        chave = 'pintada_un' if tipo == "Pintada" else 'galva_un'
        if st.session_state.estoque[chave] >= qtd and cli:
            st.session_state.estoque[chave] -= qtd
            registrar_log("VENDA", "SAÍDA", cli.upper(), "GRADE", tipo.upper(), qtd, 0)
            salvar(); st.balloons(); st.success("Venda registrada!")
        else: st.error("Estoque insuficiente deste acabamento!")

elif menu == "🚚 CARGA":
    st.header("🚚 Entrada de Aço")
    mat = st.selectbox("Material:", ["tubo_kg", "barra_kg"])
    peso = st.number_input("Peso (Kg):", min_value=0.0)
    if st.button("ADICIONAR"):
        st.session_state.estoque[mat] += peso
        registrar_log("CARGA", "ENTRADA", "FORNECEDOR", "AÇO", mat.replace('_kg','').upper(), 0, peso)
        salvar(); st.success("Peso adicionado!")

elif menu == "RELATÓRIO":
    st.header("📋 Relatório Geral")
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE, sep=';', encoding='utf-8-sig')
        st.dataframe(df, use_container_width=True)
        st.download_button("📥 Baixar Excel", df.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig'), "Relatorio_Mark.csv", "text/csv")
