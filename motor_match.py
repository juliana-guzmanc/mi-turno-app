"""
MI TURNO · "Tu futuro también importa"
FASE 2 — Motor de Match (pandas + SQLite)

Regla de negocio (confirmada con el equipo):
  - Horario: filtro binario. Si no calza el 100% de los bloques
    requeridos por la vacante, NO se habilita la postulación.
  - Habilidades: una vez habilitada por horario, definen el % de Match.
  - Si hay brecha de habilidades, se recomienda el curso asociado y se
    muestra a cuánto subiría el match si se completa.

Cómo ejecutar:
    python3 02_motor_match.py
Requiere: pandas (pip install pandas)
Requiere el archivo mi_turno.db en la misma carpeta (generado en Fase 1).
"""

import sqlite3
import pandas as pd

DB_PATH = "mi_turno.db"


# ----------------------------------------------------------------
# 1. CARGA DE DATOS
# Python no inventa datos: todo sale de las tablas de Fase 1.
# ----------------------------------------------------------------
def cargar_tablas(con: sqlite3.Connection) -> dict:
    return {
        "usuarias":          pd.read_sql("SELECT * FROM Usuarias", con),
        "usuaria_habilidad": pd.read_sql("SELECT * FROM Usuaria_Habilidad", con),
        "horarios":          pd.read_sql("SELECT * FROM Horarios_Disponibles", con),
        "vacantes":          pd.read_sql("SELECT * FROM Vacantes WHERE activa = 1", con),
        "bloques_vacante":   pd.read_sql("SELECT * FROM Bloques_Vacante", con),
        "vacante_habilidad": pd.read_sql("SELECT * FROM Vacante_Habilidad", con),
        "cursos":            pd.read_sql("SELECT * FROM Cursos", con),
    }


# ----------------------------------------------------------------
# 2. FUNCIONES DE CRUCE
# Cada bloque horario se compara como (dia_semana, bloque),
# igual que en el prototipo HTML. Así la comparación es un simple
# cruce de conjuntos, no un cálculo de rangos de horas.
# ----------------------------------------------------------------
def bloques_usuaria(t: dict, usuaria_id: int) -> set:
    h = t["horarios"]
    sub = h[h.usuaria_id == usuaria_id]
    return set(zip(sub.dia_semana, sub.bloque))


def bloques_requeridos(t: dict, vacante_id: int) -> set:
    b = t["bloques_vacante"]
    sub = b[b.vacante_id == vacante_id]
    return set(zip(sub.dia_semana, sub.bloque))


def habilidades_usuaria(t: dict, usuaria_id: int) -> set:
    uh = t["usuaria_habilidad"]
    return set(uh[uh.usuaria_id == usuaria_id].habilidad_id)


def habilidades_requeridas(t: dict, vacante_id: int) -> set:
    vh = t["vacante_habilidad"]
    return set(vh[vh.vacante_id == vacante_id].habilidad_id)


# ----------------------------------------------------------------
# 3. MOTOR DE MATCH
# ----------------------------------------------------------------
def calcular_match(t: dict, usuaria_id: int, vacante_id: int) -> dict:
    disponible = bloques_usuaria(t, usuaria_id)
    requerido = bloques_requeridos(t, vacante_id)
    calce_horario = requerido & disponible
    score_horario = len(calce_horario) / len(requerido) if requerido else 0.0
    habilitada = score_horario >= 1.0  # regla dura: 100% o no habilita

    skills_usuaria = habilidades_usuaria(t, usuaria_id)
    skills_vacante = habilidades_requeridas(t, vacante_id)
    calce_skills = skills_vacante & skills_usuaria
    score_habilidades = (len(calce_skills) / len(skills_vacante)
                          if skills_vacante else 1.0)

    # El % de match solo tiene sentido de negocio si está habilitada.
    match_score = round(score_habilidades * 100, 1) if habilitada else 0.0

    brechas = sorted(skills_vacante - skills_usuaria)
    cursos_df = t["cursos"][t["cursos"].habilidad_id.isin(brechas)]
    cursos_recomendados = cursos_df[["nombre", "duracion_horas"]].to_dict("records")

    # Si hay brecha y está habilitada por horario, mostramos el
    # potencial: qué match lograría si completa los cursos.
    match_potencial = 100.0 if (habilitada and brechas) else None

    return {
        "usuaria_id": usuaria_id,
        "vacante_id": vacante_id,
        "score_horario": round(score_horario, 2),
        "score_habilidades": round(score_habilidades, 2),
        "match_score": match_score,
        "habilitada_postular": int(habilitada),
        "brechas_habilidad": brechas,
        "cursos_recomendados": cursos_recomendados,
        "match_potencial": match_potencial,
    }


def motor_match_usuaria(t: dict, usuaria_id: int) -> pd.DataFrame:
    filas = [calcular_match(t, usuaria_id, vid) for vid in t["vacantes"].vacante_id]
    df = pd.DataFrame(filas)
    return df.sort_values(["habilitada_postular", "match_score"], ascending=[False, False])


# ----------------------------------------------------------------
# 4. DEMO: corre el motor para cada usuaria de prueba
# ----------------------------------------------------------------
def main():
    con = sqlite3.connect(DB_PATH)
    t = cargar_tablas(con)

    for _, u in t["usuarias"].iterrows():
        print(f"\n=== {u.nombre} (usuaria_id={u.usuaria_id}, comuna={u.comuna}) ===")
        df = motor_match_usuaria(t, u.usuaria_id)
        vista = df[["vacante_id", "score_horario", "score_habilidades",
                     "match_score", "habilitada_postular"]]
        print(vista.to_string(index=False))

        for _, fila in df.iterrows():
            if fila.cursos_recomendados:
                estado = "habilitada por horario" if fila.habilitada_postular else "bloqueada por horario"
                print(f"  → Vacante {fila.vacante_id} ({estado}): "
                      f"brecha en habilidad(es) {fila.brechas_habilidad}")
                for c in fila.cursos_recomendados:
                    print(f"     · Curso sugerido: {c['nombre']} ({c['duracion_horas']} h)")
                if pd.notna(fila.match_potencial):
                    print(f"     · Si completa el curso, su match sube a {fila.match_potencial}%")

    con.close()
