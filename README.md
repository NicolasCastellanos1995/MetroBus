# MetroBus --- Proyecto Final de Data Analytics

Análisis de la operación de MetroBus a partir de datos de viajes,
incidencias, mantenimiento, vehículos, conductores, líneas, paradas,
tarifas y depósitos.

## Stack tecnológico

-   Python 3.13
-   pandas, NumPy, Matplotlib, SQLAlchemy y psycopg2
-   PostgreSQL
-   Docker / Docker Compose
-   Power BI
-   Jupyter Notebook

## Ejecución

Requisitos: Docker Desktop y Jupyter/Python.

1.  Clonar el repositorio.
2.  Copiar `.env.example` como `.env`.
3.  Levantar PostgreSQL y ejecutar el ETL:

``` bash
docker compose up --build
```

El pipeline carga los CSV de `data/raw`, aplica las transformaciones y
carga los datos limpios en PostgreSQL.

Para reproducir la fase de análisis exploratorio:

``` bash
jupyter notebook 01_eda.ipynb
```

La fase SQL puede reproducirse mediante `02_sql.sql` sobre la base
PostgreSQL generada.

Conexión local a PostgreSQL:

-   Host: `localhost`
-   Puerto: `5433`
-   Base de datos: `metrobus`
-   Usuario: `metrobus`

##  Arquitectura

```text
┌──────────────────────┐
│      CSV RAW         │
│    data/raw/*.csv    │
└──────────┬───────────┘
           │
           │ Extract
           ▼
┌──────────────────────┐
│     Python ETL       │
│       Pandas         │
│                      │
│  - Limpieza          │
│  - Transformación    │
│  - Validación        │
└──────────┬───────────┘
           │
           │ Load
           ▼
┌──────────────────────┐
│    PostgreSQL 16     │
│       Docker         │
└──────────┬───────────┘
           │
           ├──────────────► SQL
           │
           ▼
┌──────────────────────┐
│      Power BI        │
│      Dashboard       │
└──────────────────────┘
```

##  Estructura del proyecto

```text
tfm/
│
├── data/
│   ├── raw/                    # CSV originales
│   └── processed/              # Datos procesados si fueran necesarios
│
├── sql/
│   └── schema.sql              # Esquema PostgreSQL
│
├── src/
│   └── metrobus/
│       ├── config.py           # Configuración del proyecto
│       ├── extract.py          # Extracción de los CSV
│       ├── transform.py        # Limpieza, transformación y validación
│       ├── load.py             # Carga en PostgreSQL
│       ├── pipeline.py         # Orquestación del ETL
│       └── watch.py            # Monitorización automática de CSV
│
├── 01_eda.ipynb                # Análisis exploratorio de datos
├── 02_sql.sql                  # Consultas SQL de negocio
├── 03_gobierno.md              # Gobierno y calidad del dato
├── 04_dashboard.pbix           # Dashboard Power BI
├── 05_presentacion.pdf         # Presentación ejecutiva
│
├── Dockerfile                  # Imagen del servicio ETL
├── docker-compose.yml          # PostgreSQL + ETL
├── requirements.txt            # Dependencias Python
└── README.md
```

## Actualización automática de los CSV

El servicio ETL utiliza `watchdog` para monitorizar:

```text
data/raw/*.csv
```

Cuando se modifica y guarda uno de los archivos:

```text
CSV modificado
       │
       ▼
watch.py detecta el cambio
       │
       ▼
pipeline.py
       │
       ├── Extract
       ├── Transform
       ├── Validate
       └── Load
       │
       ▼
PostgreSQL actualizado
```

Por ejemplo, si se modifica:

```text
data/raw/dim_linea.csv
```

el contenedor detectará el cambio y mostrará:

```text
Cambio detectado: dim_linea.csv
Ejecutando pipeline...

1/3 Extrayendo CSV...
2/3 Transformando...
3/3 Cargando PostgreSQL...

Pipeline terminado.
Pipeline actualizado correctamente.
```

Por tanto, no es necesario ejecutar manualmente el pipeline cada vez que cambia la fuente.

---

El proyecto distingue entre tres capas:

```text
RAW
 │
 │ datos originales
 ▼
ETL
 │
 │ limpieza + reglas + validaciones
 ▼
POSTGRESQL
 │
 │ datos preparados
 ▼
POWER BI
```

Los archivos originales permanecen sin modificar.

Las transformaciones están implementadas mediante código reproducible y no mediante modificaciones manuales de los CSV.

---

## Decisión no obvia

Los valores atípicos no se eliminaron automáticamente. Se utilizó IQR
para detectarlos y posteriormente se evaluaron mediante reglas de
negocio, conservando aquellos que representaban situaciones operativas
plausibles y corrigiendo únicamente los valores con evidencia de error.

## Hallazgo principal

Los retrasos no se distribuyen uniformemente: cambian según línea,
parada y franja horaria, permitiendo identificar puntos críticos
concretos de la red.

Además, frecuencia e impacto no siempre coinciden: algunas incidencias
menos frecuentes, como los accidentes graves, concentran un coste
estimado considerablemente mayor.
