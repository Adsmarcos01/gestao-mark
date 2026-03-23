import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="SISTEMA MARK EVENTOS", layout="wide")

# --- CSS PERSONALIZADO (CORES DA MARCA) ---
st.markdown("""
    <style>
    /* Fundo e Texto Principal */
    .main { background-color: #0A0A0A; color: #FFFFFF; }
    
    /* Barra Lateral */
    [data-testid="stSidebar"] { 
        background-color: #000000; 
        border-right: 2px solid #EBC92C; 
    }
    
    /* Título Estilizado no Menu */
    .titulo-mark {
        color: #EBC92C;
        text-align: center;
        font-family: 'Arial Black', Gadget, sans-serif;
        border-bottom: 2px solid #EBC92C;
        padding-bottom: 10px;
        margin-bottom: 20px;
    }

    /* Cartões de Métricas (Dashboard) */
    [data-testid="stMetric"] { 
        background-color: #161616; 
        border-radius: 10px; 
        border-left: 5px solid #EBC92C; 
        padding: 20px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.5);
    }
    
    /* Botões Amarelos Mark Eventos */
    .stButton>button {
        width: 100%;
        background-color: #EBC92C;
        color: #000000;
        font-weight: bold;
        border-radius: 8px;
        border: none;
        height: 3.5em;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #FFFFFF;
        color: #000000;
        transform: scale(1.02);
    }

    /* Inputs e Seletores */
    input { background-color: #1c1f26 !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# --- BANCO DE DATOS ---
DB_FILE = "dados_mark_v7.csv"
STOCK_FILE = "estoque_mark_v7.csv"
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

# --- BARRA LATERAL (SEM LOGO) ---
with st.sidebar:
    st.markdown("<h1 class='titulo-mark'>MARK<br>EVENTOS</h1>", unsafe_allow_html=True)
    menu = st.radio("NAVEGAÇÃO", ["🏠 PAINEL", "🔨 PRODUÇÃO", "🤝 VENDAS", "🚚 CARGA", "📊 RELATÓRIO"])

# --- CONTEÚDO ---
if menu == "🏠 PAINEL":
    st.markdown("<h2 style='color: #EBC92C;'>📊 Gestão de Inventário</h2>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.metric("GRADES PRONTAS", f"{int(st.session_state.estoque['prontas'])} un")
    c2.metric("TUBO 1.1/4 (Kg)", f"{st.session_state.estoque['tubo']:.1f}")
    c3.metric("BARRA 3/8 (Kg)", f"{st.session_state.estoque['barra']:.1f}")

elif menu == "🔨 PRODUÇÃO":
    st.header("🔨 Registrar Nova Fabricação")
    qtd = st.number_input("Quantidade de grades fabricadas:", min_value=1, step=1)
    if st.button("CONFIRMAR PRODUÇÃO"):
        g_t, g_b = qtd * CON_TUBO, qtd * CON_BARRA
        if st.session_state.estoque['tubo'] >= g_t:
            st.session_state.estoque['tubo'] -= g_t
            st.session_state.estoque['barra'] -= g_b
            st.session_state.estoque['prontas'] += qtd
            registrar_log("PRODUCAO", "FABRICAÇÃO", "INTERNO", "GRADE", qtd, g_t+g_b)
            salvar_estoque()
            st.success(f"Sucesso! {qtd} grades adicionadas ao estoque.")
        else: st.error("Materia-prima insuficiente no galpão!")

elif menu == "🤝 VENDAS":
    st.header("🤝 Registrar Venda")
    cli = st.text_input("Nome do Cliente:")
    qtd = st.number_input("Quantidade vendida:", min_value=1, step=1)
    if st.button("FINALIZAR VENDA"):
        if st.session_state.estoque['prontas'] >= qtd and cli:
            st.session_state.estoque['prontas'] -= qtd
            registrar_log("VENDA", "SAÍDA", cli.upper(), "GRADE", qtd, 0)
            salvar_estoque()
            st.balloons()
            st.success("Venda registrada com sucesso!")
        else: st.error("Erro: Verifique estoque ou nome do cliente.")

elif menu == "🚚 CARGA":
    st.header("🚚 Entrada de Matéria-Prima")
    mat = st.selectbox("Selecione o Material:", ["tubo", "barra"])
    nf = st.text_input("Nota Fiscal:")
    peso = st.number_input("Peso total (Kg):", min_value=0.0)
    if st.button("ATUALIZAR GALPÃO"):
        st.session_state.estoque[mat] += peso
        registrar_log("CARGA", "ENTRADA", f"NF: {nf}", mat, 0, peso)
        salvar_estoque()
        st.success("Estoque abastecido!")

elif menu == "RELATÓRIO":
    st.header("📋 Relatório Excel")
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE, sep=';', encoding='utf-8-sig')
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
        st.download_button("📥 Baixar Excel", csv, "Relatorio_Mark.csv", "text/csv")
