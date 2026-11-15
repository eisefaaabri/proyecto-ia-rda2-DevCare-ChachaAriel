# DevCare · Segmentación de Perfiles de Productividad de Desarrolladores

**Proyecto 2 · Clustering con Machine Learning y Aplicación Web**  
*Inteligencia Artificial · Ingeniería en Sistemas de Información (PUCE)*

| | |
|---|---|
| **Autor** | Ariel Chacha |
| **Docente** | Dr. Henry N. Roa |
| **Dataset** | [AI Developer Productivity Dataset (Kaggle)](https://www.kaggle.com/datasets/atharvasoundankar/ai-developer-productivity-dataset) (`ai_dev_productivity.csv`) |
| **Repositorio** | [github.com/eisefaaabri/proyecto-ia-rda2-DevCare-ChachaAriel](https://github.com/eisefaaabri/proyecto-ia-rda2-DevCare-ChachaAriel.git) |

---

## Descripción del proyecto

Este proyecto aplica técnicas de **aprendizaje no supervisado (Clustering)** sobre el dataset `ai_dev_productivity.csv` (500 registros, 9 variables) para identificar perfiles de hábitos de trabajo en desarrolladores de software y orientar intervenciones de gestión diferenciadas (descanso y prevención de desgaste, redistribución de carga o capacitación en herramientas de IA).

El flujo completo abarca desde el análisis exploratorio de datos (EDA), reducción de dimensionalidad con **PCA**, entrenamiento y comparación de **K-Means** y **DBSCAN** dentro de pipelines reproducibles de `scikit-learn`, hasta la puesta en marcha de una **aplicación web interactiva en Streamlit** que clasifica nuevos registros y alerta sobre perfiles atípicos.

---

## Características principales

- **Preprocesamiento sin fuga de datos (*data leakage*):** Escalado mediante `StandardScaler` integrado en el `Pipeline` exportado con `joblib`.
- **Reducción de dimensionalidad (PCA):** Proyección en 2 componentes principales (`PC1`: intensidad de trabajo; `PC2`: desgaste frente a descanso), que retienen el **60.3 %** de la varianza para visualización espacial.
- **Segmentación con K-Means ($K = 3$):** Selección fundamentada mediante método del codo, coeficiente de Silhouette y accionabilidad de negocio sobre las 8 variables continuas escaladas:
  1. **Intensivos en equilibrio:** Alta dedicación y uso de herramientas de IA con buen descanso, baja carga cognitiva y alta tasa de éxito en tareas.
  2. **Intensivos en riesgo de desgaste:** Jornada intensa pero con déficit de sueño, alta carga cognitiva y mayor incidencia de *bugs*.
  3. **Baja actividad:** Menor volumen de horas de código, *commits* y adopción de IA, con baja tasa de tareas completadas con éxito.
- **Detección de perfiles atípicos con DBSCAN:** Uso de la distancia al punto *core* más cercano (`NearestNeighbors` con `min_samples = 16`) frente al umbral `eps` para advertir cuando un nuevo registro se aleja de la distribución histórica.
- **Aplicación web en Streamlit:** Formulario validado en escala original, asignación instantánea de segmento con recomendaciones accionables, comparativa frente al promedio del grupo (en unidades originales y puntaje $Z$) y mapa interactivo PCA 2D.

---

## Estructura del repositorio

```text
PROYECTORDA2/
├── .streamlit/
│   └── config.toml                   # Configuración visual y tema de la app
├── app/
│   ├── app.py                        # Interfaz de usuario en Streamlit
│   └── servicio.py                   # Carga en caché del artefacto, validación e inferencia
├── data/
│   └── ai_dev_productivity.csv       # Dataset original (500 filas, 9 columnas)
├── docs/
│   └── MANUAL_INSTALACION.md         # Guía detallada de instalación y resolución de problemas
├── models/
│   └── modelo_clustering.pkl         # Artefacto serializado (Pipeline, PCA 2D, detector DBSCAN y metadatos)
├── notebooks/
│   └── Proyecto2_Clustering.ipynb    # Notebook con EDA, PCA, modelado, evaluación y exportación
├── requirements.txt                  # Dependencias con versiones fijadas (Python 3.12)
└── README.md
```

---

## Requisitos previos

- **Sistema operativo:** Windows 10 / 11 (comandos indicados para PowerShell)
- **Python:** `3.12.x`

---

## Instalación y ejecución rápida

1. **Clonar el repositorio y entrar a la carpeta del proyecto:**

   ```powershell
   git clone https://github.com/eisefaaabri/proyecto-ia-rda2-DevCare-ChachaAriel.git
   cd proyecto-ia-rda2-DevCare-ChachaAriel
   ```

2. **Crear y activar el entorno virtual:**

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   *(Si PowerShell restringe la ejecución de scripts, ejecuta antes `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned`).*

3. **Instalar las dependencias exactas:**

   ```powershell
   python -m pip install -r requirements.txt
   ```

4. **Iniciar la aplicación web en Streamlit:**

   ```powershell
   python -m streamlit run app/app.py
   ```

   La aplicación se abrirá automáticamente en `http://localhost:8501`.

5. **Abrir o re-ejecutar el notebook (opcional):**

   El modelo ya se incluye pre-entrenado en `models/modelo_clustering.pkl`. Si deseas inspeccionar o ejecutar el notebook desde cero:

   ```powershell
   python -m jupyter notebook notebooks/Proyecto2_Clustering.ipynb
   ```

Para más detalles sobre pruebas de verificación y solución de problemas frecuentes, consulta [docs/MANUAL_INSTALACION.md](docs/MANUAL_INSTALACION.md).

---

## Tecnologías utilizadas

- **Python 3.12**
- **scikit-learn 1.9.1** (`StandardScaler`, `PCA`, `KMeans`, `DBSCAN`, `NearestNeighbors`, `Pipeline`)
- **pandas 3.1.1** y **numpy 2.5.4**
- **matplotlib 3.11.2**, **seaborn 0.13.2** y **altair 6.3.0**
- **Streamlit 1.67.0**
- **joblib 1.6.0**
