import streamlit as st
import sqlite3
import pandas as pd
import urllib.parse
from datetime import datetime

# Importación defensiva del motor de compatibilidad
try:
    import motor_match
except ImportError:
    motor_match = None

# ---------------------------------------------------------
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS CSS (PALETA OFICIAL)
# ---------------------------------------------------------
st.set_page_config(
    page_title="Mi Turno | Oportunidades Flexibles",
    page_icon="🌸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Paleta oficial: Ciruela (#432C46), Terracota (#C96B5B), Dorado (#D4AF37), Crema (#FAF7F2), Verde Salvia (#6F8F7A)
css_code = """
<style>
    /* Estilos Globales */
    .stApp {
        background-color: #FAF7F2;
        color: #2D2D2D;
        font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    }

    /* Sidebar Izquierda (Navegación) */
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

    /* Banner Hero Principal */
    .hero-banner {
        background: linear-gradient(135deg, #432C46 0%, #C96B5B 100%);
        border-radius: 16px;
        padding: 28px 32px;
        color: #FAF7F2;
        margin-bottom: 24px;
        box-shadow: 0 4px 14px rgba(67, 44, 70, 0.15);
    }
    .hero-title {
        font-size: 2.1rem;
        font-weight: 700;
        margin-bottom: 8px;
        color: #FAF7F2;
    }
    .hero-subtitle {
        font-size: 1.02rem;
        opacity: 0.92;
    }

    /* Métricas / KPIs */
    .kpi-card {
        background-color: #FFFFFF;
        border-radius: 12px;
        padding: 16px;
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
        font-size: 0.8rem;
        color: #666666;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* Tarjeta de Trabajo (Job Card SaaS) */
    .job-card-container {
        background-color: #FFFFFF;
        border-radius: 14px;
        padding: 20px;
        margin-bottom: 8px;
        border: 1px solid #EAE5DC;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
    }
    .job-title {
        color: #432C46;
        font-size: 1.25rem;
        font-weight: 700;
        margin-bottom: 2px;
    }
    .job-company {
        color: #C96B5B;
        font-weight: 600;
        font-size: 0.9rem;
        margin-bottom: 10px;
    }

    /* Insignias / Badges */
    .badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-right: 6px;
        margin-bottom: 6px;
    }
    .badge-gold { background-color: #FFF8E7; color: #9A7B1C; border: 1px solid #D4AF37; }
    .badge-green { background-color: #EBF3ED; color: #3E5C46; border: 1px solid #6F8F7A; }
    .badge-orange { background-color: #FDF3ED; color: #C96B5B; border: 1px solid #C96B5B; }
    .badge-purple { background-color: #F3EEF4; color: #432C46; border: 1px solid #432C46; }

    /* Indicador Anillo de Match */
    .match-circle {
        width: 76px;
        height: 76px;
        border-radius: 50%;
        background: conic-gradient(#D4AF37 var(--percentage), #EAE5DC 0);
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto;
    }
    .match-circle-inner {
        width: 62px;
        height: 62px;
        border-radius: 50%;
        background-color: #FFFFFF;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        color: #432C46;
        font-size: 1.05rem;
    }

    /* Panel Lateral Derecho (Perfil) */
    .profile-card-right {
        background-color: #FFFFFF;
        border-radius: 14px;
        padding: 20px;
        border: 1px solid #EAE5DC;
        box-shadow: 0 2px 10px rgba(0,0,0,0.03);
    }

    /* Botones */
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
# 2. BASE DE DATOS Y ESTRUCTURA DE TABLAS (PERSISTENTE)
# ---------------------------------------------------------
DB_PATH = "mi_turno.db"

def get_db_cursor():
    """Conexión segura que retorna objetos Row accesibles como diccionarios."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_cursor()
    cur = conn.cursor()
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS Usuarias (
        id_usuaria INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT, email TEXT, telefono TEXT, comuna TEXT, direccion TEXT
    );""")
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS Habilidades (
        id_habilidad INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre_habilidad TEXT UNIQUE, tipo_habilidad TEXT
    );""")
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS Usuaria_Habilidad (
        id_usuaria INTEGER, id_habilidad INTEGER, nivel TEXT,
        PRIMARY KEY (id_usuaria, id_habilidad)
    );""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS Horarios_Disponibles (
        id_disponibilidad INTEGER PRIMARY KEY AUTOINCREMENT,
        id_usuaria INTEGER, bloque_horario TEXT
    );""")
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS Vacantes (
        id_vacante INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo TEXT, empresa TEXT, comuna TEXT, horario TEXT, sueldo INTEGER,
        requiere_capacitacion INTEGER DEFAULT 0, curso_sugerido TEXT
    );""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS Postulaciones (
        id_postulacion INTEGER PRIMARY KEY AUTOINCREMENT,
        id_usuaria INTEGER, id_vacante INTEGER, fecha_postulacion TEXT, estado TEXT DEFAULT 'Pendiente'
    );""")

    # Datos semilla si la base de datos está vacía
    if cur.execute("SELECT COUNT(*) FROM Usuarias").fetchone()[0] == 0:
        cur.execute("INSERT INTO Usuarias (nombre, email, telefono, comuna) VALUES ('Juliana Guzmán', 'juliana@email.com', '+56912345678', 'La Pintana')")
        cur.execute("INSERT INTO Usuarias (nombre, email, telefono, comuna) VALUES ('Camila Soto', 'camila@email.com', '+56987654321', 'Maipú')")

    if cur.execute("SELECT COUNT(*) FROM Vacantes").fetchone()[0] == 0:
        cur.execute("INSERT INTO Vacantes (titulo, empresa, comuna, horario, sueldo, requiere_capacitacion, curso_sugerido) VALUES ('Asistente de ventas', 'Comercial Vida', 'La Cisterna', 'Lunes a viernes • 09:00–14:00', 320000, 0, '')")
        cur.execute("INSERT INTO Vacantes (titulo, empresa, comuna, horario, sueldo, requiere_capacitacion, curso_sugerido) VALUES ('Atención al cliente', 'Servicios Norte', 'El Bosque', 'Sábado y domingo • 10:00–18:00', 180000, 1, 'Atención al cliente (40 hrs)')")
        cur.execute("INSERT INTO Vacantes (titulo, empresa, comuna, horario, sueldo, requiere_capacitacion, curso_sugerido) VALUES ('Apoyo en tienda', 'Mercado Local', 'La Pintana', 'Turnos rotativos', 280000, 1, 'Manipulación de alimentos (8 hrs)')")
        cur.execute("INSERT INTO Vacantes (titulo, empresa, comuna, horario, sueldo, requiere_capacitacion, curso_sugerido) VALUES ('Cuidado de Adulto Mayor', 'Hogar Cálido', 'Maipú', 'Turno Mañana • 08:00-13:00', 350000, 1, 'Atención y cuidado del adulto mayor (40 hrs)')")

    conn.commit()
    conn.close()

init_db()

def parse_vacante(v):
    v_dict = dict(v)
    id_v = v_dict.get('id_vacante') or v_dict.get('id') or 1
    titulo = v_dict.get('titulo') or v_dict.get('nombre_vacante') or 'Oportunidad Flexible'
    empresa = v_dict.get('empresa') or v_dict.get('nombre_empresa') or 'Empresa Aliada'
    comuna = v_dict.get('comuna') or v_dict.get('ubicacion') or 'Santiago'
    horario = v_dict.get('horario') or v_dict.get('jornada') or 'Turnos Flexibles'
    
    sueldo_val = v_dict.get('sueldo') or v_dict.get('pago') or v_dict.get('monto') or 0
    try:
        sueldo = int(sueldo_val)
    except:
        sueldo = 0
        
    req_cap = bool(v_dict.get('requiere_capacitacion') or v_dict.get('capacitacion'))
    curso = v_dict.get('curso_sugerido') or v_dict.get('curso') or ''

    return {
        'id_vacante': id_v,
        'titulo': titulo,
        'empresa': empresa,
        'comuna': comuna,
        'horario': horario,
        'sueldo': sueldo,
        'requiere_capacitacion': req_cap,
        'curso_sugerido': curso
    }

HABILIDADES_PRACTICAS = [
    "Cuidado de niños", "Cuidado de adultos mayores", "Aseo y sanitización", 
    "Cocina casera", "Cuidado textil", "Atención a público", 
    "Reposición y stock", "Apoyo en eventos", "Costura y arreglos", "Manejo de caja"
]

FORTALEZAS_COTIDIANAS = [
    "Trabajo bajo presión", "Organización del hogar", "Atención al detalle", 
    "Responsabilidad y puntualidad", "Trabajo en equipo", "Autonomía", 
    "Adaptabilidad", "Comunicación asertiva"
]

CATALOGO_CURSOS = [
    "Atención al cliente (40 hrs)", "Manipulación de alimentos (8 hrs)",
    "Atención y cuidado del adulto mayor (40 hrs)", "Técnicas de sanitización e higiene institucional (16 hrs)",
    "Caja bancaria y medios de pago digitales (30 hrs)", "Logística de bodega y reposición (20 hrs)"
]

# ---------------------------------------------------------
# 3. SIDEBAR DE NAVEGACIÓN
# ---------------------------------------------------------
st.sidebar.markdown("# 🌸 Mi Turno")
st.sidebar.markdown("<p style='font-size:0.85rem; opacity:0.8;'>Conectamos oportunidades con personas.</p>", unsafe_allow_html=True)

rol = st.sidebar.radio("Selecciona tu Rol:", ["Soy Postulante", "Soy Empresa / Empleador"])
st.sidebar.markdown("---")

if rol == "Soy Postulante":
    opcion = st.sidebar.radio("NAVEGACIÓN", ["Inicio / Oportunidades", "Mi Perfil", "Mis Postulaciones"])
else:
    opcion = st.sidebar.radio("PARA EMPRESAS", ["Ranking de Candidatas", "Publicar un Turno", "Mis Publicaciones"])

# ---------------------------------------------------------
# 4. MÓDULO POSTULANTE
# ---------------------------------------------------------
if rol == "Soy Postulante":

    if opcion == "Inicio / Oportunidades":
        
        st.markdown("""
        <div class="hero-banner">
            <div class="hero-title">Encuentra un turno que sí pueda funcionar contigo.</div>
            <div class="hero-subtitle">Mi Turno conecta a personas que buscan oportunidades laborales flexibles con empresas que valoran su talento.</div>
        </div>
        """, unsafe_allow_html=True)

        conn = get_db_cursor()
        usuarias_rows = conn.execute("SELECT * FROM Usuarias").fetchall()
        vacantes_rows = conn.execute("SELECT * FROM Vacantes").fetchall()
        total_vacantes = len(vacantes_rows)
        conn.close()

        usuarias = [dict(u) for u in usuarias_rows]
        raw_vacantes = [dict(v) for v in vacantes_rows]

        if usuarias:
            u_dict = {f"{u.get('nombre', 'Usuaria')} ({u.get('comuna', 'Sin Comuna')})": u for u in usuarias}
            u_sel_nombre = st.selectbox("👩 Simular vista para la postulante:", list(u_dict.keys()))
            u_activa = u_dict[u_sel_nombre]

            conn = get_db_cursor()
            postulaciones_ids = [p['id_vacante'] for p in conn.execute("SELECT id_vacante FROM Postulaciones WHERE id_usuaria = ?", (u_activa.get('id_usuaria'),)).fetchall()]
            conn.close()

            col_k1, col_k2, col_k3, col_k4 = st.columns(4)
            col_k1.markdown(f'<div class="kpi-card"><div class="kpi-value">{total_vacantes}</div><div class="kpi-label">Vacantes Disponibles</div></div>', unsafe_allow_html=True)
            col_k2.markdown('<div class="kpi-card"><div class="kpi-value">12</div><div class="kpi-label">Alta Compatibilidad</div></div>', unsafe_allow_html=True)
            col_k3.markdown('<div class="kpi-card"><div class="kpi-value">18</div><div class="kpi-label">Turnos Flexibles</div></div>', unsafe_allow_html=True)
            col_k4.markdown(f'<div class="kpi-card"><div class="kpi-value">{len(postulaciones_ids)}</div><div class="kpi-label">Mis Postulaciones</div></div>', unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            col_main, col_right = st.columns([2.8, 1.2])

            with col_main:
                st.markdown(f"### Oportunidades seleccionadas para {u_activa.get('nombre')}")

                for idx, raw_v in enumerate(raw_vacantes):
                    v = parse_vacante(raw_v)
                    
                    comuna_u = str(u_activa.get('comuna', '')).strip().lower()
                    comuna_v = str(v['comuna']).strip().lower()

                    if motor_match and hasattr(motor_match, 'calcular_match'):
                        try:
                            res = motor_match.calcular_match(u_activa.get('id_usuaria'), v['id_vacante'])
                            match_pct = res.get('porcentaje', 85)
                        except:
                            match_pct = 92 if comuna_u == comuna_v else 78
                    else:
                        match_pct = 92 if comuna_u == comuna_v else 78

                    proximidad = "📍 Misma comuna - A 15 min" if comuna_u == comuna_v else "🚌 A 35 min"

                    c_card, c_ring, c_why = st.columns([2.2, 0.9, 1.3])

                    with c_card:
                        sueldo_str = f"${v['sueldo']:,}" if v['sueldo'] > 0 else "A convenir"
                        st.markdown(f"""
                        <div class="job-card-container">
                            <div class="job-title">{v['titulo']}</div>
                            <div class="job-company">{v['empresa']} • {v['comuna']}</div>
                            <div style="font-size: 0.88rem; color: #555; margin-bottom: 8px;">
                                🕒 {v['horario']} | 💰 {sueldo_str} approx.
                            </div>
                            <div>
                                <span class="badge badge-gold">{proximidad}</span>
                                <span class="badge badge-green">🟢 Horario disponible</span>
                                {"<span class='badge badge-orange'>🟠 Requiere capacitación</span>" if v['requiere_capacitacion'] else "<span class='badge badge-purple'>✨ Sin capacitación previa</span>"}
                            </div>
                            {f"<div style='font-size:0.78rem; color:#C96B5B; margin-top:6px;'>📚 <i>Curso sugerido: {v['curso_sugerido']}</i></div>" if v['requiere_capacitacion'] and v['curso_sugerido'] else ""}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        btn_key = f"btn_postular_{idx}_{v['id_vacante']}"
                        ya_postulo = v['id_vacante'] in postulaciones_ids

                        if ya_postulo:
                            st.button("✔ Postulado", key=btn_key, disabled=True)
                        else:
                            if st.button("Postular a Oportunidad", key=btn_key):
                                conn = get_db_cursor()
                                conn.execute("INSERT INTO Postulaciones (id_usuaria, id_vacante, fecha_postulacion) VALUES (?, ?, ?)",
                                             (u_activa.get('id_usuaria'), v['id_vacante'], datetime.now().strftime("%Y-%m-%d")))
                                conn.commit()
                                conn.close()
                                st.success("¡Postulación enviada exitosamente!")
                                st.rerun()

                    with c_ring:
                        st.markdown(f"""
                        <div style="text-align: center; margin-top: 10px;">
                            <div class="match-circle" style="--percentage: {match_pct}%;">
                                <div class="match-circle-inner">{match_pct}%</div>
                            </div>
                            <div style="font-size: 0.75rem; color: #666; margin-top: 6px; font-weight:600;">Compatible</div>
                        </div>
                        """, unsafe_allow_html=True)

                    with c_why:
                        st.markdown(f"""
                        <div style="background:#FFFFFF; padding:12px; border-radius:10px; border:1px solid #EAE5DC; font-size:0.75rem;">
                            <strong>✨ ¿Por qué encaja?</strong><br>
                            ✔️ Horario: 30%<br>
                            ✔️ Ubicación: 25%<br>
                            ✔️ Habilidades: 20%<br>
                            ✔️ Experiencia: 15%
                        </div>
                        """, unsafe_allow_html=True)

                    st.markdown("<br>", unsafe_allow_html=True)

            with col_right:
                conn = get_db_cursor()
                forts_db = conn.execute("""
                    SELECT h.nombre_habilidad 
                    FROM Habilidades h
                    JOIN Usuaria_Habilidad uh ON h.id_habilidad = uh.id_habilidad
                    WHERE uh.id_usuaria = ? AND h.tipo_habilidad = 'fortaleza_cotidiana'
                """, (u_activa.get('id_usuaria'),)).fetchall()
                conn.close()

                list_forts = [f['nombre_habilidad'] for f in forts_db] if forts_db else ["Responsabilidad", "Trabajo en equipo", "Organización"]
                badges_html = "".join([f'<span class="badge badge-gold">{f}</span>' for f in list_forts])

                st.markdown(f"""
                <div class="profile-card-right">
                    <h3 style="color:#432C46; margin-top:0;">Tu perfil profesional</h3>
                    <p style="font-size:0.9rem; margin-bottom:4px;"><strong>{u_activa.get('nombre')}</strong></p>
                    <p style="font-size:0.8rem; color:#666;">📍 {u_activa.get('comuna')} | ✉ {u_activa.get('email')}</p>
                    <br>
                    <div style="background-color: #EBF3ED; padding: 6px 12px; border-radius: 20px; font-size: 0.8rem; color: #3E5C46; font-weight: bold; display: inline-block; margin-bottom: 15px;">
                        ✔ Perfil 85% completo
                    </div>
                    <br><br>
                    <h4 style="color:#432C46; font-size:0.9rem; margin-bottom:6px;">⭐ Tus fortalezas destacadas</h4>
                    <div>
                        {badges_html}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                st.markdown("""
                <div style="background-color: #FFF8E7; padding: 16px; border-radius: 12px; border: 1px solid #D4AF37;">
                    <h4 style="margin:0 0 6px 0; color:#432C46; font-size:0.9rem;">💡 ¿Necesitas apoyo?</h4>
                    <p style="font-size:0.8rem; color:#555; margin:0;">Toma cursos sugeridos para aumentar tu porcentaje de compatibilidad con mejores turnos.</p>
                </div>
                """, unsafe_allow_html=True)

    elif opcion == "Mi Perfil":
        st.markdown("## 👤 Mi Perfil y Captura de Talento")
        st.write("Registra tus datos de contacto, habilidades prácticas e identifícate con tus fortalezas cotidianas.")

        conn = get_db_cursor()
        usuarias_list = [dict(u) for u in conn.execute("SELECT * FROM Usuarias").fetchall()]
        conn.close()

        u_opts = {f"{u['nombre']} ({u['comuna']})": u['id_usuaria'] for u in usuarias_list}
        modo = st.radio("Acción:", ["Editar Perfil Existente", "Crear Nuevo Perfil"], horizontal=True)

        if modo == "Editar Perfil Existente" and u_opts:
            sel_u = st.selectbox("Selecciona tu perfil:", list(u_opts.keys()))
            id_u = u_opts[sel_u]
            conn = get_db_cursor()
            datos_u = dict(conn.execute("SELECT * FROM Usuarias WHERE id_usuaria = ?", (id_u,)).fetchone())
            conn.close()
        else:
            id_u = None
            datos_u = {}

        with st.form("form_perfil_full"):
            col1, col2 = st.columns(2)
            with col1:
                nombre = st.text_input("Nombre Completo", value=datos_u.get('nombre', ''))
                email = st.text_input("Correo Electrónico", value=datos_u.get('email', ''))
            with col2:
                telefono = st.text_input("WhatsApp (ej: +56912345678)", value=datos_u.get('telefono', '+569'))
                comuna = st.text_input("Comuna de residencia", value=datos_u.get('comuna', 'La Cisterna'))

            st.markdown("### 🧩 Habilidades Prácticas (Selecciona las que dominas)")
            pracs_sel = st.multiselect("Actividades prácticas:", HABILIDADES_PRACTICAS)

            st.markdown("### ✦ Fortalezas Cotidianas / Soft Skills")
            forts_sel = st.multiselect("Destaca tus cualidades cotidianas:", FORTALEZAS_COTIDIANAS)

            st.markdown("### 🕐 Disponibilidad Horaria por Bloques")
            bloques_sel = st.multiselect(
                "Selecciona los bloques en que podrías realizar un turno:",
                ["Lunes a Viernes (Mañanas 08:00–14:00)", "Lunes a Viernes (Tardes 14:00–20:00)", "Fines de Semana (Sábado/Domingo)", "Noches / Turnos Rotativos"],
                default=["Lunes a Viernes (Mañanas 08:00–14:00)"]
            )

            if st.form_submit_button("💾 Guardar Mi Perfil"):
                conn = get_db_cursor()
                cur = conn.cursor()
                if id_u:
                    cur.execute("UPDATE Usuarias SET nombre=?, email=?, telefono=?, comuna=? WHERE id_usuaria=?",
                                (nombre, email, telefono, comuna, id_u))
                else:
                    cur.execute("INSERT INTO Usuarias (nombre, email, telefono, comuna) VALUES (?, ?, ?, ?)",
                                (nombre, email, telefono, comuna))
                    id_u = cur.lastrowid

                cur.execute("DELETE FROM Usuaria_Habilidad WHERE id_usuaria=?", (id_u,))
                cur.execute("DELETE FROM Horarios_Disponibles WHERE id_usuaria=?", (id_u,))

                for h in pracs_sel:
                    cur.execute("INSERT OR IGNORE INTO Habilidades (nombre_habilidad, tipo_habilidad) VALUES (?, 'practica')", (h,))
                    cur.execute("SELECT id_habilidad FROM Habilidades WHERE nombre_habilidad=?", (h,))
                    hid = cur.fetchone()['id_habilidad']
                    cur.execute("INSERT INTO Usuaria_Habilidad (id_usuaria, id_habilidad, nivel) VALUES (?, ?, 'Alto')", (id_u, hid))

                for f in forts_sel:
                    cur.execute("INSERT OR IGNORE INTO Habilidades (nombre_habilidad, tipo_habilidad) VALUES (?, 'fortaleza_cotidiana')", (f,))
                    cur.execute("SELECT id_habilidad FROM Habilidades WHERE nombre_habilidad=?", (f,))
                    hid = cur.fetchone()['id_habilidad']
                    cur.execute("INSERT INTO Usuaria_Habilidad (id_usuaria, id_habilidad, nivel) VALUES (?, ?, 'Alto')", (id_u, hid))

                for b in bloques_sel:
                    cur.execute("INSERT INTO Horarios_Disponibles (id_usuaria, bloque_horario) VALUES (?, ?)", (id_u, b))

                conn.commit()
                conn.close()
                st.success("✅ ¡Tu perfil ha sido guardado e integrado exitosamente en la base de datos!")

    elif opcion == "Mis Postulaciones":
        st.markdown("## 📋 Mis Postulaciones")
        conn = get_db_cursor()
        posts = [dict(p) for p in conn.execute("""
            SELECT p.id_postulacion, u.nombre as Postulante, v.titulo as Vacante, v.empresa as Empresa, v.comuna as Comuna, p.fecha_postulacion as Fecha
            FROM Postulaciones p
            JOIN Usuarias u ON p.id_usuaria = u.id_usuaria
            JOIN Vacantes v ON p.id_vacante = v.id_vacante
        """).fetchall()]
        conn.close()
        if posts:
            st.dataframe(pd.DataFrame(posts), use_container_width=True)
        else:
            st.info("Aún no registradas postulaciones.")

# ---------------------------------------------------------
# 5. MÓDULO EMPRESA
# ---------------------------------------------------------
else:
    if opcion == "Ranking de Candidatas":
        st.markdown("## 📊 Ranking de Candidatas por Vacante")
        conn = get_db_cursor()
        vacantes_list = [dict(v) for v in conn.execute("SELECT * FROM Vacantes").fetchall()]

        if vacantes_list:
            v_opts = {f"{v.get('titulo')} - {v.get('empresa')}": v.get('id_vacante') for v in vacantes_list}
            v_sel = st.selectbox("Selecciona una Vacante para ver las postulantes:", list(v_opts.keys()))
            id_v = v_opts[v_sel]

            candidatas = [dict(c) for c in conn.execute("""
                SELECT u.id_usuaria, u.nombre, u.email, u.telefono, u.comuna
                FROM Usuarias u
                JOIN Postulaciones p ON u.id_usuaria = p.id_usuaria
                WHERE p.id_vacante = ?
            """, (id_v,)).fetchall()]

            if candidatas:
                for idx_c, cand in enumerate(candidatas):
                    forts_db = conn.execute("""
                        SELECT h.nombre_habilidad 
                        FROM Habilidades h
                        JOIN Usuaria_Habilidad uh ON h.id_habilidad = uh.id_habilidad
                        WHERE uh.id_usuaria = ? AND h.tipo_habilidad = 'fortaleza_cotidiana'
                    """, (cand['id_usuaria'],)).fetchall()
                    
                    list_forts = [f['nombre_habilidad'] for f in forts_db] if forts_db else ["Responsabilidad", "Organización", "Autonomía"]
                    forts_badges = "".join([f'<span class="badge badge-gold">{f}</span>' for f in list_forts])

                    num_clean = str(cand.get('telefono', '')).replace("+", "").replace(" ", "")
                    msg = urllib.parse.quote(f"Hola {cand.get('nombre')}, te contactamos de {v_sel} sobre tu postulación en Mi Turno.")
                    url_wa = f"https://wa.me/{num_clean}?text={msg}"
                    url_mail = f"mailto:{cand.get('email')}?subject=Contacto%20Mi%20Turno"

                    st.markdown(f"""
                    <div style="background:white; padding:18px; border-radius:12px; border-left:6px solid #C96B5B; margin-bottom:12px; box-shadow:0 2px 8px rgba(0,0,0,0.04);">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <h3 style="margin:0; color:#432C46;">{cand.get('nombre')}</h3>
                            <span class="badge badge-gold">⭐ Match Efectivo</span>
                        </div>
                        <p style="margin:4px 0; font-size:0.85rem; color:#666;">📍 Comuna: {cand.get('comuna')} | ✉ {cand.get('email')}</p>
                        <div style="margin-top:6px;">
                            <strong>Fortalezas:</strong> {forts_badges}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    col_b1, col_b2, _ = st.columns([1.2, 1.2, 2.6])
                    with col_b1:
                        st.markdown(f'<a href="{url_wa}" target="_blank"><button style="width:100%; background-color:#25D366; color:white; border:none; padding:8px; border-radius:6px; font-weight:bold; cursor:pointer;">💬 WhatsApp Directo</button></a>', unsafe_allow_html=True)
                    with col_b2:
                        st.markdown(f'<a href="{url_mail}"><button style="width:100%; background-color:#432C46; color:white; border:none; padding:8px; border-radius:6px; font-weight:bold; cursor:pointer;">✉ Enviar Correo</button></a>', unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)
            else:
                st.info("Aún no hay postulantes para esta vacante.")
        else:
            st.info("No existen vacantes registradas.")
        conn.close()

    elif opcion == "Publicar un Turno":
        st.markdown("## ➕ Publicar una Nueva Vacante")
        with st.form("form_vacante"):
            col1, col2 = st.columns(2)
            with col1:
                titulo = st.text_input("Título del Puesto", value="Atención al Cliente Part-Time")
                empresa = st.text_input("Nombre de la Empresa", value="Comercial Vida")
                comuna = st.text_input("Comuna del empleo", value="La Cisterna")
            with col2:
                horario = st.text_input("Horario / Jornada", value="Lunes a Viernes • 09:00–14:00")
                sueldo = st.number_input("Sueldo Estimado ($)", value=320000, step=10000)
                req_cap = st.checkbox("¿Requiere capacitación previa?")
                curso = st.selectbox("Curso Sugerido", CATALOGO_CURSOS)

            if st.form_submit_button("📢 Publicar Turno"):
                conn = get_db_cursor()
                conn.execute("""
                    INSERT INTO Vacantes (titulo, empresa, comuna, horario, sueldo, requiere_capacitacion, curso_sugerido)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (titulo, empresa, comuna, horario, sueldo, 1 if req_cap else 0, curso))
                conn.commit()
                conn.close()
                st.success("¡Vacante creada con éxito y disponible de inmediato!")

        st.markdown("---")
        st.markdown("### 📥 Carga Masiva de Vacantes (CSV o Excel)")
        st.write("Sube un archivo con las columnas: `titulo`, `empresa`, `comuna`, `horario`, `sueldo`, `requiere_capacitacion`, `curso_sugerido`")
        up = st.file_uploader("Subir listado", type=["csv", "xlsx"])
        if up:
            try:
                df = pd.read_csv(up) if up.name.endswith(".csv") else pd.read_excel(up)
                conn = get_db_cursor()
                for _, row in df.iterrows():
                    conn.execute("""
                        INSERT INTO Vacantes (titulo, empresa, comuna, horario, sueldo, requiere_capacitacion, curso_sugerido)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        row.get('titulo', 'Puesto Flexible'),
                        row.get('empresa', 'Empresa Aliada'),
                        row.get('comuna', 'Santiago'),
                        row.get('horario', 'Flexibles'),
                        int(row.get('sueldo', 0)),
                        int(row.get('requiere_capacitacion', 0)),
                        row.get('curso_sugerido', '')
                    ))
                conn.commit()
                conn.close()
                st.success(f"✅ ¡Se cargaron {len(df)} vacantes masivamente en la base de datos `mi_turno.db`!")
            except Exception as e:
                st.error(f"Error procesando el archivo: {e}")

    elif opcion == "Mis Publicaciones":
        st.markdown("## 🏢 Vacantes Registradas en el Sistema")
        conn = get_db_cursor()
        vacs = [dict(v) for v in conn.execute("SELECT * FROM Vacantes").fetchall()]
        conn.close()
        if vacs:
            st.dataframe(pd.DataFrame(vacs), use_container_width=True)
        else:
            st.info("No hay vacantes actualmente publicadas.")
