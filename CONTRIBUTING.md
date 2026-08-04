# Guía de contribución

Este repositorio constituye un espacio de colaboración para el análisis de datos de eye-tracking y la construcción de redes a partir de ellos. Las siguientes directrices tienen como propósito facilitar la organización del trabajo entre los colaboradores.

> Se trata mayormente de recomendaciones y no de reglas estrictas.

## Convención de nombres de ramas

Con el fin de mantener el repositorio ordenado, se solicita que las ramas sigan el patrón descrito a continuación. Esta convención se aplica de manera automática, su objetivo es facilitar la identificación del propósito de cada rama.

Todas las ramas deben comenzar con uno de los siguientes prefijos:

- `feature/` — scripts de nuevos, de creación o análisis de redes
- `fix/` — corrección de errores
- `data/` — carga, limpieza o modificación de conjuntos de datos
- `refactor/` — reorganización de código o archivos sin alterar su comportamiento
- `chore/` — tareas de mantenimiento, actualización de dependencias, etc.
- `docs/` — cambios en documentación

**Ejemplos:**

- `feature/analisis-centralidad`
- `fix/error-importar-script`
- `data/limpieza-meco-l2`
- `refactor/cognition-load`

> Tras el prefijo, se recomienda utilizar únicamente minúsculas, números y guiones.

## Estructura del repositorio

A continuación se describe la organización general de carpetas:

- `data/` — conjunto de datos crudos y procesados asociados al proyecto MECO, por ahora solo datos asociados a MECO L2. Los archivos `.csv` y `.rds` se encuentran en `.gitignore` debido a su tamaño y **no se versionan**.
- `scripts/` — *scripts* auxiliares para conversiones de formato, limpieza y tareas similares.
- `networks/<tipo>/` — *notebooks* y código específico de cada tipo de red.

## Estilo de código

Las siguientes son recomendaciones orientativas para mantener la coherencia del código:

- **Comentarios**: pueden redactarse en español o inglés. Se valora que aporten contexto y no se limiten a reiterar el código.
- **Rutas**: se deben utilizar rutas relativas al repositorio. No se admiten rutas absolutas del tipo `C:/Users/...` o `/home/...`.

## Flujo de trabajo para contribuciones

1. Crear una rama a partir de la rama principal (`main`) utilizando el prefijo adecuado según la convención descrita.
2. Realizar los cambios en *commits* pequeños y con mensajes descriptivos en español o inglés. No se exige un formato específico, aunque se recomienda que el mensaje refleje con claridad el propósito del cambio.
3. Una vez finalizados los cambios, abrir un *Pull Request* y completar la plantilla provista, incluso para modificaciones menores.
4. El archivo `CODEOWNERS` se encarga de solicitar la revisión de los mantenedores. Las revisiones buscan asegurar la calidad y coherencia del trabajo, y se procuran ágiles.
