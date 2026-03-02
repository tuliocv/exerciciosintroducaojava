import os
import json
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st
from filelock import FileLock

# =========================
# Config
# =========================
st.set_page_config(page_title="Exercícios — Check de Aula", page_icon="🧩", layout="centered")

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

CSV_PATH = DATA_DIR / "feedback_exercicios.csv"
JSONL_PATH = DATA_DIR / "feedback_exercicios.jsonl"
LOCK_PATH = DATA_DIR / "feedback_exercicios.lock"

TEACHER_PASS = st.secrets.get("app", {}).get("teacher_password", "")

# =========================
# Exercícios
# =========================
EXS = [
    {"id": "Exemplo 1", "title": "Exiba seu nome na tela", "prompt": "Desenvolva um programa que exiba seu nome na tela."},
    {"id": "Exemplo 2", "title": "Operações com x=5 e y=2", "prompt": "Calcule soma, subtração, multiplicação e divisão para x=5 e y=2."},
    {"id": "Exemplo 3", "title": "2a + 3b (a=3, b=5)", "prompt": "Exiba o resultado de 2a + 3b, com a=3 e b=5."},
    {"id": "Ex 4", "title": "Média de 3 números", "prompt": "Calcule a média aritmética de 3 números inseridos pelo usuário."},
    {"id": "Ex 5", "title": "Média final A1/A2/A3 (30/30/40)", "prompt": "Calcule média final com A1=30%, A2=30%, A3=40%."},
    {"id": "Ex 7", "title": "Salário líquido (desconto 21%)", "prompt": "Dado salário bruto, calcule salário líquido com desconto aproximado de 21%."},
    {"id": "Ex 8", "title": "Velocidade média", "prompt": "Pergunte distância (km) e tempo (h) e calcule velocidade média (km/h)."},
    {"id": "Ex 9", "title": "Carro alugado: R$60/dia + R$0,15/km", "prompt": "Pergunte km e dias e calcule o total (60/dia e 0,15 por km)."},
    {"id": "Ex 10", "title": "Estimativa de dias de vida perdidos (fumante)", "prompt": "Pergunte cigarros/dia e anos fumando. 10 min por cigarro. Retorne dias perdidos."},
]

STATUS_OPTS = ["✅ Feito", "❌ Não consegui"]
DIF_OPTS = ["Fácil", "Médio", "Difícil"]

# =========================
# Persistência (safe)
# =========================
def append_submission(row: dict):
    """Salva em JSONL (log) e mantém CSV atualizado. Protege com lock."""
    with FileLock(str(LOCK_PATH)):
        # 1) JSONL append (auditoria)
        with open(JSONL_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

        # 2) Atualiza CSV (tabela para analytics)
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
            "timestamp", "student_id", "student_name", "class_group",
            "exercise_id", "exercise_title",
            "status", "difficulty", "comment"
        ])
    return pd.read_csv(CSV_PATH)

# =========================
# Modo professor
# =========================
def is_teacher() -> bool:
    if not TEACHER_PASS:
        return False
    return st.session_state.get("teacher_ok", False)

def teacher_login_box():
    if not TEACHER_PASS:
        st.info("🔐 Modo professor desativado (nenhuma senha configurada em st.secrets).")
        return
    with st.expander("🔐 Modo professor"):
        pwd = st.text_input("Senha do professor", type="password")
        if st.button("Entrar", use_container_width=True):
            st.session_state["teacher_ok"] = (pwd == TEACHER_PASS)
        if is_teacher():
            st.success("Modo professor ativado ✅")

# =========================
# UI - Cabeçalho
# =========================
st.title("🧩 Exercícios em Aula — Registro de Tentativas")
st.caption("Para cada exercício: marque se conseguiu e a dificuldade. As respostas ficam salvas para analytics do professor.")

teacher_login_box()
st.divider()

# =========================
# Identificação do aluno
# =========================
st.subheader("👤 Identificação")
colA, colB, colC = st.columns([1.2, 2, 1.2])

with colA:
    student_id = st.text_input("RA / ID", placeholder="Ex: 1234567")
with colB:
    student_name = st.text_input("Nome", placeholder="Ex: Ana Silva")
with colC:
    class_group = st.text_input("Turma", placeholder="Ex: T1 / Noite")

if not student_id and not student_name:
    st.info("Dica: preencha pelo menos **RA/ID** ou **Nome** para registrar suas respostas.")

st.divider()

# =========================
# Navegação exercícios
# =========================
with st.sidebar:
    st.header("📚 Exercícios")
    labels = [f"{e['id']} — {e['title']}" for e in EXS]
    idx = st.radio("Escolha um exercício", list(range(len(EXS))), format_func=lambda i: labels[i])
    st.divider()
    st.caption("A cada exercício, registre status e dificuldade.")

ex = EXS[idx]

st.subheader(f"{ex['id']}: {ex['title']}")
st.write(ex["prompt"])

st.markdown("### ✅ Registro do aluno")

# Campos de registro (por exercício)
status_key = f"status_{ex['id']}"
dif_key = f"dif_{ex['id']}"
comment_key = f"comment_{ex['id']}"

status = st.radio("Você conseguiu fazer?", STATUS_OPTS, key=status_key, horizontal=True)
difficulty = st.radio("Como foi a dificuldade?", DIF_OPTS, key=dif_key, horizontal=True)
comment = st.text_area("Comentário (opcional)", key=comment_key, height=90, placeholder="Ex: travei na divisão / usei Scanner / etc.")

col1, col2 = st.columns([1, 1])
with col1:
    if st.button("💾 Salvar registro deste exercício", use_container_width=True):
        if not (student_id.strip() or student_name.strip()):
            st.warning("Preencha pelo menos **RA/ID** ou **Nome** antes de salvar.")
        else:
            row = {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "student_id": student_id.strip(),
                "student_name": student_name.strip(),
                "class_group": class_group.strip(),
                "exercise_id": ex["id"],
                "exercise_title": ex["title"],
                "status": status,
                "difficulty": difficulty,
                "comment": (comment or "").strip(),
            }
            append_submission(row)
            st.success("Registro salvo ✅")
            # força "reset" do comentário opcional para evitar reenvio igual sem querer
            st.session_state[comment_key] = ""

with col2:
    if st.button("➡️ Próximo exercício", use_container_width=True):
        st.session_state["__go_next__"] = True

# Avança automaticamente (sem recarregar página)
if st.session_state.get("__go_next__", False):
    st.session_state["__go_next__"] = False
    # move rádio da sidebar para o próximo
    next_idx = min(idx + 1, len(EXS) - 1)
    st.experimental_set_query_params(ex=str(next_idx))
    # fallback: se não usar query params, só informa
    st.info("Selecione o próximo exercício na barra lateral (➡️).")

st.divider()

# =========================
# Painel do professor (analytics)
# =========================
if is_teacher():
    st.subheader("📊 Painel do Professor (Analytics)")

    df = load_df()
    if df.empty:
        st.warning("Ainda não há registros salvos.")
    else:
        # Filtros
        c1, c2, c3 = st.columns([1.2, 1.2, 1.6])
        with c1:
            turma_sel = st.selectbox("Filtrar por turma", ["(Todas)"] + sorted([x for x in df["class_group"].dropna().unique().tolist() if str(x).strip()]))
        with c2:
            ex_sel = st.selectbox("Filtrar por exercício", ["(Todos)"] + [e["id"] for e in EXS])
        with c3:
            last_n = st.slider("Mostrar últimos N registros", 50, 2000, 300)

        dff = df.copy()
        if turma_sel != "(Todas)":
            dff = dff[dff["class_group"].astype(str) == turma_sel]
        if ex_sel != "(Todos)":
            dff = dff[dff["exercise_id"].astype(str) == ex_sel]

        # Ordena e limita
        if "timestamp" in dff.columns:
            dff = dff.sort_values("timestamp", ascending=False)
        dff_view = dff.head(last_n)

        st.markdown("#### 🧾 Registros (amostra)")
        st.dataframe(dff_view, use_container_width=True, hide_index=True)

        # KPIs
        st.markdown("#### 📌 Resumo")
        total = len(dff)
        feito = int((dff["status"] == "✅ Feito").sum())
        nao = int((dff["status"] == "❌ Não consegui").sum())
        perc_feito = (feito / total) * 100 if total else 0

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Registros", f"{total}")
        k2.metric("✅ Feito", f"{feito}")
        k3.metric("❌ Não consegui", f"{nao}")
        k4.metric("% Feito", f"{perc_feito:.1f}%")

        # Gráficos
        st.markdown("#### 📈 Distribuições")
        g1, g2 = st.columns(2)

        with g1:
            st.caption("Status")
            st.bar_chart(dff["status"].value_counts())

        with g2:
            st.caption("Dificuldade")
            order = ["Fácil", "Médio", "Difícil"]
            vc = dff["difficulty"].value_counts()
            vc = vc.reindex(order).fillna(0)
            st.bar_chart(vc)

        st.markdown("#### 🧠 Mapa por exercício (agregado)")
        agg = (
            dff.groupby(["exercise_id", "exercise_title"])
               .agg(
                   registros=("status", "count"),
                   feito=("status", lambda s: (s == "✅ Feito").sum()),
                   nao_consegui=("status", lambda s: (s == "❌ Não consegui").sum()),
                   dificil=("difficulty", lambda s: (s == "Difícil").sum()),
                   medio=("difficulty", lambda s: (s == "Médio").sum()),
                   facil=("difficulty", lambda s: (s == "Fácil").sum()),
               )
               .reset_index()
        )
        agg["%feito"] = (agg["feito"] / agg["registros"] * 100).round(1)
        st.dataframe(agg.sort_values(["%feito", "registros"], ascending=[True, False]), use_container_width=True, hide_index=True)

        st.markdown("#### ⬇️ Download dos dados")
        csv_bytes = dff.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Baixar CSV filtrado",
            data=csv_bytes,
            file_name="feedback_exercicios_filtrado.csv",
            mime="text/csv",
            use_container_width=True
        )

        # Download do CSV completo (arquivo)
        if CSV_PATH.exists():
            st.download_button(
                "Baixar CSV completo (arquivo)",
                data=CSV_PATH.read_bytes(),
                file_name="feedback_exercicios_completo.csv",
                mime="text/csv",
                use_container_width=True
            )

else:
    st.caption("Professor: ative o modo professor para ver analytics e baixar os dados.")

st.divider()
st.caption("Salvamento local em `data/feedback_exercicios.csv` e log em `data/feedback_exercicios.jsonl`.")
