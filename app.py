import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="Gestor de Fiscalização PT - E-REDES",
    page_icon="⚡",
    layout="wide"
)

# Configuração da Checklist Estrutura
CHECKLIST_ESTRUTURA = {
    "1. Construção Civil e Infraestrutura": [
        {"id": "01", "texto": "Acesso direto e desimpedido a partir da via pública."},
        {"id": "02", "texto": "Portas com abertura para o exterior desimpedidas com fechadura operacional (Canhão Chave2)."},
        {"id": "03", "texto": "Grelhas de ventilação limpas, com rede mosquiteira/antideflagrante e IP regulamentar."},
        {"id": "04", "texto": "Sinalização exterior de segurança (placas de aviso 'Alta Tensão' e Chapa do PT na Porta)"},
        {"id": "05", "texto": "Tubos de passagem de cabos (cuba/cave) devidamente selados contra água e roedores."},
        {"id": "06", "texto": "Plataforma de Manobras (AI/AS)"}
    ],
    "2. Rede de Terras": [
        {"id": "07", "texto": "Separação regulamentar das terras de Proteção e Terras de Serviço e identificação das mesmas"},
        {"id": "08", "texto": "Mapa de Terras e croqui Simples da resistências de terras (<20 Ohm)"},
        {"id": "09", "texto": "Todas as massas metálicas (portas, quadros, calhas, ferragens da Tubagem e Terras de Apoio/Poste) ligadas à terra com ligadores amovíveis."}
    ],
    "3. Equipamento de Média Tensão (MT)": [
        {"id": "10", "texto": "Terminações/terminais de cabos de MT limpos, alinhados e sem vincos estruturais."},
        {"id": "11", "texto": "Encravamentos mecânicos das chaves de terra testados e 100% operacionais."},
        {"id": "12", "texto": "Instalação de BRA com a Identificação correcta (Nº da Cela + Nº Orgão)"},
        {"id": "13", "texto": "Instalação da alavanca para o Secc/IntSecc (AS/AI)"}
    ],
    "4. Transformador de Potência": [
        {"id": "14", "texto": "Placa de características (kVA, tensões nominal/secundária, grupo) coincide com projeto aprovado."},
        {"id": "15", "texto": "Aperto mecânico dos bornes (MT e BT) verificado criteriosamente com chave dinamométrica."},
        {"id": "16", "texto": "Comutador de tomadas em vazio posicionado na tomada correta para o arranque de exploração."},
        {"id": "17", "texto": "Acessórios instalados corretamente (termómetro, amortecedores de vibração, relé Buchholz)."}
    ],
    "5. Quadro Geral de Baixa Tensão (QGBT)": [
        {"id": "18", "texto": "Barramentos de cobre perfeitamente alinhados e com aperto verificado."},
        {"id": "19", "texto": "Fusíveis de proteção instalados com o tamanho e calibre adequados à potência do transformador."},
        {"id": "20", "texto": "Circuitos de serviços auxiliares (iluminação interna, tomadas, comando) operacionais."},
        {"id": "21", "texto": "DTC, Totalizador, Quadros de Comando, Contagem, Controlo e Comunicações (P4C ou Q4C)"}
    ],
    "6. Documentação e Equipamentos de Segurança": [
        {"id": "22", "texto": "Kit de segurança regulamentar completo em obra (tapete isolante, alavanca de manobra pregada na parede, lanterna, aloquetes, Luvas)."},
        {"id": "24", "texto": "Cartaz de primeiros socorros em caso de acidente elétrico."},
        {"id": "25", "texto": "Pavimento envolvente do PTD e/ou Muros."},
        {"id": "26", "texto": "Relatórios de ensaios aos cabos e certificados de conformidade"}
    ]
}

# Estabelecer ligação com o Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Ler dados da Nuvem com tratamento de exceções
try:
    df_obras = conn.read(worksheet="Obras", ttl=5)
    df_respostas = conn.read(worksheet="Respostas", ttl=5)
except Exception:
    df_obras = pd.DataFrame(columns=["obra_ref", "data_vistoria"])
    df_respostas = pd.DataFrame(columns=["obra_ref", "item_id", "estado", "data_verificacao", "observacoes"])

# Garantir tipos de dados corretos
if not df_respostas.empty:
    df_respostas["item_id"] = df_respostas["item_id"].astype(str)

# Estados de navegação
if "obra_selecionada" not in st.session_state:
    st.session_state.obra_selecionada = None

# Interface - Barra Lateral
st.sidebar.title("⚡ Rede de Fiscalização")
st.sidebar.markdown("**Fiscal:** Joel Machado Rocha")

if st.session_state.obra_selecionada:
    if st.sidebar.button("⬅️ Voltar ao Dashboard", use_container_width=True):
        st.session_state.obra_selecionada = None
        st.rerun()

# --- ECRÃ 1: DASHBOARD ---
if st.session_state.obra_selecionada is None:
    st.title("📂 Central de Fiscalizações de PTs")
    st.subheader("Base de dados na nuvem partilhada em tempo real")
    st.markdown("---")
    
    # Criar Nova Obra
    with st.expander("➕ REGISTAR NOVO POSTO DE TRANSFORMAÇÃO", expanded=False):
        col_n1, col_n2 = st.columns([3, 1])
        nova_ref = col_n1.text_input("Referência / Localização do PT", placeholder="Ex: PT FLG 0266")
        nova_data = col_n2.date_input("Data de Vistoria", value=datetime.now().date())
        
        if st.button("Publicar Novo PT na Nuvem", type="primary"):
            if nova_ref.strip() == "":
                st.error("Insira uma referência válida.")
            elif not df_obras.empty and nova_ref in df_obras["obra_ref"].values:
                st.error("Esse PT já se encontra registado.")
            else:
                nova_linha_obra = pd.DataFrame([{"obra_ref": nova_ref, "data_vistoria": str(nova_data)}])
                df_obras = pd.concat([df_obras, nova_linha_obra], ignore_index=True)
                
                novas_linhas_resp = []
                for cat, itens in CHECKLIST_ESTRUTURA.items():
                    for item in itens:
                        novas_linhas_resp.append({
                            "obra_ref": nova_ref,
                            "item_id": str(item["id"]),
                            "estado": "Pendente",
                            "data_verificacao": str(nova_data),
                            "observacoes": ""
                        })
                df_respostas = pd.concat([df_respostas, pd.DataFrame(novas_linhas_resp)], ignore_index=True)
                
                conn.update(worksheet="Obras", data=df_obras)
                conn.update(worksheet="Respostas", data=df_respostas)
                st.success("PT adicionado com sucesso à nuvem!")
                st.rerun()

    # Listar Obras
    st.markdown("### 🏢 Postos de Transformação em Curso")
    if df_obras.empty:
        st.info("Nenhum PT registado no sistema de momento.")
    else:
        for _, row in df_obras.iterrows():
            ref = str(row["obra_ref"])
            dt = row["data_vistoria"]
            
            df_pt_resp = df_respostas[df_respostas["obra_ref"] == ref] if not df_respostas.empty else pd.DataFrame()
            conf = len(df_pt_resp[df_pt_resp["estado"] == "Conforme"]) if not df_pt_resp.empty else 0
            n_conf = len(df_pt_resp[df_pt_resp["estado"] == "Não Conforme"]) if not df_pt_resp.empty else 0
            na_it = len(df_pt_resp[df_pt_resp["estado"] == "N/A"]) if not df_pt_resp.empty else 0
            
            total_itens = 26
            prog = int(((conf + n_conf + na_it) / total_itens) * 100) if not df_pt_resp.empty else 0
            
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([3, 1.5, 2, 1])
                c1.markdown(f"#### 🏭 {ref}")
                c2.markdown(f"📅 **Data:** {dt}")
                c3.markdown(f"📊 **Progresso:** {prog}% (✅ {conf} | ❌ {n_conf})")
                if c4.button("Inspecionar 📂", key=f"btn_{ref}", use_container_width=True):
                    st.session_state.obra_selecionada = ref
                    st.rerun()

# --- ECRÃ 2: ENTRADA DE DADOS DA CHECKLIST ---
else:
    ref_atual = st.session_state.obra_selecionada
    st.title(f"⚡ Inspecionando: {ref_atual}")
    st.markdown("---")
    
    df_filtrado = df_respostas[df_respostas["obra_ref"] == ref_atual].copy()
    
    conf = len(df_filtrado[df_filtrado["estado"] == "Conforme"])
    n_conf = len(df_filtrado[df_filtrado["estado"] == "Não Conforme"])
    na_it = len(df_filtrado[df_filtrado["estado"] == "N/A"])
    prog = int(((conf + n_conf + na_it) / 26) * 100)
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Progresso do PT", f"{prog}%")
    m2.metric("Itens Conformes ✅", conf)
    m3.metric("Inconformidades Detetadas ❌", n_conf)
    st.progress(prog / 100)
    st.markdown(" ")

    modificado = False

    for categoria, itens in CHECKLIST_ESTRUTURA.items():
        with st.expander(f"📂 {categoria.upper()}", expanded=True):
            col_id, col_txt, col_est, col_dt, col_obs = st.columns([0.6, 5, 2, 1.8, 4])
            col_id.markdown("**ID**")
            col_txt.markdown("**Item de Verificação**")
            col_est.markdown("**Estado**")
            col_dt.markdown("**Data Verif.**")
            col_obs.markdown("**Observações / Anomalias**")
            st.divider()

            for item in itens:
                i_id = str(item["id"])
                
                row_idx = df_respostas[(df_respostas["obra_ref"] == ref_atual) & (df_respostas["item_id"] == i_id)].index
                
                if len(row_idx) > 0:
                    idx = row_idx[0]
                    dados_linha = df_respostas.loc[idx]
                    
                    c_id, c_txt, c_est, c_dt, c_obs = st.columns([0.6, 5, 2, 1.8, 4])
                    
                    c_id.info(f"**{i_id}**")
                    c_txt.markdown(f"<div style='padding-top: 5px;'>{item['texto']}</div>", unsafe_allow_html=True)
                    
                    opcoes = ["Pendente", "Conforme", "Não Conforme", "N/A"]
                    est_atual = dados_linha["estado"] if dados_linha["estado"] in opcoes else "Pendente"
                    v_est = c_est.selectbox(f"Est_{i_id}", opcoes, index=opcoes.index(est_atual), label_visibility="collapsed")
                    
                    try:
                        v_dt_padrao = datetime.strptime(str(dados_linha["data_verificacao"]), "%Y-%m-%d").date()
                    except Exception:
                        v_dt_padrao = datetime.now().date()
                    v_dt = c_dt.date_input(f"Dt_{i_id}", value=v_dt_padrao, label_visibility="collapsed")
                    
                    v_obs = c_obs.text_input(f"Obs_{i_id}", value=str(dados_linha["observacoes"]) if pd.notna(dados_linha["observacoes"]) else "", placeholder="Notas...", label_visibility="collapsed")
                    
                    if v_est != dados_linha["estado"] or str(v_dt) != str(dados_linha["data_verificacao"]) or v_obs != str(dados_linha["observacoes"]):
                        df_respostas.loc[idx, "estado"] = v_est
                        df_respostas.loc[idx, "data_verificacao"] = str(v_dt)
                        df_respostas.loc[idx, "observacoes"] = v_obs
                        modificado = True

    if modificado:
        conn.update(worksheet="Respostas", data=df_respostas)
        st.rerun()
