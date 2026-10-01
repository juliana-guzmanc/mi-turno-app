
"""
ENCAJA · Plataforma de empleabilidad basada en datos
Streamlit + SQLite + motor_match.py

Compatible con la base mi_turno.db incluida en el proyecto y tolerante
a variaciones de nombres de columnas entre versiones del prototipo.
"""

import os
import sqlite3
import html
import urllib.parse
from datetime import date

import pandas as pd
import streamlit as st

from motor_match import cargar_tablas, motor_match_usuaria, calcular_match


DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mi_turno.db")

# ============================================================
# CONFIGURACIÓN
# ============================================================

st.set_page_config(
    page_title="ENCAJA | Empleo que encaja con tu vida",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Paleta ENCAJA
PLUM = "#432C46"
TERRACOTTA = "#C96B5B"
GOLD = "#D4AF37"
CREAM = "#FAF7F2"
WHITE = "#FFFFFF"
SAGE = "#6F8F7A"
AMBER = "#D69A45"
TEXT = "#2E3035"
MUTED = "#6B6E73"
BORDER = "#E8E1DC"
SOFT_PLUM = "#F4EDF5"
SOFT_GOLD = "#FBF4DF"
SOFT_GREEN = "#EAF4EE"
SOFT_ORANGE = "#FFF1E7"

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');

    .stApp {{
        background: {CREAM};
        color: {TEXT};
    }}

    [data-testid="stHeader"] {{
        background: transparent;
    }}

    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, {PLUM} 0%, #351F38 100%);
    }}

    [data-testid="stSidebar"] * {{
        color: #FFFFFF !important;
    }}

    .block-container {{
        padding-top: 1.4rem;
        padding-bottom: 3rem;
        max-width: 1500px;
    }}

    h1, h2, h3 {{
        font-family: "DM Sans", sans-serif !important;
        color: {PLUM} !important;
        letter-spacing: -0.03em;
    }}

    p, div, label, span {{
        font-family: "DM Sans", sans-serif;
    }}

    .hero {{
        border-radius: 24px;
        min-height: 245px;
        padding: 35px 40px;
        color: white;
        background:
            radial-gradient(circle at 90% 20%, rgba(255,255,255,.18), transparent 25%),
            linear-gradient(110deg, {PLUM} 0%, #69445F 58%, {TERRACOTTA} 130%);
        box-shadow: 0 14px 35px rgba(67,44,70,.15);
        margin-bottom: 22px;
    }}

    .hero-kicker {{
        text-transform: uppercase;
        font-size: .76rem;
        letter-spacing: .18em;
        opacity: .8;
        font-weight: 700;
    }}

    .hero h1 {{
        color: white !important;
        font-size: 2.4rem !important;
        margin: 8px 0;
        max-width: 680px;
    }}

    .hero p {{
        color: rgba(255,255,255,.9);
        max-width: 700px;
        font-size: 1rem;
        line-height: 1.55;
    }}

    .brand {{
        padding: 18px 10px 26px;
    }}

    .brand-name {{
        font-size: 2rem;
        font-weight: 800;
        letter-spacing: -.05em;
    }}

    .brand-sub {{
        font-size: .82rem;
        line-height: 1.35;
        opacity: .8;
        margin-top: 2px;
    }}

    .side-title {{
        font-size: .68rem;
        text-transform: uppercase;
        letter-spacing: .16em;
        opacity: .55;
        margin: 20px 0 8px;
    }}

    .side-note {{
        margin-top: 25px;
        padding: 16px;
        border: 1px solid rgba(255,255,255,.18);
        border-radius: 15px;
        font-size: .82rem;
        line-height: 1.5;
        background: rgba(255,255,255,.06);
    }}

    .kpi {{
        background: {WHITE};
        border: 1px solid {BORDER};
        border-radius: 18px;
        padding: 18px;
        min-height: 125px;
        box-shadow: 0 6px 18px rgba(67,44,70,.06);
    }}

    .kpi-icon {{
        width: 38px;
        height: 38px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        border-radius: 50%;
        background: {SOFT_PLUM};
        color: {PLUM};
        font-size: 1.05rem;
        margin-bottom: 7px;
    }}

    .kpi-label {{
        font-size: .78rem;
        color: {MUTED};
        font-weight: 600;
    }}

    .kpi-value {{
        font-size: 1.85rem;
        font-weight: 800;
        color: {PLUM};
        line-height: 1.05;
        margin-top: 5px;
    }}

    .kpi-foot {{
        font-size: .72rem;
        color: {SAGE};
        margin-top: 5px;
    }}

    .card {{
        background: {WHITE};
        border: 1px solid {BORDER};
        border-radius: 20px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 7px 20px rgba(67,44,70,.055);
    }}

    .job-title {{
        font-size: 1.16rem;
        font-weight: 800;
        color: {PLUM};
        margin-top: 2px;
    }}

    .company {{
        text-transform: uppercase;
        color: {MUTED};
        letter-spacing: .08em;
        font-size: .67rem;
        font-weight: 700;
    }}

    .job-meta {{
        color: {MUTED};
        font-size: .82rem;
        margin: 5px 0;
    }}

    .job-desc {{
        color: {TEXT};
        font-size: .83rem;
        line-height: 1.45;
        margin-top: 10px;
    }}

    .badge {{
        display: inline-block;
        border-radius: 999px;
        padding: 6px 10px;
        font-size: .70rem;
        font-weight: 700;
        margin: 4px 4px 2px 0;
    }}

    .badge-gold {{
        background: {SOFT_GOLD};
        color: #876E15;
    }}

    .badge-green {{
        background: {SOFT_GREEN};
        color: #47705A;
    }}

    .badge-orange {{
        background: {SOFT_ORANGE};
        color: #A65B2C;
    }}

    .match-ring {{
        width: 92px;
        height: 92px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-direction: column;
        margin: auto;
        background: conic-gradient({GOLD} var(--pct), #EFE9DF 0);
        position: relative;
    }}

    .match-ring::before {{
        content: "";
        position: absolute;
        width: 72px;
        height: 72px;
        border-radius: 50%;
        background: {WHITE};
    }}

    .match-number, .match-label {{
        position: relative;
        z-index: 1;
    }}

    .match-number {{
        font-size: 1.35rem;
        font-weight: 800;
        color: {PLUM};
    }}

    .match-label {{
        font-size: .62rem;
        color: {MUTED};
    }}

    .why {{
        background: #FCFAF7;
        border-radius: 13px;
        padding: 12px;
        margin-top: 10px;
    }}

    .why-title {{
        color: {PLUM};
        font-size: .75rem;
        font-weight: 800;
        margin-bottom: 7px;
    }}

    .why-row {{
        display: flex;
        justify-content: space-between;
        font-size: .68rem;
        padding: 3px 0;
        color: {MUTED};
    }}

    .profile-card {{
        background: {WHITE};
        border: 1px solid {BORDER};
        border-radius: 20px;
        padding: 22px;
        box-shadow: 0 7px 20px rgba(67,44,70,.055);
        margin-bottom: 15px;
    }}

    .strength {{
        display: inline-block;
        padding: 7px 11px;
        border-radius: 999px;
        background: {SOFT_GOLD};
        color: #806B18;
        font-size: .72rem;
        font-weight: 700;
        margin: 3px;
    }}

    .section-kicker {{
        color: {TERRACOTTA};
        text-transform: uppercase;
        letter-spacing: .14em;
        font-size: .68rem;
        font-weight: 800;
    }}

    .quote {{
        border-radius: 18px;
        background: linear-gradient(135deg, #F7EFEF, #FFF9F0);
        border: 1px solid {BORDER};
        padding: 22px;
        color: {PLUM};
        font-family: "Playfair Display", serif;
        font-size: 1.03rem;
        line-height: 1.5;
    }}

    .empty {{
        text-align: center;
        padding: 50px 20px;
        color: {MUTED};
    }}

    .company-panel {{
        background: linear-gradient(135deg, {PLUM}, #65445E);
        border-radius: 22px;
        padding: 25px;
        color: white;
        margin-bottom: 18px;
    }}

    .company-panel h2 {{
        color: white !important;
        margin: 0;
    }}

    .contact-btn {{
        display: inline-block;
        text-decoration: none !important;
        padding: 8px 11px;
        border-radius: 10px;
        margin: 3px 3px 3px 0;
        font-size: .74rem;
        font-weight: 700;
    }}

    .mail-btn {{
        background: {SOFT_PLUM};
        color: {PLUM} !important;
    }}

    .wa-btn {{
        background: {SOFT_GREEN};
        color: #47705A !important;
    }}

    .stButton > button {{
        border-radius: 11px !important;
        border: 1px solid {TERRACOTTA} !important;
        background: {TERRACOTTA} !important;
        color: white !important;
        font-weight: 700 !important;
        min-height: 40px;
    }}

    .stButton > button:hover {{
        background: #B85B4D !important;
        border-color: #B85B4D !important;
    }}

    div[data-baseweb="select"] > div {{
        border-radius: 11px;
        border-color: {BORDER};
    }}

    .small-muted {{
        font-size: .72rem;
        color: {MUTED};
    }}

    .warning-box {{
        background: {SOFT_ORANGE};
        border: 1px solid #F1D4C0;
        border-radius: 14px;
        padding: 13px;
        color: #85502D;
        font-size: .82rem;
    }}

    @media (max-width: 900px) {{
        .hero h1 {{ font-size: 1.8rem !important; }}
        .hero {{ padding: 25px; }}
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SQLITE / COMPATIBILIDAD
# ============================================================

@st.cache_resource
def get_connection():
    con = sqlite3.connect(DB_PATH, check_same_thread=False)
    con.execute("PRAGMA foreign_keys = ON")
    return con


con = get_connection()


def table_exists(name):
    return con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (name,),
    ).fetchone() is not None


def columns(table):
    if not table_exists(table):
        return []
    return [r[1] for r in con.execute(f'PRAGMA table_info("{table}")').fetchall()]


def first_col(table, candidates, default=None):
    cols = columns(table)
    for c in candidates:
        if c in cols:
            return c
    return default


def qcol(name):
    return '"' + str(name).replace('"', '""') + '"'


def add_column_if_missing(table, col, definition):
    if col not in columns(table):
        try:
            con.execute(f'ALTER TABLE {qcol(table)} ADD COLUMN {qcol(col)} {definition}')
            con.commit()
        except sqlite3.OperationalError:
            pass


def prepare_compatibility():
    """
    Agrega únicamente campos opcionales que la maqueta necesita.
    No elimina ni modifica las columnas originales.
    """
    if table_exists("Usuarias"):
        add_column_if_missing("Usuarias", "telefono", "TEXT")
        add_column_if_missing("Usuarias", "direccion", "TEXT")

    if table_exists("Habilidades"):
        add_column_if_missing(
            "Habilidades",
            "tipo_habilidad",
            "TEXT DEFAULT 'practica'"
        )

    if table_exists("Vacantes"):
        add_column_if_missing("Vacantes", "comuna", "TEXT")
        add_column_if_missing("Vacantes", "direccion", "TEXT")
        add_column_if_missing("Vacantes", "horario", "TEXT")
        add_column_if_missing("Vacantes", "sueldo", "REAL")
        add_column_if_missing("Vacantes", "requiere_capacitacion", "INTEGER DEFAULT 0")
        add_column_if_missing("Vacantes", "curso_sugerido", "TEXT")

    # Compatibilidad con la variante escrita con tilde.
    if table_exists("Vacantes") and "requería_capacitacion" in columns("Vacantes"):
        pass

    if table_exists("Postulaciones"):
        add_column_if_missing("Postulaciones", "fecha_postulacion", "TEXT")


prepare_compatibility()


# ============================================================
# DATOS
# ============================================================

def reload_tables():
    # El motor original espera estas tablas/columnas.
    return cargar_tablas(con)


def safe_df(sql, params=()):
    try:
        return pd.read_sql_query(sql, con, params=params)
    except Exception:
        return pd.DataFrame()


def get_users():
    df = safe_df("SELECT * FROM Usuarias ORDER BY nombre")
    return df


def get_jobs():
    if not table_exists("Vacantes"):
        return pd.DataFrame()

    # JOIN empresa cuando existe.
    if table_exists("Empresas"):
        return safe_df("""
            SELECT v.*, e.nombre AS empresa_nombre, e.contacto_email AS empresa_email,
                   e.comuna AS empresa_comuna
            FROM Vacantes v
            LEFT JOIN Empresas e ON e.empresa_id = v.empresa_id
            WHERE COALESCE(v.activa,1)=1
            ORDER BY v.vacante_id DESC
        """)
    return safe_df("SELECT * FROM Vacantes WHERE COALESCE(activa,1)=1 ORDER BY vacante_id DESC")


def get_skills():
    if not table_exists("Habilidades"):
        return pd.DataFrame()
    return safe_df("SELECT * FROM Habilidades ORDER BY nombre")


def ensure_requested_skills():
    """
    Mantiene visibles las habilidades solicitadas por la maqueta.
    En la BD actual Habilidades tiene una restricción de rubro;
    por eso las nuevas se almacenan en el rubro administrativo
    sin tocar los registros existentes.
    """
    if not table_exists("Habilidades"):
        return

    add_column_if_missing("Habilidades", "tipo_habilidad", "TEXT DEFAULT 'practica'")

    practical = [
        "Cuidado de niños",
        "Cuidado de adultos mayores",
        "Aseo/Sanitización",
        "Cocina",
        "Cuidado textil",
        "Atención a público",
        "Reposición/Stock",
        "Apoyo en eventos",
        "Costura",
        "Manejo de caja",
    ]

    strengths = [
        "Trabajo bajo presión",
        "Organización del hogar",
        "Atención al detalle",
        "Responsabilidad/Puntualidad",
        "Trabajo en equipo",
        "Autonomía",
        "Adaptabilidad",
        "Comunicación asertiva",
    ]

    valid_rubros = ["Gastronomía", "Peluquería", "Administración", "Análisis de Datos"]
    fallback_rubro = "Administración"

    for name in practical:
        exists = con.execute(
            "SELECT habilidad_id FROM Habilidades WHERE lower(nombre)=lower(?)",
            (name,),
        ).fetchone()
        if not exists:
            try:
                con.execute(
                    "INSERT INTO Habilidades (nombre, rubro, tipo_habilidad) VALUES (?,?,?)",
                    (name, fallback_rubro, "practica"),
                )
            except sqlite3.IntegrityError:
                pass

    for name in strengths:
        exists = con.execute(
            "SELECT habilidad_id FROM Habilidades WHERE lower(nombre)=lower(?)",
            (name,),
        ).fetchone()
        if not exists:
            try:
                con.execute(
                    "INSERT INTO Habilidades (nombre, rubro, tipo_habilidad) VALUES (?,?,?)",
                    (name, fallback_rubro, "fortaleza_cotidiana"),
                )
            except sqlite3.IntegrityError:
                pass

    # Clasifica algunos registros históricos conocidos.
    for name in practical:
        con.execute(
            "UPDATE Habilidades SET tipo_habilidad='practica' WHERE lower(nombre)=lower(?)",
            (name,),
        )
    con.commit()


ensure_requested_skills()


# ============================================================
# HELPERS DE NEGOCIO
# ============================================================

DAYS = [
    (0, "Lunes"),
    (1, "Martes"),
    (2, "Miércoles"),
    (3, "Jueves"),
    (4, "Viernes"),
    (5, "Sábado"),
]

BLOCKS = {
    "Mañana": ("09:00", "13:00"),
    "Tarde": ("14:00", "18:00"),
    "Noche": ("18:00", "22:00"),
}


def get_user_id_by_name(name):
    col = first_col("Usuarias", ["usuaria_id", "id_usuaria"])
    ncol = first_col("Usuarias", ["nombre"])
    row = con.execute(
        f"SELECT {qcol(col)} FROM Usuarias WHERE {qcol(ncol)}=?",
        (name,),
    ).fetchone()
    return row[0] if row else None


def user_name(uid):
    row = con.execute("SELECT nombre FROM Usuarias WHERE usuaria_id=?", (uid,)).fetchone()
    return row[0] if row else "Postulante"


def get_user_skills(uid, tipo=None):
    sql = """
        SELECT h.habilidad_id, h.nombre, COALESCE(h.tipo_habilidad,'practica') AS tipo_habilidad,
               uh.nivel
        FROM Usuaria_Habilidad uh
        JOIN Habilidades h ON h.habilidad_id = uh.habilidad_id
        WHERE uh.usuaria_id=?
    """
    df = safe_df(sql, (uid,))
    if tipo and not df.empty:
        df = df[df.tipo_habilidad == tipo]
    return df


def get_user_schedule(uid):
    if not table_exists("Horarios_Disponibles"):
        return pd.DataFrame()
    return safe_df(
        "SELECT * FROM Horarios_Disponibles WHERE usuaria_id=? ORDER BY dia_semana, bloque",
        (uid,),
    )


def get_job_blocks(vacancy_id):
    if not table_exists("Bloques_Vacante"):
        return pd.DataFrame()
    return safe_df(
        "SELECT * FROM Bloques_Vacante WHERE vacante_id=? ORDER BY dia_semana, bloque",
        (vacancy_id,),
    )


def schedule_text(vacancy_id):
    df = get_job_blocks(vacancy_id)
    if df.empty:
        return ""
    chunks = []
    for _, r in df.iterrows():
        day = DAYS[int(r["dia_semana"])][1] if int(r["dia_semana"]) < 6 else str(r["dia_semana"])
        chunks.append(f"{day} {r['hora_inicio']}-{r['hora_fin']}")
    return " · ".join(chunks)


def job_required_skill_names(vacancy_id):
    df = safe_df("""
        SELECT h.nombre
        FROM Vacante_Habilidad vh
        JOIN Habilidades h ON h.habilidad_id=vh.habilidad_id
        WHERE vh.vacante_id=?
        ORDER BY h.nombre
    """, (vacancy_id,))
    return df.nombre.tolist() if not df.empty else []


def proximity_label(user_comuna, job_comuna):
    if not user_comuna or not job_comuna:
        return "📍 Ubicación por confirmar"
    if str(user_comuna).strip().lower() == str(job_comuna).strip().lower():
        return "📍 Misma comuna"
    return f"📍 {job_comuna}"


def empresa_contact_email(vacancy_id):
    if not table_exists("Vacantes"):
        return ""
    if "empresa_id" in columns("Vacantes") and table_exists("Empresas"):
        row = con.execute("""
            SELECT e.contacto_email
            FROM Vacantes v JOIN Empresas e ON e.empresa_id=v.empresa_id
            WHERE v.vacante_id=?
        """, (vacancy_id,)).fetchone()
        return row[0] if row else ""
    return ""


def normalize_phone(phone):
    digits = "".join(ch for ch in str(phone or "") if ch.isdigit())
    if digits.startswith("56"):
        return digits
    if digits.startswith("9") and len(digits) == 9:
        return "56" + digits
    return digits


def user_has_applied(uid, vid):
    if not table_exists("Postulaciones"):
        return False
    row = con.execute(
        "SELECT 1 FROM Postulaciones WHERE usuaria_id=? AND vacante_id=? LIMIT 1",
        (uid, vid),
    ).fetchone()
    return row is not None


def insert_postulation(uid, vid, result):
    if user_has_applied(uid, vid):
        return False, "Ya registraste una postulación a esta oportunidad."

    cols = columns("Postulaciones")
    data = {}

    mapping = {
        "usuaria_id": uid,
        "id_usuaria": uid,
        "vacante_id": vid,
        "id_vacante": vid,
        "score_horario": float(result.get("score_horario", 0)),
        "score_habilidades": float(result.get("score_habilidades", 0)),
        "match_score": float(result.get("match_score", 0)),
        "habilitada_postular": int(result.get("habilitada_postular", 0)),
        "estado": "postulo",
        "fecha": str(date.today()),
        "fecha_postulacion": str(date.today()),
    }

    for k, v in mapping.items():
        if k in cols:
            data[k] = v

    if not data:
        return False, "No se encontró una estructura compatible para registrar la postulación."

    names = ", ".join(qcol(k) for k in data)
    placeholders = ", ".join("?" for _ in data)

    try:
        con.execute(
            f"INSERT INTO Postulaciones ({names}) VALUES ({placeholders})",
            tuple(data.values()),
        )
        con.commit()
        return True, "Postulación registrada correctamente."
    except sqlite3.IntegrityError as e:
        return False, f"No fue posible registrar la postulación: {e}"


def upsert_user_profile(uid, nombre, email, telefono, comuna, direccion):
    cols = columns("Usuarias")
    values = {
        "nombre": nombre.strip(),
        "email": email.strip(),
        "telefono": telefono.strip(),
        "comuna": comuna.strip(),
        "direccion": direccion.strip(),
    }
    values = {k: v for k, v in values.items() if k in cols}

    set_clause = ", ".join(f"{qcol(k)}=?" for k in values if k != "email")
    params = [v for k, v in values.items() if k != "email"]

    # email suele ser UNIQUE; actualizar por id evita problemas de duplicación.
    if "email" in values and "email" in cols:
        # No se permite cambiar a un email usado por otra usuaria.
        duplicate = con.execute(
            "SELECT usuaria_id FROM Usuarias WHERE email=? AND usuaria_id<>?",
            (values["email"], uid),
        ).fetchone()
        if duplicate:
            return False, "Ese correo ya está registrado por otra usuaria."

    if set_clause:
        params.append(uid)
        con.execute(
            f"UPDATE Usuarias SET {set_clause} WHERE {qcol(first_col('Usuarias',['usuaria_id','id_usuaria']))}=?",
            params,
        )

    # Si la versión de la tabla no tiene email, no se hace nada con él.
    if "email" in values and "email" in cols:
        con.execute(
            "UPDATE Usuarias SET email=? WHERE usuaria_id=?",
            (values["email"], uid),
        )

    con.commit()
    return True, "Perfil actualizado."


def save_user_skills(uid, selected_names):
    skills = get_skills()
    if skills.empty:
        return

    con.execute("DELETE FROM Usuaria_Habilidad WHERE usuaria_id=?", (uid,))

    for name in selected_names:
        row = skills[skills.nombre == name]
        if row.empty:
            continue
        hid = int(row.iloc[0].habilidad_id)
        con.execute(
            "INSERT INTO Usuaria_Habilidad (usuaria_id, habilidad_id, nivel) VALUES (?,?,?)",
            (uid, hid, "intermedio"),
        )

    con.commit()


def save_user_schedule(uid, selected):
    if not table_exists("Horarios_Disponibles"):
        return

    con.execute("DELETE FROM Horarios_Disponibles WHERE usuaria_id=?", (uid,))

    cols = columns("Horarios_Disponibles")
    for day_num, block in selected:
        start, end = BLOCKS[block]
        data = {}

        candidates = {
            "usuaria_id": uid,
            "id_usuaria": uid,
            "dia_semana": day_num,
            "dia": day_num,
            "bloque": block,
            "bloque_horario": block,
            "hora_inicio": start,
            "hora_fin": end,
        }

        for k, v in candidates.items():
            if k in cols:
                data[k] = v

        names = ", ".join(qcol(k) for k in data)
        placeholders = ", ".join("?" for _ in data)
        try:
            con.execute(
                f"INSERT INTO Horarios_Disponibles ({names}) VALUES ({placeholders})",
                tuple(data.values()),
            )
        except sqlite3.IntegrityError:
            pass

    con.commit()


def match_for_user(uid):
    tablas = reload_tables()
    df = motor_match_usuaria(tablas, int(uid))
    return df


def match_one(uid, vid):
    tablas = reload_tables()
    return calcular_match(tablas, int(uid), int(vid))


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown(
        """
        <div class="brand">
            <div class="brand-name">✦ ENCAJA</div>
            <div class="brand-sub">El trabajo que encaja con tu vida.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="side-title">Navegación</div>', unsafe_allow_html=True)

    role = st.radio(
        "Rol",
        ["Soy Postulante", "Soy Empresa"],
        label_visibility="collapsed",
    )

    if role == "Soy Postulante":
        page = st.radio(
            "Sección",
            ["Inicio", "Mis oportunidades", "Mi perfil"],
            label_visibility="collapsed",
        )
    else:
        page = st.radio(
            "Sección",
            ["Panel empresa", "Publicar turno", "Candidatas"],
            label_visibility="collapsed",
        )

    st.markdown('<div class="side-title">Tu identidad</div>', unsafe_allow_html=True)

    users = get_users()
    if users.empty:
        st.error("No existen usuarias en la base.")
        st.stop()

    user_names = users.nombre.tolist()

    default_idx = 0
    if "selected_uid" in st.session_state:
        current = users[users.usuaria_id == st.session_state.selected_uid]
        if not current.empty:
            default_idx = user_names.index(current.iloc[0].nombre)

    selected_user_name = st.selectbox(
        "Postulante de demostración",
        user_names,
        index=default_idx,
        key="sidebar_user",
    )
    selected_uid = int(users.iloc[user_names.index(selected_user_name)].usuaria_id)
    st.session_state.selected_uid = selected_uid

    st.markdown(
        """
        <div class="side-note">
            <strong>Una solución basada en datos</strong><br>
            No se trata solo de encontrar trabajo, sino de encontrar una oportunidad que pueda encajar con tu realidad.
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# VISTA POSTULANTE
# ============================================================

def render_hero():
    st.markdown(
        """
        <div class="hero">
            <div class="hero-kicker">Tu talento importa</div>
            <h1>Encuentra una oportunidad que sí pueda funcionar contigo.</h1>
            <p>
                ENCAJA conecta personas que buscan oportunidades laborales flexibles
                con empresas que necesitan talento, utilizando disponibilidad,
                habilidades y ubicación para encontrar coincidencias.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpis(uid):
    jobs = get_jobs()
    matches = match_for_user(uid) if not jobs.empty else pd.DataFrame()

    total = len(jobs)
    high = int((matches.match_score >= 80).sum()) if not matches.empty else 0
    available = int((matches.habilitada_postular == 1).sum()) if not matches.empty else 0
    applications = safe_df(
        "SELECT * FROM Postulaciones WHERE usuaria_id=?",
        (uid,),
    )
    applied = len(applications)

    vals = [
        ("💼", "Vacantes disponibles", total, "Activas ahora"),
        ("★", "Alta compatibilidad", high, "80% o más"),
        ("◷", "Turnos compatibles", available, "Horario 100% compatible"),
        ("▣", "Postulaciones", applied, "En seguimiento"),
    ]

    cols = st.columns(4)
    for col, (icon, label, value, foot) in zip(cols, vals):
        with col:
            st.markdown(
                f"""
                <div class="kpi">
                    <div class="kpi-icon">{icon}</div>
                    <div class="kpi-label">{html.escape(label)}</div>
                    <div class="kpi-value">{value}</div>
                    <div class="kpi-foot">{html.escape(foot)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_profile_summary(uid):
    u = safe_df("SELECT * FROM Usuarias WHERE usuaria_id=?", (uid,))
    if u.empty:
        return

    row = u.iloc[0]
    skills = get_user_skills(uid)
    strengths = skills[skills.tipo_habilidad == "fortaleza_cotidiana"] if not skills.empty else pd.DataFrame()

    email = row.get("email", "")
    comuna = row.get("comuna", "")
    phone = row.get("telefono", "") if "telefono" in row.index else ""

    filled = 0
    for field in [row.get("nombre",""), email, comuna]:
        if str(field).strip():
            filled += 1
    if phone:
        filled += 1
    if not skills.empty:
        filled += 1
    if not get_user_schedule(uid).empty:
        filled += 1

    pct = min(100, round(filled / 6 * 100))

    strength_html = "".join(
        f'<span class="strength">{html.escape(str(x))}</span>'
        for x in strengths.nombre.tolist()[:6]
    )
    if not strength_html:
        strength_html = '<span class="small-muted">Aún no registras fortalezas cotidianas.</span>'

    st.markdown(
        f"""
        <div class="profile-card">
            <div class="section-kicker">Mi perfil</div>
            <h2 style="margin:5px 0 4px;">{html.escape(str(row.get("nombre","")))}</h2>
            <div class="small-muted">Analista de Datos / Perfil de empleabilidad</div>
            <div style="margin-top:14px; color:{MUTED}; font-size:.8rem;">
                📍 {html.escape(str(comuna))}
                &nbsp;&nbsp; ✉️ {html.escape(str(email))}
                {"&nbsp;&nbsp; ☎️ " + html.escape(str(phone)) if phone else ""}
            </div>
            <div style="margin-top:15px; height:7px; border-radius:10px; background:#EEE8E2;">
                <div style="width:{pct}%;height:7px;border-radius:10px;background:{SAGE};"></div>
            </div>
            <div class="small-muted" style="margin-top:5px;">Perfil {pct}% completo</div>
            <div style="margin-top:14px;">
                <strong style="color:{PLUM}; font-size:.82rem;">✦ Tus fortalezas destacadas</strong><br>
                {strength_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_match_ring(score):
    score = max(0, min(100, float(score or 0)))
    return f"""
    <div class="match-ring" style="--pct:{score}%;">
        <span class="match-number">{score:.0f}%</span>
        <span class="match-label">Compatible</span>
    </div>
    """


def render_job_card(uid, job_row, match_row):
    vid = int(job_row.vacante_id)
    score = float(match_row.match_score)
    enabled = bool(match_row.habilitada_postular)
    horario_score = float(match_row.score_horario)
    skill_score = float(match_row.score_habilidades)

    company = job_row.get("empresa_nombre", job_row.get("empresa", "Empresa"))
    title = job_row.get("titulo", "Oportunidad laboral")
    comuna = job_row.get("comuna", job_row.get("empresa_comuna", ""))
    desc = job_row.get("descripcion", "")
    sueldo = job_row.get("sueldo", None)
    schedule = job_row.get("horario", "") or schedule_text(vid)
    course_list = match_row.get("cursos_recomendados", []) or []

    if pd.isna(sueldo) if sueldo is not None else True:
        salary_text = ""
    else:
        try:
            salary_text = f"${float(sueldo):,.0f}".replace(",", ".")
        except Exception:
            salary_text = str(sueldo)

    badges = [
        f'<span class="badge badge-gold">★ {score:.0f}% Compatible</span>'
    ]

    if enabled:
        badges.append('<span class="badge badge-green">🟢 Horario disponible</span>')
    else:
        badges.append('<span class="badge badge-orange">🟠 Revisar horario</span>')

    user = safe_df("SELECT comuna FROM Usuarias WHERE usuaria_id=?", (uid,))
    user_comuna = user.iloc[0].comuna if not user.empty else ""
    prox = proximity_label(user_comuna, comuna)
    if "Misma comuna" in prox:
        badges.append(f'<span class="badge badge-green">{html.escape(prox)}</span>')
    else:
        badges.append(f'<span class="badge badge-orange">{html.escape(prox)}</span>')

    # La brecha se obtiene del motor real.
    if course_list:
        course = course_list[0]
        course_name = str(course.get("nombre", "Curso sugerido"))
        duration = course.get("duracion_horas", "")
        badges.append('<span class="badge badge-orange">🟠 Requiere capacitación</span>')
        course_html = (
            f'<div class="small-muted">📚 Curso sugerido: '
            f'<strong>{html.escape(course_name)}</strong>'
            f'{" (" + str(duration) + " h)" if duration else ""}</div>'
        )
    else:
        course_html = ""

    why = f"""
        <div class="why">
            <div class="why-title">✦ ¿Por qué encaja?</div>
            <div class="why-row"><span>Horario</span><strong>{horario_score*100:.0f}%</strong></div>
            <div class="why-row"><span>Habilidades</span><strong>{skill_score*100:.0f}%</strong></div>
            <div class="why-row"><span>Ubicación</span><strong>{"Compatible" if "Misma comuna" in prox else "Otra comuna"}</strong></div>
            <div class="why-row"><span>Regla de acceso</span><strong>{"Cumple" if enabled else "No cumple"}</strong></div>
        </div>
    """

    safe_title = html.escape(str(title))
    safe_company = html.escape(str(company))
    safe_comuna = html.escape(str(comuna or "Ubicación por confirmar"))
    safe_schedule = html.escape(str(schedule or "Horario por confirmar"))
    safe_desc = html.escape(str(desc or "Oportunidad seleccionada según tu perfil."))

    st.markdown(
        f"""
        <div class="card">
            <div style="display:grid;grid-template-columns:minmax(0,1fr) 115px 190px;gap:16px;align-items:center;">
                <div>
                    <div class="company">{safe_company}</div>
                    <div class="job-title">{safe_title}</div>
                    <div class="job-meta">📍 {safe_comuna} &nbsp;·&nbsp; ◷ {safe_schedule}</div>
                    {f'<div class="job-meta">💰 {html.escape(salary_text)}</div>' if salary_text else ''}
                    <div style="margin-top:7px;">{"".join(badges)}</div>
                    <div class="job-desc">{safe_desc}</div>
                    {course_html}
                </div>
                <div>
                    {render_match_ring(score)}
                </div>
                <div>
                    {why}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    b1, b2, b3 = st.columns([1, 1, 3])
    with b1:
        if st.button("Ver oportunidad →", key=f"view_{vid}"):
            st.session_state[f"show_job_{vid}"] = not st.session_state.get(f"show_job_{vid}", False)
    with b2:
        if enabled:
            if st.button("♡ Postularme", key=f"apply_{vid}"):
                ok, msg = insert_postulation(uid, vid, match_row.to_dict())
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.info(msg)
        else:
            st.button("Horario no compatible", key=f"disabled_{vid}", disabled=True)

    if st.session_state.get(f"show_job_{vid}", False):
        with st.container(border=True):
            st.markdown(f"### {safe_title}")
            st.write(desc or "Esta oportunidad no tiene descripción adicional.")
            required = job_required_skill_names(vid)
            if required:
                st.write("**Habilidades requeridas:** " + " · ".join(required))
            if course_list:
                st.info(
                    "Puedes fortalecer tu perfil con: "
                    + ", ".join(str(c.get("nombre")) for c in course_list)
                )


def render_opportunities(uid):
    jobs = get_jobs()
    matches = match_for_user(uid)

    if jobs.empty:
        st.markdown('<div class="empty">No hay vacantes activas en este momento.</div>', unsafe_allow_html=True)
        return

    merged = jobs.merge(
        matches,
        left_on="vacante_id",
        right_on="vacante_id",
        how="left",
    )

    st.markdown("### Oportunidades para ti")
    st.caption("Vacantes ordenadas por compatibilidad según tu disponibilidad y perfil.")

    f1, f2, f3 = st.columns(3)
    with f1:
        comuna_values = ["Todas"] + sorted(
            [str(x) for x in merged.get("comuna", pd.Series(dtype=str)).dropna().unique()]
        )
        selected_comuna = st.selectbox("📍 Ubicación", comuna_values)
    with f2:
        rubros = ["Todos"] + sorted([str(x) for x in merged.rubro.dropna().unique()])
        selected_rubro = st.selectbox("◷ Rubro", rubros)
    with f3:
        compatibility = st.selectbox(
            "✦ Compatibilidad",
            ["Todas", "80% o más", "60% o más"],
        )

    if selected_comuna != "Todas" and "comuna" in merged.columns:
        merged = merged[merged.comuna.astype(str) == selected_comuna]
    if selected_rubro != "Todos":
        merged = merged[merged.rubro.astype(str) == selected_rubro]
    if compatibility == "80% o más":
        merged = merged[merged.match_score >= 80]
    elif compatibility == "60% o más":
        merged = merged[merged.match_score >= 60]

    merged = merged.sort_values(
        ["habilitada_postular", "match_score"],
        ascending=[False, False],
    )

    if merged.empty:
        st.info("No hay oportunidades con los filtros seleccionados.")
        return

    left, right = st.columns([2.3, 1])

    with left:
        for _, row in merged.iterrows():
            render_job_card(uid, row, row)

    with right:
        render_profile_summary(uid)

        avg = float(merged.match_score.mean()) if not merged.empty else 0
        st.markdown(
            f"""
            <div class="profile-card" style="text-align:center;">
                <div class="section-kicker">Compatibilidad promedio</div>
                {render_match_ring(avg)}
                <div style="color:{MUTED};font-size:.78rem;margin-top:8px;">
                    En base a tu perfil y disponibilidad
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="profile-card">
                <div style="font-size:1.5rem;">💡</div>
                <h3 style="margin:4px 0;">¿Necesitas apoyo?</h3>
                <div class="small-muted">
                    Si una oportunidad te interesa pero tienes una brecha de habilidades,
                    ENCAJA puede mostrarte cursos sugeridos para aumentar tu compatibilidad.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="quote">
                “No se trata solo de encontrar un trabajo,
                sino de encontrar el trabajo que encaje con tu vida.”
                <br><br><span style="font-family:DM Sans;font-size:.75rem;">— ENCAJA</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_home(uid):
    render_hero()
    render_kpis(uid)

    st.markdown("<br>", unsafe_allow_html=True)
    render_opportunities(uid)


def render_profile(uid):
    u = safe_df("SELECT * FROM Usuarias WHERE usuaria_id=?", (uid,))
    if u.empty:
        st.error("No se encontró la usuaria.")
        return
    row = u.iloc[0]

    skills = get_skills()
    practical = skills[skills.tipo_habilidad.fillna("practica") == "practica"]
    strengths = skills[skills.tipo_habilidad.fillna("practica") == "fortaleza_cotidiana"]

    selected = set(get_user_skills(uid).nombre.tolist())

    st.markdown("## Mi perfil")
    st.caption("Capturamos también habilidades y fortalezas que muchas veces no aparecen en un CV tradicional.")

    with st.form("profile_form"):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("Nombre", value=str(row.get("nombre", "")))
            phone = st.text_input("WhatsApp", value=str(row.get("telefono", "") if "telefono" in row.index else ""))
            email = st.text_input("Email", value=str(row.get("email", "")))
        with c2:
            comuna = st.text_input("Comuna", value=str(row.get("comuna", "")))
            address = st.text_input("Dirección", value=str(row.get("direccion", "") if "direccion" in row.index else ""))

        st.markdown("### Habilidades prácticas")
        practical_names = practical.nombre.tolist()
        practical_selected = []
        pc = st.columns(2)
        for i, skill in enumerate(practical_names):
            with pc[i % 2]:
                if st.checkbox(skill, value=skill in selected, key=f"pr_{skill}"):
                    practical_selected.append(skill)

        st.markdown("### <span style='color:#D4AF37;'>✦ Fortalezas cotidianas</span>", unsafe_allow_html=True)
        strength_names = strengths.nombre.tolist()
        strength_selected = []
        sc = st.columns(2)
        for i, skill in enumerate(strength_names):
            with sc[i % 2]:
                if st.checkbox(
                    skill,
                    value=skill in selected,
                    key=f"st_{skill}",
                ):
                    strength_selected.append(skill)

        st.markdown("### Disponibilidad horaria")
        current_schedule = get_user_schedule(uid)
        current_pairs = set(
            (int(r.dia_semana), str(r.bloque))
            for _, r in current_schedule.iterrows()
            if "dia_semana" in current_schedule.columns and "bloque" in current_schedule.columns
        )

        selected_slots = []
        cols_day = st.columns(3)
        for i, (day_num, day_name) in enumerate(DAYS):
            with cols_day[i % 3]:
                st.markdown(f"**{day_name}**")
                for block in BLOCKS:
                    if st.checkbox(
                        block,
                        value=(day_num, block) in current_pairs,
                        key=f"slot_{day_num}_{block}",
                    ):
                        selected_slots.append((day_num, block))

        save = st.form_submit_button("Guardar mi perfil")

    if save:
        ok, msg = upsert_user_profile(uid, name, email, phone, comuna, address)
        if ok:
            save_user_skills(uid, practical_selected + strength_selected)
            save_user_schedule(uid, selected_slots)
            st.success("Tu perfil fue guardado correctamente.")
            st.rerun()
        else:
            st.error(msg)

    st.markdown("---")
    render_profile_summary(uid)


# ============================================================
# EMPRESA
# ============================================================

def get_companies():
    if not table_exists("Empresas"):
        return pd.DataFrame()
    return safe_df("SELECT * FROM Empresas ORDER BY nombre")


def render_company_home():
    companies = get_companies()
    jobs = get_jobs()
    users = get_users()

    st.markdown(
        """
        <div class="company-panel">
            <div class="section-kicker" style="color:#F1D6CE;">Modo empresa</div>
            <h2>Encuentra personas que realmente coincidan con tu oportunidad.</h2>
            <p style="color:rgba(255,255,255,.85);">
                Publica turnos y utiliza ENCAJA para ordenar candidatas según
                disponibilidad y habilidades.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c = st.columns(4)
    stats = [
        ("🏢", "Empresas", len(companies)),
        ("💼", "Vacantes activas", len(jobs)),
        ("👩", "Candidatas", len(users)),
        ("✦", "Postulaciones", len(safe_df("SELECT * FROM Postulaciones"))),
    ]
    for col, (icon, label, val) in zip(c, stats):
        with col:
            st.markdown(
                f"""
                <div class="kpi">
                    <div class="kpi-icon">{icon}</div>
                    <div class="kpi-label">{label}</div>
                    <div class="kpi-value">{val}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("### Tus publicaciones")
    if jobs.empty:
        st.info("Todavía no hay vacantes activas.")
        return

    show = jobs[["vacante_id", "titulo", "rubro", "activa"]].copy()
    show.columns = ["ID", "Vacante", "Rubro", "Activa"]
    st.dataframe(show, use_container_width=True, hide_index=True)


def insert_company(name, rubro, comuna, email):
    try:
        cur = con.execute(
            "INSERT INTO Empresas (nombre,rubro,comuna,contacto_email) VALUES (?,?,?,?)",
            (name.strip(), rubro, comuna.strip(), email.strip()),
        )
        con.commit()
        return cur.lastrowid
    except Exception as e:
        st.error(f"No fue posible crear la empresa: {e}")
        return None


def insert_vacancy(
    empresa_id,
    titulo,
    rubro,
    descripcion,
    comuna,
    direccion,
    horario,
    sueldo,
    requiere_capacitacion,
    curso_sugerido,
    skill_ids,
    blocks,
):
    cols = columns("Vacantes")

    values = {
        "empresa_id": empresa_id,
        "titulo": titulo,
        "rubro": rubro,
        "descripcion": descripcion,
        "fecha_publicacion": str(date.today()),
        "activa": 1,
        "comuna": comuna,
        "direccion": direccion,
        "horario": horario,
        "sueldo": sueldo,
        "requiere_capacitacion": int(requiere_capacitacion),
        "requería_capacitacion": int(requiere_capacitacion),
        "curso_sugerido": curso_sugerido,
    }

    data = {k: v for k, v in values.items() if k in cols}

    try:
        names = ", ".join(qcol(k) for k in data)
        placeholders = ", ".join("?" for _ in data)
        cur = con.execute(
            f"INSERT INTO Vacantes ({names}) VALUES ({placeholders})",
            tuple(data.values()),
        )
        vid = cur.lastrowid

        # Habilidades requeridas
        if table_exists("Vacante_Habilidad"):
            vh_cols = columns("Vacante_Habilidad")
            for hid in skill_ids:
                payload = {}
                if "vacante_id" in vh_cols:
                    payload["vacante_id"] = vid
                elif "id_vacante" in vh_cols:
                    payload["id_vacante"] = vid

                if "habilidad_id" in vh_cols:
                    payload["habilidad_id"] = hid
                elif "id_habilidad" in vh_cols:
                    payload["id_habilidad"] = hid

                if "obligatoria" in vh_cols:
                    payload["obligatoria"] = 1
                elif "nivel_requerido" in vh_cols:
                    payload["nivel_requerido"] = "intermedio"

                n = ", ".join(qcol(k) for k in payload)
                p = ", ".join("?" for _ in payload)
                con.execute(
                    f"INSERT OR IGNORE INTO Vacante_Habilidad ({n}) VALUES ({p})",
                    tuple(payload.values()),
                )

        # Bloques de turno
        if table_exists("Bloques_Vacante"):
            bcols = columns("Bloques_Vacante")
            for day_num, block in blocks:
                start, end = BLOCKS[block]
                payload = {}

                candidates = {
                    "vacante_id": vid,
                    "id_vacante": vid,
                    "dia_semana": day_num,
                    "dia": day_num,
                    "bloque": block,
                    "bloque_horario": block,
                    "hora_inicio": start,
                    "hora_fin": end,
                }
                for k, v in candidates.items():
                    if k in bcols:
                        payload[k] = v

                n = ", ".join(qcol(k) for k in payload)
                p = ", ".join("?" for _ in payload)
                try:
                    con.execute(
                        f"INSERT OR IGNORE INTO Bloques_Vacante ({n}) VALUES ({p})",
                        tuple(payload.values()),
                    )
                except sqlite3.IntegrityError:
                    pass

        con.commit()
        return vid
    except Exception as e:
        con.rollback()
        st.error(f"No fue posible publicar el turno: {e}")
        return None


def render_publish():
    companies = get_companies()
    skills = get_skills()

    st.markdown("## Publicar un turno")
    st.caption("La publicación alimentará directamente la base SQLite.")

    with st.form("publish_form"):
        if not companies.empty:
            company_options = {
                f"{r.nombre} · {r.comuna}": int(r.empresa_id)
                for _, r in companies.iterrows()
            }
            selected_company = st.selectbox("Empresa", list(company_options))
            empresa_id = company_options[selected_company]
        else:
            st.warning("No existen empresas registradas.")
            empresa_id = None

        titulo = st.text_input("Título del turno", placeholder="Ej.: Atención al cliente media jornada")
        rubro_options = ["Gastronomía", "Peluquería", "Administración", "Análisis de Datos"]
        rubro = st.selectbox("Rubro", rubro_options)
        descripcion = st.text_area("Descripción", placeholder="Describe las funciones principales.")
        c1, c2 = st.columns(2)
        with c1:
            comuna = st.text_input("Comuna")
            direccion = st.text_input("Dirección")
        with c2:
            sueldo = st.number_input("Sueldo / pago aproximado", min_value=0.0, step=10000.0)
            requires = st.checkbox("Requiere capacitación")

        course_options = [""] + (
            safe_df("SELECT nombre FROM Cursos ORDER BY nombre").nombre.tolist()
            if table_exists("Cursos") else []
        )
        curso = st.selectbox("Curso sugerido", course_options)

        st.markdown("### Habilidades requeridas")
        skill_selected = []
        if not skills.empty:
            cols = st.columns(2)
            for i, name in enumerate(skills.nombre.tolist()):
                with cols[i % 2]:
                    if st.checkbox(name, key=f"vac_skill_{i}"):
                        skill_selected.append(
                            int(skills[skills.nombre == name].iloc[0].habilidad_id)
                        )

        st.markdown("### Bloques del turno")
        blocks = []
        day_cols = st.columns(3)
        for i, (day_num, day_name) in enumerate(DAYS):
            with day_cols[i % 3]:
                st.markdown(f"**{day_name}**")
                for block in BLOCKS:
                    if st.checkbox(block, key=f"vac_slot_{day_num}_{block}"):
                        blocks.append((day_num, block))

        submitted = st.form_submit_button("Publicar turno")

    if submitted:
        if not empresa_id or not titulo.strip():
            st.error("Debes seleccionar una empresa e ingresar el título.")
        elif not blocks:
            st.error("Selecciona al menos un bloque horario.")
        else:
            horario = " · ".join(
                f"{DAYS[d][1]} {BLOCKS[b][0]}-{BLOCKS[b][1]}"
                for d, b in blocks
            )
            vid = insert_vacancy(
                empresa_id=empresa_id,
                titulo=titulo,
                rubro=rubro,
                descripcion=descripcion,
                comuna=comuna,
                direccion=direccion,
                horario=horario,
                sueldo=sueldo,
                requiere_capacitacion=requires,
                curso_sugerido=curso,
                skill_ids=skill_selected,
                blocks=blocks,
            )
            if vid:
                st.success(f"Turno publicado correctamente. ID de vacante: {vid}")
                st.rerun()

    st.markdown("---")
    st.markdown("### Carga masiva CSV / Excel")

    uploaded = st.file_uploader(
        "Sube un archivo con columnas como: titulo, rubro, descripcion, comuna, direccion, sueldo",
        type=["csv", "xlsx"],
    )

    if uploaded is not None:
        try:
            if uploaded.name.lower().endswith(".csv"):
                bulk = pd.read_csv(uploaded)
            else:
                bulk = pd.read_excel(uploaded)

            st.dataframe(bulk.head(10), use_container_width=True)

            if st.button("Importar publicaciones", key="bulk_import"):
                if companies.empty:
                    st.error("Necesitas al menos una empresa registrada.")
                else:
                    default_company = int(companies.iloc[0].empresa_id)
                    imported = 0
                    for _, r in bulk.iterrows():
                        title = str(r.get("titulo", "")).strip()
                        if not title:
                            continue

                        rubro_val = str(r.get("rubro", "Administración"))
                        if rubro_val not in ["Gastronomía", "Peluquería", "Administración", "Análisis de Datos"]:
                            rubro_val = "Administración"

                        vid = insert_vacancy(
                            empresa_id=default_company,
                            titulo=title,
                            rubro=rubro_val,
                            descripcion=str(r.get("descripcion", "")),
                            comuna=str(r.get("comuna", "")),
                            direccion=str(r.get("direccion", "")),
                            horario=str(r.get("horario", "")),
                            sueldo=float(r.get("sueldo", 0) or 0),
                            requiere_capacitacion=bool(r.get("requiere_capacitacion", False)),
                            curso_sugerido=str(r.get("curso_sugerido", "")),
                            skill_ids=[],
                            blocks=[],
                        )
                        if vid:
                            imported += 1

                    st.success(f"Se importaron {imported} publicaciones.")
                    st.rerun()
        except Exception as e:
            st.error(f"No se pudo leer el archivo: {e}")


def render_candidates():
    jobs = get_jobs()
    users = get_users()

    st.markdown("## Panel de candidatas")
    st.caption("Ordenadas por compatibilidad con cada oportunidad.")

    if jobs.empty:
        st.info("No existen vacantes activas.")
        return

    selected_job = st.selectbox(
        "Selecciona una vacante",
        jobs.vacante_id.tolist(),
        format_func=lambda vid: str(
            jobs.loc[jobs.vacante_id == vid, "titulo"].iloc[0]
        ),
    )

    # Ranking con el mismo motor usado por postulantes.
    # IMPORTANTE: aquí mostramos únicamente a quienes postularon a esta vacante.
    applicant_ids = set()
    if table_exists("Postulaciones"):
        p_uid = first_col("Postulaciones", ["usuaria_id", "id_usuaria"])
        p_vid = first_col("Postulaciones", ["vacante_id", "id_vacante"])
        if p_uid and p_vid:
            rows = con.execute(
                f"SELECT {qcol(p_uid)} FROM Postulaciones WHERE {qcol(p_vid)}=?",
                (int(selected_job),),
            ).fetchall()
            applicant_ids = {int(r[0]) for r in rows}

    if not applicant_ids:
        st.info("Todavía no hay candidatas que hayan postulado a esta vacante.")
        return

    ranking = []
    for _, u in users.iterrows():
        if int(u.usuaria_id) not in applicant_ids:
            continue
        try:
            result = match_one(int(u.usuaria_id), int(selected_job))
            ranking.append({
                "usuaria_id": int(u.usuaria_id),
                "nombre": u.nombre,
                "comuna": u.comuna,
                "email": u.email,
                "telefono": u.get("telefono", ""),
                "match": float(result["match_score"]),
                "horario": float(result["score_horario"]),
                "habilitada": int(result["habilitada_postular"]),
                "brechas": result.get("brechas_habilidad", []),
                "cursos": result.get("cursos_recomendados", []),
            })
        except Exception:
            pass

    rank = pd.DataFrame(ranking)
    if rank.empty:
        st.info("No fue posible calcular candidatas.")
        return

    rank = rank.sort_values(
        ["habilitada", "match"],
        ascending=[False, False],
    )

    for _, candidate in rank.iterrows():
        uid = int(candidate.usuaria_id)
        skills = get_user_skills(uid)
        strengths = (
            skills[skills.tipo_habilidad == "fortaleza_cotidiana"].nombre.tolist()
            if not skills.empty else []
        )

        email = str(candidate.email or "")
        phone = normalize_phone(candidate.telefono)

        mailto = (
            "mailto:" + urllib.parse.quote(email)
            if email else "#"
        )
        wa = (
            "https://wa.me/" + phone
            if phone else "#"
        )

        strength_html = "".join(
            f'<span class="strength">{html.escape(str(s))}</span>'
            for s in strengths[:8]
        )
        if not strength_html:
            strength_html = '<span class="small-muted">Sin fortalezas registradas</span>'

        status = (
            '<span class="badge badge-green">🟢 Horario compatible</span>'
            if candidate.habilitada
            else '<span class="badge badge-orange">🟠 Horario no compatible</span>'
        )

        st.markdown(
            f"""
            <div class="card">
                <div style="display:grid;grid-template-columns:1fr 105px 260px;gap:20px;align-items:center;">
                    <div>
                        <div class="company">CANDIDATA</div>
                        <div class="job-title">{html.escape(str(candidate.nombre))}</div>
                        <div class="job-meta">📍 {html.escape(str(candidate.comuna))} · ✉️ {html.escape(email)}</div>
                        <div>{status}
                            <span class="badge badge-gold">★ {candidate.match:.0f}% Match</span>
                        </div>
                        <div style="margin-top:10px;">
                            <strong style="color:{PLUM};font-size:.78rem;">✦ Fortalezas cotidianas</strong><br>
                            {strength_html}
                        </div>
                    </div>
                    <div>{render_match_ring(candidate.match)}</div>
                    <div>
                        <div class="small-muted" style="margin-bottom:8px;">Contacto directo</div>
                        <a class="contact-btn mail-btn" href="{mailto}" target="_blank">✉ Enviar correo</a>
                        <a class="contact-btn wa-btn" href="{wa}" target="_blank">◉ WhatsApp Directo</a>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# ROUTER
# ============================================================

if role == "Soy Postulante":
    if page == "Inicio":
        render_home(selected_uid)
    elif page == "Mis oportunidades":
        st.markdown("## Mis oportunidades")
        render_opportunities(selected_uid)
    else:
        render_profile(selected_uid)
else:
    if page == "Panel empresa":
        render_company_home()
    elif page == "Publicar turno":
        render_publish()
    else:
        render_candidates()

st.markdown(
    f"""
    <div style="text-align:center;margin-top:35px;padding-top:20px;border-top:1px solid {BORDER};
                color:{MUTED};font-size:.72rem;">
        ENCAJA · El trabajo que encaja con tu vida · Plataforma demostrativa basada en datos
    </div>
    """,
    unsafe_allow_html=True,
)
