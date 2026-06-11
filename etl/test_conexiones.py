import psycopg2
from pymongo import MongoClient
from cassandra.cluster import Cluster
import redis

print("=== PROBANDO CONEXIONES ===")

# PostgreSQL
try:
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="red_social_db",
        user="postgres",
        password="postgres"
    )
    print("✅ PostgreSQL OK")
    conn.close()

except Exception as e:
    print("❌ PostgreSQL:", e)

# MongoDB
try:
    mongo = MongoClient("mongodb://localhost:27017/")
    mongo.admin.command("ping")

    print("✅ MongoDB OK")

except Exception as e:
    print("❌ MongoDB:", e)

# Redis
try:
    r = redis.Redis(
        host="localhost",
        port=6379,
        decode_responses=True
    )

    r.ping()

    print("✅ Redis OK")

except Exception as e:
    print("❌ Redis:", e)

# Cassandra
try:
    cluster = Cluster(["localhost"])

    session = cluster.connect()

    print("✅ Cassandra OK")

    cluster.shutdown()

except Exception as e:
    print("❌ Cassandra:", e)