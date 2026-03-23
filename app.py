import streamlit as st
import pandas as pd
from datetime import datetime
import os
import urllib.parse
import plotly.express as px # Biblioteca para gráficos profissionais

# --- CONFIGURAÇÃO E ESTILO ---
st.set_page_config(page_title="SISTEMA MARK EVENTOS", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #000000 !important; }
    [data-testid="stSidebar"] { background-color: #000000 !important; border-right: 2px solid #EBC92C; }
    .titulo-mark { color: #EBC92C !important; text-align: center; font-family: 'Arial Black'; border-bottom: 2px solid #EBC92C; padding-bottom: 10px; }
    .stButton>button { background-color: #EBC92C !important; color: #000; font-weight: bold; width: 100%; border-radius: 8px; }
    [data-testid="stMetric"] { background-color: #111; border-left: 5px solid #EBC92C; padding: 10px; border-radius: 10px; }
    h1, h2, h3 { color: #EBC92C !important; }
    .stDataFrame { background-color: #111; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN SIMPLES ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.markdown("<h1 style='text-align:center;'>🔐 ACESSO RESTRITO - MARK</h1>", unsafe_allow_html=True)
    senha = st.text_input("Digite a senha de acesso:", type="password")
    if st.button("ENTRAR"):
        if senha == "mark2026": # VOCÊ PODE MUDAR SUA SENHA AQUI
            st.session_state.autenticado = True
            st.rerun()
        else:
            st.error("Senha incorreta!")
    st.stop()

# --- CONSTANTES ---
CON_TUBO_KG = 4.235 # Exemplo (6.12m * 0.692)
CON_BARRA_KG = 6.60 
DB_FILE = "log_atividades_mark.csv"
STOCK_FILE = "estoque_mark_atual.csv"

# AGENDA DE CONTATOS - Altere aqui
CONTATOS = {
    "Meu WhatsApp": "5531981041586",
    "Produção": "5531900000000",
    "Escritório": "5531900000000"
}

# --- FUNÇÕES ---
def registrar_log(cat, op, cli, prod, status, qtd, kg):
    agora = datetime.now()
    novo = pd.DataFrame([{
        'ID': int(agora.timestamp()), # ID único para poder deletar depois
        'DATA': agora.strftime("%d/%m/%Y"),
        'OPERACAO': op, 'CLIENTE_NF': cli, 'PRODUTO': prod,
        'TIPO': status, 'QTD': qtd, 'PESO_KG': round(kg, 2),
        'CATEGORIA': cat
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
    menu = st.radio("MENU", ["🏠 DASHBOARD", "🔨 PRODUÇÃO", "🎨 ACABAMENTO", "🤝 VENDAS", "🚚 CARGA", "📊 RELATÓRIO"])
    if st.button("SAIR"):
        st.session_state.autenticado = False
        st.rerun()

# --- LÓGICA CAPACIDADE ---
cap_tubo = int(st.session_state.estoque['tubo_kg'] // CON_TUBO_KG) if st.session_state.estoque['tubo_kg'] > 0 else 0
cap_barra = int(st.session_state.estoque['barra_kg'] // CON_BARRA_KG) if st.session_state.estoque['barra_kg'] > 0 else 0
total_possivel = min(cap_tubo, cap_barra)

# --- PÁGINAS ---
if menu == "🏠 DASHBOARD":
    st.header("📈 Painel de Controle")
    
    # Métricas Principais
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("CRUAS", f"{int(st.session_state.estoque['crua_un'])} Un")
    c2.metric("PINTADAS", f"{int(st.session_state.estoque['pintada_un'])} Un")
    c3.metric("GALVA", f"{int(st.session_state.estoque['galva_un'])} Un")
    c4.metric("CAPACIDADE", f"{total_possivel} Un")

    st.divider()
    
    # Gráficos
    g1, g2 = st.columns(2)
    with g1:
        st.subheader("Divisão de Estoque Pronto")
        dados_pizza = pd.DataFrame({
            'Tipo': ['Crua', 'Pintada', 'Galva'],
            'Qtd': [st.session_state.estoque['crua_un'], st.session_state.estoque['pintada_un'], st.session_state.estoque['galva_un']]
        })
        fig = px.pie(dados_pizza, values='Qtd', names='Tipo', hole=.4, color_discrete_sequence=['#555', '#EBC92C', '#AAA'])
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
        st.plotly_chart(fig, use_container_width=True)
    
    with g2:
        st.subheader("Matéria-Prima (Kg)")
        dados_barra = pd.DataFrame({
            'Material': ['Tubo 1.1/4', 'Barra 3/8'],
            'Kg': [st.session_state.estoque['tubo_kg'], st.session_state.estoque['barra_kg']]
        })
        fig2 = px.bar(dados_barra, x='Material', y='Kg', color='Material', color_discrete_sequence=['#EBC92C', '#888'])
        fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white", showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

elif menu == "🔨 PRODUÇÃO":
    st.header("🔨 Registrar Fabricação")
    qtd = st.number_input("Grades produzidas hoje:", min_value=1, step=1)
    if st.button("CONFIRMAR SOLDA"):
        t_t, t_b = qtd * CON_TUBO_KG, qtd * CON_BARRA_KG
        if st.session_state.estoque['tubo_kg'] >= t_t:
            st.session_state.estoque['tubo_kg'] -= t_t; st.session_state.estoque['barra_kg'] -= t_b
            st.session_state.estoque['crua_un'] += qtd
            registrar_log("PRODUCAO", "FABRICAÇÃO", "INTERNO", "GRADE", "CRUA", qtd, t_t+t_b)
            salvar(); st.success("Produção registrada!")
        else: st.error("Falta material!")

elif menu == "🎨 ACABAMENTO":
    st.header("🎨 Enviar para Acabamento")
    tipo = st.selectbox("Tipo de Banho/Cor:", ["Pintura Preta", "Galvanização"])
    qtd = st.number_input("Quantidade:", min_value=1)
    if st.button("ATUALIZAR STATUS"):
        if st.session_state.estoque['crua_un'] >= qtd:
            st.session_state.estoque['crua_un'] -= qtd
            chave = 'pintada_un' if "Pintura" in tipo else 'galva_un'
            st.session_state.estoque[chave] += qtd
            registrar_log("ACABAMENTO", "PROCESSO", "INTERNO", "GRADE", tipo.upper(), qtd, 0)
            salvar(); st.success("Estoque atualizado!")

elif menu == "🤝 VENDAS":
    st.header("🤝 Registrar Saída / Venda")
    tipo = st.selectbox("Produto:", ["Pintada", "Galvanizada"])
    cli = st.text_input("Cliente ou NF:")
    qtd = st.number_input("Qtd Vendida:", min_value=1)
    if st.button("FINALIZAR VENDA"):
        chave = 'pintada_un' if tipo == "Pintada" else 'galva_un'
        if st.session_state.estoque[chave] >= qtd and cli:
            st.session_state.estoque[chave] -= qtd
            registrar_log("VENDA", "SAÍDA", cli.upper(), "GRADE", tipo.upper(), qtd, 0)
            salvar(); st.balloons(); st.success("Venda concluída!")

elif menu == "🚚 CARGA":
    st.header("🚚 Entrada de Matéria-Prima")
    mat = st.selectbox("Material:", ["TUBO 1.1/4", "BARRA 3/8"])
    peso = st.number_input("Peso (Kg):", min_value=0.0)
    if st.button("ADICIONAR AO ESTOQUE"):
        chave = 'tubo_kg' if "TUBO" in mat else 'barra_kg'
        st.session_state.estoque[chave] += peso
        registrar_log("CARGA", "ENTRADA", "FORNECEDOR", "AÇO", mat, 0, peso)
        salvar(); st.success("Carga registrada!")

elif menu == "📊 RELATÓRIO":
    st.header("📊 Histórico e Gestão de Dados")
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE, sep=';', encoding='utf-8-sig')
        
        # Função para deletar linha
        st.subheader("🗑️ Corrigir Erros")
        id_deletar = st.number_input("Digite o ID da linha para apagar (veja na tabela abaixo):", step=1, value=0)
        if st.button("❌ APAGAR REGISTRO"):
            df = df[df['ID'] != id_deletar]
            df.to_csv(DB_FILE, index=False, sep=';', encoding='utf-8-sig')
            st.warning("Registro removido! Recarregue a página.")

        st.divider()
        st.dataframe(df.sort_values(by='ID', ascending=False), use_container_width=True)

        # --- WHATSAPP ---
        st.subheader("📲 Compartilhar Resumo")
        contato = st.selectbox("Enviar para:", list(CONTATOS.keys()))
        vendas_hoje = df[df['CATEGORIA'] == 'VENDA'].tail(3)
        
        msg = f"*📢 MARK EVENTOS - {datetime.now().strftime('%d/%m/%Y')}*\n\n"
        msg += f"*ESTOQUE:* Cruas: {int(st.session_state.estoque['crua_un'])} | Pintadas: {int(st.session_state.estoque['pintada_un'])} | Galva: {int(st.session_state.estoque['galva_un'])}\n\n"
        if not vendas_hoje.empty:
            msg += "*VENDAS RECENTES:*\n"
            for _, r in vendas_hoje.iterrows(): msg += f"- {r['CLIENTE_NF']}: {r['QTD']} Un\n"
        
        link_zap = f"https://wa.me/{CONTATOS[contato]}?text={urllib.parse.quote(msg)}"
        st.markdown(f'<a href="{link_zap}" target="_blank"><button style="background-color:#25D366; color:white; border:none; padding:15px; border-radius:10px; width:100%; cursor:pointer;">📲 ENVIAR PARA {contato.upper()}</button></a>', unsafe_allow_html=True)
