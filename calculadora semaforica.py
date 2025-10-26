# -*- coding: utf-8 -*-
"""
Created on Sun Oct 26 14:13:24 2025

@author: gteix
"""

import streamlit as st
import pandas as pd
import math
from datetime import datetime


# -------------------------------------------------------------
# FUNÇÕES DE CÁLCULO
# -------------------------------------------------------------
def calcular_entreverdes(d2, v, aad, tr, i, c, travessia=False):
    g = 9.8
    ty = tr + (v / 3.6) / (2 * (aad + i * g))
    trc = (d2 + c) / (v / 3.6)

    # Regras mínimas de segurança
    if v <= 40 and ty < 3:
        ty = 3
    elif v in (50, 60) and ty < 4:
        ty = 4
    elif v == 70 and ty < 5:
        ty = 5

    # Limite máximo 5s
    if ty > 5:
        trc += (ty - 5)
        ty = 5

    # Acréscimo travessia
    if travessia:
        trc += 1

    total = math.ceil(ty + trc)
    return {"amarelo": round(ty, 2), "vermelho": round(trc, 2), "total": total}


def webster(tp, fluxos, saturacoes):
    yi = [v / s for v, s in zip(fluxos, saturacoes)]
    soma_yi = sum(yi)
    if soma_yi >= 1:
        raise ValueError("Σyi deve ser menor que 1 para o método de Webster.")
    ciclo_otimo = ((1.5 * tp) + 5) / (1 - soma_yi)
    return round(ciclo_otimo, 0), yi, soma_yi


def tempo_verde(tc, tp, fluxos, saturacoes):
    yi = [v / s for v, s in zip(fluxos, saturacoes)]
    soma_yi = sum(yi)
    if soma_yi == 0:
        raise ValueError("Σyi não pode ser zero.")
    teg = tc - tp
    tempos = [round(teg * (y / soma_yi), 0) for y in yi]
    return tempos, yi, soma_yi


# -------------------------------------------------------------
# INTERFACE STREAMLIT
# -------------------------------------------------------------
st.set_page_config(page_title="Calculadora Semafórica", page_icon="🚦", layout="centered")

st.title("🚦 Calculadora de Sinalização Semafórica")
st.markdown("Ferramenta baseada no **Manual Brasileiro de Sinalização de Trânsito (Volume V)**")
st.markdown(
    """ 
    Você pode baixar o documento completo clicando no link abaixo:  
    👉 [Baixar Manual em PDF](https://www.gov.br/transportes/pt-br/assuntos/transito/arquivos-senatran/docs/copy_of___05___MBST_Vol._V___Sinalizacao_Semaforica.pdf)
    """,
    unsafe_allow_html=True
)

# -------------------------------------------------------------
st.divider()
st.header("Tempo de Entreverdes por Fase")

num_fases = st.number_input("Número de Fases", 2, 6, 3)
fases = []
tp_total = 0

for i in range(num_fases):
    with st.expander(f"⚙️ Parâmetros da Fase {i+1}", expanded=(i == 0)):
        d2 = st.number_input(f"Distância de Percurso (m) - Fase {i+1}", value=24.0, key=f"d2_{i}")
        v = st.number_input(f"Velocidade (km/h) - Fase {i+1}", value=40.0, key=f"v_{i}")
        aad = st.number_input(f"Máx. Taxa de Frenagem (m/s²) - Fase {i+1}", value=3.0, key=f"aad_{i}")
        tr = st.number_input(f"Tempo de Reação (s) - Fase {i+1}", value=1.0, key=f"tr_{i}")
        i_slope = st.number_input(f"Inclinação (%) - Fase {i+1}", value=0.0, key=f"i_{i}") / 100
        c = st.number_input(f"Comprimento do Veículo (m) - Fase {i+1}", value=12.0, key=f"c_{i}")
        travessia = st.checkbox("Travessia de Pedestres no estágio subsequente?", key=f"ped_{i}")

        if st.button(f"Calcular Fase {i+1}", key=f"calc_{i}"):
            res = calcular_entreverdes(d2, v, aad, tr, i_slope, c, travessia)
            st.success(
                f"Fase {i+1}: Amarelo = {res['amarelo']}s | Vermelho = {res['vermelho']}s | Total = {res['total']}s"
            )
            fases.append(res)

if st.button("Calcular Todas as Fases"):
    fases = []
    tp_total = 0

    for i in range(num_fases):
        res = calcular_entreverdes(
            st.session_state[f"d2_{i}"],
            st.session_state[f"v_{i}"],
            st.session_state[f"aad_{i}"],
            st.session_state[f"tr_{i}"],
            st.session_state[f"i_{i}"],
            st.session_state[f"c_{i}"],
            st.session_state[f"ped_{i}"],
        )
        fases.append({
            "Fase": f"Fase {i+1}",
            "Tempo de Amarelo (s)": res["amarelo"],
            "Tempo de Vermelho (s)": res["vermelho"],
            "Entreverdes Total (s)": res["total"]
        })
        tp_total += res["total"]

    st.session_state["tp_total"] = tp_total
    st.session_state["df_fases"] = pd.DataFrame(fases)

    st.dataframe(st.session_state["df_fases"])
    st.info(f"**Tempo Perdido Total (Tp): {tp_total:.1f} s**")

# -------------------------------------------------------------
st.divider()
st.header("Método de Webster")

tp = st.number_input("Tempo Perdido Total (Tp) [s]", value=float(st.session_state.get("tp_total", 9)))

fluxos = []
saturacoes = []

cols = st.columns(2)
for i in range(num_fases):
    with cols[0]:
        fluxo = st.number_input(f"Fluxo de Veículos - Fase {i+1} (vph)", min_value=0, value=100, key=f"fluxo_{i}")
        fluxos.append(fluxo)
    with cols[1]:
        sat = st.number_input(f"Fluxo de Saturação - Fase {i+1} (vph)", min_value=1, value=1800, key=f"sat_{i}")
        saturacoes.append(sat)

if st.button("Calcular Ciclo Ótimo (Webster)", key="btn_webster"):
    try:
        tc, yi, soma_yi = webster(tp, fluxos, saturacoes)
        st.session_state["tc"] = tc
        st.session_state["fluxos"] = fluxos
        st.session_state["saturacoes"] = saturacoes

        st.success(f"**Ciclo Ótimo: {tc:.1f} s**")
        st.write(f"Σyi = {soma_yi:.3f}")
        st.write(f"yi = {', '.join([f'{y:.3f}' for y in yi])}")
    except Exception as e:
        st.error(str(e))

# -------------------------------------------------------------
st.divider()
st.header("Tempo Verde Efetivo")

tc_default = st.session_state.get("tc", 60.0)
tc_input = st.number_input("Tempo de Ciclo (tc) [s]", value=tc_default, min_value=1.0)
tp_input = st.number_input("Tempo Perdido (Tp) [s]", value=int(tp))

if st.button("Calcular Tempos Verdes"):
    fluxos = st.session_state.get("fluxos", [])
    saturacoes = st.session_state.get("saturacoes", [])

    if not fluxos or not saturacoes:
        st.error("⚠️ Você precisa calcular o Método de Webster primeiro para definir os fluxos.")
    else:
        try:
            tempos, yi, soma_yi = tempo_verde(tc_input, tp_input, fluxos, saturacoes)
            df_verde = pd.DataFrame({
                "Fase": [f"Fase {i+1}" for i in range(len(tempos))],
                "Tempo Verde Efetivo (s)": tempos
            })

            st.session_state["df_verde"] = df_verde
            st.session_state["tc"] = tc_input

            st.dataframe(df_verde)
            if any(t < 12 for t in tempos):
                st.warning("⚠️ Pelo menos uma fase possui tempo verde inferior a 12 segundos.")
        except Exception as e:
            st.error(str(e))

# -------------------------------------------------------------
st.divider()
st.header("📤 Exportar Resultados")

if st.button("📥 Baixar CSV"):
    df_export_parts = []

    if "df_fases" in st.session_state:
        df_fases = st.session_state["df_fases"].copy()
        df_fases.insert(0, "Tipo", "Entreverdes por Fase")
        df_export_parts.append(df_fases)

    if "df_verde" in st.session_state:
        df_verde = st.session_state["df_verde"].copy()
        df_verde.insert(0, "Tipo", "Tempos Verdes Efetivos")
        df_export_parts.append(df_verde)

    resumo = pd.DataFrame({
        "Tipo": ["Resumo"],
        "Tp_Total (s)": [round(st.session_state.get("tp_total", 0), 1)],
        "Ciclo Ótimo Webster (s)": [round(st.session_state.get("tc", 0), 1)],
        "Data Exportação": [datetime.now().strftime("%d/%m/%Y %H:%M")]
    })
    df_export_parts.append(resumo)

    df_export = pd.concat(df_export_parts, ignore_index=True)
    csv = df_export.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="📥 Baixar Resultados em CSV",
        data=csv,
        file_name=f"calculadora_semaforo_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv"
    )



















