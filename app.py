# -*- coding: utf-8 -*-
"""
ENCAJA - app.py (Streamlit)  |  Requiere: streamlit>=1.35, pandas, openpyxl (Excel)
Ejecutar: streamlit run app.py
Coloca este archivo junto a mi_turno.db y motor_match.py.
"""
import inspect
import re
import sqlite3
import unicodedata
from contextlib import closing, contextmanager
from html import escape as esc
from urllib.parse import quote

import pandas as pd
import streamlit as st

try:
    import motor_match
    MOTOR_ERROR = ""
except Exception as _e:  # pragma: no cover
    motor_match = None
    MOTOR_ERROR = str(_e)

DB_PATH = "mi_turno.db"
MARCA = "ENCAJA"
C_CIRUELA, C_TERRACOTA, C_DORADO = "#432C46", "#C96B5B", "#D4AF37"

DIAS = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
SIETE = ["lun", "mar", "mie", "jue", "vie", "sab", "dom"]
FULL = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
BLOQUES = {"Mañana": "08:00-13:00", "Tarde": "13:00-18:00", "Noche": "18:00-22:00"}
BLOQ_MIN = {"Mañana": (480, 780), "Tarde": (780, 1080), "Noche": (1080, 1320)}
RUBROS = ["Gastronomía", "Peluquería", "Administración", "Análisis de Datos"]

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
RUBRO_DE = {"Cocina": "Gastronomía", "Apoyo en eventos": "Gastronomía", "Aseo/Sanitización": "Gastronomía"}
RUBRO_DEFECTO = "Administración"   # solo para cumplir el CHECK de Habilidades.rubro
OPCIONALES = {"rubro"}             # se omite si la tabla no tiene esa columna

MIN_MISMA_COMUNA = 15              # estimación para "misma comuna"
TIEMPOS_MIN = {                    # minutos entre comunas (editable)
    # ("La Cisterna", "El Bosque"): 25,
}

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


def norm(s):
    return unicodedata.normalize("NFD", str(s)).encode("ascii", "ignore").decode().lower().strip()


PKS = {"Usuarias": "usuaria_id", "Vacantes": "vacante_id", "Habilidades": "habilidad_id", "Cursos": "curso_id"}
VAC_CAND = {
    "empresa": ["empresa", "nombre_empresa", "empresa_nombre", "razon_social"],
    "titulo": ["titulo", "puesto", "cargo", "nombre_puesto", "nombre"],
    "comuna": ["comuna", "ubicacion"],
    "sueldo": ["sueldo", "salario", "sueldo_aprox", "remuneracion", "sueldo_mensual"],
    "horario_texto": ["horario_texto", "horario", "descripcion_horario"],
}
VC = {}


def pu(): return PKS["Usuarias"]
def pv(): return PKS["Vacantes"]
def ph(): return PKS["Habilidades"]


def detectar_estructura():
    """Detecta claves primarias y nombres reales de columnas de Vacantes."""
    with db() as con:
        for t in PKS:
            info = [r for r in con.execute(f"PRAGMA table_info({t})")]
            pks = [r["name"] for r in info if r["pk"]]
            if pks:
                PKS[t] = pks[0]
        cols = {r["name"].lower(): r["name"] for r in con.execute("PRAGMA table_info(Vacantes)")}
        for k, cand in VAC_CAND.items():
            VC[k] = next((cols[c] for c in cand if c in cols), k)


def _valor_defecto(con, tabla, col):
    ddl = con.execute("SELECT sql FROM sqlite_master WHERE name=?", (tabla,)).fetchone()
    m = re.search(rf"CHECK\s*\(\s*{col['name']}\s+IN\s*\(([^)]*)\)", (ddl[0] if ddl else "") or "", re.I)
    if m:
        return m.group(1).split(",")[0].strip().strip("'\"")
    return 0 if "INT" in (col["type"] or "").upper() else "General"


def insertar(con, tabla, datos):
    """INSERT que completa columnas NOT NULL/CHECK de la tabla existente. Devuelve el rowid."""
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


SCHEMA = """
CREATE TABLE IF NOT EXISTS Usuarias (usuaria_id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL, email TEXT NOT NULL UNIQUE, comuna TEXT NOT NULL, whatsapp TEXT);
CREATE TABLE IF NOT EXISTS Vacantes (vacante_id INTEGER PRIMARY KEY AUTOINCREMENT, empresa TEXT, titulo TEXT, comuna TEXT, sueldo INTEGER, horario_texto TEXT);
CREATE TABLE IF NOT EXISTS Habilidades (habilidad_id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL UNIQUE, rubro TEXT NOT NULL, tipo TEXT);
CREATE TABLE IF NOT EXISTS Usuaria_Habilidad (usuaria_id INTEGER NOT NULL, habilidad_id INTEGER NOT NULL, nivel TEXT DEFAULT 'básico', PRIMARY KEY (usuaria_id, habilidad_id));
CREATE TABLE IF NOT EXISTS Vacante_Habilidad (vacante_id INTEGER NOT NULL, habilidad_id INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS Horarios_Disponibles (usuaria_id INTEGER NOT NULL, dia TEXT, bloque TEXT);
CREATE TABLE IF NOT EXISTS Bloques_Vacante (vacante_id INTEGER NOT NULL, dia TEXT, bloque TEXT);
CREATE TABLE IF NOT EXISTS Cursos (curso_id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, horas INTEGER, habilidad_id INTEGER);
CREATE TABLE IF NOT EXISTS Postulaciones (postulacion_id INTEGER PRIMARY KEY AUTOINCREMENT, usuaria_id INTEGER NOT NULL,
    vacante_id INTEGER NOT NULL, fecha TEXT DEFAULT CURRENT_TIMESTAMP, UNIQUE(usuaria_id, vacante_id));
"""


@st.cache_resource
def ensure_schema():
    with db() as con:
        con.executescript(SCHEMA)
        cols = {r["name"].lower() for r in con.execute("PRAGMA table_info(Usuarias)")}
        if "whatsapp" not in cols:
            con.execute("ALTER TABLE Usuarias ADD COLUMN whatsapp TEXT")
        hcols = {r["name"].lower() for r in con.execute("PRAGMA table_info(Habilidades)")}
        if "tipo" not in hcols:
            con.execute("ALTER TABLE Habilidades ADD COLUMN tipo TEXT")
        vcols = {r["name"].lower() for r in con.execute("PRAGMA table_info(Vacantes)")}
        for k, cand in VAC_CAND.items():
            if not any(c in vcols for c in cand):
                con.execute(f"ALTER TABLE Vacantes ADD COLUMN {k} {'INTEGER' if k == 'sueldo' else 'TEXT'}")
        hab = {c["name"] for c in con.execute("PRAGMA table_info(Habilidades)")}
        for lista, tipo in ((HAB_PRACTICAS, "practica"), (FORTALEZAS, "fortaleza")):
            for nombre in lista:
                if con.execute("SELECT 1 FROM Habilidades WHERE lower(nombre)=lower(?)", (nombre,)).fetchone():
                    continue
                d = {"nombre": nombre, "tipo": tipo}
                if "rubro" in hab:
                    d["rubro"] = RUBRO_DE.get(nombre, RUBRO_DEFECTO)
                insertar(con, "Habilidades", d)
    return True


# ----------------------------------------------------------------------------
# Disponibilidad: se adapta a Horarios_Disponibles / Bloques_Vacante tal como existen
# (dia + hora_inicio + hora_fin, o dia + bloque)
# ----------------------------------------------------------------------------
_ESQ = {}


def _check_in(ddl, col):
    m = re.search(rf"CHECK\s*\(\s*{re.escape(col)}\s+IN\s*\(([^)]*)\)", ddl or "", re.I)
    return [x.strip().strip("'\"") for x in m.group(1).split(",")] if m else []


def _buscar(cols, pats):
    for p in pats:
        for n in cols:
            if re.search(p, n.lower()):
                return n
    return None


def esq_horario(tabla):
    if tabla in _ESQ:
        return _ESQ[tabla]
    with db() as con:
        cols = [r["name"] for r in con.execute(f"PRAGMA table_info({tabla})")]
        row = con.execute("SELECT sql FROM sqlite_master WHERE name=?", (tabla,)).fetchone()
        ddl = row[0] if row else ""
        e = {"tabla": tabla, "cols": cols}
        e["dia"] = _buscar(cols, [r"^dia$", r"dia_semana", r"^dia", r"day"])
        e["ini"] = _buscar(cols, [r"hora_inicio", r"inicio", r"desde", r"start"])
        e["fin"] = _buscar(cols, [r"hora_fin", r"^fin$", r"_fin$", r"hasta", r"termino", r"end"])
        e["bloque"] = _buscar(cols, [r"bloque", r"franja", r"jornada", r"turno"])

        def muestra(c):
            if not c:
                return []
            return [r[0] for r in con.execute(f"SELECT DISTINCT {c} FROM {tabla} WHERE {c} IS NOT NULL LIMIT 20")]

        dias_m = muestra(e["dia"])
        permit = _check_in(ddl, e["dia"]) if e["dia"] else []
        dias = None
        if permit:
            rep = {norm(v)[:3]: v for v in permit if norm(v)[:3] in SIETE}
            if len(rep) == 7:
                dias = [rep[k] for k in SIETE]
        if dias is None and dias_m:
            if all(isinstance(v, (int, float)) for v in dias_m):
                base = 0 if 0 in dias_m else 1
                dias = [base + i for i in range(7)]
            else:
                largos = any(len(str(v)) > 4 for v in dias_m)
                nombres = FULL if largos else [f[:3] for f in FULL]
                if all(str(v).islower() for v in dias_m):
                    nombres = [n.lower() for n in nombres]
                dias = nombres
        e["dias"] = dias or FULL
        ini_m = muestra(e["ini"])
        if ini_m and all(isinstance(v, (int, float)) for v in ini_m):
            e["horaf"] = "int"
        elif ini_m and any(len(str(v)) > 5 for v in ini_m):
            e["horaf"] = "hms"
        else:
            e["horaf"] = "hm"
        pb = _check_in(ddl, e["bloque"]) if e["bloque"] else []
        e["bloques"] = {b: next((v for v in pb if norm(v).startswith(norm(b)[:4])), b) for b in BLOQUES}
        e["clave"] = _buscar(cols, [r"usuaria_id" if "usuaria" in tabla.lower() or "horarios" in tabla.lower() else r"vacante_id"])
    _ESQ[tabla] = e
    return e


def _a_min(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return int(v) * 60
    m = re.match(r"\s*(\d{1,2})(?::(\d{2}))?", str(v))
    return int(m.group(1)) * 60 + int(m.group(2) or 0) if m else None


def _hora(minutos, f):
    h, m = divmod(minutos, 60)
    return h if f == "int" else (f"{h:02d}:{m:02d}:00" if f == "hms" else f"{h:02d}:{m:02d}")


def _dia_idx(v, e):
    if isinstance(v, (int, float)) or str(v).strip().isdigit():
        base = e["dias"][0] if isinstance(e["dias"][0], int) else 1
        return (int(v) - base) % 7
    k = norm(v)[:3]
    return SIETE.index(k) if k in SIETE else None


def guardar_bloques(con, tabla, clave_val, conjunto):
    e = esq_horario(tabla)
    if not e["clave"]:
        raise RuntimeError(f"No encuentro la columna que enlaza {tabla} (columnas: {e['cols']}).")
    for d, b in sorted(conjunto, key=lambda x: (DIAS.index(x[0]), list(BLOQUES).index(x[1]))):
        i = DIAS.index(d)
        fila = {e["clave"]: clave_val, e["dia"]: e["dias"][i]} if e["dia"] else None
        if fila is None:
            raise RuntimeError(f"No reconozco la estructura de {tabla} (columnas: {e['cols']}).")
        if e["ini"] and e["fin"]:
            a, z = BLOQ_MIN[b]
            fila[e["ini"]], fila[e["fin"]] = _hora(a, e["horaf"]), _hora(z, e["horaf"])
        elif e["bloque"]:
            fila[e["bloque"]] = e["bloques"][b]
        else:
            raise RuntimeError(f"No reconozco la estructura de {tabla} (columnas: {e['cols']}).")
        insertar(con, tabla, fila)


def leer_bloques(tabla, clave_val):
    e = esq_horario(tabla)
    if not (e["clave"] and e["dia"]):
        return set()
    out = set()
    cols = [e["dia"]] + ([e["ini"], e["fin"]] if e["ini"] and e["fin"] else [e["bloque"]] if e["bloque"] else [])
    with db() as con:
        filas = con.execute(f"SELECT {','.join(cols)} FROM {tabla} WHERE {e['clave']}=?", (clave_val,)).fetchall()
    for f in filas:
        i = _dia_idx(f[0], e)
        if i is None:
            continue
        if len(cols) == 3:
            a, z = _a_min(f[1]), _a_min(f[2])
            if a is None or z is None:
                continue
            for b, (ba, bz) in BLOQ_MIN.items():
                if max(0, min(z, bz) - max(a, ba)) >= 0.5 * (bz - ba):
                    out.add((DIAS[i], b))
        elif len(cols) == 2:
            for b in BLOQUES:
                if norm(f[1]).startswith(norm(b)[:4]):
                    out.add((DIAS[i], b))
    return out


# ----------------------------------------------------------------------------
# Motor de match: se detecta automáticamente la función de motor_match.py
# ----------------------------------------------------------------------------
def _funciones_motor():
    if motor_match is None:
        return []
    fs = [(n, f) for n, f in inspect.getmembers(motor_match, inspect.isfunction)
          if not n.startswith("_") and f.__module__ == motor_match.__name__]
    fs.sort(key=lambda x: (0 if re.search(r"match|calcul|score|compat", x[0].lower()) else 1, x[0]))
    return fs


def _kwargs(fn, uid, vid, con):
    kw = {}
    for n, p in inspect.signature(fn).parameters.items():
        l = n.lower()
        if p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD):
            continue
        if "vacante" in l:
            if vid is None:
                return None
            kw[n] = vid
        elif re.search(r"usuari|user|uid|postulante|candidata|^id$", l):
            kw[n] = uid
        elif re.search(r"^(con|conn|cnx|conexion|connection)$", l):
            kw[n] = con
        elif re.search(r"db|ruta|path|archivo|bd|sqlite", l):
            kw[n] = DB_PATH
        elif p.default is p.empty:
            return None
    return kw


def _a_df(out):
    if isinstance(out, pd.DataFrame):
        return out
    if isinstance(out, (list, tuple)) and out and isinstance(out[0], dict):
        return pd.DataFrame(out)
    return None


def motor_df(uid):
    """Devuelve (DataFrame del motor | None, nombre de la función usada)."""
    pref = st.session_state.get("_fn_motor")
    fs = _funciones_motor()
    if pref:
        fs = [x for x in fs if x[0] == pref] + [x for x in fs if x[0] != pref]
    for n, f in fs:
        with closing(sqlite3.connect(DB_PATH)) as con:
            kw = _kwargs(f, uid, None, con)
            if kw is None:
                continue
            try:
                df = _a_df(f(**kw))
            except Exception:
                continue
        if df is None or "vacante_id" not in df.columns:
            continue
        df = df.copy()
        if "match_score" not in df.columns:
            alt = next((c for c in ("score_total", "score", "compatibilidad") if c in df.columns), None)
            if alt is None:
                continue
            df["match_score"] = df[alt]
        st.session_state["_fn_motor"] = n
        return df, n
    return None, None


def _fmt_curso(r):
    if r is None:
        return None
    if isinstance(r, pd.DataFrame):
        r = r.iloc[0].to_dict() if len(r) else None
    if isinstance(r, tuple) and len(r) == 2 and isinstance(r[0], str) and isinstance(r[1], (int, float)):
        return f"{r[0]} ({r[1]} h)"
    if isinstance(r, (list, tuple)):
        r = r[0] if r else None
    if isinstance(r, dict):
        nom = r.get("nombre") or r.get("curso") or r.get("nombre_curso") or next(iter(r.values()), None)
        h = r.get("horas") or r.get("duracion_horas") or r.get("duracion")
        return f"{nom} ({h} h)" if nom and h else (str(nom) if nom else None)
    return str(r) if r else None


def curso_sugerido(uid, vid):
    for n, f in _funciones_motor():
        if not re.search(r"curso|capacit", n.lower()):
            continue
        with closing(sqlite3.connect(DB_PATH)) as con:
            kw = _kwargs(f, uid, vid, con)
            if kw is None:
                continue
            try:
                txt = _fmt_curso(f(**kw))
            except Exception:
                continue
        if txt:
            return txt
    try:
        d = q(f"""SELECT c.nombre, c.horas FROM Cursos c
                  JOIN Vacante_Habilidad vh ON vh.habilidad_id = c.habilidad_id
                  WHERE vh.vacante_id=? AND c.habilidad_id NOT IN
                    (SELECT habilidad_id FROM Usuaria_Habilidad WHERE usuaria_id=?) LIMIT 1""", (vid, uid))
        if not d.empty:
            return f"{d.iloc[0]['nombre']} ({d.iloc[0]['horas']} h)"
    except Exception:
        pass
    return None


def _match_interno(uid):
    """Respaldo si motor_match.py no responde: horario 100% para postular."""
    h_u = leer_bloques("Horarios_Disponibles", uid)
    s_u = set(q("SELECT habilidad_id FROM Usuaria_Habilidad WHERE usuaria_id=?", (uid,))["habilidad_id"])
    filas = []
    for vid in q(f"SELECT {pv()} AS id FROM Vacantes")["id"]:
        b_v = leer_bloques("Bloques_Vacante", int(vid))
        s_v = set(q("SELECT habilidad_id FROM Vacante_Habilidad WHERE vacante_id=?", (int(vid),))["habilidad_id"])
        sh = len(b_v & h_u) / len(b_v) if b_v else 0.0
        ss = len(s_v & s_u) / len(s_v) if s_v else 1.0
        ok = sh >= 1.0
        filas.append({"vacante_id": vid, "score_horario": sh, "score_habilidades": ss,
                      "match_score": round(0.6 * sh + 0.4 * ss, 2) if ok else 0.0, "habilitada_postular": int(ok)})
    return pd.DataFrame(filas, columns=["vacante_id", "score_horario", "score_habilidades", "match_score", "habilitada_postular"])


# ----------------------------------------------------------------------------
# Datos
# ----------------------------------------------------------------------------
def horario_legible(vid, fallback=None):
    b = leer_bloques("Bloques_Vacante", vid)
    if not b:
        return fallback or "Horario por definir"
    partes = []
    for bloque in BLOQUES:
        dias = [d for d in DIAS if (d, bloque) in b]
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
        return "📍 Distancia no disponible", None
    a, b = str(c_user).strip(), str(c_vac).strip()
    if a.lower() == b.lower():
        return f"📍 A ~{MIN_MISMA_COMUNA} min - Misma comuna", True
    m = TIEMPOS_MIN.get((a, b)) or TIEMPOS_MIN.get((b, a))
    return (f"📍 A {m} min - {esc(b)}" if m else f"📍 Otra comuna ({esc(b)})"), False


def wa_numero(raw):
    d = re.sub(r"\D", "", raw or "")
    if len(d) == 9 and d.startswith("9"):
        return "56" + d
    if len(d) == 8:
        return "569" + d
    return d


def split_lista(s):
    return [x.strip() for x in str(s).split(";") if x.strip()]


def insertar_requisitos(con, vid, habilidades):
    for h in habilidades:
        fila = con.execute(f"SELECT {ph()} AS id FROM Habilidades WHERE lower(nombre)=lower(?)", (h,)).fetchone()
        if fila:
            insertar(con, "Vacante_Habilidad", {"vacante_id": vid, "habilidad_id": fila["id"]})


def calcular_tabla(uid):
    campos = ", ".join(f"{VC[k]} AS {k}" for k in VAC_CAND)
    v = q(f"SELECT {pv()} AS id, {campos} FROM Vacantes")
    m, fn = motor_df(uid)
    if m is None:
        m = _match_interno(uid)
    st.session_state["_motor_usado"] = fn
    m = m.drop_duplicates("vacante_id")
    df = v.merge(m, left_on="id", right_on="vacante_id", how="left")
    for col in ("score_horario", "score_habilidades", "match_score"):
        if col not in df:
            df[col] = 0.0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    if "habilitada_postular" not in df:
        df["habilitada_postular"] = (df["score_horario"] >= 1.0).astype(int)
    df["habilitada_postular"] = df["habilitada_postular"].fillna(0)
    blend = 0.6 * df["score_horario"] + 0.4 * df["score_habilidades"]
    base = df["match_score"].where(df["match_score"] > 0, blend)
    df["pct"] = (100 * base.where(base <= 1, base / 100)).round().astype(int).clip(0, 100)
    col_curso = next((c for c in df.columns if "curso" in c.lower()), None)
    cursos = []
    for _, r in df.iterrows():
        txt = None
        if r["score_habilidades"] < 1:
            txt = (str(r[col_curso]) if col_curso and pd.notna(r[col_curso]) else None) or curso_sugerido(uid, int(r["id"]))
        cursos.append(txt)
    df["curso"] = cursos
    return df.sort_values("pct", ascending=False).reset_index(drop=True)


def perfil_completo(uid):
    u = q(f"SELECT nombre, email, comuna, whatsapp FROM Usuarias WHERE {pu()}=?", (uid,)).iloc[0]
    hs = q(f"SELECT h.nombre FROM Usuaria_Habilidad uh JOIN Habilidades h ON h.{ph()}=uh.habilidad_id WHERE uh.usuaria_id=?", (uid,))["nombre"].tolist()
    pasos = [bool(u["nombre"]), bool(u["email"]), bool(u["comuna"]), bool(u["whatsapp"]),
             any(h in HAB_PRACTICAS for h in hs), any(h in FORTALEZAS for h in hs),
             bool(leer_bloques("Horarios_Disponibles", uid))]
    return int(round(100 * sum(pasos) / len(pasos))), [h for h in hs if h in FORTALEZAS]


# ----------------------------------------------------------------------------
# Estilos
# ----------------------------------------------------------------------------
CSS = """
<style>
:root{--ciruela:#432C46;--terracota:#C96B5B;--dorado:#D4AF37;--crema:#FAF7F2;--suave:#6f5a74}
.stApp{background:var(--crema)}
.block-container{padding-top:1.4rem;max-width:1400px}
h1,h2,h3{color:var(--ciruela)!important;font-weight:800!important}
[data-testid="stSidebar"]{background:var(--ciruela)}
[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,[data-testid="stSidebar"] span,[data-testid="stSidebar"] div[role="radiogroup"] *{color:#FAF7F2!important}
[data-testid="stSidebar"] [data-baseweb="select"] *{color:#2b1a2e!important}
button[data-testid="stBaseButton-primary"],button[data-testid="stBaseButton-primaryFormSubmit"]{
  background:var(--terracota)!important;border:0!important;color:#fff!important;border-radius:999px!important;font-weight:700}
button[data-testid="stBaseButton-secondary"],a[data-testid="stBaseLinkButton-secondary"]{
  border:1.5px solid var(--terracota)!important;color:var(--terracota)!important;background:#fff!important;border-radius:999px!important}
[data-testid="stVerticalBlockBorderWrapper"]{background:#fff;border-radius:16px;box-shadow:0 4px 18px rgba(67,44,70,.09);border-color:#efe6e0}
.hero{background:linear-gradient(120deg,var(--ciruela),#7a4456 68%,var(--terracota));color:#FAF7F2;border-radius:18px;padding:28px 32px;margin-bottom:16px}
.hero small{letter-spacing:.12em;opacity:.8;font-weight:700}
.hero h1{color:#FAF7F2!important;margin:6px 0;font-size:clamp(1.5rem,3.2vw,2.3rem);line-height:1.15}
.hero p{margin:0;opacity:.92;max-width:560px}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:18px}
.kpi{background:#fff;border-radius:16px;box-shadow:0 4px 18px rgba(67,44,70,.09);padding:14px 16px;display:flex;gap:12px;align-items:center}
.kpi .ic{width:44px;height:44px;border-radius:50%;display:grid;place-items:center;font-size:1.2rem;color:#fff;flex:none}
.kpi b{display:block;font-size:1.9rem;color:var(--ciruela);line-height:1}
.kpi span{color:var(--suave);font-size:.8rem}
.vcard{display:grid;grid-template-columns:minmax(0,1fr) 118px 210px;gap:14px;align-items:center}
.vmain{display:flex;gap:14px;align-items:flex-start}
.logo{width:54px;height:54px;border-radius:50%;display:grid;place-items:center;color:#fff;font-weight:800;flex:none}
.up{text-transform:uppercase;letter-spacing:.06em;font-size:.7rem!important}
.vt{font-size:1.12rem;font-weight:800;color:var(--ciruela)}.vm{color:var(--suave);font-size:.86rem}
.badge{display:inline-block;font-size:.76rem;font-weight:700;border-radius:999px;padding:4px 11px;margin:6px 6px 0 0;background:#f4e8ee;color:var(--ciruela)}
.b-ok{background:#e1f2e8;color:#2f7a5b}.b-warn{background:#fbe9d6;color:#b4651b}
.b-gold{background:#f7ecc4;color:#7a6110;border:1px solid var(--dorado)}.b-prox{background:#e3f1e8;color:#2f6a4b}
.vring{text-align:center;background:#fbf3f1;border-radius:14px;padding:10px 4px}
.ring{width:84px;height:84px;border-radius:50%;display:grid;place-items:center;margin:0 auto;
  background:conic-gradient(var(--c) calc(var(--p)*1%),#eadfe0 0)}
.ring span{width:64px;height:64px;border-radius:50%;background:#fff;display:grid;place-items:center;font-weight:800;color:var(--ciruela)}
.stars{color:var(--dorado);letter-spacing:2px;font-size:.9rem}
.vwhy{background:#fbf8f3;border-radius:14px;padding:10px 12px;font-size:.8rem;color:var(--suave)}
.vwhy b{color:var(--ciruela);display:block;margin-bottom:4px}
.vwhy div{display:flex;justify-content:space-between;padding:2px 0}
.ok{color:#2f7a5b}.parcial{color:#b4651b}
.curso{font-size:.78rem;color:var(--suave);margin-top:6px}
.side{background:#fff;border-radius:16px;box-shadow:0 4px 18px rgba(67,44,70,.09);padding:16px 18px;margin-bottom:14px}
.side h4{margin:0 0 8px;color:var(--ciruela);font-weight:800}
.avatar{width:62px;height:62px;border-radius:50%;background:var(--ciruela);color:#FAF7F2;display:grid;place-items:center;font-size:1.5rem;font-weight:800}
.bar{height:7px;border-radius:9px;background:#eadfe0;overflow:hidden;margin:8px 0}
.bar i{display:block;height:100%;background:linear-gradient(90deg,#2f7a5b,#6fbf9a)}
.fort{background:#fbf5df;border-radius:12px;padding:10px;margin-top:10px}
.quote{font-style:italic;color:var(--suave)}
.st-key-fortalezas{background:#fbf5df;border:1px solid var(--dorado);border-radius:14px;padding:12px 16px}
@media (max-width:900px){.vcard{grid-template-columns:1fr}.kpis{grid-template-columns:repeat(2,1fr)}.hero{padding:20px}}
</style>
"""


def ring_html(pct, grande=False):
    color = C_DORADO if pct >= 80 else C_TERRACOTA if pct >= 60 else "#a99aa8"
    estrellas = "★" * max(1, round(pct / 20)) if pct >= 40 else "☆"
    return (f"<div class='ring' style='--p:{pct};--c:{color}'><span>{pct}%</span></div>"
            f"<div class='stars'>{estrellas}</div><div class='vm'>Compatible</div>")


def iniciales(txt):
    p = [w for w in re.split(r"\s+", str(txt or "?").strip()) if w]
    return esc("".join(w[0] for w in p[:2]).upper() or "?")


# ----------------------------------------------------------------------------
# Vistas Postulante
# ----------------------------------------------------------------------------
def html_vacante(r, comuna_user):
    prox, misma = proximidad(comuna_user, r["comuna"])
    bloqueada = not bool(r["habilitada_postular"])
    badges = [f"<span class='badge b-gold'>★ {int(r['pct'])}% Compatible</span>",
              "<span class='badge b-warn'>🔒 Horario no calza</span>" if bloqueada
              else "<span class='badge b-ok'>🟢 Horario disponible</span>",
              f"<span class='badge b-prox'>{prox}</span>"]
    if r["score_habilidades"] < 1:
        badges.append("<span class='badge b-warn'>🟠 Requiere capacitación</span>")
    curso = f"<div class='curso'>📚 Curso sugerido: {esc(r['curso'])}</div>" if r.get("curso") else ""
    fondo = C_CIRUELA if int(r["id"]) % 2 else C_TERRACOTA

    def fila(n, v):
        cls = "ok" if v >= 0.99 else "parcial"
        return f"<div><span>{'✓' if v >= 0.99 else '◐'} {n}</span><span class='{cls}'>{int(round(v * 100))}%</span></div>"

    ubic = "<div><span>✓ Ubicación</span><span class='ok'>Misma comuna</span></div>" if misma else \
           "<div><span>◐ Ubicación</span><span class='parcial'>Otra comuna</span></div>"
    return ("<div class='vcard'><div class='vmain'>"
            f"<div class='logo' style='background:{fondo}'>{iniciales(r['empresa'])}</div><div>"
            f"<div class='vm up'>{esc(str(r['empresa'] or ''))}</div><div class='vt'>{esc(str(r['titulo'] or ''))}</div>"
            f"<div class='vm'>{esc(str(r['comuna'] or ''))} · {esc(horario_legible(int(r['id']), r['horario_texto']))}</div>"
            f"<div class='vm'>{sueldo_fmt(r['sueldo'])}</div>{''.join(badges)}{curso}</div></div>"
            f"<div class='vring'>{ring_html(int(r['pct']))}</div>"
            f"<div class='vwhy'><b>✦ ¿Por qué encaja?</b>{fila('Horario', r['score_horario'])}{ubic}"
            f"{fila('Habilidades', r['score_habilidades'])}</div></div>")


def tarjeta_vacante(r, uid, comuna_user, prefijo):
    vid = int(r["id"])
    ya = not q("SELECT 1 FROM Postulaciones WHERE usuaria_id=? AND vacante_id=?", (uid, vid)).empty
    bloqueada = not bool(r["habilitada_postular"])
    with st.container(border=True):
        st.markdown(html_vacante(r, comuna_user), unsafe_allow_html=True)
        c1, c2, _ = st.columns([1.4, 1.2, 4])
        if ya:
            c1.button("✅ Postulada", key=f"{prefijo}_p_{vid}", disabled=True)
        elif c1.button("Postular", key=f"{prefijo}_p_{vid}", type="primary", disabled=bloqueada):
            with db() as con:
                con.execute("INSERT OR IGNORE INTO Postulaciones(usuaria_id, vacante_id) VALUES(?,?)", (uid, vid))
            st.toast("¡Postulación enviada!", icon="🎉")
            st.rerun()
        guardados = st.session_state.setdefault(f"g_{uid}", set())
        if vid in guardados:
            if c2.button("Quitar", key=f"{prefijo}_g_{vid}"):
                guardados.discard(vid)
                st.rerun()
        elif c2.button("♡ Guardar", key=f"{prefijo}_g_{vid}"):
            guardados.add(vid)
            st.toast("Guardado")
            st.rerun()


def ir(pagina):
    st.session_state["nav_post"] = pagina


def panel_lateral(uid, df):
    u = q(f"SELECT nombre, email, comuna, whatsapp FROM Usuarias WHERE {pu()}=?", (uid,)).iloc[0]
    comp, fort = perfil_completo(uid)
    chips = "".join(f"<span class='badge b-gold'>{esc(f)}</span>" for f in fort[:4]) or "<span class='vm'>Aún sin fortalezas</span>"
    st.markdown(
        "<div class='side'><h4>Tu perfil profesional</h4>"
        f"<div style='display:flex;gap:12px;align-items:center'><div class='avatar'>{iniciales(u['nombre'])}</div>"
        f"<div><b style='color:#432C46'>{esc(u['nombre'])}</b><div class='vm'>📍 {esc(u['comuna'] or '')}</div></div></div>"
        f"<div class='vm' style='margin-top:8px'>✉ {esc(u['email'] or '')}<br>💬 {esc(u['whatsapp'] or 'Sin WhatsApp')}</div>"
        f"<div class='bar'><i style='width:{comp}%'></i></div><div class='vm'>✔ Perfil {comp}% completo</div>"
        f"<div class='fort'><b style='color:#432C46'>★ Tus fortalezas destacadas</b><br>{chips}</div></div>",
        unsafe_allow_html=True)
    st.button("✏️ Editar perfil", on_click=ir, args=("Mi perfil",), key="btn_editar")
    prom = int(df["pct"].mean()) if len(df) else 0
    st.markdown(f"<div class='side'><h4>Tu compatibilidad promedio</h4>{ring_html(prom)}"
                "<div class='vm' style='text-align:center'>En base a tu perfil y disponibilidad</div></div>", unsafe_allow_html=True)
    st.markdown("<div class='side'><h4>💡 ¿Necesitas apoyo?</h4><div class='vm'>Si no encuentras la oportunidad ideal, "
                "puedes tomar cursos para mejorar tu perfil y aumentar tus posibilidades.</div></div>", unsafe_allow_html=True)
    if st.button("Ver cursos sugeridos", type="primary", key="btn_cursos"):
        cursos = sorted({c for c in df["curso"].dropna()})
        if cursos:
            for c in cursos:
                st.markdown(f"📚 {c}")
        else:
            st.info("Por ahora no hay cursos sugeridos para ti.")
    st.markdown("<div class='side quote'>“No se trata solo de encontrar un trabajo, sino de encontrar el trabajo "
                "que encaje con tu vida.”<br><small>— ENCAJA</small></div>", unsafe_allow_html=True)


def page_inicio(uid):
    u = q(f"SELECT nombre, comuna FROM Usuarias WHERE {pu()}=?", (uid,)).iloc[0]
    df = calcular_tabla(uid)
    n_post = int(q("SELECT COUNT(*) n FROM Postulaciones WHERE usuaria_id=?", (uid,)).iloc[0]["n"])
    centro, lado = st.columns([3.3, 1.15], gap="large")
    with centro:
        st.markdown(f"<div class='hero'><small>OPORTUNIDADES QUE SE ADAPTAN A TU REALIDAD</small>"
                    f"<h1>Hola, {esc(str(u['nombre']).split()[0])}. Encuentra un turno que sí encaje contigo.</h1>"
                    f"<p>{MARCA} conecta a personas que buscan trabajo flexible con empresas que necesitan talento.</p></div>",
                    unsafe_allow_html=True)
        kp = [("💼", C_CIRUELA, len(df), "Vacantes disponibles"), ("★", C_DORADO, int((df["pct"] >= 80).sum()), "Alta compatibilidad (80% o más)"),
              ("🕐", C_TERRACOTA, int(df["habilitada_postular"].astype(bool).sum()), "Turnos con horario compatible"),
              ("📋", C_DORADO, n_post, "Postulaciones en seguimiento")]
        st.markdown("<div class='kpis'>" + "".join(
            f"<div class='kpi'><div class='ic' style='background:{c}'>{i}</div><div><b>{v}</b><span>{t}</span></div></div>"
            for i, c, v, t in kp) + "</div>", unsafe_allow_html=True)
        st.subheader("Oportunidades para ti")
        st.caption("Vacantes seleccionadas según tu disponibilidad y perfil.")
        f1, f2, f3 = st.columns(3)
        comunas = ["Todas"] + sorted(x for x in df["comuna"].dropna().unique())
        fc = f1.selectbox("Ubicación", comunas)
        ft = f2.selectbox("Tipo de turno", ["Todos", *BLOQUES, "Fin de semana"])
        fm = f3.selectbox("Compatibilidad", ["Todas", "80% o más", "60% o más"])
        if fc != "Todas":
            df_f = df[df["comuna"] == fc]
        else:
            df_f = df
        if ft != "Todos":
            ids = []
            for vid in df_f["id"]:
                b = leer_bloques("Bloques_Vacante", int(vid))
                if (ft == "Fin de semana" and any(d in ("Sáb", "Dom") for d, _ in b)) or (ft in BLOQUES and any(x == ft for _, x in b)):
                    ids.append(vid)
            df_f = df_f[df_f["id"].isin(ids)]
        if fm != "Todas":
            df_f = df_f[df_f["pct"] >= int(fm.split("%")[0])]
        if df_f.empty:
            st.info("No hay vacantes con esos filtros.")
        for _, r in df_f.iterrows():
            tarjeta_vacante(r, uid, u["comuna"], "ini")
    with lado:
        panel_lateral(uid, df)


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
    idx = ids.index(st.session_state.get("uid_sel")) if st.session_state.get("uid_sel") in ids else 0
    sel = st.selectbox("Perfil a editar", ids, index=idx,
                       format_func=lambda i: "➕ Nueva postulante" if i is None else nombres[i])
    datos = {"nombre": "", "whatsapp": "", "email": "", "comuna": ""}
    hab_sel, hor_sel = set(), set()
    if sel is not None:
        datos.update({k: (v or "") for k, v in q(f"SELECT nombre, whatsapp, email, comuna FROM Usuarias WHERE {pu()}=?", (sel,)).iloc[0].items()})
        hab_sel = set(q(f"SELECT h.nombre FROM Usuaria_Habilidad uh JOIN Habilidades h ON h.{ph()}=uh.habilidad_id WHERE uh.usuaria_id=?", (sel,))["nombre"])
        hor_sel = leer_bloques("Horarios_Disponibles", sel)
    k = f"_{sel}"
    with st.form("form_perfil"):
        c1, c2 = st.columns(2)
        nombre = c1.text_input("Nombre", datos["nombre"], key="nom" + k)
        comuna = c2.text_input("Comuna", datos["comuna"], key="com" + k)
        whatsapp = c1.text_input("WhatsApp (ej: +56 9 1234 5678)", datos["whatsapp"], key="wsp" + k)
        email = c2.text_input("Email", datos["email"], key="mail" + k)

        st.markdown("##### 🧩 Habilidades prácticas")
        cols = st.columns(3)
        practicas = [h for i, h in enumerate(HAB_PRACTICAS)
                     if cols[i % 3].checkbox(h, value=h in hab_sel, key=f"hp{k}_{i}")]

        st.markdown("##### ✦ Fortalezas cotidianas")
        try:
            caja = st.container(key="fortalezas")
        except TypeError:
            caja = st.container()
        with caja:
            cols = st.columns(2)
            fortalezas = [h for i, h in enumerate(FORTALEZAS)
                          if cols[i % 2].checkbox(f"✨ {h}", value=h in hab_sel, key=f"fo{k}_{i}")]

        st.markdown("##### 🕐 Disponibilidad por día y bloque")
        cab = st.columns([1.4] + [1] * 7)
        for j, d in enumerate(DIAS):
            cab[j + 1].markdown(f"**{d}**")
        horarios = set()
        for b, rango in BLOQUES.items():
            fila = st.columns([1.4] + [1] * 7)
            fila[0].markdown(f"**{b}**  \n<small>{rango}</small>", unsafe_allow_html=True)
            for j, d in enumerate(DIAS):
                if fila[j + 1].checkbox(f"{d} {b}", value=(d, b) in hor_sel, key=f"hr{k}_{d}_{b}", label_visibility="collapsed"):
                    horarios.add((d, b))
        enviado = st.form_submit_button("💾 Guardar perfil", type="primary")

    if enviado:
        if not (nombre.strip() and comuna.strip() and email.strip()):
            st.error("Nombre, comuna y email son obligatorios.")
            return
        try:
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
                    insertar(con, "Usuaria_Habilidad", {"usuaria_id": uid, "habilidad_id": fila["id"]})
                guardar_bloques(con, "Horarios_Disponibles", uid, horarios)
        except sqlite3.IntegrityError as e:
            if "email" in str(e).lower():
                st.error("Ese email ya está registrado en otro perfil.")
                return
            raise
        st.session_state["uid_pend"] = uid
        st.session_state["flash"] = "Perfil guardado. Ya puedes ver tus oportunidades en Inicio."
        if not whatsapp.strip():
            st.session_state["flash"] += " Sin WhatsApp las empresas solo podrán escribirte por correo."
        st.rerun()


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
        sueldo = c1.number_input("Sueldo mensual aprox. (CLP)", min_value=0, step=10000, value=300000)
        dias = st.multiselect("Días", DIAS)
        bloques = st.multiselect("Bloques", list(BLOQUES))
        reqs = st.multiselect("Habilidades requeridas", HAB_PRACTICAS)
        ok = st.form_submit_button("Publicar vacante", type="primary")
    if ok:
        if not (empresa.strip() and titulo.strip() and dias and bloques):
            st.error("Completa empresa, puesto, días y bloques.")
        else:
            with db() as con:
                vid = insertar(con, "Vacantes", {VC["empresa"]: empresa.strip(), VC["titulo"]: titulo.strip(),
                                                 VC["comuna"]: comuna.strip(), VC["sueldo"]: int(sueldo), "rubro": rubro})
                guardar_bloques(con, "Bloques_Vacante", vid, {(d, b) for d in dias for b in bloques})
                insertar_requisitos(con, vid, reqs)
            st.success("Vacante publicada. Las compatibilidades se recalculan al instante.")

    st.divider()
    st.subheader("Carga masiva (CSV o Excel)")
    plantilla = pd.DataFrame([{"empresa": "Comercial Vida", "titulo": "Asistente de ventas", "comuna": "La Cisterna",
                               "rubro": "Administración", "sueldo": 320000, "dias": "Lun;Mar;Mié", "bloques": "Mañana",
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
                d = {VC["empresa"]: emp, VC["titulo"]: tit, VC["comuna"]: str(r.get("comuna", "")).strip(), VC["sueldo"]: sue}
                if str(r.get("rubro", "")).strip() in RUBROS:
                    d["rubro"] = str(r["rubro"]).strip()
                vid = insertar(con, "Vacantes", d)
                dd = [x for x in split_lista(r.get("dias", "")) if x in DIAS]
                bb = [x for x in split_lista(r.get("bloques", "")) if x in BLOQUES]
                guardar_bloques(con, "Bloques_Vacante", vid, {(x, y) for x in dd for y in bb})
                insertar_requisitos(con, vid, split_lista(r.get("habilidades", "")))
                n += 1
        st.success(f"{n} vacantes importadas.")


def page_publicaciones():
    st.subheader("Mis publicaciones")
    df = q(f"""SELECT v.{pv()} AS id, v.{VC['empresa']} AS empresa, v.{VC['titulo']} AS puesto, v.{VC['comuna']} AS comuna,
               (SELECT COUNT(*) FROM Postulaciones p WHERE p.vacante_id=v.{pv()}) AS postulaciones FROM Vacantes v ORDER BY 1 DESC""")
    if df.empty:
        st.info("Aún no hay vacantes publicadas.")
    else:
        st.dataframe(df, hide_index=True, use_container_width=True)


def page_candidatas():
    st.subheader("Candidatas")
    st.caption("Solo aparecen las personas que postularon a la vacante.")
    vs = q(f"SELECT {pv()} AS id, {VC['empresa']} AS empresa, {VC['titulo']} AS titulo FROM Vacantes ORDER BY 2, 3")
    if vs.empty:
        st.info("Aún no hay vacantes publicadas.")
        return
    etiquetas = {int(r.id): f"{r.empresa} — {r.titulo}" for r in vs.itertuples()}
    vid = st.selectbox("Vacante", list(etiquetas), format_func=etiquetas.get)
    ap = q(f"""SELECT u.{pu()} AS id, u.nombre, u.whatsapp, u.email, u.comuna, p.fecha FROM Postulaciones p
               JOIN Usuarias u ON u.{pu()}=p.usuaria_id WHERE p.vacante_id=?""", (int(vid),))
    if ap.empty:
        st.info("Todavía nadie ha postulado a esta vacante.")
        return
    filas = []
    for r in ap.itertuples():
        t = calcular_tabla(int(r.id))
        t = t[t["id"] == vid]
        filas.append((r, int(t["pct"].iloc[0]) if not t.empty else 0))
    for pos, (r, pct) in enumerate(sorted(filas, key=lambda x: -x[1]), start=1):
        hs = q(f"SELECT h.nombre FROM Usuaria_Habilidad uh JOIN Habilidades h ON h.{ph()}=uh.habilidad_id WHERE uh.usuaria_id=?", (int(r.id),))
        fort = [x for x in hs["nombre"] if x in FORTALEZAS]
        prac = [x for x in hs["nombre"] if x not in FORTALEZAS]
        with st.container(border=True):
            a, b = st.columns([5, 1.3])
            a.markdown(
                f"<div class='vm'>#{pos} · 📍 {esc(r.comuna or '')}</div><div class='vt'>{esc(r.nombre or '')}</div>"
                + "".join(f"<span class='badge b-gold'>✨ {esc(x)}</span>" for x in fort)
                + "".join(f"<span class='badge'>{esc(x)}</span>" for x in prac), unsafe_allow_html=True)
            b.markdown(f"<div class='vring'>{ring_html(pct)}</div>", unsafe_allow_html=True)
            c1, c2, _ = st.columns([1.3, 1.6, 4])
            asunto = quote(f"Oportunidad laboral: {etiquetas[vid]}")
            c1.link_button("✉️ Enviar correo", f"mailto:{r.email}?subject={asunto}", disabled=not r.email)
            num = wa_numero(r.whatsapp)
            texto = quote(f"Hola {r.nombre}, te contactamos por tu postulación a {etiquetas[vid]}.")
            c2.link_button("💬 WhatsApp directo", f"https://wa.me/{num}?text={texto}", disabled=not num)


# ----------------------------------------------------------------------------
# Diagnóstico
# ----------------------------------------------------------------------------
def mostrar_diagnostico():
    with st.expander("🔧 Diagnóstico (motor y esquema)", expanded=True):
        usado = st.session_state.get("_motor_usado")
        if motor_match is None:
            st.warning(f"No pude importar motor_match.py: {MOTOR_ERROR}")
        else:
            st.markdown(f"**Función del motor en uso:** `{usado or 'ninguna reconocida (se usa el cálculo interno)'}`")
            st.markdown("**Funciones en motor_match.py:**")
            for n, f in _funciones_motor():
                st.code(f"{n}{inspect.signature(f)}")
        with db() as con:
            ddl = [r[0] for r in con.execute("SELECT sql FROM sqlite_master WHERE type='table' AND sql IS NOT NULL")]
        st.code(";\n\n".join(ddl), language="sql")


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
def main():
    st.set_page_config(page_title=MARCA, page_icon="🧡", layout="wide")
    try:
        ensure_schema()
        detectar_estructura()
    except Exception as e:
        st.error(f"No pude preparar la base de datos: {type(e).__name__}: {e}")
        mostrar_diagnostico()
        st.stop()
    if "uid_pend" in st.session_state:
        st.session_state["uid_sel"] = st.session_state.pop("uid_pend")
        st.session_state["nav_post"] = "Inicio"
    if "flash" in st.session_state:
        st.toast(st.session_state.pop("flash"), icon="✅")
    st.markdown(CSS, unsafe_allow_html=True)

    rol = st.session_state.get("rol", "Soy Postulante")
    uid = None
    with st.sidebar:
        st.markdown(f"## 🧡 {MARCA}")
        st.caption("Conectamos oportunidades con personas.")
        if rol == "Soy Postulante":
            pag = st.radio("Navegación", ["Inicio", "Guardados", "Mi perfil"], key="nav_post")
            us = q(f"SELECT {pu()} AS id, nombre FROM Usuarias ORDER BY nombre")
            if not us.empty:
                ids = us["id"].tolist()
                if st.session_state.get("uid_sel") not in ids:
                    st.session_state["uid_sel"] = ids[0]
                uid = st.selectbox("Usuaria", ids, key="uid_sel", format_func=dict(zip(us["id"], us["nombre"])).get)
        else:
            pag = st.radio("Navegación", ["Publicar un turno", "Mis publicaciones", "Candidatas"], key="nav_emp")
        st.radio("Cambiar de rol", ["Soy Postulante", "Soy Empresa"], key="rol")
        st.markdown("<p style='font-style:italic;opacity:.8;margin-top:24px'>Más oportunidades,<br>más historias. ♡</p>",
                    unsafe_allow_html=True)
        usado = st.session_state.get("_motor_usado")
        st.caption(f"Motor: motor_match.{usado}" if usado else "Motor: cálculo interno")
        ver = st.checkbox("Diagnóstico")

    try:
        if st.session_state.get("rol", rol) != rol:
            st.rerun()
        if rol == "Soy Postulante":
            if pag == "Mi perfil":
                page_perfil()
            elif uid is None:
                st.info("Primero crea tu perfil en “Mi perfil”.")
                page_perfil()
            elif pag == "Inicio":
                page_inicio(uid)
            else:
                page_guardados(uid)
        elif pag == "Publicar un turno":
            page_publicar()
        elif pag == "Mis publicaciones":
            page_publicaciones()
        else:
            page_candidatas()
    except Exception as e:
        st.error(f"{type(e).__name__}: {e}")
        mostrar_diagnostico()
    if ver:
        mostrar_diagnostico()


main()
