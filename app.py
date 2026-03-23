import streamlit as st
import pandas as pd
from datetime import datetime
import os
import urllib.parse
import plotly.express as px

# --- CONFIGURAÇÃO E ESTILO ---
st.set_page_config(page_title="SISTEMA MARK EVENTOS", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #000000 !important; }
    [data-testid="stSidebar"] { background-color: #000000 !important; border-right: 2px solid #EBC92C; }
    .titulo-mark { color: #EBC92C !important; text-align: center; font-family: 'Arial Black'; border-bottom: 2px solid #EBC92C; padding-bottom: 10px; }
    .stButton>button { background-color: #EBC92C !important; color: #000; font-weight: bold; width: 100%; border-radius: 8px; height: 3em; }
    [data-testid="stMetric"] { background-color: #111; border-left: 5px solid #EBC92C; padding: 10px; border-radius: 10px; }
    h1, h2, h3 { color: #EBC92C !important; }
    .stDataFrame { background-color: #111; border-radius: 10px; }
    label { color: #FFFFFF !important; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.markdown("<h1 style='text-align:center;'>🔐 ACESSO RESTRITO - MARK</h1>", unsafe_allow_html=True)
    col_l, col_r = st.columns([1,1])
    with col_l:
        senha = st.text_input("Senha de acesso:", type="password")
        if st.button("ENTRAR"):
            if senha == "mark2026":
                st.session_state.autenticado = True
                st.rerun()
            else:
                st.error("Senha incorreta!")
    st.stop()

# --- CONSTANTES ---
PESO_TUBO_METRO = 0.692
METROS_POR_GRADE = 6.12
CON_TUBO_KG = round(METROS_POR_GRADE * PESO_TUBO_METRO, 3) 
CON_BARRA_KG = 6.60 
DB_FILE = "log_atividades_mark.csv"
STOCK_FILE = "estoque_mark_atual.csv"

# AGENDA DE CONTATOS (Altere os números aqui)
CONTATOS = {
    "Meu WhatsApp": "5531981041586",
    "Produção": "5531900000000",
    "Escritório": "5531900000000"
}

# --- FUNÇÕES ---
def registrar_log(cat, op, cli, prod, status, qtd, kg):
    agora = datetime.now()
    novo = pd.DataFrame([{
        'ID': int(agora.timestamp()),
        'DATA': agora.strftime("%d/%m/%Y"),
        'HORA': agora.strftime("%H:%M:%S"),
        'OPERACAO': op, 
        'CLIENTE_NF': cli, 
        'PRODUTO': prod,
        'TIPO': status, 
        'QTD': qtd, 
        'PESO_KG': round(kg, 2),
        'CATEGORIA': cat
    }])
    header = not os.path.exists(DB_FILE)
    novo.to_csv(DB_FILE, mode='a', header=header, index=False, sep=';', encoding='utf-8-sig')

if 'estoque' not in st.session_state:
    if os.path.exists(STOCK_FILE):
        try: st.session_state.estoque = pd.read_csv(STOCK_FILE, sep=';').to_dict('records')[0]
        except: st.session_state.estoque = {'tubo_kg': 0.0, 'barra_kg': 0.0, 'crua_un': 0, 'pintada_un': 0, 'galva_un': 0}
    else:
        st.session_state.estoque = {'tubo_kg': 0.0, 'barra_kg': 0.0, 'crua_un': 0, 'pintada_un': 0, 'galva_un': 0}

def salvar():
    pd.DataFrame([st.session_state.estoque]).to_csv(STOCK_FILE, index=False, sep=';', encoding='utf-8-sig')

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h1 class='titulo-mark'>MARK<br>EVENTOS</h1>", unsafe_allow_html=True)
    menu = st.radio("MENU", ["🏠 DASHBOARD", "🔨 PRODUÇÃO", "🎨 ACABAMENTO", "🤝 VENDAS", "🚚 CARGA", "📊 RELATÓRIO"])
    if st.button("SAIR"):
        st.session_state.autenticado = False
        st.rerun()

# --- LÓGICA CAPACIDADE ---
cap_tubo = int(st.session_state.estoque['tubo_kg'] // CON_TUBO_KG) if st.session_state.estoque['tubo_kg'] > 0 else 0
cap_barra = int(st.session_state.estoque['barra_kg'] // CON_BARRA_KG) if st.session_state.estoque['barra_kg'] > 0 else 0
total_possivel = min(cap_tubo, cap_barra)
gargalo = "Tubo" if cap_tubo <= cap_barra else "Barra"

# --- PÁGINAS ---
if menu == "🏠 DASHBOARD":
    st.header("📈 Painel de Controle")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("CRUAS", f"{int(st.session_state.estoque['crua_un'])} Un")
    c2.metric("PINTADAS", f"{int(st.session_state.estoque['pintada_un'])} Un")
    c3.metric("GALVA", f"{int(st.session_state.estoque['galva_un'])} Un")
    c4.metric("CAPACIDADE", f"{total_possivel} Un")
    
    st.divider()
    g1, g2 = st.columns(2)
    with g1:
        st.subheader("Estoque de Grades")
        dados_p = pd.DataFrame({'Tipo':['Crua','Pintada','Galva'], 'Qtd':[st.session_state.estoque['crua_un'], st.session_state.estoque['pintada_un'], st.session_state.estoque['galva_un']]})
        fig = px.pie(dados_p, values='Qtd', names='Tipo', hole=.4, color_discrete_sequence=['#555', '#EBC92C', '#AAA'])
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color="white")
        st.plotly_chart(fig, use_container_width=True)
    with g2:
        st.subheader("Matéria-Prima (Kg)")
        dados_b = pd.DataFrame({'Item':['Tubo','Barra'], 'Kg':[st.session_state.estoque['tubo_kg'], st.session_state.estoque['barra_kg']]})
        fig2 = px.bar(dados_b, x='Item', y='Kg', color='Item', color_discrete_sequence=['#EBC92C', '#888'])
        fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color="white", showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

elif menu == "🔨 PRODUÇÃO":
    st.header("🔨 Fabricação")
    qtd = st.number_input("Quantidade produzida:", min_value=1, step=1)
    if st.button("CONFIRMAR SOLDA"):
        t_t, t_b = qtd * CON_TUBO_KG, qtd * CON_BARRA_KG
        if st.session_state.estoque['tubo_kg'] >= t_t:
            st.session_state.estoque['tubo_kg'] -= t_t; st.session_state.estoque['barra_kg'] -= t_b
            st.session_state.estoque['crua_un'] += qtd
            registrar_log("PRODUCAO", "FABRICAÇÃO", "INTERNO", "GRADE", "CRUA", qtd, t_t+t_b); salvar(); st.success("Registrado!")
        else: st.error("Material insuficiente!")

elif menu == "🎨 ACABAMENTO":
    st.header("🎨 Acabamento")
    tipo = st.selectbox("Tipo:", ["Pintura", "Galvanização"])
    qtd = st.number_input("Quantidade:", min_value=1)
    if st.button("CONFIRMAR"):
        if st.session_state.estoque['crua_un'] >= qtd:
            st.session_state.estoque['crua_un'] -= qtd
            chave = 'pintada_un' if "Pintura" in tipo else 'galva_un'
            st.session_state.estoque[chave] += qtd
            registrar_log("ACABAMENTO", "PROCESSO", "INTERNO", "GRADE", tipo.upper(), qtd, 0); salvar(); st.success("Atualizado!")
        else: st.error("Sem grades cruas!")

elif menu == "🤝 VENDAS":
    st.header("🤝 Vendas")
    tipo = st.selectbox("Modelo:", ["Pintada", "Galvanizada"])
    cli = st.text_input("Cliente/NF:")
    qtd = st.number_input("Quantidade:", min_value=1)
    if st.button("REGISTRAR SAÍDA"):
        chave = 'pintada_un' if tipo == "Pintada" else 'galva_un'
        if st.session_state.estoque[chave] >= qtd and cli:
            st.session_state.estoque[chave] -= qtd
            registrar_log("VENDA", "SAÍDA", cli.upper(), "GRADE", tipo.upper(), qtd, 0); salvar(); st.balloons(); st.success("Vendido!")
        else: st.error("Erro no estoque ou cliente vazio!")

elif menu == "🚚 CARGA":
    st.header("🚚 Carga")
    mat = st.selectbox("Material:", ["TUBO 1.1/4", "BARRA 3/8"])
    peso = st.number_input("Peso (Kg):", min_value=0.0)
    if st.button("ADICIONAR"):
        chave = 'tubo_kg' if "TUBO" in mat else 'barra_kg'
        st.session_state.estoque[chave] += peso
        registrar_log("CARGA", "ENTRADA", "FORNECEDOR", "AÇO", mat, 0, peso); salvar(); st.success("Adicionado!")

elif menu == "📊 RELATÓRIO":
    st.header("📊 Gestão do Relatório")
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE, sep=';', encoding='utf-8-sig')
        
        if 'ID' in df.columns:
            st.subheader("🗑️ Corrigir Lançamento")
            id_del = st.number_input("ID para apagar:", step=1, value=0)
            if st.button("❌ APAGAR"):
                df = df[df['ID'] != id_del]
                df.to_csv(DB_FILE, index=False, sep=';', encoding='utf-8-sig')
                st.warning("Removido! Por favor, atualize a página.")
            st.divider()
            st.dataframe(df.sort_values(by='ID', ascending=False), use_container_width=True)
        else:
            st.warning("⚠️ Histórico antigo detectado. Registre uma nova ação para atualizar o formato.")
            st.dataframe(df, use_container_width=True)

        # WHATSAPP
        st.subheader("📲 WhatsApp")
        contato = st.selectbox("Enviar para:", list(CONTATOS.keys()))
        v_hoje = df[df['CATEGORIA'] == 'VENDA'].tail(3) if 'CATEGORIA' in df.columns else pd.DataFrame()
        msg = f"*📢 MARK EVENTOS - {datetime.now().strftime('%d/%m/%Y')}*\n\n*ESTOQUE:* Cruas: {int(st.session_state.estoque['crua_un'])} | Pintadas: {int(st.session_state.estoque['pintada_un'])} | Galva: {int(st.session_state.estoque['galva_un'])}\n\n"
        if not v_hoje.empty:
            msg += "*VENDAS:* " + ", ".join([f"{r['CLIENTE_NF']} ({r['QTD']})" for _, r in v_hoje.iterrows()])
        
        link = f"https://wa.me/{CONTATOS[contato]}?text={urllib.parse.quote(msg)}"
        st.markdown(f'<a href="{link}" target="_blank"><button style="background-color:#25D366; color:white; border:none; padding:15px; border-radius:10px; width:100%; cursor:pointer; font-weight:bold;">📲 ENVIAR RESUMO</button></a>', unsafe_allow_html=True)
