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
    [data-testid="stSidebar"] .stMarkdown p, [data-testid="stSidebar"] label, [data-testid="stSidebar"] .stRadio div {
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
CON_TUBO_KG = round(METROS_POR_GRADE * PESO_TUBO_METRO, 3) 
CON_BARRA_KG = 6.60 

DB_FILE = "log_atividades_mark.csv"
STOCK_FILE = "estoque_mark_atual.csv"

# --- FUNÇÕES DE DADOS ---
def registrar_log(cat, op, cli_nf, prod, status, qtd, kg):
    agora = datetime.now()
    novo = pd.DataFrame([{
        'DATA': agora.strftime("%d/%m/%Y"), 
        'HORA': agora.strftime("%H:%M:%S"),
        'CATEGORIA': cat, 
        'OPERACAO': op, 
        'CLIENTE_NF': cli_nf,
        'PRODUTO': prod, 
        'STATUS/TIPO': status, 
        'QTD (Un)': qtd, 
        'PESO (Kg)': str(round(kg, 2)).replace('.', ',')
    }])
    header = not os.path.exists(DB_FILE)
    novo.to_csv(DB_FILE, mode='a', header=header, index=False, sep=';', encoding='utf-8-sig')

if 'estoque' not in st.session_state:
    if os.path.exists(STOCK_FILE):
        try:
            st.session_state.estoque = pd.read_csv(STOCK_FILE, sep=';').to_dict('records')[0]
        except:
            st.session_state.estoque = {'tubo_kg': 0.0, 'barra_kg': 0.0, 'crua_un': 0, 'pintada_un': 0, 'galva_un': 0}
    else:
        st.session_state.estoque = {'tubo_kg': 0.0, 'barra_kg': 0.0, 'crua_un': 0, 'pintada_un': 0, 'galva_un': 0}

def salvar():
    pd.DataFrame([st.session_state.estoque]).to_csv(STOCK_FILE, index=False, sep=';', encoding='utf-8-sig')

# --- MENU LATERAL ---
with st.sidebar:
    st.markdown("<h1 class='titulo-mark'>MARK<br>EVENTOS</h1>", unsafe_allow_html=True)
    menu = st.radio("NAVEGAÇÃO", ["🏠 PAINEL", "🔨 PRODUÇÃO CRUA", "🎨 ACABAMENTO", "🤝 VENDAS", "🚚 CARGA", "📊 RELATÓRIO"])

# --- PÁGINAS ---
if menu == "🏠 PAINEL":
    st.header("📊 Resumo de Estoque e Capacidade")
    c1, c2, c3 = st.columns(3)
    c1.metric("GRADES CRUAS", f"{int(st.session_state.estoque['crua_un'])} Un")
    c2.metric("GRADES PINTADAS", f"{int(st.session_state.estoque['pintada_un'])} Un")
    c3.metric("GRADES GALVA.", f"{int(st.session_state.estoque['galva_un'])} Un")
    st.divider()
    ca, cb = st.columns(2)
    ca.metric("ESTOQUE TUBO 1.1/4", f"{st.session_state.estoque['tubo_kg']:.2f} Kg")
    cb.metric("ESTOQUE BARRA 3/8", f"{st.session_state.estoque['barra_kg']:.2f} Kg")

    cap_tubo = int(st.session_state.estoque['tubo_kg'] // CON_TUBO_KG) if st.session_state.estoque['tubo_kg'] > 0 else 0
    cap_barra = int(st.session_state.estoque['barra_kg'] // CON_BARRA_KG) if st.session_state.estoque['barra_kg'] > 0 else 0
    total_possivel = min(cap_tubo, cap_barra)
    gargalo = "Tubo" if cap_tubo <= cap_barra else "Barra"

    st.markdown(f"""
        <div class='capacidade-box'>
            <h3 style='margin:0; color:#EBC92C;'>🚀 POTENCIAL DE PRODUÇÃO IMEDIATA</h3>
            <p style='font-size: 2.5rem; font-weight: bold; margin: 10px 0;'>{total_possivel} <span style='font-size:1.2rem;'>Unidades</span></p>
            <p style='color:#AAAAAA;'>Item limitante: <b>{gargalo}</b></p>
        </div>
    """, unsafe_allow_html=True)

elif menu == "🔨 PRODUÇÃO CRUA":
    st.header("🔨 Fabricação")
    qtd = st.number_input("Quantidade de grades soldadas:", min_value=1, step=1)
    if st.button("REGISTRAR PRODUÇÃO"):
        t_t, t_b = qtd * CON_TUBO_KG, qtd * CON_BARRA_KG
        if st.session_state.estoque['tubo_kg'] >= t_t and st.session_state.estoque['barra_kg'] >= t_b:
            st.session_state.estoque['tubo_kg'] -= t_t
            st.session_state.estoque['barra_kg'] -= t_b
            st.session_state.estoque['crua_un'] += qtd
            registrar_log("PRODUCAO", "SOLDA", "INTERNO", "GRADE", "CRUA", qtd, t_t+t_b)
            salvar()
            st.success("Registrado com sucesso!")
        else: st.error("Material insuficiente!")

elif menu == "🎨 ACABAMENTO":
    st.header("🎨 Acabamento")
    tipo = st.selectbox("Destino:", ["Pintura", "Galvanização"])
    qtd = st.number_input("Quantidade:", min_value=1, step=1)
    if st.button("CONFIRMAR"):
        if st.session_state.estoque['crua_un'] >= qtd:
            st.session_state.estoque['crua_un'] -= qtd
            chave = 'pintada_un' if tipo == "Pintura" else 'galva_un'
            st.session_state.estoque[chave] += qtd
            registrar_log("ACABAMENTO", "PROCESSO", "INTERNO", "GRADE", tipo.upper(), qtd, 0)
            salvar()
            st.success("Movido com sucesso!")
        else: st.error("Sem grades cruas no estoque!")

elif menu == "🤝 VENDAS":
    st.header("🤝 Vendas")
    tipo = st.selectbox("Tipo:", ["Pintada", "Galvanizada"])
    cli = st.text_input("Cliente/Nota Fiscal:")
    qtd = st.number_input("Quantidade:", min_value=1, step=1)
    if st.button("FINALIZAR VENDA"):
        chave = 'pintada_un' if tipo == "Pintada" else 'galva_un'
        if st.session_state.estoque[chave] >= qtd and cli:
            st.session_state.estoque[chave] -= qtd
            registrar_log("VENDA", "SAÍDA", cli.upper(), "GRADE", tipo.upper(), qtd, 0)
            salvar()
            st.balloons()
            st.success("Venda registrada!")
        else: st.error("Estoque insuficiente ou falta nome do cliente!")

elif menu == "🚚 CARGA":
    st.header("🚚 Carga de Aço")
    mat = st.selectbox("Material:", ["TUBO 1.1/4", "BARRA 3/8"])
    peso = st.number_input("Peso Total (Kg):", min_value=0.0)
    if st.button("ADICIONAR"):
        chave = 'tubo_kg' if "TUBO" in mat else 'barra_kg'
        st.session_state.estoque[chave] += peso
        registrar_log("CARGA", "ENTRADA", "FORNECEDOR", "AÇO", mat, 0, peso)
        salvar()
        st.success(f"{peso} Kg adicionados!")

elif menu == "📊 RELATÓRIO":
    st.header("📋 Histórico de Atividades")
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE, sep=';', encoding='utf-8-sig')
        if not df.empty:
            st.dataframe(df, use_container_width=True)
            csv_data = df.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
            st.download_button("📥 Baixar Excel", csv_data, "Relatorio_Mark.csv", "text/csv")
        else:
            st.info("Arquivo de log vazio. Realize uma operação.")
    else:
        st.warning("⚠️ Nenhum registro encontrado ainda.")
