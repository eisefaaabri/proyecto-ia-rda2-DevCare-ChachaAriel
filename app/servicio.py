"""Lógica de la aplicación: carga del modelo exportado, validación de la entrada y asignación de segmento.

No depende de Streamlit, para que la interfaz (app.py) solo se ocupe de mostrar resultados.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import joblib
import pandas as pd
import sklearn

RUTA_MODELO = Path(__file__).resolve().parent.parent / "models" / "modelo_clustering.pkl"

CLAVES_REQUERIDAS = {"pipeline", "pca_2d", "detector_atipicos", "features", "rangos", "segmentos",
                     "perfiles", "promedio_global", "historico_2d", "varianza_pca", "meta"}


class ErrorModelo(Exception):
    """El modelo exportado falta, está dañado o no tiene la estructura esperada."""


class EntradaInvalida(ValueError):
    """El registro ingresado no cumple el contrato de entrada del modelo."""


@dataclass(frozen=True)
class Asignacion:
    cluster: int
    nombre: str
    color: str
    descripcion: str
    acciones: tuple[str, ...]
    pc1: float
    pc2: float
    atipico: bool
    distancia_core: float
    eps: float


def cargar_artefacto(ruta: Path = RUTA_MODELO) -> dict:
    if not ruta.exists():
        raise ErrorModelo("No se encontró el modelo exportado (models/modelo_clustering.pkl). "
                          "Ejecuta el notebook completo para generarlo.")
    try:
        artefacto = joblib.load(ruta)
    except Exception as exc:  # archivo dañado o generado con otras versiones de las librerías
        raise ErrorModelo("El archivo del modelo no se pudo leer. Vuelve a generarlo ejecutando el notebook "
                          "con las versiones indicadas en requirements.txt.") from exc

    if not isinstance(artefacto, dict) or not CLAVES_REQUERIDAS <= artefacto.keys():
        raise ErrorModelo("El archivo del modelo no tiene la estructura esperada. "
                          "Vuelve a ejecutar el notebook para exportarlo de nuevo.")
    return artefacto


def aviso_version(artefacto: dict) -> str | None:
    """Mensaje si scikit-learn no coincide con la versión con que se exportó el modelo."""
    exportado = artefacto["meta"].get("sklearn_version")
    if exportado and exportado != sklearn.__version__:
        return (f"El modelo se exportó con scikit-learn {exportado} y aquí está instalada la versión "
                f"{sklearn.__version__}. Instala las versiones de requirements.txt para evitar diferencias.")
    return None


def validar_registro(valores: dict, artefacto: dict) -> pd.DataFrame:
    """Devuelve el registro como DataFrame con las columnas y el orden del entrenamiento."""
    fila = []
    for variable in artefacto["features"]:
        if variable not in valores:
            raise EntradaInvalida(f"Falta el valor de «{variable}».")
        try:
            valor = float(valores[variable])
        except (TypeError, ValueError):
            raise EntradaInvalida(f"El valor de «{variable}» debe ser un número.") from None
        if not math.isfinite(valor):
            raise EntradaInvalida(f"El valor de «{variable}» debe ser un número.")

        rango = artefacto["rangos"][variable]
        if not rango["min"] <= valor <= rango["max"]:
            raise EntradaInvalida(f"«{variable}» debe estar entre {rango['min']:g} y {rango['max']:g}: "
                                  "son los límites de los datos con que se entrenó el modelo.")
        if rango["entero"] and not valor.is_integer():
            raise EntradaInvalida(f"«{variable}» debe ser un número entero.")
        fila.append(valor)
    return pd.DataFrame([fila], columns=artefacto["features"])


def asignar(valores: dict, artefacto: dict) -> Asignacion:
    entrada = validar_registro(valores, artefacto)

    pipeline = artefacto["pipeline"]
    cluster = int(pipeline.predict(entrada)[0])                       # escala con el escalador ajustado y asigna
    pc1, pc2 = artefacto["pca_2d"].transform(pipeline[:-1].transform(entrada))[0]

    # Regla de DBSCAN: distancia al punto core más cercano frente a eps
    detector = artefacto["detector_atipicos"]
    escalado = detector["pipeline_dbscan"][:-1].transform(entrada)
    distancia = float(detector["nn_core"].kneighbors(escalado)[0][0, 0])

    segmento = artefacto["segmentos"][cluster]
    return Asignacion(cluster=cluster, nombre=segmento["nombre"], color=segmento["color"],
                      descripcion=segmento["descripcion"], acciones=tuple(segmento["acciones"]),
                      pc1=float(pc1), pc2=float(pc2), atipico=distancia > detector["eps"],
                      distancia_core=distancia, eps=float(detector["eps"]))


def comparar_con_perfil(valores: dict, artefacto: dict, cluster: int) -> pd.DataFrame:
    """Registro frente al promedio de su segmento y al promedio general, en escala original y estandarizada."""
    variables = artefacto["features"]
    escalador = artefacto["pipeline"].named_steps["escalar"]
    registro = pd.Series({v: float(valores[v]) for v in variables})
    segmento = artefacto["perfiles"].loc[cluster, variables]
    general = artefacto["promedio_global"][variables]

    return pd.DataFrame({
        "variable": variables,
        "registro": registro.to_numpy(),
        "promedio_segmento": segmento.to_numpy(dtype=float),
        "promedio_general": general.to_numpy(dtype=float),
        "z_registro": (registro.to_numpy() - escalador.mean_) / escalador.scale_,
        "z_segmento": (segmento.to_numpy(dtype=float) - escalador.mean_) / escalador.scale_,
    })


def resumen_segmentos(artefacto: dict) -> pd.DataFrame:
    """Perfil promedio de cada segmento, con su tamaño y su proporción de tareas exitosas."""
    perfiles = artefacto["perfiles"]
    tabla = perfiles[artefacto["features"]].copy()
    tabla.insert(0, "segmento", [artefacto["segmentos"][c]["nombre"] for c in perfiles.index])
    tabla["registros"] = perfiles["n_registros"].astype(int)
    tabla["pct_exito"] = perfiles["task_success"] * 100
    return tabla.reset_index(drop=True)
