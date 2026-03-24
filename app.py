import streamlit as st
import pandas as pd
from datetime import datetime
import os
import urllib.parse
import plotly.express as px

# --- ESTILO VISUAL DE ALTO CONTRASTE ---
st.set_page_config(page_title="SISTEMA MARK EVENTOS", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #000000 !important; color: #FFFFFF !important; }
    [data-testid="stSidebar"] { background-color: #000000 !important; border-right: 2px solid #EBC92C; }
    .titulo-mark { color: #EBC92C !important; text-align: center; font-family: 'Arial Black'; border-bottom: 2px solid #EBC92C; padding-bottom: 10px; }
    .stButton>button { background-color: #EBC92C !important; color: #000 !important; font-weight: 900 !important; width: 100%; border-radius: 8px; height: 3.5em; }
    [data-testid="stMetric"] { background-color: #1A1A1A !important; border-left: 5px solid #EBC92C; padding: 15px; border-radius: 10px; }
    [data-testid="stMetricValue"] { color: #FFFFFF !important; }
    [data-testid="stMetricLabel"] { color: #EBC92C !important; font-weight: bold !important; }
    label, .stMarkdown, p, span { color: #E0E0E0 !important; font-size: 1.05rem; }
    input, select, .stSelectbox div { background-color: #1A1A1A !important; color: #FFFFFF !important; border: 1px solid #EBC92C !important; }
    h1, h2, h3 { color: #EBC92C !important; font-weight: bold !important; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.markdown("<h1 style='text-align:center;'>🔐 ACESSO RESTRITO - MARK</h1>", unsafe_allow_html=True)
    col_l, _ = st.columns([1,1])
    with col_l:
        senha = st.text_input("Senha:", type="password")
        if st.button("ENTRAR"):
            if senha == "mark2026":
                st.session_state.autenticado = True
                st.rerun()
    st.stop()

# --- CONSTANTES E BANCO DE DADOS ---
DB_FILE = "log_atividades_mark.csv"
STOCK_FILE = "estoque_mark_atual.csv"
CON_TUBO_KG, CON_BARRA_KG = 4.235, 6.60

CONTATOS = {"Meu WhatsApp": "5531981041586", "Produção": "5531900000000"}

# --- FUNÇÕES ---
def registrar_log(cat, op, cli, prod, status, qtd, kg):
    agora = datetime.now()
    novo = pd.DataFrame([{
        'ID': int(agora.timestamp()), 'DATA': agora.strftime("%d/%m/%Y"),
        'OPERACAO': op, 'CLIENTE_NF': cli, 'PRODUTO': prod,
        'TIPO': status, 'QTD': qtd, 'PESO_KG': round(kg, 2), 'CATEGORIA': cat
    }])
    novo.to_csv(DB_FILE, mode='a', header=not os.path.exists(DB_FILE), index=False, sep=';', encoding='utf-8-sig')

if 'estoque' not in st.session_state:
    if os.path.exists(STOCK_FILE):
        st.session_state.estoque = pd.read_csv(STOCK_FILE, sep=';').to_dict('records')[0]
    else:
        st.session_state.estoque = {'tubo_kg': 0.0, 'barra_kg': 0.0, 'crua_un': 0, 'pintada_un': 0, 'galva_un': 0}

def salvar():
    pd.DataFrame([st.session_state.estoque]).to_csv(STOCK_FILE, index=False, sep=';', encoding='utf-8-sig')

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h1 class='titulo-mark'>MARK<br>EVENTOS</h1>", unsafe_allow_html=True)
    menu = st.radio("Navegação", ["🏠 DASHBOARD", "🔨 PRODUÇÃO", "🎨 ACABAMENTO", "🤝 VENDAS", "🚚 CARGA", "📊 RELATÓRIO"])

# --- DASHBOARD COM GRÁFICOS DE VENDAS ---
if menu == "🏠 DASHBOARD":
    st.header("📈 Painel de Performance")
    
    # Métricas Rápidas
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("CRUAS", f"{int(st.session_state.estoque['crua_un'])} Un")
    c2.metric("PINTADAS", f"{int(st.session_state.estoque['pintada_un'])} Un")
    c3.metric("GALVA", f"{int(st.session_state.estoque['galva_un'])} Un")
    cap = min(int(st.session_state.estoque['tubo_kg']//CON_TUBO_KG), int(st.session_state.estoque['barra_kg']//CON_BARRA_KG))
    c4.metric("CAPACIDADE", f"{cap} Un")

    st.divider()

    if os.path.exists(DB_FILE):
        df_raw = pd.read_csv(DB_FILE, sep=';', encoding='utf-8-sig', on_bad_lines='skip')
        if 'QTD (Un)' in df_raw.columns: df_raw = df_raw.rename(columns={'QTD (Un)': 'QTD'})
        
        # Filtro de Vendas
        df_vendas = df_raw[df_raw['CATEGORIA'] == 'VENDA'].copy()
        
        col_g1, col_g2 = st.columns(2)

        with col_g1:
            st.subheader("📦 Vendas por Modelo")
            if not df_vendas.empty:
                # Agrupa vendas por TIPO (Pintada/Galva)
                vendas_modelo = df_vendas.groupby('TIPO')['QTD'].sum().reset_index()
                fig_vendas = px.bar(vendas_modelo, x='TIPO', y='QTD', color='TIPO', 
                                   color_discrete_sequence=['#EBC92C', '#AAAAAA'], text_auto=True)
                fig_vendas.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color="white", showlegend=False)
                st.plotly_chart(fig_vendas, use_container_width=True)
            else:
                st.info("Nenhuma venda registrada ainda.")

        with col_g2:
            st.subheader("👥 Maiores Clientes (Qtd)")
            if not df_vendas.empty:
                # Agrupa vendas por CLIENTE
                vendas_cli = df_vendas.groupby('CLIENTE_NF')['QTD'].sum().sort_values(ascending=False).head(5).reset_index()
                fig_cli = px.pie(vendas_cli, values='Qtd' if 'Qtd' in vendas_cli else 'QTD', names='CLIENTE_NF', hole=.4,
                                color_discrete_sequence=px.colors.sequential.YlOrBr)
                fig_cli.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color="white")
                st.plotly_chart(fig_cli, use_container_width=True)
            else:
                st.info("Aguardando dados de vendas.")
    
    st.divider()
    # Estoque de Matéria Prima
    st.subheader("🏗️ Saldo de Matéria-Prima (Kg)")
    dados_b = pd.DataFrame({'Material':['Tubo','Barra'], 'Peso':[st.session_state.estoque['tubo_kg'], st.session_state.estoque['barra_kg']]})
    fig_mat = px.bar(dados_b, x='Material', y='Peso', color='Material', color_discrete_sequence=['#EBC92C', '#555'], orientation='v')
    fig_mat.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color="white", showlegend=False)
    st.plotly_chart(fig_mat, use_container_width=True)

# --- RESTANTE DAS PÁGINAS (MANTIDAS) ---
elif menu == "🔨 PRODUÇÃO":
    st.header("🔨 Produção")
    qtd = st.number_input("Qtd produzida:", min_value=1, step=1)
    if st.button("REGISTRAR"):
        t_t, t_b = qtd * CON_TUBO_KG, qtd * CON_BARRA_KG
        if st.session_state.estoque['tubo_kg'] >= t_t:
            st.session_state.estoque['tubo_kg'] -= t_t; st.session_state.estoque['barra_kg'] -= t_b
            st.session_state.estoque['crua_un'] += qtd
            registrar_log("PRODUCAO", "FABRICAÇÃO", "INTERNO", "GRADE", "CRUA", qtd, t_t+t_b); salvar(); st.success("Feito!")
        else: st.error("Falta material!")

elif menu == "🎨 ACABAMENTO":
    st.header("🎨 Acabamento")
    tipo = st.selectbox("Tipo:", ["Pintura", "Galvanização"])
    qtd = st.number_input("Qtd:", min_value=1)
    if st.button("ATUALIZAR"):
        if st.session_state.estoque['crua_un'] >= qtd:
            st.session_state.estoque['crua_un'] -= qtd
            chave = 'pintada_un' if "Pintura" in tipo else 'galva_un'
            st.session_state.estoque[chave] += qtd
            registrar_log("ACABAMENTO", "PROCESSO", "INTERNO", "GRADE", tipo.upper(), qtd, 0); salvar(); st.success("Ok!")

elif menu == "🤝 VENDAS":
    st.header("🤝 Vendas")
    tipo = st.selectbox("Material:", ["Pintada", "Galvanizada"])
    cli = st.text_input("Cliente:")
    qtd = st.number_input("Qtd:", min_value=1)
    if st.button("VENDER"):
        chave = 'pintada_un' if tipo == "Pintada" else 'galva_un'
        if st.session_state.estoque[chave] >= qtd and cli:
            st.session_state.estoque[chave] -= qtd
            registrar_log("VENDA", "SAÍDA", cli.upper(), "GRADE", tipo.upper(), qtd, 0); salvar(); st.balloons(); st.success("Vendido!")

elif menu == "🚚 CARGA":
    st.header("🚚 Carga")
    mat = st.selectbox("Item:", ["TUBO 1.1/4", "BARRA 3/8"])
    peso = st.number_input("Peso (Kg):", min_value=0.0)
    if st.button("ADICIONAR"):
        chave = 'tubo_kg' if "TUBO" in mat else 'barra_kg'
        st.session_state.estoque[chave] += peso
        registrar_log("CARGA", "ENTRADA", "FORNECEDOR", "AÇO", mat, 0, peso); salvar(); st.success("Adicionado!")

elif menu == "📊 RELATÓRIO":
    st.header("📊 Relatório Completo")
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE, sep=';', encoding='utf-8-sig', on_bad_lines='skip')
        if 'QTD (Un)' in df.columns: df = df.rename(columns={'QTD (Un)': 'QTD'})
        st.dataframe(df.sort_values(by='ID', ascending=False), use_container_width=True)
        
        st.divider()
        contato = st.selectbox("Enviar resumo para:", list(CONTATOS.keys()))
        msg = f"*📢 MARK EVENTOS - {datetime.now().strftime('%d/%m/%Y')}*\n\nEstoque: Crua ({int(st.session_state.estoque['crua_un'])}) | Pintada ({int(st.session_state.estoque['pintada_un'])}) | Galva ({int(st.session_state.estoque['galva_un'])})"
        link = f"https://wa.me/{CONTATOS[contato]}?text={urllib.parse.quote(msg)}"
        st.markdown(f'<a href="{link}" target="_blank"><button style="background-color:#25D366; color:white; border:none; padding:15px; border-radius:10px; width:100%; cursor:pointer; font-weight:bold;">📲 WHATSAPP {contato.upper()}</button></a>', unsafe_allow_html=True)
