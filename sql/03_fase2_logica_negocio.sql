-- =============================================================================
-- 03_fase2_logica_negocio.sql
-- Fase 2: lógica de negocio en la base de datos.
--
-- Define:
--   - Función PL/pgSQL 'crear_amistad': valida reglas y registra una solicitud.
--   - Vista 'vista_solicitudes_pendientes': solicitudes aún sin respuesta.
--   - Vista 'vista_amistades_consolidadas': amistades aceptadas con nombres.
--   - Vista 'vista_feed_noticias': publicaciones con conteo de comentarios,
--     usada por la UI y por el ETL de Redis.
-- =============================================================================


-- Elimina objetos previos en orden correcto para evitar conflictos de
-- dependencias entre vistas y funciones al re-ejecutar el script.
DROP VIEW IF EXISTS vista_feed_noticias CASCADE;
DROP VIEW IF EXISTS vista_amistades_consolidadas CASCADE;
DROP VIEW IF EXISTS vista_solicitudes_pendientes CASCADE;
DROP FUNCTION IF EXISTS crear_amistad(INT, INT);


-- =============================================================================
-- FUNCIÓN: crear_amistad(id1 INT, id2 INT) → TEXT
-- Registra una solicitud de amistad entre dos usuarios tras validar:
--   1. Que el usuario id1 exista.
--   2. Que el usuario id2 exista.
--   3. Que id1 ≠ id2 (no autoamistad).
--   4. Que no exista ya una amistad o solicitud pendiente entre ellos.
-- Si todas las validaciones pasan, inserta una fila con estado 'PENDIENTE'
-- y retorna un mensaje de éxito. Cualquier otro error se relanza con contexto.
-- =============================================================================
CREATE OR REPLACE FUNCTION crear_amistad(
    id1 INT,
    id2 INT
)
RETURNS TEXT
LANGUAGE plpgsql
AS
$$
BEGIN

    -- Validación 1: el usuario solicitante debe existir
    IF NOT EXISTS (
        SELECT 1 FROM usuarios WHERE id_usuario = id1
    ) THEN
        RAISE EXCEPTION 'El usuario % no existe.', id1;
    END IF;

    -- Validación 2: el usuario receptor debe existir
    IF NOT EXISTS (
        SELECT 1 FROM usuarios WHERE id_usuario = id2
    ) THEN
        RAISE EXCEPTION 'El usuario % no existe.', id2;
    END IF;

    -- Validación 3: un usuario no puede ser amigo de sí mismo
    IF id1 = id2 THEN
        RAISE EXCEPTION 'Un usuario no puede ser amigo de sí mismo.';
    END IF;

    -- Validación 4: la amistad (en cualquier dirección) no debe existir todavía
    IF EXISTS (
        SELECT 1
        FROM amistades
        WHERE (usuario_solicitante_id = id1 AND usuario_receptor_id = id2)
           OR (usuario_solicitante_id = id2 AND usuario_receptor_id = id1)
    ) THEN
        RAISE EXCEPTION 'La amistad ya existe o tiene una solicitud pendiente.';
    END IF;

    -- Inserta la solicitud con estado inicial PENDIENTE
    INSERT INTO amistades (
        fecha_amistad,
        estado,
        usuario_solicitante_id,
        usuario_receptor_id
    )
    VALUES (
        CURRENT_DATE,
        'PENDIENTE',
        id1,
        id2
    );

    RETURN 'Solicitud de amistad creada correctamente.';

EXCEPTION
    -- Captura cualquier otro error inesperado y lo relanza con contexto
    WHEN OTHERS THEN
        RAISE EXCEPTION 'Error al crear amistad: %', SQLERRM;

END;
$$;


-- =============================================================================
-- VISTA: vista_solicitudes_pendientes
-- Muestra las solicitudes de amistad que aún no han sido aceptadas ni
-- rechazadas, con los nombres legibles de solicitante y receptor.
-- =============================================================================
CREATE OR REPLACE VIEW vista_solicitudes_pendientes AS
SELECT
    a.id_amistad,
    u1.nombre  AS solicitante,
    u2.nombre  AS receptor,
    a.estado,
    a.fecha_amistad
FROM amistades a
INNER JOIN usuarios u1 ON a.usuario_solicitante_id = u1.id_usuario
INNER JOIN usuarios u2 ON a.usuario_receptor_id    = u2.id_usuario
WHERE a.estado = 'PENDIENTE';


-- =============================================================================
-- VISTA: vista_amistades_consolidadas
-- Muestra únicamente las amistades con estado 'ACEPTADA'.
-- Útil para construir el grafo social activo de la red.
-- =============================================================================
CREATE OR REPLACE VIEW vista_amistades_consolidadas AS
SELECT
    a.id_amistad,
    u1.nombre  AS amigo_1,
    u2.nombre  AS amigo_2,
    a.fecha_amistad
FROM amistades a
INNER JOIN usuarios u1 ON a.usuario_solicitante_id = u1.id_usuario
INNER JOIN usuarios u2 ON a.usuario_receptor_id    = u2.id_usuario
WHERE a.estado = 'ACEPTADA';


-- =============================================================================
-- VISTA: vista_feed_noticias
-- Agrega publicaciones con datos de su autor y el total de comentarios.
-- Ordenada por fecha descendente para mostrar lo más reciente primero.
-- Esta vista es usada tanto por la UI (pestaña "Cargar Feed") como por el
-- proceso ETL que la serializa en Redis como caché de lectura rápida.
-- LEFT JOIN en comentarios garantiza que publicaciones sin comentarios
-- aparezcan igual (con total_comentarios = 0).
-- =============================================================================
CREATE OR REPLACE VIEW vista_feed_noticias AS
SELECT
    p.id_publicacion,
    u.nombre              AS autor,
    p.texto_contenido,
    p.fecha_publicacion,
    p.likes_contador,
    COUNT(c.id_comentario) AS total_comentarios
FROM publicaciones p
INNER JOIN usuarios u   ON p.autor_id       = u.id_usuario
LEFT  JOIN comentarios c ON p.id_publicacion = c.publicacion_id
GROUP BY
    p.id_publicacion,
    u.nombre,
    p.texto_contenido,
    p.fecha_publicacion,
    p.likes_contador
ORDER BY p.fecha_publicacion DESC;
