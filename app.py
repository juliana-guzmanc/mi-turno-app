import streamlit as st

# ============================================================
# CONFIGURACIÓN
# ============================================================

st.set_page_config(
    page_title="Mi Turno",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# PALETA
# ============================================================

CIRUELA = "#432C46"
TERRACOTA = "#C96B5B"
CREMA = "#FAF7F2"
VERDE = "#6F8F7A"
AMBAR = "#D69A45"
CARBON = "#2E3035"
GRIS = "#6B6E73"
BLANCO = "#FFFFFF"
BORDE = "#E8E1DC"


# ============================================================
# CSS GLOBAL
# ============================================================

st.markdown(
    f"""
    <style>

    /* -------------------------------------------------------
       CONFIGURACIÓN GENERAL
    ------------------------------------------------------- */

    .stApp {{
        background-color: {CREMA};
        color: {CARBON};
    }}

    .main .block-container {{
        max-width: 1250px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }}

    html, body, [class*="css"] {{
        font-family: "Inter", "Segoe UI", sans-serif;
    }}

    /* Ocultar elementos nativos */
    #MainMenu {{
        visibility: hidden;
    }}

    footer {{
        visibility: hidden;
    }}

    header {{
        background: transparent !important;
    }}


    /* -------------------------------------------------------
       SIDEBAR
    ------------------------------------------------------- */

    section[data-testid="stSidebar"] {{
        background: {CIRUELA};
        border-right: none;
    }}

    section[data-testid="stSidebar"] > div {{
        padding: 1.5rem 1rem;
    }}

    .sidebar-logo {{
        color: {BLANCO};
        font-size: 1.65rem;
        font-weight: 800;
        margin-bottom: 0.15rem;
        letter-spacing: -0.5px;
    }}

    .sidebar-subtitle {{
        color: #D9CBD8;
        font-size: 0.82rem;
        margin-bottom: 2rem;
    }}

    .sidebar-section {{
        color: #BFAEBE;
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin: 1.5rem 0 0.6rem 0;
    }}

    /* Botones sidebar */
    section[data-testid="stSidebar"] .stButton > button {{
        width: 100%;
        border: none;
        border-radius: 10px;
        background: transparent;
        color: #EDE4EC;
        text-align: left;
        padding: 0.65rem 0.8rem;
        font-weight: 500;
        transition: all 0.2s ease;
    }}

    section[data-testid="stSidebar"] .stButton > button:hover {{
        background: rgba(255,255,255,0.10);
        color: white;
    }}


    /* -------------------------------------------------------
       HERO
    ------------------------------------------------------- */

    .hero {{
        background:
            linear-gradient(
                135deg,
                {CIRUELA} 0%,
                #5A3B58 55%,
                {TERRACOTA} 140%
            );

        border-radius: 24px;
        padding: 2.8rem 3rem;
        margin-bottom: 1.8rem;
        position: relative;
        overflow: hidden;
        box-shadow: 0 15px 40px rgba(67,44,70,0.15);
    }}

    .hero::after {{
        content: "";
        position: absolute;
        width: 280px;
        height: 280px;
        border-radius: 50%;
        background: rgba(255,255,255,0.06);
        right: -70px;
        top: -100px;
    }}

    .hero-eyebrow {{
        color: #E7D8E4;
        font-size: 0.78rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-bottom: 0.7rem;
    }}

    .hero-title {{
        color: white;
        font-size: 2.6rem;
        line-height: 1.08;
        font-weight: 800;
        letter-spacing: -1.2px;
        margin: 0;
        max-width: 700px;
    }}

    .hero-text {{
        color: #F0E8EF;
        font-size: 1rem;
        line-height: 1.6;
        margin-top: 1rem;
        max-width: 650px;
    }}


    /* -------------------------------------------------------
       TÍTULOS
    ------------------------------------------------------- */

    .section-title {{
        color: {CIRUELA};
        font-size: 1.45rem;
        font-weight: 800;
        margin-top: 1.5rem;
        margin-bottom: 0.2rem;
    }}

    .section-description {{
        color: {GRIS};
        font-size: 0.9rem;
        margin-bottom: 1rem;
    }}


    /* -------------------------------------------------------
       MÉTRICAS
    ------------------------------------------------------- */

    .metric-card {{
        background: {BLANCO};
        border: 1px solid {BORDE};
        border-radius: 16px;
        padding: 1.15rem 1.25rem;
        box-shadow: 0 5px 18px rgba(67,44,70,0.06);
        min-height: 105px;
    }}

    .metric-label {{
        color: {GRIS};
        font-size: 0.78rem;
        font-weight: 600;
        margin-bottom: 0.35rem;
    }}

    .metric-value {{
        color: {CIRUELA};
        font-size: 1.8rem;
        font-weight: 800;
    }}

    .metric-small {{
        color: {VERDE};
        font-size: 0.75rem;
        font-weight: 600;
        margin-top: 0.2rem;
    }}


    /* -------------------------------------------------------
       CARDS DE VACANTES
    ------------------------------------------------------- */

    .job-card {{
        background: {BLANCO};
        border: 1px solid {BORDE};
        border-radius: 18px;
        padding: 1.35rem;
        margin-bottom: 1rem;
        box-shadow: 0 6px 22px rgba(67,44,70,0.07);
        transition: all 0.2s ease;
    }}

    .job-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 12px 28px rgba(67,44,70,0.11);
        border-color: #D8C8D4;
    }}

    .job-company {{
        color: {TERRACOTA};
        font-size: 0.75rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.8px;
    }}

    .job-title {{
        color: {CIRUELA};
        font-size: 1.18rem;
        font-weight: 800;
        margin: 0.25rem 0 0.7rem 0;
    }}

    .job-info {{
        color: {GRIS};
        font-size: 0.82rem;
        margin: 0.3rem 0;
    }}

    .job-description {{
        color: #55585D;
        font-size: 0.84rem;
        line-height: 1.5;
        margin-top: 0.7rem;
    }}


    /* -------------------------------------------------------
       BADGES
    ------------------------------------------------------- */

    .badge {{
        display: inline-block;
        border-radius: 999px;
        padding: 0.34rem 0.65rem;
        font-size: 0.72rem;
        font-weight: 700;
        margin-right: 0.3rem;
        margin-top: 0.45rem;
    }}

    .badge-match {{
        background: #F1E6F0;
        color: {CIRUELA};
    }}

    .badge-success {{
        background: #E7F1EA;
        color: #4F745E;
    }}

    .badge-warning {{
        background: #F9EEDC;
        color: #9A6A27;
    }}

    .badge-neutral {{
        background: #F0F0F1;
        color: #65676B;
    }}


    /* -------------------------------------------------------
       COMPATIBILIDAD
    ------------------------------------------------------- */

    .compatibility {{
        background: #F8F4F7;
        border-radius: 14px;
        padding: 0.9rem;
        text-align: center;
        border: 1px solid #EDE3EB;
    }}

    .compatibility-number {{
        color: {CIRUELA};
        font-size: 1.65rem;
        font-weight: 800;
    }}

    .compatibility-label {{
        color: {GRIS};
        font-size: 0.7rem;
        font-weight: 600;
    }}


    /* -------------------------------------------------------
       BOTONES PRINCIPALES
    ------------------------------------------------------- */

    .stButton > button {{
        border-radius: 10px;
        border: 1px solid {CIRUELA};
        background: {CIRUELA};
        color: white;
        font-weight: 700;
        padding: 0.55rem 1.1rem;
        transition: all 0.2s ease;
    }}

    .stButton > button:hover {{
        background: #5A3B58;
        border-color: #5A3B58;
        transform: translateY(-1px);
    }}


    /* -------------------------------------------------------
       FILTROS
    ------------------------------------------------------- */

    div[data-baseweb="select"] > div {{
        border-radius: 10px;
        border-color: {BORDE};
        background: white;
    }}

    div[data-baseweb="input"] > div {{
        border-radius: 10px;
        border-color: {BORDE};
    }}


    /* -------------------------------------------------------
       PERFIL
    ------------------------------------------------------- */

    .profile-card {{
        background: white;
        border: 1px solid {BORDE};
        border-radius: 18px;
        padding: 1.5rem;
        box-shadow: 0 6px 22px rgba(67,44,70,0.06);
    }}

    .profile-name {{
        color: {CIRUELA};
        font-size: 1.25rem;
        font-weight: 800;
    }}

    .profile-text {{
        color: {GRIS};
        font-size: 0.82rem;
        line-height: 1.5;
    }}


    /* -------------------------------------------------------
       SECCIÓN EMPRESAS
    ------------------------------------------------------- */

    .employer-card {{
        background: linear-gradient(135deg, #FFFFFF, #F7F0F5);
        border: 1px solid #E6D9E2;
        border-radius: 20px;
        padding: 1.6rem;
        box-shadow: 0 8px 25px rgba(67,44,70,0.06);
    }}

    .employer-title {{
        color: {CIRUELA};
        font-size: 1.2rem;
        font-weight: 800;
    }}

    .employer-text {{
        color: {GRIS};
        line-height: 1.55;
        font-size: 0.85rem;
    }}

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        """
        <div class="sidebar-logo">✦ Mi Turno</div>
        <div class="sidebar-subtitle">
            Conectamos oportunidades con personas.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="sidebar-section">Navegación</div>',
        unsafe_allow_html=True
    )

    st.button("⌂  Inicio", use_container_width=True)
    st.button("◷  Mis oportunidades", use_container_width=True)
    st.button("♡  Guardados", use_container_width=True)
    st.button("◉  Mi perfil", use_container_width=True)

    st.markdown(
        '<div class="sidebar-section">Para empresas</div>',
        unsafe_allow_html=True
    )

    st.button("＋  Publicar un turno", use_container_width=True)
    st.button("▣  Mis publicaciones", use_container_width=True)


# ============================================================
# HERO
# ============================================================

st.markdown(
    """
    <div class="hero">

        <div class="hero-eyebrow">
            Oportunidades que se adaptan a tu realidad
        </div>

        <div class="hero-title">
            Encuentra un turno que sí pueda funcionar contigo.
        </div>

        <div class="hero-text">
            Mi Turno conecta a personas que buscan oportunidades
            laborales flexibles con empresas que necesitan talento.
        </div>

    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# MÉTRICAS
# ============================================================

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(
        """
        <div class="metric-card">
            <div class="metric-label">Vacantes compatibles</div>
            <div class="metric-value">24</div>
            <div class="metric-small">↑ 6 esta semana</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col2:
    st.markdown(
        """
        <div class="metric-card">
            <div class="metric-label">Alta compatibilidad</div>
            <div class="metric-value">12</div>
            <div class="metric-small">80% o más</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col3:
    st.markdown(
        """
        <div class="metric-card">
            <div class="metric-label">Turnos flexibles</div>
            <div class="metric-value">18</div>
            <div class="metric-small">Disponibles ahora</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col4:
    st.markdown(
        """
        <div class="metric-card">
            <div class="metric-label">Postulaciones</div>
            <div class="metric-value">5</div>
            <div class="metric-small">En seguimiento</div>
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# TÍTULO
# ============================================================

st.markdown(
    """
    <div class="section-title">
        Oportunidades para ti
    </div>

    <div class="section-description">
        Vacantes seleccionadas según tu disponibilidad y perfil.
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# FILTROS
# ============================================================

f1, f2, f3 = st.columns(3)

with f1:
    comuna = st.selectbox(
        "📍 Ubicación",
        ["Todas", "La Pintana", "El Bosque", "La Cisterna"]
    )

with f2:
    modalidad = st.selectbox(
        "◷ Tipo de turno",
        ["Todos", "Part-time", "Fin de semana", "Flexible"]
    )

with f3:
    compatibilidad = st.selectbox(
        "✦ Compatibilidad",
        ["Todas", "80% o más", "70% o más", "60% o más"]
    )


st.markdown("<br>", unsafe_allow_html=True)


# ============================================================
# DATOS DE EJEMPLO
# Reemplazar posteriormente por tus datos reales
# ============================================================

vacantes = [
    {
        "empresa": "Comercial Vida",
        "cargo": "Asistente de ventas",
        "ubicacion": "La Cisterna",
        "turno": "Lunes a viernes · 09:00–14:00",
        "sueldo": "$320.000 aprox.",
        "compatibilidad": 92,
        "horario": "Disponible",
        "capacitacion": False
    },
    {
        "empresa": "Servicios Norte",
        "cargo": "Atención al cliente",
        "ubicacion": "El Bosque",
        "turno": "Sábado y domingo · 10:00–18:00",
        "sueldo": "$180.000 aprox.",
        "compatibilidad": 84,
        "horario": "Disponible",
        "capacitacion": True
    },
    {
        "empresa": "Mercado Local",
        "cargo": "Apoyo en tienda",
        "ubicacion": "La Pintana",
        "turno": "Turnos rotativos",
        "sueldo": "$280.000 aprox.",
        "compatibilidad": 73,
        "horario": "Revisar disponibilidad",
        "capacitacion": True
    }
]


# ============================================================
# TARJETAS
# ============================================================

for vacante in vacantes:

    col_info, col_score = st.columns([4.5, 1])

    with col_info:

        badges = ""

        badges += f"""
        <span class="badge badge-match">
            ✦ {vacante['compatibilidad']}% Compatible
        </span>
        """

        if vacante["horario"] == "Disponible":
            badges += """
            <span class="badge badge-success">
                ● Horario disponible
            </span>
            """
        else:
            badges += """
            <span class="badge badge-warning">
                ◷ Revisar horario
            </span>
            """

        if vacante["capacitacion"]:
            badges += """
            <span class="badge badge-warning">
                ● Requiere capacitación
            </span>
            """

        st.markdown(
            f"""
            <div class="job-card">

                <div class="job-company">
                    {vacante['empresa']}
                </div>

                <div class="job-title">
                    {vacante['cargo']}
                </div>

                <div class="job-info">
                    📍 {vacante['ubicacion']}
                    &nbsp;&nbsp;•&nbsp;&nbsp;
                    ◷ {vacante['turno']}
                </div>

                <div class="job-info">
                    💰 {vacante['sueldo']}
                </div>

                <div>
                    {badges}
                </div>

                <div class="job-description">
                    Esta oportunidad coincide con parte importante
                    de tu disponibilidad y perfil.
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )

        b1, b2 = st.columns([1, 1])

        with b1:
            st.button(
                "Ver oportunidad",
                key=f"ver_{vacante['cargo']}",
                use_container_width=True
            )

        with b2:
            st.button(
                "♡ Guardar",
                key=f"guardar_{vacante['cargo']}",
                use_container_width=True
            )

    with col_score:

        st.markdown(
            f"""
            <div class="compatibility">

                <div class="compatibility-label">
                    COMPATIBILIDAD
                </div>

                <div class="compatibility-number">
                    {vacante['compatibilidad']}%
                </div>

                <div class="compatibility-label">
                    según tu perfil
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )


# ============================================================
# SECCIÓN PERFIL
# ============================================================

st.markdown(
    """
    <div class="section-title">
        Tu perfil
    </div>

    <div class="section-description">
        Mantén actualizada tu información para encontrar mejores coincidencias.
    </div>
    """,
    unsafe_allow_html=True
)

p1, p2 = st.columns([2, 1])

with p1:

    st.markdown(
        """
        <div class="profile-card">

            <div class="profile-name">
                Tu perfil profesional
            </div>

            <div class="profile-text">
                Hemos considerado tu experiencia, habilidades,
                disponibilidad horaria y ubicación para calcular
                la compatibilidad con cada oportunidad.
            </div>

            <br>

            <span class="badge badge-success">
                ✓ Perfil 85% completo
            </span>

            <span class="badge badge-match">
                ✦ 6 habilidades registradas
            </span>

        </div>
        """,
        unsafe_allow_html=True
    )

with p2:

    st.markdown(
        """
        <div class="profile-card">

            <div class="metric-label">
                DISPONIBILIDAD
            </div>

            <div class="metric-value">
                Part-time
            </div>

            <div class="metric-small">
                Lunes a viernes
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# EMPRESAS
# ============================================================

st.markdown("<br>", unsafe_allow_html=True)

st.markdown(
    """
    <div class="employer-card">

        <div class="employer-title">
            ¿Eres empresa o empleador?
        </div>

        <div class="employer-text">
            Publica tus turnos y encuentra personas que realmente
            coincidan con los horarios y requisitos de tu oportunidad.
            Menos tiempo filtrando. Más coincidencias relevantes.
        </div>

    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("<br>", unsafe_allow_html=True)

st.button(
    "＋ Publicar un turno",
    use_container_width=False
)


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    f"""
    <div style="
        text-align:center;
        color:#8A8589;
        font-size:0.75rem;
        margin-top:3rem;
        padding-top:1.5rem;
        border-top:1px solid {BORDE};
    ">
        <strong style="color:{CIRUELA};">Mi Turno</strong>
        · Oportunidades que se adaptan a tu realidad.
    </div>
    """,
    unsafe_allow_html=True
)
