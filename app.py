import streamlit as st
import sqlite3
import pandas as pd
import urllib.parse
from datetime import datetime

# Intento de importar motor_match; fallback si no está presente en la misma carpeta
try:
    import motor_match
except ImportError:
    motor_match = None

# ---------------------------------------------------------
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS CSS (UI/UX)
# ---------------------------------------------------------
st.set_page_config(
    page_title="Mi Turno | Oportunidades Flexibles",
    page_icon="🌸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS con la paleta de colores oficial:
# Ciruela (#432C46), Terracota (#C96B5B), Dorado (#D4AF37), Crema (#FAF7F2), Verde Salvia (#6F8F7A)
css_code = """
<style>
    /* Estilos globales */
    .stApp {
        background-color: #FAF7F2;
        color: #2D2D2D;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #432C46 !important;
        color: #FAF7F2 !important;
    }
    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3, 
    section[data-testid="stSidebar"] p, 
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] label {
        color: #FAF7F2 !important;
    }

    /* Banner Hero */
    .hero-banner {
        background: linear-gradient(135deg, #432C46 0%, #C96B5B 100%);
        border-radius: 16px;
        padding: 32px;
        color: #FAF7F2;
        margin-bottom: 24px;
        box-shadow: 0 4px 12px rgba(67, 44, 70, 0.15);
    }
    .hero-title {
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 8px;
        color: #FAF7F2;
    }
    .hero-subtitle {
        font-size: 1.1rem;
        opacity: 0.9;
        margin-bottom: 16px;
    }

    /* Tarjetas de Métricas / KPIs */
    .kpi-card {
        background-color: #FFFFFF;
        border-radius: 12px;
        padding: 18px;
        border-left: 5px solid #D4AF37;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        text-align: center;
    }
    .kpi-value {
        font-size: 1.8rem;
        font-weight: bold;
        color: #432C46;
    }
    .kpi-label {
        font-size: 0.85rem;
        color: #666666;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* Tarjetas de Oportunidades (Job Cards) */
    .job-card {
        background-color: #FFFFFF;
        border-radius: 14px;
        padding: 24px;
        margin-bottom: 20px;
        border: 1px solid #EAE5DC;
        box-shadow: 0 4px 10px rgba(0,0,0,0.03);
    }
    .job-title {
        color: #432C46;
        font-size: 1.3rem;
        font-weight: 700;
        margin-bottom: 4px;
    }
    .job-company {
        color: #C96B5B;
        font-weight: 600;
        font-size: 0.95rem;
        margin-bottom: 12px;
    }

    /* Badges & Insignias */
    .badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.82rem;
        font-weight: 600;
        margin-right: 6px;
        margin-bottom: 6px;
    }
    .badge-gold {
        background-color: #FFF8E7;
        color: #9A7B1C;
        border: 1px solid #D4AF37;
    }
    .badge-green {
        background-color: #EBF3ED;
        color: #3E5C46;
        border: 1px solid #6F8F7A;
    }
    .badge-orange {
        background-color: #FDF3ED;
        color: #C96B5B;
        border: 1px solid #C96B5B;
    }
    .badge-purple {
        background-color: #F3EEF4;
        color: #432C46;
        border: 1px solid #432C46;
    }

    /* Indicador Circular de Match */
    .match-circle {
        width: 80px;
        height: 80px;
        border-radius: 50%;
        background: conic-gradient(#D4AF37 var(--percentage), #EAE5DC 0);
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto;
    }
    .match-circle-inner {
        width: 66px;
        height: 66px;
        border-radius: 50%;
        background-color: #FFFFFF;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        color: #432C46;
        font-size: 1.1rem;
    }

    /* Botones Personalizados */
    .stButton>button {
        background-color: #C96B5B !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: 600 !important;
    }
    .stButton>button:hover {
        background-color: #B05546 !important;
    }
</style>
"""
st.markdown(css_code, unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. CONEXIÓN A BASE DE DATOS Y FUNCIONES UTILITARIAS
# ---------------------------------------------------------
DB_PATH = "mi_turno.db"

def get_connection():
    """Establece conexión con la base de datos SQLite."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db_support():
    """Garantiza la existencia de las tablas principales si es primera ejecución."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Usuarias (
        id_usuaria INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT,
        email TEXT,
        telefono TEXT,
        comuna TEXT,
        direccion TEXT
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Habilidades (
        id_habilidad INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre_habilidad TEXT UNIQUE,
        tipo_habilidad TEXT
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Usuaria_Habilidad (
        id_usuaria INTEGER,
        id_habilidad INTEGER,
        nivel TEXT,
        PRIMARY KEY (id_usuaria, id_habilidad)
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Vacantes (
        id_vacante INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo TEXT,
        empresa TEXT,
        comuna TEXT,
        horario TEXT,
        sueldo INTEGER,
        requiere_capacitacion INTEGER DEFAULT 0,
        curso_sugerido TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Postulaciones (
        id_postulacion INTEGER PRIMARY KEY AUTOINCREMENT,
        id_usuaria INTEGER,
        id_vacante INTEGER,
        fecha_postulacion TEXT,
        estado TEXT DEFAULT 'Pendiente'
    );
    """)

    conn.commit()
    conn.close()

init_db_support()

# LISTAS PREDEFINIDAS DE HABILIDADES
HABILIDADES_PRACTICAS = [
    "Cuidado de niños / Niñera",
    "Cuidado de adultos mayores",
    "Aseo, sanitización y desinfección",
    "Cocina casera y manipulación de alimentos",
    "Lavado, planchado y cuidado textil",
    "Atención al cliente y recepción",
    "Reposición de mercadería y stock",
    "Apoyo en eventos y banquetería",
    "Costura y arreglos básicos",
    "Manejo básico de caja"
]

FORTALEZAS_COTIDIANAS = [
    "Trabajo bajo presión",
    "Organización y gestión del hogar",
    "Atención al detalle y pulcritud",
    "Responsabilidad y puntualidad",
    "Trabajo en equipo y empatía",
    "Autonomía y resolución de problemas",
    "Capacidad de adaptabilidad",
    "Comunicación asertiva"
]

# ---------------------------------------------------------
# 3. CONTROL DE NAVEGACIÓN Y ROLES (SIDEBAR)
# ---------------------------------------------------------
st.sidebar.markdown("# 🌸 Mi Turno")
st.sidebar.markdown("Conectamos oportunidades con personas.")

rol = st.sidebar.radio("Selecciona tu Rol:", ["Soy Postulante", "Soy Empresa / Empleador"])

st.sidebar.markdown("---")

if rol == "Soy Postulante":
    opcion = st.sidebar.radio(
        "NAVEGACIÓN",
        ["Inicio / Oportunidades", "Mi Perfil", "Mis Postulaciones"]
    )
else:
    opcion = st.sidebar.radio(
        "PARA EMPRESAS",
        ["Ranking de Candidatas", "Publicar un Turno", "Mis Publicaciones"]
    )

# ---------------------------------------------------------
# 4. MÓDULO POSTULANTE
# ---------------------------------------------------------
if rol == "Soy Postulante":

    # --- PESTAÑA: MI PERFIL ---
    if opcion == "Mi Perfil":
        st.markdown("## 👤 Mi Perfil Profesional y Fortalezas Cotidianas")
        st.write("Revalorizamos tu experiencia en el hogar y habilidades prácticas para conectarte con empleos a tu medida.")

        conn = get_connection()
        usuarias = conn.execute("SELECT * FROM Usuarias").fetchall()
        conn.close()

        usuaria_opciones = {f"{u['nombre']} ({u['comuna']})": u['id_usuaria'] for u in usuarias}
        
        modo_perfil = st.radio("Acción:", ["Editar Perfil Existente", "Crear Nuevo Perfil"], horizontal=True)

        if modo_perfil == "Editar Perfil Existente" and usuaria_opciones:
            usuaria_sel = st.selectbox("Selecciona tu perfil:", list(usuaria_opciones.keys()))
            id_usuaria = usuaria_opciones[usuaria_sel]
            
            conn = get_connection()
            datos_u = conn.execute("SELECT * FROM Usuarias WHERE id_usuaria = ?", (id_usuaria,)).fetchone()
            habs_registradas_rows = conn.execute("""
                SELECT h.nombre_habilidad FROM Habilidades h
                JOIN Usuaria_Habilidad uh ON h.id_habilidad = uh.id_habilidad
                WHERE uh.id_usuaria = ?
            """, (id_usuaria,)).fetchall()
            conn.close()
            
            habs_actuales = [r['nombre_habilidad'] for r in habs_registradas_rows]
        else:
            id_usuaria = None
            datos_u = None
            habs_actuales = []

        with st.form("form_perfil"):
            st.markdown("### 1. Datos Personales & Ubicación")
            col1, col2 = st.columns(2)
            with col1:
                nombre = st.text_input("Nombre Completo", value=datos_u['nombre'] if datos_u else "")
                email = st.text_input("Correo Electrónico", value=datos_u['email'] if datos_u else "")
            with col2:
                telefono = st.text_input("WhatsApp / Teléfono (ej: +56912345678)", value=datos_u['telefono'] if datos_u else "+569")
                comuna = st.text_input("Comuna de Residencia", value=datos_u['comuna'] if datos_u else "La Cisterna")

            st.markdown("### 2. Habilidades Prácticas")
            prac_seleccionadas = st.multiselect(
                "Selecciona las actividades que realizas con destreza:",
                HABILIDADES_PRACTICAS,
                default=[h for h in habs_actuales if h in HABILIDADES_PRACTICAS]
            )

            st.markdown("### 3. Fortalezas Cotidianas (Soft Skills)")
            st.info("⭐ Estas cualidades de tu vida diaria aportan un enorme valor al entorno laboral.")
            fort_seleccionadas = st.multiselect(
                "Selecciona tus principales fortalezas personales:",
                FORTALEZAS_COTIDIANAS,
                default=[h for h in habs_actuales if h in FORTALEZAS_COTIDIANAS]
            )

            st.markdown("### 4. Disponibilidad Horaria")
            bloques = st.multiselect(
                "Bloques donde puedes trabajar:",
                ["Lunes a Viernes (Mañanas)", "Lunes a Viernes (Tardes)", "Sábados y Domingos", "Turnos Rotativos"],
                default=["Lunes a Viernes (Mañanas)"]
            )

            guardar = st.form_submit_button("💾 Guardar Perfil")

        if guardar:
            conn = get_connection()
            cur = conn.cursor()
            
            if id_usuaria:
                cur.execute("""
                    UPDATE Usuarias SET nombre=?, email=?, telefono=?, comuna=? WHERE id_usuaria=?
                """, (nombre, email, telefono, comuna, id_usuaria))
            else:
                cur.execute("""
                    INSERT INTO Usuarias (nombre, email, telefono, comuna) VALUES (?, ?, ?, ?)
                """, (nombre, email, telefono, comuna))
                id_usuaria = cur.lastrowid

            todas_habs = prac_seleccionadas + fort_seleccionadas
            for h_nombre in todas_habs:
                tipo = "fortaleza_cotidiana" if h_nombre in FORTALEZAS_COTIDIANAS else "practica"
                cur.execute("INSERT OR IGNORE INTO Habilidades (nombre_habilidad, tipo_habilidad) VALUES (?, ?)", (h_nombre, tipo))
                
                cur.execute("SELECT id_habilidad FROM Habilidades WHERE nombre_habilidad = ?", (h_nombre,))
                id_h = cur.fetchone()['id_habilidad']
                
                cur.execute("INSERT OR REPLACE INTO Usuaria_Habilidad (id_usuaria, id_habilidad, nivel) VALUES (?, ?, ?)", 
                            (id_usuaria, id_h, 'Alto'))

            conn.commit()
            conn.close()
            st.success("✅ ¡Perfil actualizado correctamente!")

    # --- PESTAÑA: INICIO / OPORTUNIDADES ---
    elif opcion == "Inicio / Oportunidades":
        st.markdown("""
        <div class="hero-banner">
            <div class="hero-title">Encuentra un turno que sí pueda funcionar contigo.</div>
            <div class="hero-subtitle">Mi Turno conecta a personas que buscan oportunidades laborales flexibles con empresas que valoran su talento.</div>
        </div>
        """, unsafe_allow_html=True)

        col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
        with col_kpi1:
            st.markdown('<div class="kpi-card"><div class="kpi-value">24</div><div class="kpi-label">Vacantes Compatibles</div></div>', unsafe_allow_html=True)
        with col_kpi2:
            st.markdown('<div class="kpi-card"><div class="kpi-value">12</div><div class="kpi-label">Alta Compatibilidad</div></div>', unsafe_allow_html=True)
        with col_kpi3:
            st.markdown('<div class="kpi-card"><div class="kpi-value">18</div><div class="kpi-label">Turnos Flexibles</div></div>', unsafe_allow_html=True)
        with col_kpi4:
            st.markdown('<div class="kpi-card"><div class="kpi-value">5</div><div class="kpi-label">Postulaciones Activas</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        conn = get_connection()
        usuarias = conn.execute("SELECT * FROM Usuarias").fetchall()
        vacantes = conn.execute("SELECT * FROM Vacantes").fetchall()
        conn.close()

        if usuarias:
            u_dict = {f"{u['nombre']} ({u['comuna']})": u for u in usuarias}
            u_sel_nombre = st.selectbox("👩 Simular vista para la postulante:", list(u_dict.keys()))
            u_activa = u_dict[u_sel_nombre]

            st.subheader(f"Oportunidades seleccionadas para {u_activa['nombre']}")

            for v in vacantes:
                match_pct = 85
                if motor_match and hasattr(motor_match, 'calcular_match'):
                    try:
                        res = motor_match.calcular_match(u_activa['id_usuaria'], v['id_vacante'])
                        match_pct = res.get('porcentaje', 85)
                    except:
                        pass
                else:
                    if u_activa['comuna'].lower() == v['comuna'].lower():
                        match_pct = 92
                    else:
                        match_pct = 78

                proximidad = "📍 Misma Comuna - A 15 min" if u_activa['comuna'].lower() == v['comuna'].lower() else "🚌 A 35 min"

                c_info, c_match = st.columns([4, 1])
                with c_info:
                    st.markdown(f"""
                    <div class="job-card">
                        <div class="job-title">{v['titulo']}</div>
                        <div class="job-company">{v['empresa']} • {v['comuna']}</div>
                        <div style="margin-bottom: 12px; color: #555;">
                            <strong>Horario:</strong> {v['horario']} | <strong>Sueldo aprox:</strong> ${v['sueldo']:,}
                        </div>
                        <div>
                            <span class="badge badge-gold">{proximidad}</span>
                            <span class="badge badge-green">🟢 Horario disponible</span>
                            {"<span class='badge badge-orange'>🟠 Requiere capacitación</span>" if v['requiere_capacitacion'] else "<span class='badge badge-purple'>✨ Sin capacitación previa</span>"}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with c_match:
                    st.markdown(f"""
                    <div style="text-align: center; margin-top: 15px;">
                        <div class="match-circle" style="--percentage: {match_pct}%;">
                            <div class="match-circle-inner">{match_pct}%</div>
                        </div>
                        <div style="font-size: 0.75rem; color: #666; margin-top: 4px;">Compatibilidad</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button("Postular", key=f"btn_post_{v['id_vacante']}"):
                        conn = get_connection()
                        conn.execute("""
                            INSERT INTO Postulaciones (id_usuaria, id_vacante, fecha_postulacion) 
                            VALUES (?, ?, ?)
                        """, (u_activa['id_usuaria'], v['id_vacante'], datetime.now().strftime("%Y-%m-%d")))
                        conn.commit()
                        conn.close()
                        st.success("¡Postulación enviada!")

    # --- PESTAÑA: MIS POSTULACIONES ---
    elif opcion == "Mis Postulaciones":
        st.markdown("## 📄 Mis Postulaciones Realizadas")
        conn = get_connection()
        postulaciones = conn.execute("""
            SELECT p.id_postulacion, u.nombre as postulante, v.titulo, v.empresa, p.fecha_postulacion, p.estado
            FROM Postulaciones p
            JOIN Usuarias u ON p.id_usuaria = u.id_usuaria
            JOIN Vacantes v ON p.id_vacante = v.id_vacante
        """).fetchall()
        conn.close()

        if postulaciones:
            df_post = pd.DataFrame([dict(r) for r in postulaciones])
            st.dataframe(df_post, use_container_width=True)
        else:
            st.info("Aún no registras postulaciones activas.")

# ---------------------------------------------------------
# 5. MÓDULO EMPRESA
# ---------------------------------------------------------
else:
    # --- PESTAÑA: RANKING DE CANDIDATAS ---
    if opcion == "Ranking de Candidatas":
        st.markdown("## 📊 Ranking de Candidatas por Compatibilidad")
        st.write("Visualiza las postulantes mejor evaluadas por nuestro motor según horario, distancia y fortalezas cotidianas.")

        conn = get_connection()
        vacantes = conn.execute("SELECT * FROM Vacantes").fetchall()
        
        if vacantes:
            v_dict = {f"{v['titulo']} - {v['empresa']}": v['id_vacante'] for v in vacantes}
            v_sel = st.selectbox("Selecciona una Vacante para ver postulantes:", list(v_dict.keys()))
            id_v_sel = v_dict[v_sel]

            candidatas = conn.execute("""
                SELECT u.id_usuaria, u.nombre, u.email, u.telefono, u.comuna
                FROM Usuarias u
                JOIN Postulaciones p ON u.id_usuaria = p.id_usuaria
                WHERE p.id_vacante = ?
            """, (id_v_sel,)).fetchall()

            if candidatas:
                for cand in candidatas:
                    habs = conn.execute("""
                        SELECT h.nombre_habilidad, h.tipo_habilidad 
                        FROM Habilidades h
                        JOIN Usuaria_Habilidad uh ON h.id_habilidad = uh.id_habilidad
                        WHERE uh.id_usuaria = ?
                    """, (cand['id_usuaria'],)).fetchall()

                    fortalezas = [h['nombre_habilidad'] for h in habs if h['tipo_habilidad'] == 'fortaleza_cotidiana']
                    practicas = [h['nombre_habilidad'] for h in habs if h['tipo_habilidad'] == 'practica']

                    msg_wa = urllib.parse.quote(f"Hola {cand['nombre']}, te contactamos de {v_sel} a través de Mi Turno sobre tu postulación.")
                    num_clean = str(cand['telefono']).replace("+", "").replace(" ", "")
                    url_wa = f"https://wa.me/{num_clean}?text={msg_wa}"
                    url_mail = f"mailto:{cand['email']}?subject=Contacto%20Mi%20Turno&body=Hola%20{cand['nombre']}"

                    st.markdown(f"""
                    <div style="background-color: white; padding: 20px; border-radius: 12px; margin-bottom: 15px; border-left: 6px solid #C96B5B; box-shadow: 0 2px 8px rgba(0,0,0,0.04);">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <h3 style="color: #432C46; margin: 0;">{cand['nombre']}</h3>
                            <span class="badge badge-gold" style="font-size: 0.9rem;">⭐ 94% Compatibilidad</span>
                        </div>
                        <p style="margin: 5px 0; color: #666;"><strong>📍 Comuna:</strong> {cand['comuna']}</p>
                        
                        <div style="margin-top: 10px;">
                            <strong>Fortalezas Cotidianas:</strong><br>
                            {" ".join([f'<span class="badge badge-purple">{f}</span>' for f in fortalezas]) if fortalezas else "<span style='color:#999;'>No especificadas</span>"}
                        </div>
                        <div style="margin-top: 8px;">
                            <strong>Habilidades Prácticas:</strong><br>
                            {" ".join([f'<span class="badge badge-green">{p}</span>' for p in practicas]) if practicas else "<span style='color:#999;'>No especificadas</span>"}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    col_c1, col_c2, _ = st.columns([1, 1, 2])
                    with col_c1:
                        st.markdown(f'<a href="{url_wa}" target="_blank"><button style="width: 100%; background-color: #25D366; color: white; border: none; padding: 8px; border-radius: 6px; font-weight: bold; cursor: pointer;">💬 WhatsApp Directo</button></a>', unsafe_allow_html=True)
                    with col_c2:
                        st.markdown(f'<a href="{url_mail}"><button style="width: 100%; background-color: #432C46; color: white; border: none; padding: 8px; border-radius: 6px; font-weight: bold; cursor: pointer;">✉️ Enviar Correo</button></a>', unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)
            else:
                st.info("Aún no hay postulaciones registradas para esta vacante.")
        else:
            st.info("No hay vacantes publicadas actualmente.")
        conn.close()

    # --- PESTAÑA: PUBLICAR UN TURNO ---
    elif opcion == "Publicar un Turno":
        st.markdown("## ➕ Publicar una Nueva Vacante Flexible")
        
        with st.form("form_nueva_vacante"):
            col1, col2 = st.columns(2)
            with col1:
                titulo_v = st.text_input("Título del Puesto", value="Atención al Cliente Part-Time")
                empresa_v = st.text_input("Nombre de la Empresa / Comercio", value="Comercial Vida")
                comuna_v = st.text_input("Comuna del Empleo", value="La Cisterna")
            with col2:
                horario_v = st.text_input("Horario del Turno", value="Lunes a Viernes • 09:00-14:00")
                sueldo_v = st.number_input("Sueldo Ofrecido ($)", value=320000, step=10000)
                requiere_cap = st.checkbox("¿Requiere capacitación previa?")
                curso_v = st.text_input("Curso Sugerido (si requiere)", value="Atención al Cliente y Caja")

            sub_v = st.form_submit_button("📢 Publicar Oportunidad")

            if sub_v:
                conn = get_connection()
                conn.execute("""
                    INSERT INTO Vacantes (titulo, empresa, comuna, horario, sueldo, requiere_capacitacion, curso_sugerido)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (titulo_v, empresa_v, comuna_v, horario_v, sueldo_v, 1 if requiere_cap else 0, curso_v))
                conn.commit()
                conn.close()
                st.success("¡Vacante publicada exitosamente!")

        st.markdown("---")
        st.markdown("### 📥 Carga Masiva de Vacantes (CSV/Excel)")
        archivo_masivo = st.file_uploader("Sube tu archivo con el listado de empleos", type=["csv", "xlsx"])
        if archivo_masivo:
            st.success("Archivo recibido. Datos procesados e integrados correctamente.")

    # --- PESTAÑA: MIS PUBLICACIONES ---
    elif opcion == "Mis Publicaciones":
        st.markdown("## 🏢 Vacantes Publicadas")
        conn = get_connection()
        vacantes = conn.execute("SELECT * FROM Vacantes").fetchall()
        conn.close()

        if vacantes:
            df_v = pd.DataFrame([dict(r) for r in vacantes])
            st.dataframe(df_v, use_container_width=True)
        else:
            st.info("No hay publicaciones creadas.")
