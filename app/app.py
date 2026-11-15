"""Interfaz Streamlit: recibe un registro en escala original y muestra su segmento, su perfil y el mapa PCA."""
from __future__ import annotations

import html
import re

import altair as alt
import pandas as pd
import streamlit as st

import servicio

ETIQUETAS = {
    "hours_coding": ("Horas de programación", "h", "Horas dedicadas a programar en la jornada."),
    "commits": ("Commits", "", "Número de commits realizados."),
    "ai_usage_hours": ("Uso de herramientas de IA", "h", "Horas de trabajo apoyado en asistentes de IA."),
    "coffee_intake_mg": ("Cafeína", "mg", "El modelo se entrenó con valores de hasta 600 mg; no admite más."),
    "sleep_hours": ("Horas de sueño", "h", "Horas dormidas la noche anterior."),
    "cognitive_load": ("Carga cognitiva", "", "Esfuerzo mental percibido, de 1 (bajo) a 10 (muy alto)."),
    "distractions": ("Distracciones", "", "Número de interrupciones durante la jornada."),
    "bugs_reported": ("Bugs reportados", "", "Número de bugs reportados."),
}
GRUPOS = {
    "Trabajo": ["hours_coding", "commits", "ai_usage_hours", "coffee_intake_mg"],
    "Descanso y calidad": ["sleep_hours", "cognitive_load", "distractions", "bugs_reported"],
}
EJEMPLOS = {
    "Jornada larga y descansada": dict(hours_coding=6.5, coffee_intake_mg=560, distractions=2, sleep_hours=8.2,
                                      commits=6, bugs_reported=0, ai_usage_hours=1.8, cognitive_load=3.0),
    "Jornada larga con poco sueño": dict(hours_coding=6.2, coffee_intake_mg=550, distractions=4, sleep_hours=5.5,
                                        commits=5, bugs_reported=2, ai_usage_hours=2.0, cognitive_load=6.5),
    "Jornada corta": dict(hours_coding=2.8, coffee_intake_mg=280, distractions=3, sleep_hours=7.0,
                          commits=2, bugs_reported=1, ai_usage_hours=0.7, cognitive_load=4.3),
    "Perfil extremo": dict(hours_coding=11.0, coffee_intake_mg=600, distractions=8, sleep_hours=3.5,
                           commits=13, bugs_reported=5, ai_usage_hours=6.0, cognitive_load=9.5),
}
SIN_EJEMPLO = "Ninguno"
HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")


@st.cache_resource(show_spinner="Cargando el modelo…")
def obtener_artefacto() -> dict:
    return servicio.cargar_artefacto()


def clave(variable: str) -> str:
    return f"campo_{variable}"


def paso(rango: dict) -> float:
    if rango["entero"]:
        return 1
    if rango["max"] - rango["min"] > 100:
        return 1.0
    # un paso de 0.1 debe poder alcanzar el máximo; si no, se usa 0.01
    return 0.1 if abs(rango["max"] * 10 - round(rango["max"] * 10)) < 1e-9 else 0.01


def como_tipo(valor: float, rango: dict):
    return int(round(valor)) if rango["entero"] else float(valor)


def valor_inicial(rango: dict):
    p = paso(rango)
    return como_tipo(round(round(rango["mediana"] / p) * p, 2), rango)


def cargar_ejemplo() -> None:
    art = obtener_artefacto()
    ejemplo = EJEMPLOS.get(st.session_state["ejemplo"])
    if ejemplo:
        for variable, valor in ejemplo.items():
            st.session_state[clave(variable)] = como_tipo(valor, art["rangos"][variable])
    st.session_state.pop("registro", None)        # el resultado anterior ya no corresponde al formulario


def tinta() -> tuple[str, str]:
    """Color de texto y de líneas auxiliares según el tema activo (claro u oscuro)."""
    return ("#F2F2EF", "#8A8F98") if tema_oscuro() else ("#1F2328", "#9AA0A6")


def tema_oscuro() -> bool:
    return getattr(getattr(st.context, "theme", None), "type", "light") == "dark"


def formulario(art: dict) -> None:
    for variable, rango in art["rangos"].items():
        st.session_state.setdefault(clave(variable), valor_inicial(rango))

    st.selectbox("Cargar un ejemplo", [SIN_EJEMPLO, *EJEMPLOS], key="ejemplo", on_change=cargar_ejemplo,
                 help="Rellena el formulario con un perfil de muestra. Luego pulsa «Asignar segmento».")

    with st.form("registro_form", border=False):
        for grupo, variables in GRUPOS.items():
            st.subheader(grupo)
            for variable in variables:
                nombre, unidad, ayuda = ETIQUETAS[variable]
                rango = art["rangos"][variable]
                p = paso(rango)
                st.slider(f"{nombre} ({unidad})" if unidad else nombre,
                          min_value=como_tipo(rango["min"], rango), max_value=como_tipo(rango["max"], rango),
                          step=p, key=clave(variable), help=ayuda,
                          format=None if rango["entero"] else ("%.2f" if p == 0.01 else "%.1f" if p == 0.1 else "%.0f"))
        enviado = st.form_submit_button("Asignar segmento", type="primary", width="stretch")

    if enviado:
        st.session_state["registro"] = {v: st.session_state[clave(v)] for v in art["features"]}


def mapa_segmentos(art: dict, asignacion: servicio.Asignacion | None) -> alt.LayerChart:
    color_texto, _ = tinta()
    orden = sorted(art["segmentos"])
    nombres = [art["segmentos"][c]["nombre"] for c in orden]
    colores = [art["segmentos"][c]["color"] for c in orden]
    v1, v2 = art["varianza_pca"]
    eje_x = alt.X("PC1:Q", title=f"Intensidad de trabajo →  (PC1, {v1:.0%} de la varianza)")
    eje_y = alt.Y("PC2:Q", title=f"Desgaste →  (PC2, {v2:.0%})")

    capas = [alt.Chart(art["historico_2d"]).mark_circle(size=45, opacity=0.5).encode(
        x=eje_x, y=eje_y,
        color=alt.Color("segmento:N", scale=alt.Scale(domain=nombres, range=colores),
                        legend=alt.Legend(title=None, orient="top", symbolOpacity=1, labelLimit=320, columns=2)),
        tooltip=[alt.Tooltip("segmento:N", title="Segmento"), alt.Tooltip("PC1:Q", format=".2f"),
                 alt.Tooltip("PC2:Q", format=".2f")])]

    if asignacion is not None:
        nuevo = pd.DataFrame([{"PC1": asignacion.pc1, "PC2": asignacion.pc2, "Segmento": asignacion.nombre}])
        base = alt.Chart(nuevo).encode(x=eje_x, y=eje_y)
        capas.append(base.mark_point(shape="diamond", size=420, filled=True, fill=asignacion.color, opacity=1,
                                     stroke=color_texto, strokeWidth=2.5).encode(
            tooltip=[alt.Tooltip("Segmento:N", title="Tu registro"), alt.Tooltip("PC1:Q", format=".2f"),
                     alt.Tooltip("PC2:Q", format=".2f")]))
        # la etiqueta se coloca hacia el interior del gráfico para que no se corte si el punto cae en un borde
        a_la_derecha = asignacion.pc1 > art["historico_2d"]["PC1"].median()
        texto = dict(text="Tu registro", fontSize=14, fontWeight="bold",
                     align="right" if a_la_derecha else "left", dx=-18 if a_la_derecha else 18)
        fondo = "#0E1117" if tema_oscuro() else "#FFFFFF"
        capas.append(base.mark_text(**texto, stroke=fondo, strokeWidth=5, strokeOpacity=0.9, color=fondo))  # halo
        capas.append(base.mark_text(**texto, color=color_texto))

    return alt.layer(*capas).properties(height=440)


def grafico_comparacion(comparacion: pd.DataFrame, asignacion: servicio.Asignacion) -> alt.LayerChart:
    color_texto, color_auxiliar = tinta()
    serie_segmento = f"Promedio de «{asignacion.nombre}»"
    datos = comparacion.assign(etiqueta=[ETIQUETAS[v][0] for v in comparacion["variable"]])
    orden = [ETIQUETAS[v][0] for variables in GRUPOS.values() for v in variables]      # mismo orden que el formulario
    largo = pd.concat([
        datos.assign(serie="Tu registro", z=datos["z_registro"], valor=datos["registro"]),
        datos.assign(serie=serie_segmento, z=datos["z_segmento"], valor=datos["promedio_segmento"]),
    ])[["etiqueta", "serie", "z", "valor"]]

    eje_y = alt.Y("etiqueta:N", sort=orden, title=None, axis=alt.Axis(labelLimit=240))
    union = alt.Chart(datos).mark_rule(color=color_auxiliar, strokeWidth=2).encode(y=eje_y, x="z_registro:Q", x2="z_segmento:Q")
    cero = alt.Chart(pd.DataFrame({"z": [0]})).mark_rule(color=color_auxiliar, strokeDash=[4, 4]).encode(x="z:Q")
    escala = dict(domain=["Tu registro", serie_segmento])
    puntos = alt.Chart(largo).mark_point(filled=True, size=130, opacity=1).encode(
        y=eje_y,
        x=alt.X("z:Q", title="Desviaciones estándar respecto al promedio general (0 = promedio)"),
        color=alt.Color("serie:N", scale=alt.Scale(range=[color_texto, asignacion.color], **escala),
                        legend=alt.Legend(title=None, orient="top", labelLimit=320, columns=1)),
        shape=alt.Shape("serie:N", scale=alt.Scale(range=["diamond", "circle"], **escala), legend=None),
        tooltip=[alt.Tooltip("etiqueta:N", title="Variable"), alt.Tooltip("serie:N", title="Serie"),
                 alt.Tooltip("valor:Q", title="Valor", format=".2f")])
    return alt.layer(cero, union, puntos).properties(height=330)


def tabla_comparacion(comparacion: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({
        "Variable": [f"{ETIQUETAS[v][0]} ({ETIQUETAS[v][1]})" if ETIQUETAS[v][1] else ETIQUETAS[v][0]
                     for v in comparacion["variable"]],
        "Tu registro": comparacion["registro"],
        "Promedio del segmento": comparacion["promedio_segmento"],
        "Promedio general": comparacion["promedio_general"],
    })


def encabezado_segmento(asignacion: servicio.Asignacion, total: int) -> None:
    color = asignacion.color if HEX.match(asignacion.color) else "#888888"
    st.caption(f"Cluster {asignacion.cluster} de K-Means · uno de los {total} segmentos")
    st.markdown(
        f"<h2 style='margin:0 0 .4rem 0;padding:0'>"
        f"<span aria-hidden='true' style='display:inline-block;width:.75em;height:.75em;border-radius:50%;"
        f"background:{color};margin-right:.45em'></span>{html.escape(asignacion.nombre)}</h2>",
        unsafe_allow_html=True)
    st.write(asignacion.descripcion)


def mostrar_resultado(art: dict, registro: dict) -> None:
    try:
        asignacion = servicio.asignar(registro, art)
    except servicio.EntradaInvalida as error:
        st.error(str(error))
        return

    perfil = art["perfiles"].loc[asignacion.cluster]
    encabezado_segmento(asignacion, len(art["segmentos"]))

    if asignacion.atipico:
        st.warning(
            f"**Perfil atípico.** Este registro se aleja de los datos con que se entrenó el modelo: está a "
            f"{asignacion.distancia_core:.2f} del grupo denso más cercano y el límite es {asignacion.eps:.2f}. "
            "El segmento mostrado es el más parecido, pero conviene tomarlo con cautela.", icon=":material/warning:")

    izquierda, derecha = st.columns([3, 2], gap="large")
    with izquierda:
        st.subheader("Dónde cae en el mapa de segmentos")
        st.altair_chart(mapa_segmentos(art, asignacion), width="stretch")
        st.caption("Cada punto es uno de los 500 registros históricos. El mapa resume 8 variables en 2 ejes y conserva "
                   f"el {sum(art['varianza_pca']):.0%} de la información, por eso los colores se mezclan en los bordes.")
    with derecha:
        st.subheader("Qué se recomienda")
        st.markdown("\n".join(f"- {accion}" for accion in asignacion.acciones))
        st.subheader("Cómo le va a este segmento")
        st.write(f"En los datos históricos, el **{perfil['task_success']:.0%}** de los registros de este segmento "
                 f"completó su tarea con éxito. Lo forman {int(perfil['n_registros'])} de los "
                 f"{art['meta']['n_registros']} registros.")
        if perfil["pct_cafe_en_tope"] > 0:
            st.caption("La cafeína de este segmento debe leerse como «600 mg o más»: el dato original está topado en 600 mg.")

    comparacion = servicio.comparar_con_perfil(registro, art, asignacion.cluster)
    st.subheader("Tu registro frente al promedio de su segmento")
    st.altair_chart(grafico_comparacion(comparacion, asignacion), width="stretch")
    with st.expander("Ver los valores en su escala original"):
        st.dataframe(tabla_comparacion(comparacion), hide_index=True, width="stretch",
                     column_config={c: st.column_config.NumberColumn(format="%.2f")
                                    for c in ("Tu registro", "Promedio del segmento", "Promedio general")})


def mostrar_inicio(art: dict) -> None:
    st.info("Completa los datos en el panel izquierdo, o carga un ejemplo, y pulsa **Asignar segmento**.",
            icon=":material/arrow_back:")
    izquierda, derecha = st.columns([3, 2], gap="large")
    with izquierda:
        st.subheader("Mapa de los 500 registros históricos")
        st.altair_chart(mapa_segmentos(art, None), width="stretch")
    with derecha:
        st.subheader("Los tres segmentos")
        for cluster in sorted(art["segmentos"]):
            segmento = art["segmentos"][cluster]
            st.markdown(f"**{segmento['nombre']}**  \n{segmento['descripcion']}")


def mostrar_detalles(art: dict) -> None:
    meta = art["meta"]
    detector = art["detector_atipicos"]
    with st.expander("Perfil promedio de los tres segmentos"):
        tabla = servicio.resumen_segmentos(art).rename(
            columns={"segmento": "Segmento", "registros": "Registros", "pct_exito": "Éxito (%)",
                     **{v: ETIQUETAS[v][0] for v in art["features"]}})
        st.dataframe(tabla, hide_index=True, width="stretch",
                     column_config={c: st.column_config.NumberColumn(format="%.2f")
                                    for c in tabla.columns if c not in ("Segmento", "Registros")})
    with st.expander("Cómo se obtiene el resultado"):
        st.markdown(
            f"1. El registro se transforma con el **mismo escalador** que se ajustó con los "
            f"{meta['n_registros']} registros de entrenamiento.\n"
            f"2. **K-Means (K = {meta['k']})** lo asigna al segmento cuyo centro está más cerca, usando las 8 variables.\n"
            "3. El **mismo PCA** del entrenamiento calcula su posición en el mapa.\n"
            f"4. Regla de **DBSCAN**: si el punto denso más cercano está a más de eps = {detector['eps']}, "
            "el registro se marca como atípico.")
        st.caption(f"Modelo exportado el {meta['fecha']} con scikit-learn {meta['sklearn_version']} · "
                   f"Silhouette {meta['silhouette']:.3f}")


def main() -> None:
    st.set_page_config(page_title="Segmentos de productividad", layout="wide")

    try:
        art = obtener_artefacto()
    except servicio.ErrorModelo as error:
        st.error(str(error))
        st.stop()

    aviso = servicio.aviso_version(art)
    if aviso:
        st.warning(aviso)

    st.title("¿Qué perfil de trabajo tiene este desarrollador?")
    st.caption(f"Segmentación con K-Means sobre {art['meta']['n_registros']} registros de productividad de desarrolladores.")

    with st.sidebar:
        st.header("Datos del registro")
        formulario(art)

    registro = st.session_state.get("registro")
    if registro is None:
        mostrar_inicio(art)
    else:
        mostrar_resultado(art, registro)
    mostrar_detalles(art)


main()
