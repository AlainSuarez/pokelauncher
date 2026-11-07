# Plan de desarrollo de PokéLauncher

## Objetivo

Crear un launcher local para organizar una colección de juegos Pokémon, iniciarlos con emuladores instalados, consultar las partidas y, posteriormente, transferir Pokémon entre partidas compatibles.

El desarrollo prioriza Linux y GNOME. La aplicación debe funcionar sin conexión después de instalarse y configurarse. No incluye la distribución de ROMs, BIOS ni partidas.

## Arquitectura propuesta

- **Interfaz:** HTML/CSS con plantillas Jinja (`base.html`, includes y páginas separadas), JavaScript por responsabilidad, sin Node en ejecución. HTMX se evaluará al crear la búsqueda de Pokédex; Alpine.js queda opcional.
- **Servidor local:** Flask con fábrica de aplicación y Blueprints de páginas y API, servido por Waitress en localhost. Servicios y repositorios separados de las rutas.
- **Persistencia:** SQLite para rutas y asociaciones; los favoritos y la vista siguen en el navegador. Se ampliará a perfiles y registros de operaciones.
- **Lectura de partidas:** ayudante C# basado en una versión fijada de PKHeX.Core, comunicado con Python mediante JSON por entrada y salida estándar.
- **Acceso inicial:** navegador conectado a `127.0.0.1`.
- **Escritorio opcional:** ventana con pywebview reutilizando la interfaz y los servicios existentes.
- **Instalación:** versiones publicadas en GitHub, instalador por usuario y servicio `systemd --user`.

La versión de Python, dependencias y requisitos de .NET se fijarán al implementar cada componente. Antes de distribuir PKHeX.Core se revisarán su licencia y las obligaciones aplicables al paquete final.

## Fase 1 — Cerrar la biblioteca visual

**Objetivo:** dejar estable y coherente la experiencia actual antes de conectar emuladores.

- [x] Catálogo inicial de 28 juegos, de Game Boy a Nintendo 3DS.
- [x] Carátulas y fichas con información de cada juego.
- [x] Búsqueda, filtros, ordenación, favoritos y vistas de cuadrícula y lista.
- [x] Corregir el mensaje de colección vacía para que respete el atributo `hidden`.
- [ ] Revisar combinaciones de búsqueda, consola, colección y favoritos.
- [ ] Revisar el restablecimiento de filtros y el contador de resultados.
- [ ] Comprobar fichas, navegación y enlaces directos a juegos.
- [ ] Revisar navegación con teclado, foco y cierre de ventanas de detalle.
- [ ] Revisar diseño en escritorio y pantallas pequeñas.
- [ ] Comprobar imágenes ausentes y estados sin resultados.
- [ ] Identificar las rutas y estados de colección actualmente definidos de forma estática para sustituirlos en la fase 2.

**Criterio de cierre:** los controles visuales funcionan de forma consistente y los estados vacíos aparecen únicamente cuando corresponde. La ejecución real de juegos queda para la fase 2.

## Fase 2 — Servidor local, configuración y emuladores

**Objetivo:** poder configurar la colección real y lanzar juegos desde la interfaz.

### 2.1 Base del servidor y persistencia

- [x] Crear el servidor Python y servir la interfaz existente.
- [x] Definir API local y respuestas de error comprensibles.
- [ ] Crear la base SQLite y un mecanismo de migraciones.
- [ ] Separar las entidades juego, archivo ROM, perfil de emulador y partida.
- [ ] Migrar preferencias y favoritos del navegador cuando sea posible.
- [x] Escuchar únicamente en la interfaz local y proteger las operaciones con validación de origen y token de sesión.
- [x] Ejecutar procesos con argumentos separados, sin construir comandos de shell a partir de entradas del usuario.

### 2.2 Panel de configuración y biblioteca real

- [x] Permitir registrar varias carpetas de ROMs y volver a escanearlas.
- [ ] Asociar archivos a juegos mediante nombres y metadatos disponibles.
- [x] Permitir corregir asociaciones manualmente.
- [ ] Contemplar idiomas, revisiones y varias ROMs del mismo juego.
- [ ] Mostrar archivos ausentes, duplicados y asociaciones pendientes.
- [x] Sustituir los estados estáticos de colección por asociaciones de ROMs verificadas en disco.
- [x] Configurar carpetas de partidas y asociaciones manuales.

### 2.3 Adaptadores de emuladores

- [ ] Comprobar las opciones de lanzamiento de mGBA, melonDS y Azahar.
- [ ] Implementar primero un recorrido completo con mGBA.
- [ ] Añadir melonDS y Azahar tras validar el primer adaptador.
- [x] Permitir elegir ejecutable o instalación Flatpak compatible.
- [ ] Configurar un emulador predeterminado por consola y excepciones por juego.
- [ ] Añadir comprobación de configuración y mensajes para rutas inválidas.
- [ ] Conectar el botón Jugar y registrar el proceso iniciado.
- [ ] Detectar el cierre de las sesiones iniciadas por el launcher.

**Validación:** escanear una carpeta de prueba, asociar una ROM, configurar un emulador y abrir el juego. Verificar también rutas con espacios, archivos ausentes y configuraciones inválidas.

**Criterio de cierre:** los juegos configurados se lanzan desde la biblioteca y la configuración persiste entre reinicios.

## Fase 3 — Visor de partidas de solo lectura

**Objetivo:** consultar entrenador, equipo y cajas sin modificar los archivos originales.

### Navegación y página de juego

La navegación principal desde la biblioteca abrirá una página dedicada a cada juego. Esta página tendrá una URL propia y permitirá volver a la biblioteca conservando búsqueda, filtros, orden y posición. Se implementará sobre la interfaz existente, sin exigir Node ni un framework.

- [ ] Crear una vista dedicada por juego con enlace directo y soporte para atrás y adelante del navegador.
- [ ] Mostrar cabecera con carátula, información del juego y acción Jugar.
- [ ] Organizar el contenido en resumen, partidas y configuración del juego.
- [ ] Permitir seleccionar la partida activa cuando existan varias, sin confundirla con la ROM seleccionada.
- [ ] Mostrar el entrenador, equipo y cajas de la partida seleccionada, con estados claros cuando todavía no haya una partida asociada o compatible.
- [ ] Permitir consultar el detalle de cada Pokémon dentro del contexto de su partida.
- [ ] Añadir navegación al juego anterior y siguiente respetando la lista filtrada de procedencia.

El modal actual se conservará como base para una futura vista rápida. Más adelante se evaluará una acción explícita de vista rápida en las tarjetas, con carrusel entre juegos y un enlace para abrir la página completa. La página y el modal compartirán datos y componentes para mantener su contenido coherente. El modal no será el contenedor principal del visor de partidas.

La estructura de la página puede adelantarse a la fase 2 para alojar la selección de ROM, emulador y partida. La presentación de datos de Pokémon depende del lector de esta fase.

### Integración de lectura

- [ ] Realizar una prueba de integración con PKHeX.Core y una partida compatible.
- [ ] Fijar la versión de la biblioteca y documentar formatos admitidos.
- [ ] Crear el ayudante C# con un contrato JSON versionado.
- [ ] Leer copias temporales de las partidas, sin exponer operaciones de escritura.
- [ ] Resolver la asociación entre ROM, juego y partida, con selección manual disponible.
- [ ] Mostrar entrenador, progreso y tiempo jugado cuando estén disponibles.
- [ ] Mostrar equipo y cajas con especie, apodo, nivel, movimientos y objeto.
- [ ] Añadir naturaleza, habilidad, IVs, EVs y estadísticas según la generación.
- [ ] Mostrar fecha de lectura y fecha de modificación de la partida.
- [ ] Actualizar tras el cierre del emulador y mediante una acción manual.
- [ ] Gestionar partidas corruptas, formatos no reconocidos y archivos que cambian durante la lectura.
- [ ] Comprobar que el archivo original permanece idéntico después de consultar sus datos.

**Alcance inicial:** partidas normales de juegos oficiales. Los save states, la lectura de memoria en tiempo real y la compatibilidad con ROM hacks quedan fuera del alcance inicial.

**Validación:** usar partidas de prueba autorizadas y comprobar campos conocidos, errores de formato y conservación del hash del original.

**Criterio de cierre:** visualizar correctamente el último estado guardado de las partidas incluidas en la matriz de soporte, sin escribir en ellas.

## Fase 4 — Transferencias entre partidas compatibles

**Objetivo:** mover Pokémon mediante operaciones verificables y recuperables.

Esta fase introduce escritura en partidas. Mantendrá una interfaz separada del visor de solo lectura.

### 4.1 Compatibilidad y primera transferencia

- [ ] Definir una matriz de compatibilidad por juego, generación y dirección.
- [ ] Seleccionar dos juegos de una misma generación para el primer caso admitido.
- [ ] Diferenciar transferencia de Pokémon, migración de una partida entre emuladores e intercambio mediante enlace emulado.
- [ ] Validar especie, formato, restricciones del destino y espacio disponible.
- [ ] Mostrar una previsualización del origen, destino y posibles cambios de representación.
- [ ] Definir la semántica de mover: retirar del origen e insertar en el destino.
- [ ] Bloquear casos no soportados con una explicación concreta.

### 4.2 Escritura y recuperación

- [ ] Exigir que las partidas no estén en uso y detectar sesiones conocidas del launcher.
- [ ] Documentar las limitaciones para detectar emuladores abiertos externamente.
- [ ] Crear copias de seguridad de ambas partidas antes de escribir.
- [ ] Comprobar que los originales no han cambiado desde su lectura.
- [ ] Preparar y validar ambos archivos resultantes antes de sustituir los originales.
- [ ] Registrar las etapas de la operación para recuperar interrupciones entre escrituras.
- [ ] Añadir restauración de copias de seguridad e historial de transferencias.
- [ ] Ampliar a otras generaciones únicamente tras validar sus conversiones y restricciones.

**Validación:** trabajar sobre copias de prueba; comprobar origen y destino con el lector y el emulador. Simular falta de espacio, cambios externos, archivos inválidos e interrupciones durante la operación.

**Criterio de cierre:** completar y recuperar transferencias en los casos expresamente admitidos. No se promete compatibilidad universal ni reproducción automática de efectos de intercambio.

## Fase 5 — Instalación y mantenimiento en Linux

**Objetivo:** instalar una versión publicada desde GitHub y usarla sin preparar un entorno de desarrollo.

- [ ] Elegir y documentar las distribuciones y arquitecturas Linux soportadas inicialmente.
- [ ] Publicar paquetes versionados con dependencias fijadas y sumas de comprobación.
- [ ] Crear un instalador descargable mediante `curl`, con instrucciones para revisarlo y ejecutarlo.
- [ ] Instalar en directorios del usuario, sin ejecutar la aplicación como root.
- [ ] Preparar el entorno Python e incluir o resolver el ayudante .NET cuando corresponda.
- [ ] Registrar un servicio `systemd --user` con inicio y parada documentados.
- [ ] Crear un acceso en el menú de aplicaciones.
- [ ] Separar archivos de aplicación, configuración, base de datos, registros y copias de seguridad.
- [ ] Añadir actualización con respaldo y migración de datos.
- [ ] Añadir desinstalación con conservación de datos personales por defecto.
- [ ] Probar instalación limpia, actualización, reinicio de sesión y desinstalación.

**Criterio de cierre:** instalar y abrir PokéLauncher en un equipo Linux compatible siguiendo únicamente la documentación publicada.

Un instalador preliminar puede adelantarse al finalizar la fase 2 para facilitar pruebas. El paquete definitivo debe incorporar los componentes de las fases posteriores.

## Fase 6 — Ventana de escritorio opcional

**Objetivo:** ofrecer una aplicación con ventana propia conservando la arquitectura local.

- [ ] Evaluar pywebview y sus dependencias GTK en las distribuciones elegidas.
- [ ] Reutilizar la interfaz y la lógica del servidor.
- [ ] Integrar selectores nativos de carpetas y archivos.
- [ ] Definir el comportamiento al cerrar la ventana y la relación con el servicio.
- [ ] Evitar instancias duplicadas y comprobar el arranque desde el menú.
- [ ] Comparar el paquete de escritorio con la experiencia en navegador antes de elegir el modo predeterminado.

**Criterio de cierre:** la ventana permite realizar las mismas operaciones admitidas en el navegador y gestiona correctamente su ciclo de vida.

## Fuera del alcance inicial

- Servicio web alojado, cuentas y sincronización en la nube.
- Acceso remoto o exposición del servidor a la red local.
- Descarga de ROMs, BIOS o claves.
- Lectura del equipo en memoria en tiempo real.
- Compatibilidad general con save states y ROM hacks.
- Intercambios mediante enlace emulado.
- Instaladores para Windows y macOS.

## Orden de ejecución

1. Cerrar la revisión visual de la fase 1.
2. Completar un recorrido de lanzamiento con una ROM y mGBA.
3. Extender configuración, biblioteca y adaptadores.
4. Probar la lectura de una partida con PKHeX.Core y ampliar el visor.
5. Implementar una transferencia limitada con respaldo y recuperación.
6. Consolidar instalación, actualizaciones y documentación.
7. Evaluar la ventana de escritorio y futuras plataformas.

## Seguimiento

Marcar una tarea como terminada solo cuando su comportamiento esté comprobado. Registrar las decisiones nuevas y actualizar la matriz de soporte conforme se validen emuladores y formatos. Las casillas pendientes representan trabajo planificado, no funcionalidades ya disponibles.

## Avance de la fase 2

Implementados servidor local sin dependencias externas, configuración SQLite por consola, búsqueda por extensión, asociación manual por juego y envío del lanzamiento a ejecutables nativos o Flatpak. Las carpetas de partidas solo se registran. Probados persistencia y API con solicitudes simuladas; pendientes validación visual en navegador y apertura real de cada emulador en sesión gráfica. No hay detección automática de identidad de ROMs, perfiles por juego ni instalador todavía.


## Migración a Flask — octubre de 2026

- [x] Fábrica `create_app`, Blueprints, servicios y repositorio SQLite.
- [x] Plantillas base, sidebar, cabecera, pie, biblioteca, juego y ajustes.
- [x] URLs de páginas y compatibilidad con enlaces anteriores mediante redirección.
- [x] Fragmento HTML de ajustes preparado para actualizaciones parciales.
- [x] Catálogo JSON compartido por interfaz y asociación de ROMs.
- [x] Conservar configuración existente, controles de acceso local y lanzamiento de emuladores externos.
- [ ] Validar la migración en ejecución con Flask/Waitress y en navegador; instalación de dependencias bloqueada por DNS en el entorno de trabajo.

Siguiente etapa: contenido local por juego o región. Cores integrados al final, después de contenido y lectura de partidas.


## Premisas de colaboración

Proyecto de hobby: no crear ni ampliar tests automatizados, ni ejecutar suites por iniciativa propia. Aplicar comprobaciones manuales proporcionales a los cambios. No crear ni utilizar entornos virtuales; ejecutar con el Python del sistema y documentar la instalación sin venv. Estas reglas se mantienen en `AGENTS.md`.

## Pokédex por juego — primera entrega

- [x] Pestaña Pokédex en las fichas de juegos.
- [x] Descarga de Yellow con progreso en segundo plano y caché persistente para reanudar por recurso.
- [x] SQLite compartida para especies, imágenes, Pokédex, tipos históricos y textos por edición/idioma.
- [x] Listado local, búsqueda, filtro por tipo y ficha individual.
- [ ] Completar una descarga real de los 151 Pokémon en el equipo del usuario; el entorno de trabajo no tiene resolución DNS para PokéAPI.
- [ ] Ampliar progresivamente los paquetes a las demás ediciones.

- [x] Compartir el paquete de Kanto entre Red, Blue y Yellow, incluido progreso, reanudación y reutilización de las descargas anteriores de Yellow.

- [x] Separar la disponibilidad de la Pokédex común de los recursos completos de cada edición; habilitar Kanto en FireRed y LeafGreen y retirar los enlaces genéricos a Yellow en otras regiones.
- [ ] Siguiente etapa de contenido: encuentros, movimientos y MT/MO por edición o grupo de versiones.

- [x] Estadísticas base históricas en la ficha, integradas en la tarjeta existente con valores, barras y total; importación automática desde la caché para las generaciones disponibles.

- [x] Ampliar las fichas con información general compartida y un bloque por edición, aprendizaje de movimientos disponible en caché, defensas históricas, familia evolutiva regional y referencias generales desplegables.

### Integración PKHeX.Core — primera entrega (2026-11-02)

- Ayudante C# opcional con PKHeX.Core 26.10.18 y contrato JSON v1.
- Servicio Python de lectura sobre copia temporal, límite de tamaño, tiempo máximo, comprobación SHA-256 y detección de cambios del original.
- Asociación manual independiente por juego y sugerencias de la carpeta de partidas de la consola.
- Visor de entrenador, equipo y cajas dentro del panel Partidas, con estilos limitados a ese panel.
- Identificadores de especies vistas/capturadas preparados para la siguiente etapa, sin porcentajes todavía.
- Comprobaciones manuales de renderizado, errores y autorización realizadas sin ejecutar suites ni añadir tests.
- Pendientes: compilar el ayudante en .NET 10, validar partidas reales por edición, revisión visual en navegador, detalle ampliado de Pokémon. Las copias se actualizan manualmente por decisión del usuario. La fase de lectura completa sigue abierta hasta esa validación.

Ajuste de lectura: se permite seguir jugando mientras se consulta una copia. Hasta tres intentos con dos segundos entre ellos, estado Cargando y conservación transaccional de la última copia válida y sus datos en SQLite. Los cambios del original posteriores a la copia no invalidan la lectura.

Simplificación del visor: configuración de carpetas y botón Examinar solo en Configuración. En Partidas quedan selección, Actualizar e información. La primera partida única se carga automáticamente si no hay copia previa; cambiar de partida carga su información. Filtrado conservador por juego para guardados con nombre de ROM.

### Compilación y primera lectura real (2026-11-02)

- SDK 10.0.113 y runtime 10.0.13 instalados por el usuario.
- Ayudante compilado y publicado usando la DLL PKHeX.Core 26.8.26.0 de su AppImage; opción `PKHeXCorePath` para compilación con biblioteca local. El camino predeterminado conserva NuGet 26.10.18, aún sin validar en esta sesión por restricciones de red.
- Lectura real de Pokémon Y correcta y copia persistida en base temporal. Datos obtenidos: entrenador, equipo, cajas, vistos y capturados. SHA-256 original conservado.
- Archivo real detectado para Rubí Omega: formato no reconocido por esta DLL; pendiente de diagnóstico. SHA-256 original conservado.
- API confirma lector disponible; no se han ejecutado suites ni creado tests automatizados.

### Visor visual de partidas

Equipo con ilustraciones y tipos de la caché local, ficha de entrenador y cajas como cuadrícula por posiciones con inspector de Pokémon. Imágenes opcionales, sin descargas al leer. Estilos limitados a Partidas. Revisión visual en Firefox de escritorio y móvil con datos de Y, y comprobaciones puntuales de rutas e imágenes sin suites de tests.

Corrección del visor X/Y: número de cajas desbloqueadas leído del guardado y Caja de Combate independiente de seis posiciones, con ilustraciones. Validado con copia de Y: siete cajas normales y seis Pokémon de combate; conservado SHA-256. Actualización manual necesaria para lecturas previas.

Corrección de lecturas antiguas X/Y: reinterpretación automática de la copia persistida cuando falta información de cajas desbloqueadas o combate, conservando los bytes y las fechas. Comprobado en una base temporal con la ruta original deliberadamente inexistente: siete cajas y seis Pokémon de combate.
