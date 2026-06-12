import sys
import psycopg2
sys.path.append(
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            ".."
        )
    )
)
from etl.etl_poliglota import ejecutar_etl

from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QTextEdit,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
)

# Importar ETL
# Ajusta la ruta según tu estructura
# from etl.etl_poliglota import ejecutar_etl


class AdminPanel(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Panel Administrador - Red Social Políglota")
        self.resize(1000, 700)

        self.init_ui()

    def init_ui(self):

        layout_principal = QVBoxLayout()

        titulo = QLabel("Administración de Red Social")
        layout_principal.addWidget(titulo)

        # ============================
        # BOTÓN ETL
        # ============================

        self.btn_etl = QPushButton(
            "Ejecutar Proceso ETL Políglota"
        )

        self.btn_etl.clicked.connect(
            self.ejecutar_etl
        )

        layout_principal.addWidget(
            self.btn_etl
        )

        # ============================
        # LOG
        # ============================

        self.log = QTextEdit()
        self.log.setReadOnly(True)

        layout_principal.addWidget(
            self.log
        )

        # ============================
        # FORM AMISTAD
        # ============================

        form_layout = QHBoxLayout()

        self.id1 = QLineEdit()
        self.id1.setPlaceholderText(
            "ID Usuario 1"
        )

        self.id2 = QLineEdit()
        self.id2.setPlaceholderText(
            "ID Usuario 2"
        )

        btn_amistad = QPushButton(
            "Crear Amistad"
        )

        btn_amistad.clicked.connect(
            self.crear_amistad
        )

        form_layout.addWidget(self.id1)
        form_layout.addWidget(self.id2)
        form_layout.addWidget(btn_amistad)

        layout_principal.addLayout(
            form_layout
        )

        # ============================
        # TABLA FEED
        # ============================

        self.tabla = QTableWidget()

        layout_principal.addWidget(
            self.tabla
        )

        btn_cargar_feed = QPushButton(
            "Cargar Feed"
        )

        btn_cargar_feed.clicked.connect(
            self.cargar_feed
        )

        layout_principal.addWidget(
            btn_cargar_feed
        )

        self.setLayout(
            layout_principal
        )

    # ==================================
    # ETL
    # ==================================

    def ejecutar_etl(self):

        try:
            self.log.append(
                "Iniciando ETL..."
            )

            ejecutar_etl()

            self.log.append(
                "ETL ejecutado correctamente."
            )

        except Exception as e:

            self.log.append(
                f"ERROR ETL: {e}"
            )
            
    # ==================================
    # CREAR AMISTAD
    # ==================================

    def crear_amistad(self):

        try:

            usuario1 = int(
                self.id1.text()
            )

            usuario2 = int(
                self.id2.text()
            )

            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                database="red_social_db",
                user="postgres",
                password="postgres"
            )

            cursor = conn.cursor()

            cursor.execute(
                "SELECT crear_amistad(%s,%s)",
                (usuario1, usuario2)
            )

            resultado = cursor.fetchone()

            conn.commit()

            QMessageBox.information(
                self,
                "Éxito",
                resultado[0]
            )

            cursor.close()
            conn.close()

        except Exception as e:

            QMessageBox.critical(
                self,
                "Error",
                str(e)
            )

    # ==================================
    # FEED
    # ==================================

    def cargar_feed(self):

        try:

            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                database="red_social_db",
                user="postgres",
                password="postgres"
            )

            cursor = conn.cursor()

            cursor.execute("""
                SELECT *
                FROM vista_feed_noticias
                LIMIT 20
            """)

            datos = cursor.fetchall()

            columnas = [desc[0]
                         for desc
                         in cursor.description]

            self.tabla.setRowCount(
                len(datos)
            )

            self.tabla.setColumnCount(
                len(columnas)
            )

            self.tabla.setHorizontalHeaderLabels(
                columnas
            )

            for fila_idx, fila in enumerate(datos):

                for col_idx, valor in enumerate(fila):

                    self.tabla.setItem(
                        fila_idx,
                        col_idx,
                        QTableWidgetItem(
                            str(valor)
                        )
                    )

            cursor.close()
            conn.close()

        except Exception as e:

            QMessageBox.critical(
                self,
                "Error",
                str(e)
            )


if __name__ == "__main__":

    app = QApplication(sys.argv)

    ventana = AdminPanel()

    ventana.show()

    sys.exit(app.exec())