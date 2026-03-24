import streamlit as st
import pandas as pd
from datetime import datetime
import os
import urllib.parse
import plotly.express as px

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="MARK EVENTOS - Gestão", layout="wide", initial_sidebar_state="expanded")

# --- CSS PERSONALIZADO (VISUAL DARK PREMIUM) ---
st.markdown("""
    <style>
    .stApp { background-color: #12141D !important; color: #FFFFFF !important; }
    [data-testid="stSidebar"] { background-color: #1A1C26 !important; border-right: 1px solid #2D303E; width: 260px !important; }
    
    /* Logo e Menu */
    .logo-text { color: #FFB800; font-family: 'Arial Black'; font-weight: 800; font-size: 26px; text-align: center; margin-bottom: 30px; border-bottom: 2px solid #FFB800; padding-bottom: 10px; }
    
    /* Cards de Conteúdo */
    .main-card { background-color: #1A1C26; border: 1px solid #2D303E; border-radius: 15px; padding: 25px; margin-bottom: 20px; }
    
    /* Estilo de Inputs */
    label { color: #E0E0E0 !important; font-weight: bold !important; }
    input, select, textarea, .stSelectbox div { background-color: #12141D !important; color: white !important; border: 1px solid #2D303E !important; border-radius: 10px !important; }
    
    /* Botão Azul Profissional */
    .stButton>button { background-color: #2D7FF9 !important; color: white !important; border: none !important; border-radius: 12px !important; height: 50px !important; font-weight: bold !important; width: 100%; transition: 0.3s; }
    .stButton>button:hover { background-color: #1A66D6 !important; transform: scale(1.01); }

    /* Métricas Laterais (Projeção) */
    .projecao-card { background-color: #1A1C26; border-radius: 15px; border: 1px solid #2D303E; padding: 20px; }
    .metric-title { color: #9499B0; font-size: 13px; text-transform: uppercase; margin-bottom: 5px; }
    .metric-value { color: #FFFFFF; font-size: 24px; font-weight: bold; margin-bottom: 15px; }
    .metric-unit { font-size: 14px; color: #9499B0; }

    /* Tabelas */
    .stDataFrame { border: 1px solid #2D303E; border-radius: 10px; }
    
    /* Esconder elementos padrão */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.markdown("<h1 style='text-align:center; color: #FFB800;'>MARK EVENTOS</h1>", unsafe_allow_html=True)
    col_l, _ = st.columns([1,1])
    with col_l:
        senha = st.text_input("Senha de Acesso:", type="password")
        if st.button("ENTRAR NO SISTEMA"):
            if senha == "mark2026":
                st.session_state.autenticado = True
                st.rerun()
            else: st.error("Senha incorreta!")
    st.stop()

# --- CONSTANTES TÉCNICAS ---
PESO_TUBO_METRO = 0.692
METROS_POR_GRADE = 6.12
CON_TUBO_KG = round(METROS_POR_GRADE * PESO_TUBO_METRO, 3) 
CON_BARRA_KG = 6.60 
DB_FILE = "log_atividades_mark.csv"
STOCK_FILE = "estoque_mark_atual.csv"
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
    st.markdown('<div class="logo-text">MARK EVENTOS</div>', unsafe_allow_html=True)
    menu = st.radio("", ["🏠 Visão Geral", "🔨 Produção", "🎨 Acabamento", "🤝 Vendas", "📥 Entrada Material", "📜 Histórico"], label_visibility="collapsed")
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    if st.button("Sair"):
        st.session_state.autenticado = False
        st.rerun()

# --- 🏠 VISÃO GERAL (DASHBOARD) ---
if menu == "🏠 Visão Geral":
    st.header("🏠 Painel de Performance")
    
    # Cards Superiores
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("GRADES CRUAS", f"{int(st.session_state.estoque['crua_un'])} Un")
    c2.metric("PINTADAS", f"{int(st.session_state.estoque['pintada_un'])} Un")
    c3.metric("GALVANIZADAS", f"{int(st.session_state.estoque['galva_un'])} Un")
    cap = min(int(st.session_state.estoque['tubo_kg']//CON_TUBO_KG), int(st.session_state.estoque['barra_kg']//CON_BARRA_KG)) if st.session_state.estoque['tubo_kg'] > 0 else 0
    c4.metric("CAPACIDADE FAB.", f"{cap} Un")

    st.divider()

    if os.path.exists(DB_FILE):
        df_v = pd.read_csv(DB_FILE, sep=';', encoding='utf-8-sig', on_bad_lines='skip')
        if 'QTD (Un)' in df_v.columns: df_v = df_v.rename(columns={'QTD (Un)': 'QTD'})
        
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.subheader("📦 Vendas por Modelo")
            vendas_m = df_v[df_v['CATEGORIA']=='VENDA'].groupby('TIPO')['QTD'].sum().reset_index()
            fig = px.bar(vendas_m, x='TIPO', y='QTD', color='TIPO', color_discrete_sequence=['#2D7FF9', '#FFB800'])
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        
        with col_g2:
            st.subheader("🏗️ Matéria-Prima (Kg)")
            dados_m = pd.DataFrame({'Item':['Tubos','Barras'], 'Kg':[st.session_state.estoque['tubo_kg'], st.session_state.estoque['barra_kg']]})
            fig2 = px.bar(dados_m, x='Item', y='Kg', color='Item', color_discrete_sequence=['#FFB800', '#555'])
            fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white", showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)

# --- 🔨 PRODUÇÃO (SOLDA) ---
elif menu == "🔨 Produção":
    st.header("🔨 Registrar Fabricação")
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    qtd = st.number_input("Quantidade de grades soldadas:", min_value=1, step=1)
    if st.button("CONFIRMAR PRODUÇÃO"):
        t_t, t_b = qtd * CON_TUBO_KG, qtd * CON_BARRA_KG
        if st.session_state.estoque['tubo_kg'] >= t_t:
            st.session_state.estoque['tubo_kg'] -= t_t; st.session_state.estoque['barra_kg'] -= t_b
            st.session_state.estoque['crua_un'] += qtd
            registrar_log("PRODUCAO", "FABRICAÇÃO", "INTERNO", "GRADE", "CRUA", qtd, t_t+t_b); salvar()
            st.success(f"Sucesso! {qtd} grades cruas adicionadas ao estoque.")
        else: st.error("Aço insuficiente no estoque!")
    st.markdown('</div>', unsafe_allow_html=True)

# --- 🎨 ACABAMENTO ---
elif menu == "🎨 Acabamento":
    st.header("🎨 Enviar para Pintura/Galva")
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    tipo = st.selectbox("Tipo de Processo:", ["Pintura", "Galvanização"])
    qtd_a = st.number_input("Qtd de grades cruas enviadas:", min_value=1)
    if st.button("REGISTRAR ACABAMENTO"):
        if st.session_state.estoque['crua_un'] >= qtd_a:
            st.session_state.estoque['crua_un'] -= qtd_a
            chave = 'pintada_un' if "Pintura" in tipo else 'galva_un'
            st.session_state.estoque[chave] += qtd_a
            registrar_log("ACABAMENTO", "PROCESSO", "INTERNO", "GRADE", tipo.upper(), qtd_a, 0); salvar()
            st.success("Estoque de acabados atualizado!")
        else: st.error("Sem grades cruas suficientes!")
    st.markdown('</div>', unsafe_allow_html=True)

# --- 🤝 VENDAS ---
elif menu == "🤝 Vendas":
    st.header("🤝 Registrar Saída / Venda")
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    mod = st.selectbox("Modelo Vendido:", ["Pintada", "Galvanizada"])
    cli = st.text_input("Cliente / NF:")
    qtd_v = st.number_input("Quantidade Vendida:", min_value=1)
    if st.button("FINALIZAR VENDA"):
        chave = 'pintada_un' if mod == "Pintada" else 'galva_un'
        if st.session_state.estoque[chave] >= qtd_v and cli:
            st.session_state.estoque[chave] -= qtd_v
            registrar_log("VENDA", "SAÍDA", cli.upper(), "GRADE", mod.upper(), qtd_v, 0); salvar()
            st.balloons(); st.success("Venda registrada com sucesso!")
        else: st.error("Erro: Estoque insuficiente ou nome do cliente vazio.")
    st.markdown('</div>', unsafe_allow_html=True)

# --- 📥 ENTRADA MATERIAL (IGUAL AO PRINT) ---
elif menu == "📥 Entrada Material":
    st.header("📥 Entrada de Matéria Prima")
    st.markdown("<p style='color:#9499B0'>Registre o recebimento de aço em kg.</p>", unsafe_allow_html=True)
    
    col_f, col_p = st.columns([2, 1])
    with col_f:
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        p_tubo = c1.number_input("TUBOS (KG)", min_value=0.0)
        p_barra = c2.number_input("BARRAS MACIÇAS (KG)", min_value=0.0)
        obs = st.text_area("FORNECEDOR / OBSERVAÇÕES")
        if st.button("Registrar Entrada"):
            st.session_state.estoque['tubo_kg'] += p_tubo
            st.session_state.estoque['barra_kg'] += p_barra
            registrar_log("CARGA", "ENTRADA", obs.upper() if obs else "FORNECEDOR", "AÇO", "MATÉRIA PRIMA", 0, p_tubo+p_barra)
            salvar(); st.success("Carga registrada!"); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col_p:
        st.markdown('<div class="projecao-card">', unsafe_allow_html=True)
        st.markdown('<p class="metric-title">ESTOQUE ATUAL (KG)</p>', unsafe_allow_html=True)
        st.markdown('<p class="metric-title">Tubos</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="metric-value">{st.session_state.estoque["tubo_kg"]:.1f} <span class="metric-unit">kg</span></p>', unsafe_allow_html=True)
        st.markdown('<p class="metric-title">Barras Maciças</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="metric-value">{st.session_state.estoque["barra_kg"]:.1f} <span class="metric-unit">kg</span></p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# --- 📜 HISTÓRICO ---
elif menu == "📜 Histórico":
    st.header("📜 Histórico de Atividades")
    if os.path.exists(DB_FILE):
        df_h = pd.read_csv(DB_FILE, sep=';', encoding='utf-8-sig', on_bad_lines='skip')
        if 'QTD (Un)' in df_h.columns: df_h = df_h.rename(columns={'QTD (Un)': 'QTD'})
        st.dataframe(df_h.sort_values(by='ID', ascending=False), use_container_width=True)
        
        st.divider()
        contato = st.selectbox("Enviar resumo para:", list(CONTATOS.keys()))
        msg = f"*📢 MARK EVENTOS - {datetime.now().strftime('%d/%m/%Y')}*\n\nEstoque: Crua ({int(st.session_state.estoque['crua_un'])}) | Pintada ({int(st.session_state.estoque['pintada_un'])}) | Galva ({int(st.session_state.estoque['galva_un'])})"
        link = f"https://wa.me/{CONTATOS[contato]}?text={urllib.parse.quote(msg)}"
        st.markdown(f'<a href="{link}" target="_blank"><button style="background-color:#25D366; color:white; border:none; padding:15px; border-radius:10px; width:100%; cursor:pointer; font-weight:bold;">📲 WHATSAPP {contato.upper()}</button></a>', unsafe_allow_html=True)
