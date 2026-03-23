import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- FORÇAR MODO ESCURO E ESTILO ---
st.set_page_config(page_title="SISTEMA MARK EVENTOS", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    /* 1. FUNDO TOTAL PRETO */
    .stApp { background-color: #000000 !important; }
    .main { background-color: #000000 !important; color: #FFFFFF !important; }
    
    /* 2. BARRA LATERAL (MENU ESQUERDO) */
    [data-testid="stSidebar"] { 
        background-color: #000000 !important; 
        border-right: 2px solid #EBC92C; 
    }
    /* Texto do Menu Lateral - Branco Puro e Negrito */
    [data-testid="stSidebar"] .stMarkdown p, 
    [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] span {
        color: #FFFFFF !important;
        font-size: 1.1rem !important;
        font-weight: 700 !important;
    }

    /* 3. TÍTULO DA MARCA */
    .titulo-mark {
        color: #EBC92C !important;
        text-align: center;
        font-family: 'Arial Black', sans-serif;
        border-bottom: 2px solid #EBC92C;
        padding-bottom: 15px;
        margin-bottom: 25px;
    }

    /* 4. CARTÕES DE ESTOQUE (MÉTRICAS) */
    [data-testid="stMetric"] { 
        background-color: #111111 !important; 
        border-radius: 12px; 
        border: 1px solid #333;
        border-left: 6px solid #EBC92C;
        padding: 20px;
    }
    [data-testid="stMetricValue"] { color: #FFFFFF !important; }
    [data-testid="stMetricLabel"] { color: #EBC92C !important; }

    /* 5. BOTÕES AMARELOS */
    .stButton>button {
        background-color: #EBC92C !important;
        color: #000000 !important;
        font-weight: 900 !important;
        border-radius: 10px !important;
        height: 3.8em;
        text-transform: uppercase;
    }

    /* 6. INPUTS E CAMPOS DE TEXTO */
    input, select, .stSelectbox div {
        background-color: #1A1A1A !important;
        color: #FFFFFF !important;
        border: 1px solid #444 !important;
    }
    label { color: #FFFFFF !important; font-weight: bold; }

    /* 7. TABELA DE DADOS */
    .stDataFrame { background-color: #000000 !important; border: 1px solid #333; }
    
    h1, h2, h3 { color: #EBC92C !important; }
    </style>
    """, unsafe_allow_html=True)

# --- BANCO DE DADOS ---
DB_FILE = "dados_mark_v8.csv"
STOCK_FILE = "estoque_mark_v8.csv"
CON_TUBO, CON_BARRA = 6.162, 6.60

def registrar_log(cat, op, cli_nf, prod, acabamento, qtd, kg):
    agora = datetime.now()
    novo = pd.DataFrame([{
        'DATA': agora.strftime("%d/%m/%Y"), 'HORA': agora.strftime("%H:%M:%S"),
        'CATEGORIA': cat, 'OPERACAO': op, 'CLIENTE_NF': cli_nf,
        'PRODUTO': prod, 'ACABAMENTO': acabamento, 'QTD': qtd, 
        'KG': str(round(kg, 2)).replace('.', ',')
    }])
    header = not os.path.exists(DB_FILE)
    novo.to_csv(DB_FILE, mode='a', header=header, index=False, sep=';', encoding='utf-8-sig')

# Inicialização de Estoque (Diferenciando por acabamento)
if 'estoque' not in st.session_state:
    if os.path.exists(STOCK_FILE):
        try: st.session_state.estoque = pd.read_csv(STOCK_FILE, sep=';').to_dict('records')[0]
        except: st.session_state.estoque = {'tubo': 0.0, 'barra': 0.0, 'pintura': 0, 'galvanizacao': 0}
    else: st.session_state.estoque = {'tubo': 0.0, 'barra': 0.0, 'pintura': 0, 'galvanizacao': 0}

def salvar_estoque():
    pd.DataFrame([st.session_state.estoque]).to_csv(STOCK_FILE, index=False, sep=';', encoding='utf-8-sig')

# --- MENU LATERAL ---
with st.sidebar:
    st.markdown("<h1 class='titulo-mark'>MARK<br>EVENTOS</h1>", unsafe_allow_html=True)
    menu = st.radio("NAVEGAÇÃO", ["🏠 PAINEL", "🔨 PRODUÇÃO", "🤝 VENDAS", "🚚 CARGA", "📊 RELATÓRIO"])

# --- PÁGINAS ---
if menu == "🏠 PAINEL":
    st.header("📊 Painel de Estoque Atual")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("GRADES (PINTURA)", f"{int(st.session_state.estoque['pintura'])} un")
    with col2:
        st.metric("GRADES (GALVANIZAÇÃO)", f"{int(st.session_state.estoque['galvanizacao'])} un")
    
    st.divider()
    c1, c2 = st.columns(2)
    with c1: st.metric("TUBO 1.1/4 (Kg)", f"{st.session_state.estoque['tubo']:.1f}")
    with c2: st.metric("BARRA 3/8 (Kg)", f"{st.session_state.estoque['barra']:.1f}")

elif menu == "🔨 PRODUÇÃO":
    st.header("🔨 Registrar Fabricação e Destino")
    destino = st.selectbox("Destinar produção para:", ["Pintura", "Galvanização"])
    qtd = st.number_input("Quantidade produzida:", min_value=1, step=1)
    
    if st.button("CONFIRMAR PRODUÇÃO"):
        g_t, g_b = qtd * CON_TUBO, qtd * CON_BARRA
        if st.session_state.estoque['tubo'] >= g_t:
            st.session_state.estoque['tubo'] -= g_t
            st.session_state.estoque['barra'] -= g_b
            
            # Adiciona no estoque específico
            chave = 'pintura' if destino == "Pintura" else 'galvanizacao'
            st.session_state.estoque[chave] += qtd
            
            registrar_log("PRODUCAO", "FABRICAÇÃO", "INTERNO", "GRADE", destino.upper(), qtd, g_t+g_b)
            salvar_estoque()
            st.success(f"Registrado! {qtd} grades enviadas para {destino}.")
        else: st.error("Massa de aço insuficiente no estoque!")

elif menu == "🤝 VENDAS":
    st.header("🤝 Registrar Venda")
    tipo_venda = st.selectbox("Tipo de Grade Vendida:", ["Pintura", "Galvanização"])
    cli = st.text_input("Nome do Cliente:")
    qtd = st.number_input("Quantidade vendida:", min_value=1, step=1)
    
    if st.button("FINALIZAR VENDA"):
        chave = 'pintura' if tipo_venda == "Pintura" else 'galvanizacao'
        if st.session_state.estoque[chave] >= qtd and cli:
            st.session_state.estoque[chave] -= qtd
            registrar_log("VENDA", "SAÍDA", cli.upper(), "GRADE", tipo_venda.upper(), qtd, 0)
            salvar_estoque()
            st.balloons()
            st.success(f"Venda de {qtd} grades ({tipo_venda}) registrada!")
        else: st.error(f"Estoque insuficiente de grades com acabamento: {tipo_venda}")

elif menu == "🚚 CARGA":
    st.header("🚚 Entrada de Matéria-Prima")
    mat = st.selectbox("Tipo:", ["tubo", "barra"])
    nf = st.text_input("Nota Fiscal:")
    peso = st.number_input("Peso (Kg):", min_value=0.0)
    if st.button("ADICIONAR AO ESTOQUE"):
        st.session_state.estoque[mat] += peso
        registrar_log("CARGA", "ENTRADA", f"NF: {nf}", mat, "MATÉRIA-PRIMA", 0, peso)
        salvar_estoque()
        st.success("Carga adicionada com sucesso!")

elif menu == "RELATÓRIO":
    st.header("📋 Histórico e Filtros Profissionais")
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE, sep=';', encoding='utf-8-sig')
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
        st.download_button("📥 Baixar Planilha Separada", csv, "Relatorio_Mark_Oficial.csv", "text/csv")
