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

# Configuração da Checklist Estrutura (Sempre que alterar aqui, atualiza para todos)
CHECKLIST_ESTRUTURA = {
    "1. Construção Civil e Infraestrutura": [
        {"id": "01", "texto": "Acesso direto e desimpedido a partir da via pública para equipamentos pesados."},
        {"id": "02", "texto": "Portas blindadas com abertura para o exterior e fechadura antipânico operacional."},
        {"id": "03", "texto": "Grelhas de ventilação limpas, com rede mosquiteira/antideflagrante e IP regulamentar."},
        {"id": "04", "texto": "Bacia de retenção de óleo do transformador 100% estanque e limpa."},
        {"id": "05", "texto": "Tubos de passagem de cabos (cuba/cave) devidamente selados contra água e roedores."},
        {"id": "06", "texto": "Sinalização exterior de segurança presente (placas de aviso 'Alta Tensão' e ID do PT)."}
    ],
    "2. Rede de Terras": [
        {"id": "07", "texto": "Separação ou interligação regulamentar das terras de Proteção (Pe) e Serviço (Ru)."},
        {"id": "08", "texto": "Relatório de ensaios valida resistência de terra conforme projeto (R < 1 Ohm)."},
        {"id": "09", "texto": "Todas as massas metálicas (portas, quadros, calhas) ligadas à terra com ligadores amovíveis."}
    ],
    "3. Equipamento de Média Tensão (MT)": [
        {"id": "10", "texto": "Manómetro de gás SF6 das celas modulares/monobloco no nível correto (zona verde)."},
        {"id": "11", "texto": "Encravamentos mecânicos das chaves de terra testados e 100% operacionais."},
        {"id": "12", "texto": "Terminações/terminais de cabos de MT limpos, alinhados e sem vincos estruturais."},
        {"id": "13", "texto": "Esquema mimético frontal reflete perfeitamente a instalação física real."}
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
        {"id": "21", "texto": "Relés de proteção diferencial e bobines de disparo testados com sucesso."}
    ],
    "6. Documentação e Equipamentos de Segurança": [
        {"id": "22", "texto": "Kit de segurança regulamentar completo em obra (banqueta/tapete isolante, vara de manobra)."},
        {"id": "23", "texto": "Luvas dielétricas guardadas em caixa própria e dentro do prazo de validade estipulado."},
        {"id": "24", "texto": "Cartaz oficial de primeiros socorros in loco em caso de acidente elétrico e frasco de colírio."},
        {"id": "25", "texto": "Extintor de CO2 carregado, com manómetro conforme e dentro da validade de inspeção."},
        {"id": "26", "texto": "Telas finais, relatórios de ensaios dielétricos de cabos e certificados disponíveis."}
    ]
}

# Estabelecer ligação com o Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Ler dados em tempo real da Nuvem
try:
    df_obras = conn.read(worksheet="Obras", ttl=5)
    df_respostas = conn.read(worksheet="Respostas", ttl=5)
except:
    df_obras = pd.DataFrame(columns=["obra_ref", "data_vistoria"])
    df_respostas = pd.DataFrame(columns=["obra_ref", "item_id", "estado", "data_verificacao", "observacoes"])

# Estados de navegação
if "obra_selecionada" not in st.session_state:
    st.session_state.obra_selecionada = None

# Interface - Barra Lateral
st.sidebar.title("⚡ Rede de Fiscalização")
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
        nova_ref = col_n1.text_input("Referência / Localização do PT")
        nova_data = col_n2.date_input("Data de Vistoria", value=datetime.now().date())
        
        if st.button("Publicar Novo PT na Nuvem", type="primary"):
            if nova_ref.strip() == "":
                st.error("Insira uma referência válida.")
            elif not df_obras.empty and nova_ref in df_obras["obra_ref"].values:
                st.error("Esse PT já se encontra registado.")
            else:
                # Adicionar nova linha às Obras
                nova_linha_obra = pd.DataFrame([{"obra_ref": nova_ref, "data_vistoria": str(nova_data)}])
                df_obras = pd.concat([df_obras, nova_linha_obra], ignore_index=True)
                
                # Criar respostas em branco padrão para este novo PT
                novas_linhas_resp = []
                for cat, itens in CHECKLIST_ESTRUTURA.items():
                    for item in itens:
                        novas_linhas_resp.append({
                            "obra_ref": nova_ref,
                            "item_id": item["id"],
                            "estado": "Pendente",
                            "data_verificacao": str(nova_data),
                            "observacoes": ""
                        })
                df_respostas = pd.concat([df_respostas, pd.DataFrame(novas_linhas_resp)], ignore_index=True)
                
                # Atualizar a folha de cálculo Google Sheets
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
            ref = row["obra_ref"]
            dt = row["data_vistoria"]
            
            # Calcular progresso a partir do DataFrame de respostas na nuvem
            df_pt_resp = df_respostas[df_respostas["obra_ref"] == ref] if not df_respostas.empty else pd.DataFrame()
            conf = len(df_pt_resp[df_pt_resp["estado"] == "Conforme"]) if not df_pt_resp.empty else 0
            n_conf = len(df_pt_resp[df_pt_resp["estado"] == "Não Conforme"]) if not df_pt_resp.empty else 0
            na_it = len(df_pt_resp[df_pt_resp["estado"] == "N/A"]) if not df_pt_resp.empty else 0
            prog = int(((conf + n_conf + na_it) / 26) * 100) if not df_pt_resp.empty else 0
            
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
    
    # Isolar apenas as respostas deste PT
    df_filtrado = df_respostas[df_respostas["obra_ref"] == ref_atual].copy()
    
    # Métricas
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
                i_id = item["id"]
                
                # Extrair linha correspondente do dataframe
                row_idx = df_respostas[(df_respostas["obra_ref"] == ref_atual) & (df_respostas["item_id"] == i_id)].index
                
                if len(row_idx) > 0:
                    idx = row_idx[0]
                    dados_linha = df_respostas.loc[idx]
                    
                    c_id, c_txt, c_est, c_dt, c_obs = st.columns([0.6, 5, 2, 1.8, 4])
                    
                    c_id.info(f"**{i_id}**")
                    c_txt.markdown(f"<div style='padding-top: 5px;'>{item['texto']}</div>", unsafe_allow_html=True)
                    
                    opcoes = ["Pendente", "Conforme", "Não Conforme", "N/A"]
                    v_est = c_est.selectbox(f"Est_{i_id}", opciones, index=opcoes.index(dados_linha["estado"]), label_visibility="collapsed")
                    
                    try:
                        v_dt_padrao = datetime.strptime(str(dados_linha["data_verificacao"]), "%Y-%m-%d").date()
                    except:
                        v_dt_padrao = datetime.now().date()
                    v_dt = c_dt.date_input(f"Dt_{i_id}", value=v_dt_padrao, label_visibility="collapsed")
                    
                    v_obs = c_obs.text_input(f"Obs_{i_id}", value=str(dados_linha["observacoes"]) if pd.notna(dados_linha["observacoes"]) else "", placeholder="Notas...", label_visibility="collapsed")
                    
                    # Se houver alteração, atualiza o DataFrame mestre
                    if v_est != dados_linha["estado"] or str(v_dt) != str(dados_linha["data_verificacao"]) or v_obs != str(dados_linha["observacoes"]):
                        df_respostas.loc[idx, "estado"] = v_est
                        df_respostas.loc[idx, "data_verificacao"] = str(v_dt)
                        df_respostas.loc[idx, "observacoes"] = v_obs
                        modificado = True

    # Se houve alguma alteração feita pelo utilizador no ecrã tátil, sincroniza imediatamente com o Google Sheets
    if modificado:
        conn.update(worksheet="Respostas", data=df_respostas)
        st.rerun()