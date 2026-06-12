DROP VIEW IF EXISTS vista_feed_noticias CASCADE;
DROP VIEW IF EXISTS vista_amistades_consolidadas CASCADE;
DROP VIEW IF EXISTS vista_solicitudes_pendientes CASCADE;

DROP FUNCTION IF EXISTS crear_amistad(INT, INT);

CREATE OR REPLACE FUNCTION crear_amistad(
id1 INT,
id2 INT
)
RETURNS TEXT
LANGUAGE plpgsql
AS
$$
BEGIN

IF NOT EXISTS (
    SELECT 1
    FROM usuarios
    WHERE id_usuario = id1
) THEN

    RAISE EXCEPTION
    'El usuario % no existe.',
    id1;

END IF;

-- ==========================================
-- Validar existencia usuario 2
-- ==========================================

IF NOT EXISTS (
    SELECT 1
    FROM usuarios
    WHERE id_usuario = id2
) THEN

    RAISE EXCEPTION
    'El usuario % no existe.',
    id2;

END IF;

-- ==========================================
-- Evitar autoamistad
-- ==========================================

IF id1 = id2 THEN

    RAISE EXCEPTION
    'Un usuario no puede ser amigo de sí mismo.';

END IF;

-- ==========================================
-- Verificar amistad existente
-- A -> B
-- B -> A
-- PENDIENTE o ACEPTADA
-- ==========================================

IF EXISTS (

    SELECT 1
    FROM amistades
    WHERE

    (
        usuario_solicitante_id = id1
        AND usuario_receptor_id = id2
    )

    OR

    (
        usuario_solicitante_id = id2
        AND usuario_receptor_id = id1
    )

) THEN

    RAISE EXCEPTION
    'La amistad ya existe o tiene una solicitud pendiente.';

END IF;

-- ==========================================
-- Insertar solicitud
-- ==========================================

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

RETURN
'Solicitud de amistad creada correctamente.';


EXCEPTION

WHEN OTHERS THEN

    RAISE EXCEPTION
    'Error al crear amistad: %',
    SQLERRM;


END;
$$;

CREATE OR REPLACE VIEW
vista_solicitudes_pendientes
AS

SELECT

a.id_amistad,

u1.nombre AS solicitante,

u2.nombre AS receptor,

a.estado,

a.fecha_amistad


FROM amistades a

INNER JOIN usuarios u1
ON a.usuario_solicitante_id =
u1.id_usuario

INNER JOIN usuarios u2
ON a.usuario_receptor_id =
u2.id_usuario

WHERE a.estado = 'PENDIENTE';

CREATE OR REPLACE VIEW
vista_amistades_consolidadas
AS

SELECT

a.id_amistad,

u1.nombre AS amigo_1,

u2.nombre AS amigo_2,

a.fecha_amistad


FROM amistades a

INNER JOIN usuarios u1
ON a.usuario_solicitante_id =
u1.id_usuario

INNER JOIN usuarios u2
ON a.usuario_receptor_id =
u2.id_usuario

WHERE a.estado = 'ACEPTADA';

CREATE OR REPLACE VIEW
vista_feed_noticias
AS

SELECT

p.id_publicacion,

u.nombre AS autor,

p.texto_contenido,

p.fecha_publicacion,

p.likes_contador,

COUNT(
    c.id_comentario
) AS total_comentarios


FROM publicaciones p

INNER JOIN usuarios u
ON p.autor_id = u.id_usuario

LEFT JOIN comentarios c
ON p.id_publicacion =
c.publicacion_id

GROUP BY

p.id_publicacion,
u.nombre,
p.texto_contenido,
p.fecha_publicacion,
p.likes_contador


ORDER BY
p.fecha_publicacion DESC;