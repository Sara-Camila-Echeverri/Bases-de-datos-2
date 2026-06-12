# =============================================================================
# app.py
# Interfaz gráfica de administración de la Red Social Políglota.
# Construida con PyQt6, permite al operador:
#   - Ejecutar el proceso ETL completo (PostgreSQL → MongoDB/Redis/Cassandra).
#   - Crear solicitudes de amistad entre dos usuarios.
#   - Visualizar el feed de noticias en una tabla.
# =============================================================================

import os
import sys

import psycopg2

# Agrega el directorio raíz del proyecto al path para que Python encuentre
# el paquete 'etl' independientemente de desde dónde se ejecute el script.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from etl.etl_poliglota import ejecutar_etl

# -----------------------------------------------------------------------------
# PARÁMETROS DE CONEXIÓN A POSTGRESQL
# Centralizados aquí para facilitar el cambio sin tocar múltiples métodos.
# -----------------------------------------------------------------------------
_PG_CONN = dict(
    host="localhost",
    port=5432,
    database="red_social_db",
    user="postgres",
    password="postgres",
)


class AdminPanel(QWidget):
    """Ventana principal del panel de administración."""

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Panel Administrador - Red Social Políglota")
        self.resize(1000, 700)

        self.init_ui()

    def init_ui(self):
        """Construye y organiza todos los widgets de la ventana."""

        layout_principal = QVBoxLayout()

        # Título de la sección
        titulo = QLabel("Administración de Red Social")
        layout_principal.addWidget(titulo)

        # Botón que dispara el proceso ETL completo
        self.btn_etl = QPushButton("Ejecutar Proceso ETL Políglota")
        self.btn_etl.clicked.connect(self.ejecutar_etl)
        layout_principal.addWidget(self.btn_etl)

        # Área de log de solo lectura donde se muestran mensajes de estado del ETL
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        layout_principal.addWidget(self.log)

        # ============================
        # FORMULARIO: CREAR AMISTAD
        # Dos campos de texto para los IDs de usuario y un botón de acción.
        # ============================
        form_layout = QHBoxLayout()

        self.id1 = QLineEdit()
        self.id1.setPlaceholderText("ID Usuario 1")

        self.id2 = QLineEdit()
        self.id2.setPlaceholderText("ID Usuario 2")

        btn_amistad = QPushButton("Crear Amistad")
        btn_amistad.clicked.connect(self.crear_amistad)

        form_layout.addWidget(self.id1)
        form_layout.addWidget(self.id2)
        form_layout.addWidget(btn_amistad)

        layout_principal.addLayout(form_layout)

        # ============================
        # TABLA: FEED DE NOTICIAS
        # Se rellena dinámicamente al presionar "Cargar Feed".
        # ============================
        self.tabla = QTableWidget()
        layout_principal.addWidget(self.tabla)

        btn_cargar_feed = QPushButton("Cargar Feed")
        btn_cargar_feed.clicked.connect(self.cargar_feed)
        layout_principal.addWidget(btn_cargar_feed)

        self.setLayout(layout_principal)

    # ------------------------------------------------------------------
    # SLOT: EJECUTAR ETL
    # Llama a ejecutar_etl() del módulo etl_poliglota y registra el
    # resultado en el área de log. Cualquier excepción se captura y
    # se muestra sin detener la aplicación.
    # ------------------------------------------------------------------
    def ejecutar_etl(self):
        try:
            self.log.append("Iniciando ETL...")
            ejecutar_etl()
            self.log.append("ETL ejecutado correctamente.")
        except Exception as e:
            self.log.append(f"ERROR ETL: {e}")

    # ------------------------------------------------------------------
    # SLOT: CREAR AMISTAD
    # Lee los IDs de los campos de texto, llama a la función PL/pgSQL
    # 'crear_amistad(id1, id2)' en PostgreSQL y muestra el mensaje de
    # retorno en un diálogo. La función en la BD valida que los usuarios
    # existan, no sean el mismo y que la amistad no esté duplicada.
    # ------------------------------------------------------------------
    def crear_amistad(self):
        try:
            usuario1 = int(self.id1.text())
            usuario2 = int(self.id2.text())

            conn = psycopg2.connect(**_PG_CONN)
            cursor = conn.cursor()

            # La función devuelve un texto con el resultado de la operación
            cursor.execute("SELECT crear_amistad(%s,%s)", (usuario1, usuario2))
            resultado = cursor.fetchone()

            if resultado is None:
                raise RuntimeError("El procedimiento no devolvió ningún resultado.")

            conn.commit()

            QMessageBox.information(self, "Éxito", resultado[0])

            cursor.close()
            conn.close()

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    # ------------------------------------------------------------------
    # SLOT: CARGAR FEED
    # Consulta la vista 'vista_feed_noticias' en PostgreSQL (máx. 20
    # filas) y puebla la QTableWidget con los resultados. Los nombres de
    # columna se obtienen dinámicamente desde el cursor para que la tabla
    # se adapte si la vista cambia en el futuro.
    # ------------------------------------------------------------------
    def cargar_feed(self):
        try:
            conn = psycopg2.connect(**_PG_CONN)
            cursor = conn.cursor()

            # La vista ya ordena por fecha descendente y agrega el conteo de comentarios
            cursor.execute("""
                SELECT *
                FROM vista_feed_noticias
                LIMIT 20
            """)

            datos = cursor.fetchall()

            if cursor.description is None:
                raise RuntimeError("La consulta del feed no devolvió columnas.")

            # Extrae los nombres de columna desde los metadatos del cursor
            columnas = [desc[0] for desc in cursor.description]

            # Configura la tabla con las dimensiones correctas
            self.tabla.setRowCount(len(datos))
            self.tabla.setColumnCount(len(columnas))
            self.tabla.setHorizontalHeaderLabels(columnas)

            # Rellena celda a celda convirtiendo todos los valores a string
            for fila_idx, fila in enumerate(datos):
                for col_idx, valor in enumerate(fila):
                    self.tabla.setItem(fila_idx, col_idx, QTableWidgetItem(str(valor)))

            cursor.close()
            conn.close()

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


# -----------------------------------------------------------------------------
# PUNTO DE ENTRADA
# Crea la aplicación Qt, instancia el panel y entra al bucle de eventos.
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)

    ventana = AdminPanel()
    ventana.show()

    sys.exit(app.exec())
