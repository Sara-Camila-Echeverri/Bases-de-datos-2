-- =============================================================================
-- 01_script_inicial.sql
-- Crea la estructura base de la base de datos relacional de la red social.
-- En esta fase las tablas se definen SIN claves foráneas intencionalmente,
-- ya que los datos de origen pueden tener inconsistencias que se limpian en
-- la fase siguiente (02_fase1_integridad.sql).
-- =============================================================================


-- 1. Tabla de Usuarios
--    Almacena los perfiles de cada miembro de la red social.
--    'email' tiene restricción UNIQUE para evitar cuentas duplicadas.
CREATE TABLE usuarios (
    id_usuario      SERIAL PRIMARY KEY,
    nombre          VARCHAR(100) NOT NULL,
    email           VARCHAR(100) UNIQUE NOT NULL,
    fecha_registro  DATE DEFAULT CURRENT_DATE,
    pais            VARCHAR(50)
);


-- 2. Tabla de Publicaciones (Posts)
--    Cada fila representa un mensaje publicado por un usuario.
--    'autor_id' referencia a usuarios pero la FK se añade en la fase 2,
--    una vez que se hayan eliminado las publicaciones con autor inexistente.
CREATE TABLE publicaciones (
    id_publicacion    SERIAL PRIMARY KEY,
    texto_contenido   TEXT,
    fecha_publicacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    likes_contador    INT DEFAULT 0,
    autor_id          INT NOT NULL   -- FK pendiente (se agrega en fase 2)
);


-- 3. Tabla de Comentarios
--    Asocia un texto de comentario a una publicación y a su autor.
--    Igual que en publicaciones, las FKs se aplican después de limpiar datos.
CREATE TABLE comentarios (
    id_comentario    SERIAL PRIMARY KEY,
    contenido        VARCHAR(255),
    fecha_comentario TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usuario_id       INT NOT NULL,   -- FK a usuarios (pendiente)
    publicacion_id   INT NOT NULL    -- FK a publicaciones (pendiente)
);


-- 4. Tabla de Amistades (Relación Muchos a Muchos entre usuarios)
--    Modela el grafo social: cada fila es una arista entre dos usuarios.
--    El campo 'estado' indica si la amistad está 'ACEPTADA' o 'PENDIENTE'.
--    Se usa un id_amistad como PK surrogate; la unicidad del par se garantiza
--    mediante un índice parcial añadido en la fase 2.
CREATE TABLE amistades (
    id_amistad             SERIAL PRIMARY KEY,
    fecha_amistad          DATE DEFAULT CURRENT_DATE,
    estado                 VARCHAR(20),              -- 'ACEPTADA' | 'PENDIENTE'
    usuario_solicitante_id INT NOT NULL,             -- FK pendiente
    usuario_receptor_id    INT NOT NULL              -- FK pendiente
);
