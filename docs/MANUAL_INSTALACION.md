# Manual de instalación y ejecución local

Proyecto 2 · Clustering con Machine Learning y Aplicación Web

Este procedimiento se probó el 15 de noviembre de 2026 en Windows 11 con Python 3.12.10, partiendo
de un entorno virtual vacío: la instalación, el notebook completo y la app terminaron sin errores.

## 1. Requisitos

| Requisito | Detalle |
|---|---|
| Sistema operativo | Windows 10 u 11 (los comandos están escritos para PowerShell) |
| Python | 3.12. Comprobar con `python --version` |
| Espacio en disco | Unos 800 MB para el entorno virtual |
| Navegador | Chrome, Edge o Firefox |
| Internet | Solo para instalar las dependencias; la app funciona sin conexión |

Si `python` no se reconoce o abre la Microsoft Store, instalar Python 3.12 con:

```powershell
winget install -e --id Python.Python.3.12
```

Después hay que cerrar y volver a abrir PowerShell.

## 2. Contenido de la carpeta

```
PROYECTORDA2/
├── app/
│   ├── app.py                  Interfaz Streamlit
│   └── servicio.py             Carga del modelo, validación y asignación
├── models/
│   └── modelo_clustering.pkl   Pipeline exportado (lo genera el notebook)
├── data/
│   └── ai_dev_productivity.csv
├── notebooks/
│   └── Proyecto2_Clustering.ipynb
├── informe/                    Informe de la aplicación y capturas
├── docs/                       Este manual, el plan y el guion de demostración
├── .streamlit/config.toml      Tema de la app
└── requirements.txt            Dependencias con versiones fijadas
```

La carpeta `.venv` no se entrega: cada equipo la crea en el paso 3.

## 3. Instalación

Abrir PowerShell **dentro de la carpeta `PROYECTORDA2`** y ejecutar, en orden:

```powershell
python -m venv .venv
```

```powershell
.\.venv\Scripts\Activate.ps1
```

```powershell
python -m pip install -r requirements.txt
```

Al activar el entorno, el indicador de la terminal empieza con `(.venv)`. La instalación tarda unos
minutos.

**Si PowerShell bloquea la activación** con un mensaje sobre la ejecución de scripts, hay dos
salidas:

- Permitirla solo para esa ventana y volver a activar:

  ```powershell
  Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
  ```

- O no activar el entorno y llamar a su Python directamente. Equivale a lo anterior:

  ```powershell
  .\.venv\Scripts\python.exe -m pip install -r requirements.txt
  ```

## 4. Ejecutar la aplicación

Desde la carpeta `PROYECTORDA2`, con el entorno activado:

```powershell
python -m streamlit run app/app.py
```

Sin activar el entorno:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app/app.py
```

- Streamlit abre el navegador en `http://localhost:8501`. Si no lo abre, escribir esa dirección.
- Para detener la app, presionar `Ctrl + C` en la terminal.
- La primera vez Streamlit puede pedir un correo: se deja vacío y se presiona Enter.

Es importante lanzar el comando desde `PROYECTORDA2` y no desde `app/`, para que se aplique el tema
de `.streamlit/config.toml`.

## 5. Ejecutar el notebook

El modelo exportado ya viene en `models/`. Solo hace falta ejecutar el notebook para revisar el
análisis o para regenerar el archivo `.pkl`.

Abrirlo en el navegador:

```powershell
python -m jupyter notebook notebooks/Proyecto2_Clustering.ipynb
```

Y elegir **Run → Run All Cells**. Otra opción es ejecutarlo completo desde la terminal, sin abrirlo:

```powershell
python -m jupyter nbconvert --to notebook --execute --inplace notebooks/Proyecto2_Clustering.ipynb
```

En ambos casos la sección 10 vuelve a escribir `models/modelo_clustering.pkl`. Si la app estaba
abierta, hay que detenerla y lanzarla de nuevo para que cargue el archivo nuevo.

También se puede abrir el notebook en VS Code y seleccionar como kernel el Python de `.venv`.

## 6. Comprobación rápida

Con la app abierta:

1. En **Cargar un ejemplo** elegir «Jornada larga y descansada» y pulsar **Asignar segmento**. Debe
   aparecer «Intensivos en equilibrio».
2. Elegir «Jornada corta» y volver a pulsar el botón. Debe aparecer «Baja actividad».
3. Elegir «Perfil extremo». Debe aparecer el aviso amarillo de **Perfil atípico**.

Si los tres resultados coinciden, la instalación está correcta.

## 7. Problemas frecuentes

| Síntoma | Causa | Solución |
|---|---|---|
| `python` no se reconoce | Python no está instalado o no está en el PATH | Instalarlo con `winget` (sección 1) y reabrir PowerShell |
| «No se encontró el modelo exportado» | Falta `models/modelo_clustering.pkl` | Ejecutar el notebook completo (sección 5) |
| «El archivo del modelo no se pudo leer» o aviso de versión de scikit-learn | Librerías distintas a las de `requirements.txt` | Reinstalar con `python -m pip install -r requirements.txt` dentro de `.venv` |
| `No module named streamlit` | El comando no usó el Python del entorno | Activar `.venv` o usar `.\.venv\Scripts\python.exe` |
| `Port 8501 is already in use` | Hay otra instancia de la app abierta | Cerrarla, o añadir `--server.port 8502` al comando |
| La app no encuentra `app/app.py` | La terminal no está en `PROYECTORDA2` | Entrar a la carpeta con `cd` antes de lanzar el comando |
