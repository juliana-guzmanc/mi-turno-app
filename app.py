# -*- coding: utf-8 -*-
"""
ENCAJA - app.py (Streamlit)
Requiere: streamlit>=1.35, pandas, openpyxl (solo para carga masiva en Excel)
Ejecutar:  streamlit run app.py
"""
import re
import sqlite3
from contextlib import contextmanager
from html import escape as esc
from urllib.parse import quote

import pandas as pd
import streamlit as st

try:
    import motor_match  # tu motor existente
except Exception:
    motor_match = None

DB_PATH = "mi_turno.db"
MARCA = "ENCAJA"

DIAS = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
BLOQUES = {"Mañana": "08:00-13:00", "Tarde": "13:00-18:00", "Noche": "18:00-22:00"}

HAB_PRACTICAS = [
    "Cuidado de niños", "Cuidado de adultos mayores", "Aseo/Sanitización", "Cocina",
    "Cuidado textil", "Atención a público", "Reposición/Stock", "Apoyo en eventos",
    "Costura", "Manejo de caja",
]
FORTALEZAS = [
    "Trabajo bajo presión", "Organización del hogar", "Atención al detalle",
    "Responsabilidad/Puntualidad", "Trabajo en equipo", "Autonomía",
    "Adaptabilidad", "Comunicación asertiva",
]

# Proximidad: minutos estimados cuando es la misma comuna y tabla editable entre comunas.
MIN_MISMA_COMUNA = 15
TIEMPOS_MIN = {
    # ("La Cisterna", "El Bosque"): 25,
}

C_CIRUELA, C_TERRACOTA, C_DORADO = "#432C46", "#C96B5B", "#D4AF37"

# ----------------------------------------------------------------------------
# Base de datos
# ----------------------------------------------------------------------------
@contextmanager
def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        yield con
        con.commit()
    finally:
        con.close()


def q(sql, params=()):
    with db() as con:
        return pd.read_sql_query(sql, con, params=params)


SCHEMA = """
CREATE TABLE IF NOT EXISTS Usuarias (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, whatsapp TEXT, email TEXT, comuna TEXT);
CREATE TABLE IF NOT EXISTS Vacantes (id INTEGER PRIMARY KEY AUTOINCREMENT, empresa TEXT, titulo TEXT, comuna TEXT, sueldo INTEGER, horario_texto TEXT);
CREATE TABLE IF NOT EXISTS Habilidades (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, tipo TEXT);
CREATE TABLE IF NOT EXISTS Usuaria_Habilidad (usuaria_id INTEGER, habilidad_id INTEGER, nivel INTEGER DEFAULT 1);
CREATE TABLE IF NOT EXISTS Vacante_Habilidad (vacante_id INTEGER, habilidad_id INTEGER);
CREATE TABLE IF NOT EXISTS Horarios_Disponibles (usuaria_id INTEGER, dia TEXT, bloque TEXT);
CREATE TABLE IF NOT EXISTS Bloques_Vacante (vacante_id INTEGER, dia TEXT, bloque TEXT);
CREATE TABLE IF NOT EXISTS Cursos (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, horas INTEGER, habilidad_id INTEGER);
CREATE TABLE IF NOT EXISTS Postulaciones (id INTEGER PRIMARY KEY AUTOINCREMENT, usuaria_id INTEGER, vacante_id INTEGER,
    fecha TEXT DEFAULT CURRENT_TIMESTAMP, UNIQUE(usuaria_id, vacante_id));
"""
COLUMNAS_EXTRA = {
    "Usuarias": {"whatsapp": "TEXT", "email": "TEXT", "comuna": "TEXT"},
    "Vacantes": {"empresa": "TEXT", "titulo": "TEXT", "comuna": "TEXT", "sueldo": "INTEGER", "horario_texto": "TEXT"},
    "Habilidades": {"tipo": "TEXT"},
}


PKS = {"Usuarias": "id", "Vacantes": "id", "Habilidades": "id", "Cursos": "id"}
RUBROS = ["Gastronomía", "Peluquería", "Administración", "Análisis de Datos"]
RUBRO_DE = {"Cocina": "Gastronomía", "Apoyo en eventos": "Gastronomía", "Aseo/Sanitización": "Gastronomía"}
RUBRO_DEFECTO = "Administración"   # solo para cumplir el CHECK de tu tabla Habilidades
OPCIONALES = {"rubro"}             # columnas que se omiten si la tabla no las tiene


def pu(): return PKS["Usuarias"]
def pv(): return PKS["Vacantes"]
def ph(): return PKS["Habilidades"]


def detectar_pks():
    with db() as con:
        for t in PKS:
            pks = [r["name"] for r in con.execute(f"PRAGMA table_info({t})") if r["pk"]]
            if pks:
                PKS[t] = pks[0]


def _valor_defecto(con, tabla, col):
    ddl = con.execute("SELECT sql FROM sqlite_master WHERE name=?", (tabla,)).fetchone()
    m = re.search(rf"CHECK\s*\(\s*{col['name']}\s+IN\s*\(([^)]*)\)", (ddl[0] if ddl else "") or "", re.I)
    if m:
        return m.group(1).split(",")[0].strip().strip("'\"")
    return 0 if "INT" in (col["type"] or "").upper() else "General"


def insertar(con, tabla, datos):
    """INSERT que respeta columnas NOT NULL/CHECK de la tabla existente. Devuelve el rowid."""
    cols = {c["name"]: c for c in con.execute(f"PRAGMA table_info({tabla})")}
    datos = {k: v for k, v in datos.items() if k in cols or k not in OPCIONALES}
    for nombre, c in cols.items():
        if nombre in datos or c["pk"]:
            continue
        if c["notnull"] and c["dflt_value"] is None:
            datos[nombre] = _valor_defecto(con, tabla, c)
    nombres = list(datos)
    cur = con.execute(f"INSERT INTO {tabla}({','.join(nombres)}) VALUES({','.join('?' * len(nombres))})",
                      list(datos.values()))
    return cur.lastrowid


def _insertar_habilidad(con, nombre, tipo):
    if con.execute("SELECT 1 FROM Habilidades WHERE lower(nombre)=lower(?)", (nombre,)).fetchone():
        return
    insertar(con, "Habilidades", {"nombre": nombre, "tipo": tipo, "rubro": RUBRO_DE.get(nombre, RUBRO_DEFECTO)})


def mostrar_esquema():
    with st.expander("🔧 Esquema de la base de datos", expanded=True):
        with db() as con:
            ddl = [r[0] for r in con.execute("SELECT sql FROM sqlite_master WHERE type='table' AND sql IS NOT NULL")]
        st.code(";\n\n".join(ddl), language="sql")


@st.cache_resource
def ensure_schema():
    with db() as con:
        con.executescript(SCHEMA)
        for tabla, cols in COLUMNAS_EXTRA.items():
            existentes = {r["name"] for r in con.execute(f"PRAGMA table_info({tabla})")}
            for col, tipo in cols.items():
                if col not in existentes:
                    con.execute(f"ALTER TABLE {tabla} ADD COLUMN {col} {tipo}")
        for lista, tipo in ((HAB_PRACTICAS, "practica"), (FORTALEZAS, "fortaleza")):
            for nombre in lista:
                _insertar_habilidad(con, nombre, tipo)
    return True


# ----------------------------------------------------------------------------
# Motor de match (usa motor_match.py si responde; si no, cálculo interno)
# ----------------------------------------------------------------------------
def _engine_df(uid):
    if motor_match is None:
        return None
    for nombre in ("calcular_match", "calcular_match_usuaria", "calcular_matches", "match_usuaria"):
        fn = getattr(motor_match, nombre, None)
        if not callable(fn):
            continue
        for args in ((uid,), (DB_PATH, uid), (uid, DB_PATH)):
            try:
                out = fn(*args)
                if isinstance(out, pd.DataFrame) and "vacante_id" in out.columns:
                    return out
            except Exception:
                continue
    return None


def _match_interno(uid):
    h_u = set(q("SELECT dia, bloque FROM Horarios_Disponibles WHERE usuaria_id=?", (uid,)).itertuples(index=False, name=None))
    s_u = set(q("SELECT habilidad_id FROM Usuaria_Habilidad WHERE usuaria_id=?", (uid,))["habilidad_id"])
    filas = []
    for vid in q(f"SELECT {pv()} AS id FROM Vacantes")["id"]:
        b_v = set(q("SELECT dia, bloque FROM Bloques_Vacante WHERE vacante_id=?", (vid,)).itertuples(index=False, name=None))
        s_v = set(q("SELECT habilidad_id FROM Vacante_Habilidad WHERE vacante_id=?", (vid,))["habilidad_id"])
        sh = len(b_v & h_u) / len(b_v) if b_v else 0.0
        ss = len(s_v & s_u) / len(s_v) if s_v else 1.0
        ok = sh >= 1.0                      # regla: solo postula si el horario calza 100%
        ms = round(0.6 * sh + 0.4 * ss, 2) if ok else 0.0
        filas.append({"vacante_id": vid, "score_horario": sh, "score_habilidades": ss,
                      "match_score": ms, "habilitada_postular": int(ok)})
    return pd.DataFrame(filas, columns=["vacante_id", "score_horario", "score_habilidades", "match_score", "habilitada_postular"])


def match_df(uid):
    df = _engine_df(uid)
    return df if df is not None else _match_interno(uid)


def curso_sugerido(uid, vid):
    if motor_match is not None:
        for nombre in ("sugerir_curso", "curso_sugerido", "recomendar_curso"):
            fn = getattr(motor_match, nombre, None)
            if callable(fn):
                try:
                    r = fn(uid, vid)
                    if isinstance(r, dict):
                        return f"{r.get('nombre', r.get('curso', ''))} ({r.get('horas', '?')} h)"
                    if r:
                        return str(r)
                except Exception:
                    pass
    try:
        d = q("""SELECT c.nombre, c.horas FROM Cursos c
                 JOIN Vacante_Habilidad vh ON vh.habilidad_id = c.habilidad_id
                 WHERE vh.vacante_id=? AND c.habilidad_id NOT IN
                   (SELECT habilidad_id FROM Usuaria_Habilidad WHERE usuaria_id=?) LIMIT 1""", (vid, uid))
        if not d.empty:
            return f"{d.iloc[0]['nombre']} ({d.iloc[0]['horas']} h)"
    except Exception:
        pass
    return None


# ----------------------------------------------------------------------------
# Utilidades
# ----------------------------------------------------------------------------
def horario_legible(vid, fallback=None):
    b = q("SELECT dia, bloque FROM Bloques_Vacante WHERE vacante_id=?", (vid,))
    if b.empty:
        return fallback or "Horario por definir"
    partes = []
    for bloque in BLOQUES:
        dias = [d for d in DIAS if ((b["dia"] == d) & (b["bloque"] == bloque)).any()]
        if dias:
            partes.append(f"{', '.join(dias)} ({bloque})")
    return " | ".join(partes)


def sueldo_fmt(s):
    try:
        return f"${int(s):,}".replace(",", ".") + " aprox."
    except Exception:
        return "Sueldo a convenir"


def proximidad(c_user, c_vac):
    if not c_user or not c_vac:
        return "📍 Distancia no disponible"
    a, b = c_user.strip(), c_vac.strip()
    if a.lower() == b.lower():
        return f"📍 A ~{MIN_MISMA_COMUNA} min - Misma comuna"
    m = TIEMPOS_MIN.get((a, b)) or TIEMPOS_MIN.get((b, a))
    return f"📍 A {m} min - {esc(b)}" if m else f"📍 Otra comuna ({esc(b)})"


def wa_numero(raw):
    d = re.sub(r"\D", "", raw or "")
    if len(d) == 9 and d.startswith("9"):
        return "56" + d
    if len(d) == 8:
        return "569" + d
    return d


def split_lista(s):
    return [x.strip() for x in str(s).split(";") if x.strip()]


def insertar_bloques(con, vid, dias, bloques):
    for d in dias:
        for b in bloques:
            if d in DIAS and b in BLOQUES:
                con.execute("INSERT INTO Bloques_Vacante(vacante_id, dia, bloque) VALUES(?,?,?)", (vid, d, b))


def insertar_requisitos(con, vid, habilidades):
    for h in habilidades:
        fila = con.execute(f"SELECT {ph()} AS id FROM Habilidades WHERE lower(nombre)=lower(?)", (h,)).fetchone()
        if fila:
            con.execute("INSERT INTO Vacante_Habilidad(vacante_id, habilidad_id) VALUES(?,?)", (vid, fila["id"]))


def calcular_tabla(uid):
    v = q(f"SELECT {pv()} AS id, empresa, titulo, comuna, sueldo, horario_texto FROM Vacantes")
    m = match_df(uid)
    df = v.merge(m, left_on="id", right_on="vacante_id", how="left")
    for col in ("score_horario", "score_habilidades", "match_score", "habilitada_postular"):
        if col not in df:
            df[col] = 0
        df[col] = df[col].fillna(0)
    blend = 0.6 * df["score_horario"] + 0.4 * df["score_habilidades"]
    df["pct"] = (100 * df["match_score"].where(df["match_score"] > 0, blend)).round().astype(int)
    return df.sort_values("pct", ascending=False).reset_index(drop=True)


# ----------------------------------------------------------------------------
# Estilos
# ----------------------------------------------------------------------------
CSS = """
<style>
:root{--ciruela:#432C46;--terracota:#C96B5B;--dorado:#D4AF37;--crema:#FAF7F2}
.stApp{background:var(--crema)}
h1,h2,h3{color:var(--ciruela)!important;font-weight:800!important}
[data-testid="stSidebar"]{background:var(--ciruela)}
[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] label,[data-testid="stSidebar"] p,[data-testid="stSidebar"] span,
[data-testid="stSidebar"] div[role="radiogroup"] *{color:#FAF7F2!important}
[data-testid="stSidebar"] [data-baseweb="select"] *{color:#2b1a2e!important}
button[data-testid="stBaseButton-primary"],button[data-testid="stBaseButton-primaryFormSubmit"]{
  background:var(--terracota)!important;border:0!important;color:#fff!important;border-radius:999px!important;font-weight:700}
button[data-testid="stBaseButton-secondary"],a[data-testid="stBaseLinkButton-secondary"]{
  border:1.5px solid var(--terracota)!important;color:var(--terracota)!important;background:#fff!important;border-radius:999px!important}
[data-testid="stVerticalBlockBorderWrapper"]{background:#fff;border-radius:16px;box-shadow:0 4px 18px rgba(67,44,70,.10);border-color:#efe6e0}
.hero{background:linear-gradient(120deg,var(--ciruela),#7a4456 70%,var(--terracota));color:#FAF7F2;border-radius:18px;padding:30px 34px;margin-bottom:18px}
.hero h1{color:#FAF7F2!important;margin:0 0 6px;font-size:2.1rem}
.hero p{margin:0;opacity:.92}
.kpi{background:#fff;border-radius:16px;box-shadow:0 4px 18px rgba(67,44,70,.10);padding:16px 18px}
.kpi b{display:block;font-size:2rem;color:var(--ciruela)}
.kpi span{color:#6b5575;font-size:.85rem}
.kpi.gold b{color:var(--dorado)}
.badge{display:inline-block;font-size:.78rem;font-weight:700;border-radius:999px;padding:4px 11px;margin:6px 6px 0 0;background:#f4e8ee;color:var(--ciruela)}
.b-ok{background:#e1f2e8;color:#2f7a5b}.b-warn{background:#fbe9d6;color:#b4651b}
.b-gold{background:#f7ecc4;color:#7a6110;border:1px solid var(--dorado)}
.b-prox{background:#e8eef7;color:#2f4b78}
.ring{width:84px;height:84px;border-radius:50%;display:grid;place-items:center;
  background:conic-gradient(var(--c) calc(var(--p)*1%),#eadfe0 0)}
.ring span{width:64px;height:64px;border-radius:50%;background:#fff;display:grid;place-items:center;font-weight:800;color:var(--ciruela)}
.stars{color:var(--dorado);letter-spacing:2px;text-align:center;font-size:.95rem}
.vt{font-size:1.1rem;font-weight:800;color:var(--ciruela)}.vm{color:#6b5575;font-size:.88rem}
.st-key-fortalezas{background:#fbf5df;border:1px solid var(--dorado);border-radius:14px;padding:12px 16px}
.st-key-fortalezas [data-baseweb="checkbox"] [aria-checked="true"]+div,
.st-key-fortalezas label[data-baseweb="checkbox"]>span:first-child{border-color:var(--dorado)!important}
</style>
"""


def ring_html(pct):
    color = C_DORADO if pct >= 80 else C_TERRACOTA if pct >= 60 else "#a99aa8"
    estrellas = "★" * max(1, round(pct / 20)) if pct >= 40 else "☆"
    return (f"<div class='ring' style='--p:{pct};--c:{color}'><span>{pct}%</span></div>"
            f"<div class='stars'>{estrellas}</div><div class='vm' style='text-align:center'>Compatible</div>")


# ----------------------------------------------------------------------------
# Vistas Postulante
# ----------------------------------------------------------------------------
def tarjeta_vacante(r, uid, comuna_user, prefijo):
    ya = not q("SELECT 1 FROM Postulaciones WHERE usuaria_id=? AND vacante_id=?", (uid, int(r["id"]))).empty
    curso = curso_sugerido(uid, int(r["id"])) if r["score_habilidades"] < 1 else None
    bloqueada = not bool(r["habilitada_postular"])
    badges = []
    badges.append("<span class='badge b-prox'>" + proximidad(comuna_user, r["comuna"]) + "</span>")
    badges.append("<span class='badge b-warn'>🔒 Horario no calza</span>" if bloqueada
                  else "<span class='badge b-ok'>🟢 Horario disponible</span>")
    if r["score_habilidades"] < 1:
        extra = f": {esc(curso)}" if curso else ""
        badges.append(f"<span class='badge b-warn'>🟠 Requiere capacitación{extra}</span>")
    if r["pct"] >= 80:
        badges.append("<span class='badge b-gold'>★ Alta compatibilidad</span>")
    with st.container(border=True):
        a, b = st.columns([5, 1.3])
        a.markdown(
            f"<div class='vm'>{esc(str(r['empresa'] or ''))}</div><div class='vt'>{esc(str(r['titulo'] or ''))}</div>"
            f"<div class='vm'>{esc(str(r['comuna'] or ''))} · {esc(horario_legible(int(r['id']), r['horario_texto']))}</div>"
            f"<div class='vm'>{sueldo_fmt(r['sueldo'])}</div>" + "".join(badges), unsafe_allow_html=True)
        b.markdown(ring_html(int(r["pct"])), unsafe_allow_html=True)
        c1, c2, _ = st.columns([1.3, 1, 4])
        if ya:
            c1.button("✅ Postulada", key=f"{prefijo}_p_{r['id']}", disabled=True)
        elif c1.button("Postular", key=f"{prefijo}_p_{r['id']}", type="primary", disabled=bloqueada):
            with db() as con:
                con.execute("INSERT OR IGNORE INTO Postulaciones(usuaria_id, vacante_id) VALUES(?,?)", (uid, int(r["id"])))
            st.toast("¡Postulación enviada!", icon="🎉")
            st.rerun()
        guardados = st.session_state.setdefault(f"g_{uid}", set())
        if int(r["id"]) in guardados:
            if c2.button("Quitar", key=f"{prefijo}_g_{r['id']}"):
                guardados.discard(int(r["id"]))
                st.rerun()
        elif c2.button("♡ Guardar", key=f"{prefijo}_g_{r['id']}"):
            guardados.add(int(r["id"]))
            st.toast("Guardado")
            st.rerun()


def page_inicio(uid):
    u = q(f"SELECT nombre, comuna FROM Usuarias WHERE {pu()}=?", (uid,)).iloc[0]
    st.markdown(f"<div class='hero'><h1>Hola, {esc(str(u['nombre']))}. Encuentra un turno que sí encaje contigo.</h1>"
                f"<p>{MARCA} conecta a personas que buscan trabajo flexible con empresas que necesitan talento.</p></div>",
                unsafe_allow_html=True)
    df = calcular_tabla(uid)
    n_post = int(q("SELECT COUNT(*) n FROM Postulaciones WHERE usuaria_id=?", (uid,)).iloc[0]["n"])
    k = st.columns(4)
    datos = [("Vacantes compatibles", int((df["pct"] >= 50).sum()), ""), ("Alta compatibilidad", int((df["pct"] >= 80).sum()), "gold"),
             ("Turnos publicados", len(df), ""), ("Postulaciones", n_post, "")]
    for col, (t, v, cls) in zip(k, datos):
        col.markdown(f"<div class='kpi {cls}'><b>{v}</b><span>{t}</span></div>", unsafe_allow_html=True)

    st.subheader("Oportunidades para ti")
    f1, f2, f3 = st.columns(3)
    comunas = ["Todas"] + sorted(x for x in df["comuna"].dropna().unique())
    fc = f1.selectbox("Ubicación", comunas)
    ft = f2.selectbox("Tipo de turno", ["Todos", *BLOQUES, "Fin de semana"])
    fm = f3.selectbox("Compatibilidad", ["Todas", "80% o más", "60% o más"])
    if fc != "Todas":
        df = df[df["comuna"] == fc]
    if ft != "Todos":
        bv = q("SELECT vacante_id, dia, bloque FROM Bloques_Vacante")
        sub = bv[bv["dia"].isin(["Sáb", "Dom"])] if ft == "Fin de semana" else bv[bv["bloque"] == ft]
        df = df[df["id"].isin(sub["vacante_id"])]
    if fm != "Todas":
        df = df[df["pct"] >= int(fm.split("%")[0])]
    if df.empty:
        st.info("No hay vacantes con esos filtros.")
    for _, r in df.iterrows():
        tarjeta_vacante(r, uid, u["comuna"], "ini")


def page_guardados(uid):
    st.subheader("Guardados")
    u = q(f"SELECT comuna FROM Usuarias WHERE {pu()}=?", (uid,)).iloc[0]
    ids = st.session_state.get(f"g_{uid}", set())
    df = calcular_tabla(uid)
    df = df[df["id"].isin(ids)]
    if df.empty:
        st.info("Aún no guardas ningún turno.")
    for _, r in df.iterrows():
        tarjeta_vacante(r, uid, u["comuna"], "gua")


def page_perfil():
    st.subheader("Mi perfil")
    st.caption("Cuéntanos lo que ya sabes hacer: toda experiencia cuenta.")
    us = q(f"SELECT {pu()} AS id, nombre FROM Usuarias ORDER BY nombre")
    ids = [None] + us["id"].tolist()
    nombres = dict(zip(us["id"], us["nombre"]))
    idx = ids.index(st.session_state.get("uid")) if st.session_state.get("uid") in ids else 0
    sel = st.selectbox("Perfil a editar", ids, index=idx,
                       format_func=lambda i: "➕ Nueva postulante" if i is None else nombres[i])
    datos = {"nombre": "", "whatsapp": "", "email": "", "comuna": ""}
    hab_sel, hor_sel = set(), set()
    if sel is not None:
        datos.update({k: (v or "") for k, v in q(f"SELECT nombre, whatsapp, email, comuna FROM Usuarias WHERE {pu()}=?", (sel,)).iloc[0].items()})
        hab_sel = set(q(f"SELECT h.nombre FROM Usuaria_Habilidad uh JOIN Habilidades h ON h.{ph()}=uh.habilidad_id WHERE uh.usuaria_id=?", (sel,))["nombre"])
        hor_sel = set(q("SELECT dia, bloque FROM Horarios_Disponibles WHERE usuaria_id=?", (sel,)).itertuples(index=False, name=None))
    k = f"_{sel}"
    with st.form("form_perfil"):
        c1, c2 = st.columns(2)
        nombre = c1.text_input("Nombre", datos["nombre"], key="nom" + k)
        comuna = c2.text_input("Comuna", datos["comuna"], key="com" + k)
        whatsapp = c1.text_input("WhatsApp (ej: +56 9 1234 5678)", datos["whatsapp"], key="wsp" + k)
        email = c2.text_input("Email", datos["email"], key="mail" + k)

        st.markdown("##### Habilidades prácticas")
        cols = st.columns(3)
        practicas = [h for i, h in enumerate(HAB_PRACTICAS)
                     if cols[i % 3].checkbox(h, value=h in hab_sel, key=f"hp{k}_{i}")]

        st.markdown("##### Fortalezas cotidianas")
        try:
            caja = st.container(key="fortalezas")
        except TypeError:
            caja = st.container()
        with caja:
            cols = st.columns(2)
            fortalezas = [h for i, h in enumerate(FORTALEZAS)
                          if cols[i % 2].checkbox(f"✨ {h}", value=h in hab_sel, key=f"fo{k}_{i}")]

        st.markdown("##### Disponibilidad horaria")
        cab = st.columns([1.4] + [1] * 7)
        for j, d in enumerate(DIAS):
            cab[j + 1].markdown(f"**{d}**")
        horarios = []
        for b, rango in BLOQUES.items():
            fila = st.columns([1.4] + [1] * 7)
            fila[0].markdown(f"**{b}**  \n<small>{rango}</small>", unsafe_allow_html=True)
            for j, d in enumerate(DIAS):
                if fila[j + 1].checkbox(f"{d} {b}", value=(d, b) in hor_sel, key=f"hr{k}_{d}_{b}", label_visibility="collapsed"):
                    horarios.append((d, b))
        enviado = st.form_submit_button("Guardar perfil", type="primary")

    if enviado:
        if not nombre.strip() or not comuna.strip():
            st.error("Nombre y comuna son obligatorios.")
            return
        with db() as con:
            if sel is None:
                uid = insertar(con, "Usuarias", {"nombre": nombre.strip(), "whatsapp": whatsapp.strip(),
                                                 "email": email.strip(), "comuna": comuna.strip()})
            else:
                uid = sel
                con.execute(f"UPDATE Usuarias SET nombre=?, whatsapp=?, email=?, comuna=? WHERE {pu()}=?",
                            (nombre.strip(), whatsapp.strip(), email.strip(), comuna.strip(), uid))
                con.execute("DELETE FROM Usuaria_Habilidad WHERE usuaria_id=?", (uid,))
                con.execute("DELETE FROM Horarios_Disponibles WHERE usuaria_id=?", (uid,))
            for h in practicas + fortalezas:
                fila = con.execute(f"SELECT {ph()} AS id FROM Habilidades WHERE nombre=?", (h,)).fetchone()
                con.execute("INSERT INTO Usuaria_Habilidad(usuaria_id, habilidad_id, nivel) VALUES(?,?,1)", (uid, fila["id"]))
            for d, b in horarios:
                con.execute("INSERT INTO Horarios_Disponibles(usuaria_id, dia, bloque) VALUES(?,?,?)", (uid, d, b))
        st.session_state["uid"] = uid
        st.success("Perfil guardado. Ya puedes ver tus oportunidades en Inicio.")
        if not (whatsapp.strip() or email.strip()):
            st.warning("Sin WhatsApp ni email las empresas no podrán contactarte.")


# ----------------------------------------------------------------------------
# Vistas Empresa
# ----------------------------------------------------------------------------
def page_publicar():
    st.subheader("Publicar un turno")
    with st.form("form_vacante"):
        c1, c2 = st.columns(2)
        empresa = c1.text_input("Empresa")
        titulo = c2.text_input("Puesto")
        comuna = c1.text_input("Comuna")
        rubro = c2.selectbox("Rubro", RUBROS)
        sueldo = c2.number_input("Sueldo mensual aprox. (CLP)", min_value=0, step=10000, value=300000)
        dias = st.multiselect("Días", DIAS)
        bloques = st.multiselect("Bloques", list(BLOQUES))
        reqs = st.multiselect("Habilidades requeridas", HAB_PRACTICAS)
        ok = st.form_submit_button("Publicar vacante", type="primary")
    if ok:
        if not (empresa.strip() and titulo.strip() and dias and bloques):
            st.error("Completa empresa, puesto, días y bloques.")
        else:
            with db() as con:
                vid = insertar(con, "Vacantes", {"empresa": empresa.strip(), "titulo": titulo.strip(),
                                                 "comuna": comuna.strip(), "sueldo": int(sueldo), "rubro": rubro})
                insertar_bloques(con, vid, dias, bloques)
                insertar_requisitos(con, vid, reqs)
            st.success("Vacante publicada. Las compatibilidades se recalculan al instante.")

    st.divider()
    st.subheader("Carga masiva (CSV o Excel)")
    plantilla = pd.DataFrame([{"empresa": "Comercial Vida", "titulo": "Asistente de ventas", "comuna": "La Cisterna",
                               "sueldo": 320000, "dias": "Lun;Mar;Mié", "bloques": "Mañana",
                               "habilidades": "Atención a público;Manejo de caja"}])
    st.download_button("Descargar plantilla CSV", plantilla.to_csv(index=False).encode("utf-8-sig"), "plantilla_vacantes.csv")
    f = st.file_uploader("Sube tu archivo", type=["csv", "xlsx"])
    if f is not None and st.button("Importar vacantes", type="primary"):
        try:
            df = pd.read_csv(f) if f.name.lower().endswith(".csv") else pd.read_excel(f)
        except Exception as e:
            st.error(f"No pude leer el archivo: {e}")
            return
        n = 0
        with db() as con:
            for r in df.fillna("").to_dict("records"):
                emp, tit = str(r.get("empresa", "")).strip(), str(r.get("titulo", "")).strip()
                if not emp or not tit:
                    continue
                try:
                    sue = int(float(r.get("sueldo") or 0))
                except ValueError:
                    sue = 0
                rub = str(r.get("rubro", "")).strip()
                datos = {"empresa": emp, "titulo": tit, "comuna": str(r.get("comuna", "")).strip(), "sueldo": sue}
                if rub in RUBROS:
                    datos["rubro"] = rub
                vid = insertar(con, "Vacantes", datos)
                insertar_bloques(con, vid, split_lista(r.get("dias", "")), split_lista(r.get("bloques", "")))
                insertar_requisitos(con, vid, split_lista(r.get("habilidades", "")))
                n += 1
        st.success(f"{n} vacantes importadas.")


def page_candidatas():
    st.subheader("Panel de candidatas")
    vs = q(f"SELECT {pv()} AS id, empresa, titulo FROM Vacantes ORDER BY empresa, titulo")
    if vs.empty:
        st.info("Aún no hay vacantes publicadas.")
        return
    etiquetas = {r.id: f"{r.empresa} — {r.titulo}" for r in vs.itertuples()}
    vid = st.selectbox("Vacante", list(etiquetas), format_func=etiquetas.get)
    ap = q(f"""SELECT u.{pu()} AS id, u.nombre, u.whatsapp, u.email, u.comuna FROM Postulaciones p
              JOIN Usuarias u ON u.{pu()}=p.usuaria_id WHERE p.vacante_id=?""", (vid,))
    if ap.empty:
        st.info("Todavía nadie ha postulado a esta vacante.")
        return
    filas = []
    for r in ap.itertuples():
        m = match_df(r.id)
        m = m[m["vacante_id"] == vid]
        sh = float(m["score_horario"].iloc[0]) if not m.empty else 0.0
        ss = float(m["score_habilidades"].iloc[0]) if not m.empty else 0.0
        ms = float(m["match_score"].iloc[0]) if not m.empty else 0.0
        filas.append((r, int(round(100 * (ms if ms > 0 else 0.6 * sh + 0.4 * ss)))))
    for pos, (r, pct) in enumerate(sorted(filas, key=lambda x: -x[1]), start=1):
        hs = q(f"SELECT h.nombre, h.tipo FROM Usuaria_Habilidad uh JOIN Habilidades h ON h.{ph()}=uh.habilidad_id WHERE uh.usuaria_id=?", (r.id,))
        fort = hs[hs["nombre"].isin(FORTALEZAS)]["nombre"].tolist()
        prac = hs[~hs["nombre"].isin(FORTALEZAS)]["nombre"].tolist()
        with st.container(border=True):
            a, b = st.columns([5, 1.3])
            a.markdown(
                f"<div class='vm'>#{pos} · {esc(r.comuna or '')}</div><div class='vt'>{esc(r.nombre or '')}</div>"
                + "".join(f"<span class='badge b-gold'>✨ {esc(x)}</span>" for x in fort)
                + "".join(f"<span class='badge'>{esc(x)}</span>" for x in prac), unsafe_allow_html=True)
            b.markdown(ring_html(pct), unsafe_allow_html=True)
            c1, c2, _ = st.columns([1.3, 1.5, 4])
            asunto = quote(f"Oportunidad laboral: {etiquetas[vid]}")
            c1.link_button("Enviar Correo", f"mailto:{r.email}?subject={asunto}", disabled=not r.email)
            num = wa_numero(r.whatsapp)
            texto = quote(f"Hola {r.nombre}, te contactamos por tu postulación a {etiquetas[vid]}.")
            c2.link_button("WhatsApp Directo", f"https://wa.me/{num}?text={texto}", disabled=not num)


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
def main():
    st.set_page_config(page_title=MARCA, page_icon="🧡", layout="wide")
    try:
        ensure_schema()
    except Exception as e:
        st.error(f"No pude preparar la tabla Habilidades: {e}")
        with db() as con:
            ddl = [r[0] for r in con.execute("SELECT sql FROM sqlite_master WHERE name='Habilidades'")]
        st.markdown("**Definición de la tabla (envíame esto):**")
        st.code("\n".join(ddl) or "(la tabla no existe)", language="sql")
        try:
            st.markdown("**Primeras filas:**")
            st.dataframe(q("SELECT * FROM Habilidades LIMIT 10"))
        except Exception:
            pass
        mostrar_esquema()
        st.stop()
    detectar_pks()
    st.markdown(CSS, unsafe_allow_html=True)
    with st.sidebar:
        st.markdown(f"## {MARCA}")
        st.caption("Conectamos oportunidades con personas.")
        rol = st.radio("Rol", ["Soy Postulante", "Soy Empresa"])
        if rol == "Soy Postulante":
            pag = st.radio("Navegación", ["Inicio", "Guardados", "Mi perfil"])
            us = q(f"SELECT {pu()} AS id, nombre FROM Usuarias ORDER BY nombre")
            uid = None
            if not us.empty:
                ids = us["id"].tolist()
                idx = ids.index(st.session_state["uid"]) if st.session_state.get("uid") in ids else 0
                uid = st.selectbox("Usuaria", ids, index=idx, format_func=dict(zip(us["id"], us["nombre"])).get)
                st.session_state["uid"] = uid
        else:
            pag = st.radio("Navegación", ["Publicar un turno", "Candidatas"])
        st.caption("Motor: motor_match.py" if motor_match else "Motor: cálculo interno")
        ver_esquema = st.checkbox("Ver esquema de la base")

    try:
        if rol == "Soy Postulante":
            if pag == "Mi perfil":
                page_perfil()
            elif uid is None:
                st.info("Primero crea tu perfil en “Mi perfil”.")
            elif pag == "Inicio":
                page_inicio(uid)
            else:
                page_guardados(uid)
        else:
            page_publicar() if pag == "Publicar un turno" else page_candidatas()
    except Exception as e:
        st.error(f"{type(e).__name__}: {e}")
        mostrar_esquema()
    if ver_esquema:
        mostrar_esquema()


main()
