import json
import psycopg2
import redis

from pymongo import MongoClient

# ==========================================
# CONEXIONES
# ==========================================

def conectar_postgres():

    return psycopg2.connect(
        host="localhost",
        port=5432,
        database="red_social_db",
        user="postgres",
        password="postgres"
    )


def conectar_mongo():

    cliente = MongoClient(
        "mongodb://localhost:27017/"
    )

    return cliente["red_social_db"]


def conectar_redis():

    return redis.Redis(
        host="localhost",
        port=6379,
        decode_responses=True
    )


# ==========================================
# MONGO
# ==========================================

def migrar_publicaciones_mongo():

    conn = None
    cursor = None

    try:

        conn = conectar_postgres()
        cursor = conn.cursor()

        db = conectar_mongo()

        coleccion = db["publicaciones"]

        coleccion.delete_many({})

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

        for pub in publicaciones:

            id_publicacion = pub[0]

            cursor.execute("""
                SELECT
                    c.id_comentario,
                    c.contenido,
                    c.fecha_comentario,
                    u.nombre
                FROM comentarios c
                JOIN usuarios u
                    ON c.usuario_id = u.id_usuario
                WHERE c.publicacion_id = %s
            """, (id_publicacion,))

            comentarios = cursor.fetchall()

            comentarios_json = []

            for comentario in comentarios:

                comentarios_json.append({
                    "id_comentario": comentario[0],
                    "texto": comentario[1],
                    "fecha": str(comentario[2]),
                    "usuario": comentario[3]
                })

            documento = {

                "id_publicacion": pub[0],
                "contenido": pub[1],
                "fecha_publicacion": str(pub[2]),
                "likes": pub[3],
                "autor": pub[4],
                "comentarios": comentarios_json

            }

            coleccion.insert_one(documento)

        print("MongoDB OK")

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# ==========================================
# REDIS
# ==========================================

def migrar_feed_redis():

    conn = None
    cursor = None

    try:

        conn = conectar_postgres()
        cursor = conn.cursor()

        r = conectar_redis()

        cursor.execute("""
            SELECT *
            FROM vista_feed_noticias
        """)

        feed = cursor.fetchall()

        feed_json = []

        for fila in feed:

            feed_json.append({
                "id_publicacion": fila[0],
                "autor": fila[1],
                "contenido": fila[2],
                "fecha": str(fila[3]),
                "likes": fila[4],
                "comentarios": fila[5]
            })

        r.set(
            "feed_noticias",
            json.dumps(feed_json)
        )

        print("Redis OK")

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# ==========================================
# CASSANDRA (opcional)
# ==========================================

def migrar_amistades_cassandra():

    try:

        from cassandra.cluster import Cluster

        cluster = Cluster(["localhost"])

        session = cluster.connect()

        session.execute("""
            CREATE KEYSPACE IF NOT EXISTS red_social
            WITH replication = {
                'class':'SimpleStrategy',
                'replication_factor':1
            }
        """)

        session.set_keyspace("red_social")

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

        conn = conectar_postgres()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                usuario_solicitante_id,
                usuario_receptor_id,
                estado
            FROM amistades
        """)

        for fila in cursor.fetchall():

            session.execute("""
                INSERT INTO amistades
                (
                    usuario_id,
                    amigo_id,
                    estado
                )
                VALUES (%s,%s,%s)
            """, fila)

        cursor.close()
        conn.close()

        cluster.shutdown()

        print("Cassandra OK")

    except Exception as e:

        print(
            f"Cassandra omitida: {e}"
        )


# ==========================================
# ETL PRINCIPAL
# ==========================================

def ejecutar_etl():

    print("===== ETL INICIADO =====")

    migrar_publicaciones_mongo()

    migrar_feed_redis()

    migrar_amistades_cassandra()

    print("===== ETL FINALIZADO =====")


if __name__ == "__main__":

    ejecutar_etl()