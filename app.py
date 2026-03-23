import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- CONFIGURAÇÃO E ESTILO (MENU BRANCO E FUNDO PRETO) ---
st.set_page_config(page_title="SISTEMA MARK EVENTOS", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #000000 !important; }
    .main { background-color: #000000 !important; color: #FFFFFF !important; }
    
    /* MENU LATERAL - TEXTO BRANCO PURO */
    [data-testid="stSidebar"] { background-color: #000000 !important; border-right: 2px solid #EBC92C; }
    [data-testid="stSidebar"] .stMarkdown p, 
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stRadio div {
        color: #FFFFFF !important; 
        font-size: 1.1rem !important; 
        font-weight: bold !important;
    }
    
    /* TÍTULO DA MARCA */
    .titulo-mark {
        color: #EBC92C !important; text-align: center; font-family: 'Arial Black', sans-serif;
        border-bottom: 2px solid #EBC92C; padding-bottom: 15px; margin-bottom: 25px;
    }

    /* ESTILO DOS BOTÕES E MÉTRICAS */
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

# --- CÁLCULOS TÉCNICOS ATUALIZADOS ---
# Tubo 1.1/4 Chapa 20 (0.90mm) -> ~0.692 kg/m
# Consumo por grade: 6.12 metros
PESO_TUBO_POR_METRO = 0.692
METRAGEM_TUBO_POR_GRADE = 6.12
CON_TUBO_KG = round(METRAGEM_TUBO_POR_GRADE * PESO_TUBO_POR_METRO, 3) # ~4.235 Kg
CON_BARRA_KG = 6.60  # Barra 3/8 mantida conforme anterior

DB_FILE = "dados_mark_v10.csv"
STOCK_FILE = "estoque_mark_v10.csv"

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

# --- MENU LATERAL ---
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
    ca.metric("ESTOQUE TUBO", f"{st.session_state.estoque['tubo_kg']:.2f} Kg")
    cb.metric("ESTOQUE BARRA", f"{st.session_state.estoque['barra_kg']:.2f} Kg")

elif menu == "🔨 PRODUÇÃO CRUA":
    st.header("🔨 Fabricação de Grades Cruas")
    st.write(f"Consumo estimado por grade: {METRAGEM_TUBO_POR_GRADE}m de tubo (~{CON_TUBO_KG} Kg)")
    qtd = st.number_input("Quantidade de grades soldadas:", min_value=1, step=1)
    if st.button("REGISTRAR PRODUÇÃO"):
        total_t, total_b = qtd * CON_TUBO_KG, qtd * CON_BARRA_KG
        if st.session_state.estoque['tubo_kg'] >= total_t:
            st.session_state.estoque['tubo_kg'] -= total_t
            st.session_state.estoque['barra_kg'] -= total_b
            st.session_state.estoque['crua_un'] += qtd
            registrar_log("PRODUCAO", "SOLDA", "INTERNO", "GRADE", "CRUA", qtd, total_t+total_b)
            salvar(); st.success(f"Produção de {qtd} Un registrada!")
        else: st.error("Material insuficiente para esta quantidade!")

elif menu == "🎨 ACABAMENTO":
    st.header("🎨 Enviar para Acabamento")
    st.info(f"Disponível para acabamento: {int(st.session_state.estoque['crua_un'])} Un (Cruas)")
    tipo = st.selectbox("Destino:", ["Pintura", "Galvanização"])
    qtd = st.number_input("Quantidade:", min_value=1, step=1)
    if st.button("CONFIRMAR PROCESSO"):
        if st.session_state.estoque['crua_un'] >= qtd:
            st.session_state.estoque['crua_un'] -= qtd
            chave = 'pintada_un' if tipo == "Pintura" else 'galva_un'
            st.session_state.estoque[chave] += qtd
            registrar_log("ACABAMENTO", "PROCESSO", "INTERNO", "GRADE", tipo.upper(), qtd, 0)
            salvar(); st.success(f"Movido para {tipo} com sucesso!")
        else: st.error("Não há grades cruas suficientes!")

elif menu == "🤝 VENDAS":
    st.header("🤝 Registrar Venda")
    tipo = st.selectbox("Tipo de Grade:", ["Pintada", "Galvanizada"])
    cli = st.text_input("Cliente/NF:")
    qtd = st.number_input("Quantidade:", min_value=1, step=1)
    if st.button("FINALIZAR VENDA"):
        chave = 'pintada_un' if tipo == "Pintada" else 'galva_un'
        if st.session_state.estoque[chave] >= qtd and cli:
            st.session_state.estoque[chave] -= qtd
            registrar_log("VENDA", "SAÍDA", cli.upper(), "GRADE", tipo.upper(), qtd, 0)
            salvar(); st.balloons(); st.success("Venda registrada!")
        else: st.error("Estoque insuficiente ou dados incompletos.")

elif menu == "🚚 CARGA":
    st.header("🚚 Entrada de Materiais (Aço)")
    mat = st.selectbox("Material:", ["TUBO 1.1/4", "BARRA 3/8"])
    peso = st.number_input("Peso Total Recebido (Kg):", min_value=0.0)
    if st.button("DAR ENTRADA"):
        chave = 'tubo_kg' if "TUBO" in mat else 'barra_kg'
        st.session_state.estoque[chave] += peso
        registrar_log("CARGA", "ENTRADA", "FORNECEDOR", "MATERIA-PRIMA", mat, 0, peso)
        salvar(); st.success(f"{peso} Kg de {mat} adicionados!")

elif menu == "RELATÓRIO":
    st.header("📋 Relatório Geral Mark Eventos")
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE, sep=';', encoding='utf-8-sig')
        st.dataframe(df, use_container_width=True)
        st.download_button("📥 Baixar Excel", df.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig'), "Relatorio_Mark_Eventos.csv", "text/csv")
