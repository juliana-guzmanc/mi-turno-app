"""
MI TURNO · "Tu futuro también importa"
FASE 3 — Interfaz en Streamlit (PASO 1)

Este primer paso solo demuestra que la app puede:
  1) conectarse a la base de datos real (mi_turno.db), y
  2) correr el MISMO motor de match que ya probamos en Colab.

No tiene todavía la grilla de horarios ni el panel INE — eso viene
en los próximos pasos, una vez que esta base funcione sin errores.
"""

import sqlite3
import pandas as pd
import streamlit as st

from motor_match import cargar_tablas, motor_match_usuaria

DB_PATH = "mi_turno.db"

# ------------------------------------------------------------
# Configuración de página
# ------------------------------------------------------------
st.set_page_config(page_title="Mi Turno", page_icon="💜", layout="centered")

st.markdown(
    """
    <style>
    .stApp { background-color: #FDF7F8; }
    h1 { color: #7B1E3A; }
    .stButton>button {
        background-color: #7B1E3A;
        color: white;
        border-radius: 10px;
        font-weight: 700;
        border: none;
    }
    .stButton>button:hover { background-color: #B03A5E; color: white; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Mi Turno")
st.caption("Tu futuro también importa")


# ------------------------------------------------------------
# Conexión a la base de datos real (se reutiliza entre clics)
# ------------------------------------------------------------
@st.cache_resource
def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


con = get_connection()
tablas = cargar_tablas(con)

st.success(f"Conectado a la base de datos: {len(tablas['usuarias'])} usuarias registradas.")


# ------------------------------------------------------------
# PASO 1: elegir una usuaria existente y ver su match real,
# calculado por el mismo motor.py que ya validamos.
# ------------------------------------------------------------
st.subheader("Probar el motor de match con una usuaria existente")

usuarias_df = tablas["usuarias"]
nombre_a_id = dict(zip(usuarias_df.nombre, usuarias_df.usuaria_id))
nombre_sel = st.selectbox("Selecciona una usuaria", usuarias_df.nombre)

if st.button("Calcular Match"):
    usuaria_id = nombre_a_id[nombre_sel]
    resultado = motor_match_usuaria(tablas, usuaria_id)

    vista = resultado[
        ["vacante_id", "score_horario", "score_habilidades", "match_score", "habilitada_postular"]
    ]
    st.dataframe(vista, use_container_width=True)

    for _, fila in resultado.iterrows():
        if fila.cursos_recomendados:
            estado = "✅ habilitada por horario" if fila.habilitada_postular else "🔒 bloqueada por horario"
            with st.expander(f"Vacante {fila.vacante_id} — {estado}"):
                for c in fila.cursos_recomendados:
                    st.write(f"📚 Curso sugerido: **{c['nombre']}** ({c['duracion_horas']} h)")
                if pd.notna(fila.match_potencial):
                    st.write(f"Si completa el curso, su match sube a **{fila.match_potencial}%**")
