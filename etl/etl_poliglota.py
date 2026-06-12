# =============================================================================
# etl_poliglota.py
# Módulo ETL (Extract, Transform, Load) de la Red Social Políglota.
# Se encarga de extraer datos desde PostgreSQL y cargarlos en las bases de
# datos NoSQL: MongoDB (publicaciones + comentarios), Redis (feed en caché)
# y Cassandra (amistades).
# =============================================================================

import json

import psycopg2
import redis
from pymongo import MongoClient

# -----------------------------------------------------------------------------
# FUNCIONES DE CONEXIÓN
# Cada función devuelve un objeto de conexión/cliente listo para usar.
# -----------------------------------------------------------------------------


def conectar_postgres():
    """Abre y devuelve una conexión a la base de datos PostgreSQL."""
    return psycopg2.connect(
        host="localhost",
        port=5432,
        database="red_social_db",
        user="postgres",
        password="postgres",
    )


def conectar_mongo():
    """Conecta al servidor MongoDB y devuelve la base de datos 'red_social_db'."""
    cliente = MongoClient("mongodb://localhost:27017/")
    return cliente["red_social_db"]


def conectar_redis():
    """Conecta a Redis y devuelve el cliente configurado para decodificar respuestas como strings."""
    return redis.Redis(host="localhost", port=6379, decode_responses=True)


# -----------------------------------------------------------------------------
# MIGRACIÓN A MONGODB
# Exporta cada publicación de PostgreSQL junto con sus comentarios anidados
# como un único documento JSON en la colección 'publicaciones' de MongoDB.
# Esto permite leer una publicación con todos sus comentarios en una sola
# consulta, aprovechando el modelo de documentos de MongoDB.
# -----------------------------------------------------------------------------


def migrar_publicaciones_mongo():

    conn = None
    cursor = None

    try:
        # Abre conexiones a PostgreSQL y MongoDB
        conn = conectar_postgres()
        cursor = conn.cursor()
        db = conectar_mongo()

        coleccion = db["publicaciones"]

        # Limpia la colección antes de recargar para evitar duplicados
        coleccion.delete_many({})

        # Obtiene todas las publicaciones junto con el nombre de su autor
        cursor.execute("""
            SELECT
                p.id_publicacion,
                p.texto_contenido,
                p.fecha_publicacion,
                p.likes_contador,
                u.nombre
            FROM publicaciones p
            JOIN usuarios u
                ON p.autor_id = u.id_usuario
        """)

        publicaciones = cursor.fetchall()

        # Recorre cada publicación y construye el documento a insertar en Mongo
        for pub in publicaciones:
            id_publicacion = pub[0]

            # Obtiene los comentarios de esta publicación junto al nombre del usuario
            cursor.execute(
                """
                SELECT
                    c.id_comentario,
                    c.contenido,
                    c.fecha_comentario,
                    u.nombre
                FROM comentarios c
                JOIN usuarios u
                    ON c.usuario_id = u.id_usuario
                WHERE c.publicacion_id = %s
            """,
                (id_publicacion,),
            )

            comentarios = cursor.fetchall()

            # Convierte cada comentario a un dict serializable como JSON
            comentarios_json = []
            for comentario in comentarios:
                comentarios_json.append(
                    {
                        "id_comentario": comentario[0],
                        "texto": comentario[1],
                        "fecha": str(comentario[2]),
                        "usuario": comentario[3],
                    }
                )

            # Documento final: publicación con sus comentarios anidados
            documento = {
                "id_publicacion": pub[0],
                "contenido": pub[1],
                "fecha_publicacion": str(pub[2]),
                "likes": pub[3],
                "autor": pub[4],
                "comentarios": comentarios_json,
            }

            coleccion.insert_one(documento)

        print("MongoDB OK")

    finally:
        # Cierra el cursor y la conexión aunque haya ocurrido un error
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# -----------------------------------------------------------------------------
# MIGRACIÓN A REDIS
# Serializa la vista 'vista_feed_noticias' de PostgreSQL a JSON y la almacena
# en Redis bajo la clave "feed_noticias". Redis actúa como caché de lectura
# rápida para el feed de la interfaz de usuario.
# -----------------------------------------------------------------------------


def migrar_feed_redis():

    conn = None
    cursor = None

    try:
        conn = conectar_postgres()
        cursor = conn.cursor()
        r = conectar_redis()

        # Lee el feed completo desde la vista de PostgreSQL
        cursor.execute("""
            SELECT *
            FROM vista_feed_noticias
        """)

        feed = cursor.fetchall()

        # Convierte cada fila a un diccionario con claves legibles
        feed_json = []
        for fila in feed:
            feed_json.append(
                {
                    "id_publicacion": fila[0],
                    "autor": fila[1],
                    "contenido": fila[2],
                    "fecha": str(fila[3]),
                    "likes": fila[4],
                    "comentarios": fila[5],
                }
            )

        # Guarda la lista serializada en Redis; expira cuando se vuelva a ejecutar el ETL
        r.set("feed_noticias", json.dumps(feed_json))

        print("Redis OK")

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# -----------------------------------------------------------------------------
# MIGRACIÓN A CASSANDRA
# Crea el keyspace y la tabla de amistades en Cassandra (si no existen) y
# carga todas las relaciones de amistad desde PostgreSQL.
# Cassandra está optimizada para lecturas de alta velocidad por clave primaria,
# lo que la hace adecuada para consultas del tipo "dame todos los amigos del
# usuario X". Si Cassandra no está disponible, la función lo informa y continúa.
# -----------------------------------------------------------------------------


def migrar_amistades_cassandra():

    try:
        from cassandra.cluster import Cluster

        # Conecta al clúster local de Cassandra
        cluster = Cluster(["localhost"])
        session = cluster.connect()

        # Crea el keyspace (espacio de nombres) si todavía no existe
        session.execute("""
            CREATE KEYSPACE IF NOT EXISTS red_social
            WITH replication = {
                'class':'SimpleStrategy',
                'replication_factor':1
            }
        """)

        session.set_keyspace("red_social")

        # Crea la tabla de amistades con clave primaria compuesta:
        # usuario_id (partition key) + amigo_id (clustering key)
        session.execute("""
            CREATE TABLE IF NOT EXISTS amistades (
                usuario_id INT,
                amigo_id INT,
                estado TEXT,
                PRIMARY KEY (
                    usuario_id,
                    amigo_id
                )
            )
        """)

        # Lee todas las amistades desde PostgreSQL
        conn = conectar_postgres()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                usuario_solicitante_id,
                usuario_receptor_id,
                estado
            FROM amistades
        """)

        # Inserta cada amistad en Cassandra
        for fila in cursor.fetchall():
            session.execute(
                """
                INSERT INTO amistades
                (
                    usuario_id,
                    amigo_id,
                    estado
                )
                VALUES (%s,%s,%s)
            """,
                fila,
            )

        cursor.close()
        conn.close()
        cluster.shutdown()

        print("Cassandra OK")

    except Exception as e:
        # Cassandra es opcional; si no está disponible se omite sin detener el ETL
        print(f"Cassandra omitida: {e}")


# -----------------------------------------------------------------------------
# PUNTO DE ENTRADA DEL ETL
# Ejecuta las tres migraciones en orden. Se puede invocar directamente desde
# la línea de comandos o desde la interfaz gráfica (AdminPanel).
# -----------------------------------------------------------------------------


def ejecutar_etl():

    print("===== ETL INICIADO =====")

    migrar_publicaciones_mongo()  # PostgreSQL → MongoDB
    migrar_feed_redis()  # PostgreSQL → Redis
    migrar_amistades_cassandra()  # PostgreSQL → Cassandra

    print("===== ETL FINALIZADO =====")


if __name__ == "__main__":
    ejecutar_etl()
