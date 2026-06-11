
DELETE FROM comentarios
WHERE publicacion_id NOT IN (
SELECT id_publicacion
FROM publicaciones
);


DELETE FROM comentarios
WHERE usuario_id NOT IN (
SELECT id_usuario
FROM usuarios
);


DELETE FROM publicaciones
WHERE autor_id NOT IN (
SELECT id_usuario
FROM usuarios
);


DELETE FROM amistades
WHERE usuario_solicitante_id NOT IN (
SELECT id_usuario
FROM usuarios
)
OR usuario_receptor_id NOT IN (
SELECT id_usuario
FROM usuarios
);

DELETE FROM amistades a
USING amistades b
WHERE a.id_amistad > b.id_amistad
AND LEAST(
    a.usuario_solicitante_id,
    a.usuario_receptor_id
) =
LEAST(
    b.usuario_solicitante_id,
    b.usuario_receptor_id
)
AND GREATEST(
    a.usuario_solicitante_id,
    a.usuario_receptor_id
) =
GREATEST(
    b.usuario_solicitante_id,
    b.usuario_receptor_id
);


ALTER TABLE publicaciones
ADD CONSTRAINT fk_publicaciones_usuario
FOREIGN KEY (autor_id)
REFERENCES usuarios(id_usuario)
ON DELETE RESTRICT
ON UPDATE CASCADE;

ALTER TABLE comentarios
ADD CONSTRAINT fk_comentarios_usuario
FOREIGN KEY (usuario_id)
REFERENCES usuarios(id_usuario)
ON DELETE RESTRICT
ON UPDATE CASCADE;

ALTER TABLE comentarios
ADD CONSTRAINT fk_comentarios_publicacion
FOREIGN KEY (publicacion_id)
REFERENCES publicaciones(id_publicacion)
ON DELETE CASCADE
ON UPDATE CASCADE;

ALTER TABLE amistades
ADD CONSTRAINT fk_amistades_solicitante
FOREIGN KEY (usuario_solicitante_id)
REFERENCES usuarios(id_usuario)
ON DELETE RESTRICT
ON UPDATE CASCADE;

ALTER TABLE amistades
ADD CONSTRAINT fk_amistades_receptor
FOREIGN KEY (usuario_receptor_id)
REFERENCES usuarios(id_usuario)
ON DELETE RESTRICT
ON UPDATE CASCADE;

ALTER TABLE amistades
ADD CONSTRAINT chk_no_autoamistad
CHECK (
usuario_solicitante_id <>
usuario_receptor_id
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_amistad_unica
ON amistades (
LEAST(
usuario_solicitante_id,
usuario_receptor_id
),
GREATEST(
usuario_solicitante_id,
usuario_receptor_id
)
);

SELECT
conname AS nombre_restriccion,
contype AS tipo
FROM pg_constraint
WHERE conrelid = 'amistades'::regclass;

SELECT
conname AS nombre_restriccion,
contype AS tipo
FROM pg_constraint
WHERE conrelid = 'comentarios'::regclass;

SELECT
conname AS nombre_restriccion,
contype AS tipo
FROM pg_constraint
WHERE conrelid = 'publicaciones'::regclass;
