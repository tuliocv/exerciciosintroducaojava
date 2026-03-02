import json
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st
from filelock import FileLock

# =========================
# Config
# =========================
st.set_page_config(page_title="Exercícios — Feedback em Aula", page_icon="🧩", layout="wide")

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

CSV_PATH = DATA_DIR / "feedback_exercicios.csv"
JSONL_PATH = DATA_DIR / "feedback_exercicios.jsonl"
LOCK_PATH = DATA_DIR / "feedback_exercicios.lock"

STATUS_OPTS = ["✅ Feito", "❌ Não consegui"]
DIF_OPTS = ["Fácil", "Médio", "Difícil"]

TEACHER_PASS = st.secrets.get("app", {}).get("teacher_password", "")

# =========================
# Exercícios (enunciados completos)
# =========================
EXS = [
    {"id": "Exemplo 1", "title": "Exibir nome",
     "prompt": "Exemplo 1: Desenvolva um programa que exiba seu nome na tela."},

    {"id": "Exemplo 2", "title": "Operações com x e y",
     "prompt": "Exemplo 2: Desenvolva um programa que calcule a soma, subtração, multiplicação e divisão dos números    x = 5 e y = 2."},

    {"id": "Exemplo 3", "title": "Expressão 2a + 3b",
     "prompt": "Exemplo 3: Construa programa que exiba o resultado de 2a + 3b, em que o valor a vale 3 e o valor b vale 5."},

    {"id": "Ex 4", "title": "Média de 3 números",
     "prompt": "Ex 4: Calcule a média aritmética de 3 números inseridos pelo usuário."},

    {"id": "Ex 5", "title": "Média final (A1/A2/A3)",
     "prompt": "Ex 5: Calcule a média final das avaliações A1, A2 e A3, sabendo que A1 e A2 possuem peso de 30% e a A3 o peso é igual a 40%."},

    {"id": "Ex 7", "title": "Salário líquido (21%)",
     "prompt": "Ex 7: Desenvolva um algoritmo que permite a inserção do salário bruto do colaborador e calcule o salário líquido, sabendo que o desconto aproximado é de 21%."},

    {"id": "Ex 8", "title": "Velocidade média",
     "prompt": "Ex 8:  Escreva um programa que calcule a velocidade média de um veículo. Para isso, pergunte a distância percorrida, em km, e o tempo gasto neste trajeto em horas."},

    {"id": "Ex 9", "title": "Carro alugado",
     "prompt": "Ex 9: Escreve um programa que pergunte a quantidade de km percorridos por um carro alugado pelo usuário, assim como a quantidade de dias pelos quais o carro ficou alugado. Calcule o preço a pagar, sabendo que o carro custa R$ 60,00 por dia e R$ 0,15 por km rodado."},

    {"id": "Ex 10", "title": "Dias de vida perdidos (estimativa)",
     "prompt": "Ex 10: Desenvolva um programa para calcular a redução do tempo de vida de um fumante. Pergunte a quantidade de cigarros fumados por dia e quantos anos ele já fumou. Considere que um fumante perde 10 minutos de vida a cada cigarro, e calcule quantos dias de vida um fumante perderá. Apresente o resultado em dias."},
]

# =========================
# Persistência
# =========================
def append_submission(row: dict):
    with FileLock(str(LOCK_PATH)):
        with open(JSONL_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

        df_new = pd.DataFrame([row])
        if CSV_PATH.exists():
            df_old = pd.read_csv(CSV_PATH)
            df = pd.concat([df_old, df_new], ignore_index=True)
        else:
            df = df_new
        df.to_csv(CSV_PATH, index=False)

def load_df() -> pd.DataFrame:
    if not CSV_PATH.exists():
        return pd.DataFrame(columns=[
            "timestamp", "team_names",
            "exercise_id", "exercise_title",
            "status", "difficulty", "comment"
        ])
    return pd.read_csv(CSV_PATH)

# =========================
# Auth professor (sidebar)
# =========================
def teacher_is_enabled() -> bool:
    return bool(TEACHER_PASS)

def teacher_is_logged() -> bool:
    return st.session_state.get("teacher_ok", False) is True

def teacher_login_ui():
    st.sidebar.subheader("🔐 Professor")
    if not teacher_is_enabled():
        st.sidebar.info("Modo professor desativado (sem `teacher_password` em secrets).")
        return

    # estado inicial
    if "teacher_ok" not in st.session_state:
        st.session_state["teacher_ok"] = False

    if teacher_is_logged():
        st.sidebar.success("Logado ✅")
        if st.sidebar.button("Sair", use_container_width=True):
            st.session_state["teacher_ok"] = False
            st.rerun()
    else:
        pwd = st.sidebar.text_input("Senha", type="password", key="teacher_pwd_sidebar")
        if st.sidebar.button("Entrar", use_container_width=True):
            st.session_state["teacher_ok"] = (pwd == TEACHER_PASS)
            st.rerun()
        st.sidebar.caption("Configure em `.streamlit/secrets.toml` ou Settings → Secrets (Cloud).")

# =========================
# Sidebar menu
# =========================
teacher_login_ui()

st.sidebar.divider()
if teacher_is_logged():
    view = st.sidebar.radio("📌 Menu", ["Aluno", "Professor"], index=0)
else:
    view = "Aluno"
    st.sidebar.radio("📌 Menu", ["Aluno"], index=0, disabled=True)

st.sidebar.divider()
st.sidebar.caption("Os dados ficam em `data/feedback_exercicios.csv`")

# =========================
# Main
# =========================
st.title("🧩 Exercícios em Aula — Status + Dificuldade")
st.caption("Selecione um exercício, marque se conseguiu e avalie a dificuldade. As respostas ficam salvas para analytics do professor.")

if view == "Aluno":
    # Identificação
    st.subheader("👥 Identificação (individual ou dupla)")
    team_names = st.text_input(
        "Nome(s) dos integrantes",
        placeholder="Ex: Ana Silva  |  ou  Ana Silva e Bruno Souza",
        key="team_names"
    )

    st.divider()

    # Seleção do exercício (centro)
    options = [f"{e['id']} — {e['title']}" for e in EXS]
    selected = st.selectbox("📌 Selecione o exercício", options, key="exercise_select")
    idx = options.index(selected)
    ex = EXS[idx]

    # Enunciado completo
    st.subheader(f"{ex['id']} — {ex['title']}")
    st.write(ex["prompt"])

    st.markdown("### ✅ Registro do grupo/aluno")

    with st.form(key=f"form_{ex['id']}", clear_on_submit=True):
        status = st.radio("Você conseguiu fazer?", STATUS_OPTS, horizontal=True, key=f"status_{ex['id']}")
        difficulty = st.radio("Como foi a dificuldade?", DIF_OPTS, horizontal=True, key=f"dif_{ex['id']}")
        comment = st.text_area(
            "Comentário (opcional)",
            height=90,
            placeholder="Ex: travei na divisão / não lembrei do Scanner / etc.",
            key=f"comment_{ex['id']}"
        )
        submitted = st.form_submit_button("💾 Salvar registro deste exercício", use_container_width=True)

    if submitted:
        if not team_names.strip():
            st.warning("Preencha **Nome(s) dos integrantes** antes de salvar.")
        else:
            row = {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "team_names": team_names.strip(),
                "exercise_id": ex["id"],
                "exercise_title": ex["title"],
                "status": status,
                "difficulty": difficulty,
                "comment": (comment or "").strip(),
            }
            append_submission(row)
            st.success("Registro salvo ✅")

elif view == "Professor":
    st.subheader("📊 Painel do Professor (Analytics)")

    df = load_df()
    if df.empty:
        st.warning("Ainda não há registros salvos.")
    else:
        c1, c2, c3 = st.columns([1.4, 1.2, 1.4])
        with c1:
            ex_sel = st.selectbox("Filtrar por exercício", ["(Todos)"] + [e["id"] for e in EXS], key="prof_ex_filter")
        with c2:
            status_sel = st.selectbox("Filtrar por status", ["(Todos)"] + STATUS_OPTS, key="prof_status_filter")
        with c3:
            last_n = st.slider("Mostrar últimos N registros", 50, 5000, 500, key="prof_last_n")

        dff = df.copy()
        if ex_sel != "(Todos)":
            dff = dff[dff["exercise_id"].astype(str) == ex_sel]
        if status_sel != "(Todos)":
            dff = dff[dff["status"].astype(str) == status_sel]

        if "timestamp" in dff.columns:
            dff = dff.sort_values("timestamp", ascending=False)

        # KPIs
        total = len(dff)
        feito = int((dff["status"] == "✅ Feito").sum())
        nao = int((dff["status"] == "❌ Não consegui").sum())
        perc_feito = (feito / total) * 100 if total else 0

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Registros", f"{total}")
        k2.metric("✅ Feito", f"{feito}")
        k3.metric("❌ Não consegui", f"{nao}")
        k4.metric("% Feito", f"{perc_feito:.1f}%")

        st.markdown("#### 📈 Distribuições")
        g1, g2 = st.columns(2)
        with g1:
            st.caption("Status")
            st.bar_chart(dff["status"].value_counts())
        with g2:
            st.caption("Dificuldade")
            order = ["Fácil", "Médio", "Difícil"]
            vc = dff["difficulty"].value_counts().reindex(order).fillna(0)
            st.bar_chart(vc)

        st.markdown("#### 🧾 Registros")
        st.dataframe(dff.head(last_n), use_container_width=True, hide_index=True)

        st.markdown("#### ⬇️ Download")
        st.download_button(
            "Baixar CSV filtrado",
            data=dff.to_csv(index=False).encode("utf-8"),
            file_name="feedback_exercicios_filtrado.csv",
            mime="text/csv",
            use_container_width=True
        )
        if CSV_PATH.exists():
            st.download_button(
                "Baixar CSV completo (arquivo)",
                data=CSV_PATH.read_bytes(),
                file_name="feedback_exercicios_completo.csv",
                mime="text/csv",
                use_container_width=True
            )
