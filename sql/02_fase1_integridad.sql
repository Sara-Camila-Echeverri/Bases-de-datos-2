-- =============================================================================
-- 02_fase1_integridad.sql
-- Fase 1 de preparación de datos: limpieza + aplicación de restricciones.
--
-- El proceso tiene dos partes:
--   1. LIMPIEZA: elimina filas huérfanas o duplicadas que impedirían crear
--      las claves foráneas y restricciones de integridad.
--   2. RESTRICCIONES: agrega FKs, CHECK e índice único ahora que los datos
--      son consistentes.
-- =============================================================================


-- =============================================================================
-- PARTE 1: LIMPIEZA DE DATOS
-- =============================================================================

-- Elimina comentarios cuya publicación ya no existe en la tabla publicaciones.
-- Si no se limpia primero, la FK comentarios→publicaciones fallaría.
DELETE FROM comentarios
WHERE publicacion_id NOT IN (
    SELECT id_publicacion
    FROM publicaciones
);

-- Elimina comentarios cuyo autor no existe en la tabla usuarios.
DELETE FROM comentarios
WHERE usuario_id NOT IN (
    SELECT id_usuario
    FROM usuarios
);

-- Elimina publicaciones cuyo autor no existe en la tabla usuarios.
DELETE FROM publicaciones
WHERE autor_id NOT IN (
    SELECT id_usuario
    FROM usuarios
);

-- Elimina amistades donde cualquiera de los dos usuarios no exista.
-- Se usa OR para cubrir ambas columnas de FK.
DELETE FROM amistades
WHERE usuario_solicitante_id NOT IN (
    SELECT id_usuario FROM usuarios
)
OR usuario_receptor_id NOT IN (
    SELECT id_usuario FROM usuarios
);

-- Elimina amistades duplicadas manteniendo solo la de menor id_amistad.
-- La técnica LEAST/GREATEST normaliza el par (A,B) == (B,A) para detectar
-- duplicados sin importar el orden en que se insertaron.
DELETE FROM amistades a
USING amistades b
WHERE a.id_amistad > b.id_amistad
  AND LEAST(a.usuario_solicitante_id, a.usuario_receptor_id)
    = LEAST(b.usuario_solicitante_id, b.usuario_receptor_id)
  AND GREATEST(a.usuario_solicitante_id, a.usuario_receptor_id)
    = GREATEST(b.usuario_solicitante_id, b.usuario_receptor_id);


-- =============================================================================
-- PARTE 2: RESTRICCIONES DE INTEGRIDAD REFERENCIAL
-- =============================================================================

-- FK: publicaciones.autor_id → usuarios.id_usuario
--   ON DELETE RESTRICT: impide borrar un usuario que tenga publicaciones.
--   ON UPDATE CASCADE:  si cambia el id del usuario, se actualiza aquí también.
ALTER TABLE publicaciones
ADD CONSTRAINT fk_publicaciones_usuario
FOREIGN KEY (autor_id)
REFERENCES usuarios(id_usuario)
ON DELETE RESTRICT
ON UPDATE CASCADE;

-- FK: comentarios.usuario_id → usuarios.id_usuario
ALTER TABLE comentarios
ADD CONSTRAINT fk_comentarios_usuario
FOREIGN KEY (usuario_id)
REFERENCES usuarios(id_usuario)
ON DELETE RESTRICT
ON UPDATE CASCADE;

-- FK: comentarios.publicacion_id → publicaciones.id_publicacion
--   ON DELETE CASCADE: si se borra una publicación, sus comentarios también.
ALTER TABLE comentarios
ADD CONSTRAINT fk_comentarios_publicacion
FOREIGN KEY (publicacion_id)
REFERENCES publicaciones(id_publicacion)
ON DELETE CASCADE
ON UPDATE CASCADE;

-- FK: amistades.usuario_solicitante_id → usuarios.id_usuario
ALTER TABLE amistades
ADD CONSTRAINT fk_amistades_solicitante
FOREIGN KEY (usuario_solicitante_id)
REFERENCES usuarios(id_usuario)
ON DELETE RESTRICT
ON UPDATE CASCADE;

-- FK: amistades.usuario_receptor_id → usuarios.id_usuario
ALTER TABLE amistades
ADD CONSTRAINT fk_amistades_receptor
FOREIGN KEY (usuario_receptor_id)
REFERENCES usuarios(id_usuario)
ON DELETE RESTRICT
ON UPDATE CASCADE;

-- CHECK: un usuario no puede enviarse una solicitud de amistad a sí mismo.
ALTER TABLE amistades
ADD CONSTRAINT chk_no_autoamistad
CHECK (usuario_solicitante_id <> usuario_receptor_id);

-- ÍNDICE ÚNICO: garantiza que el par (A,B) no se repita sin importar el orden.
-- LEAST/GREATEST normaliza el par para que (1,2) y (2,1) se traten igual.
CREATE UNIQUE INDEX IF NOT EXISTS idx_amistad_unica
ON amistades (
    LEAST(usuario_solicitante_id, usuario_receptor_id),
    GREATEST(usuario_solicitante_id, usuario_receptor_id)
);


-- =============================================================================
-- VERIFICACIÓN: consulta las restricciones creadas en cada tabla
-- =============================================================================

-- Restricciones de la tabla amistades
SELECT conname AS nombre_restriccion, contype AS tipo
FROM pg_constraint
WHERE conrelid = 'amistades'::regclass;

-- Restricciones de la tabla comentarios
SELECT conname AS nombre_restriccion, contype AS tipo
FROM pg_constraint
WHERE conrelid = 'comentarios'::regclass;

-- Restricciones de la tabla publicaciones
SELECT conname AS nombre_restriccion, contype AS tipo
FROM pg_constraint
WHERE conrelid = 'publicaciones'::regclass;
