# Red Social Políglota — Resumen de Tecnologías

---

## ¿Qué es la Persistencia Políglota?

> Usar **el motor de base de datos correcto para cada tipo de dato**, en lugar de forzar todo en un solo sistema.

En este proyecto **cinco tecnologías trabajan juntas**, cada una haciendo lo que mejor sabe hacer.

---

## Las 5 tecnologías y su rol

| Tecnología | Tipo | ¿Qué hace aquí? |
|---|---|---|
| **PostgreSQL** | Relacional SQL | Fuente principal de datos. Almacena usuarios, publicaciones, comentarios y amistades con integridad garantizada. |
| **MongoDB** | Documental NoSQL | Almacena publicaciones con sus comentarios anidados como un solo documento JSON. |
| **Cassandra** | Columnar distribuido | Almacena relaciones de amistad orientadas a consulta rápida por usuario. |
| **Redis** | Caché en memoria | Guarda el feed de noticias ya calculado para servirlo al instante. |
| **Python** | Puente de integración | Conecta todos los motores. Extrae de PostgreSQL, transforma y carga en los demás. |

---

## Cómo se relacionan entre sí

```
                    ┌─────────────────────┐
                    │    Interfaz PyQt6   │
                    └────────┬────────────┘
                             │
               ┌─────────────▼──────────────┐
               │         Python             │
               │   (ETL + lógica de app)    │
               └──┬──────┬───────┬──────────┘
                  │      │       │
         ┌────────▼─┐  ┌─▼──┐  ┌▼────────┐
         │PostgreSQL│  │    │  │  Redis  │
         │ (fuente  │  │Mongo│  │ (caché) │
         │ principal│  │ DB  │  └─────────┘
         └────┬─────┘  └─────┘
              │          ▲
              │          │ publica con
              │          │ comentarios
              │        ┌─┴───────┐
              └───────►│Cassandra│
               amistad │         │
                       └─────────┘
```

---

## El flujo en 3 pasos

### 1. Los datos nacen en PostgreSQL
- Tablas normalizadas: `usuarios`, `publicaciones`, `comentarios`, `amistades`.
- Reglas de integridad: llaves foráneas, restricciones y procedimientos almacenados.
- Es la **única fuente de verdad**.

### 2. Python corre el ETL y distribuye los datos
- **→ MongoDB:** toma cada publicación + sus comentarios y los guarda como un solo documento.
- **→ Redis:** consulta el feed de noticias y lo serializa como JSON en memoria.
- **→ Cassandra:** migra las relaciones de amistad a una tabla distribuida lista para consultas por usuario.

### 3. La interfaz PyQt6 lo une todo
- Botón **"Ejecutar ETL"** → dispara el proceso Python completo.
- Botón **"Crear Amistad"** → llama al procedimiento almacenado en PostgreSQL.
- Botón **"Cargar Feed"** → consulta la vista SQL y muestra los datos en tabla.

---

## ¿Por qué cada motor?

```
  PostgreSQL → necesito consistencia e integridad
  MongoDB    → necesito leer una publicación con TODOS sus comentarios de una vez
  Cassandra  → necesito escalar las relaciones entre millones de usuarios
  Redis      → necesito que el feed cargue rápido sin recalcular cada vez
```

---

## Stack de infraestructura

Todos los motores corren en **Docker** con un solo archivo `docker-compose.yml`:

```
postgres   → puerto 5432
mongodb    → puerto 27017
redis      → puerto 6379
cassandra  → puerto 9042
```

Un único comando `docker compose up` levanta todo el entorno.

---

## Dependencias Python

```
psycopg2-binary   → habla con PostgreSQL
pymongo           → habla con MongoDB
cassandra-driver  → habla con Cassandra
redis             → habla con Redis
PyQt6             → construye la interfaz gráfica
```

---

## En una sola línea

> PostgreSQL guarda todo con integridad → Python lo transforma y lo distribuye → MongoDB, Cassandra y Redis lo sirven rápido según el contexto → PyQt6 lo muestra al usuario.
