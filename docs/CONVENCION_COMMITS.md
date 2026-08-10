# Convencion de commits

Formato: `tipo(alcance): descripcion en minuscula (SCRUM-00)`

Tipos: feat, fix, docs, refactor, test, chore, ci

Alcances (coinciden con las etiquetas de las epicas en Jira):
infra, datos, denuncia, saneamiento, integridad, antispam, revision, portal, qa

Ejemplos:

    feat(datos): modelar tabla denuncias con enums (SCRUM-26)
    chore(infra): definir docker-compose con api y db (SCRUM-22)
    fix(saneamiento): detectar tipo por bytes de cabecera (SCRUM-42)

La clave SCRUM-00 al final es obligatoria: es lo que permite rastrear cada
commit hasta su tarea durante la sustentacion.
