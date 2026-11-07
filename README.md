# PokéLauncher

Biblioteca local de juegos Pokémon de Game Boy a Nintendo 3DS, con interfaz HTML/CSS/JavaScript, plantillas Jinja y servidor Flask. No necesita Node para ejecutarse.

Proyecto personal de hobby en desarrollo, orientado a Linux de escritorio. Incluye biblioteca visual, lanzamiento de emuladores externos, Pokédex local de Kanto y un visor opcional de partidas de solo lectura. El soporte de cada edición y las funciones pendientes se detallan más abajo.

No incluye ROMs, BIOS, emuladores ni partidas. Pokémon y las imágenes de los juegos pertenecen a sus respectivos titulares; este proyecto no está afiliado a Nintendo, Game Freak ni The Pokémon Company.

## Iniciar

Requiere Python 3.10 o posterior. Desde la carpeta del proyecto:

```bash
python -m pip install -r requirements.txt
python server.py
```

Abre **http://127.0.0.1:8765**. Mantén esa terminal abierta; `Ctrl+C` detiene el servidor. El servidor debe ejecutarse con tu usuario dentro de la sesión gráfica para abrir emuladores.

Los cambios en plantillas HTML, CSS y JavaScript se ven al recargar el navegador, sin reiniciar el servidor. Para recargar también el servidor cuando cambie Python, usa el modo de desarrollo:

```bash
python server.py --dev
```

Este modo escucha solo en localhost y mantiene desactivado el depurador interactivo. La recarga de Python reinicia el estado de sesiones del launcher; los emuladores ya abiertos siguen ejecutándose.

Puedes elegir otro puerto y directorio de datos:

```bash
python server.py --port 8766 --data-dir /ruta/a/datos
```

Por defecto, la configuración se guarda en `$XDG_DATA_HOME/pokelauncher/settings.sqlite3` o `~/.local/share/pokelauncher/settings.sqlite3`. Los favoritos y la preferencia de cuadrícula/lista siguen guardándose en el navegador; los favoritos de una apertura anterior con `file://` no se migran automáticamente.

La interfaz se sirve desde Flask; las plantillas ya no se abren mediante `file://`. Biblioteca: `/`, configuración: `/settings`, ficha: `/games/blue`. Se conservan los enlaces antiguos `/#game=blue` y `/#settings` mediante redirección en el navegador.

## Configurar ROMs y emuladores

1. Abre **Configuración** en la barra lateral.
2. En **General**, introduce la carpeta raíz de ROMs: se usan las subcarpetas `gb`, `gbc`, `gba`, `nds` y `3ds`. Las rutas alternativas de cada consola son opcionales y sustituyen la ruta derivada de la raíz. Se buscan archivos en subcarpetas, sin seguir enlaces a directorios.
3. Elige ejecutable nativo/AppImage o Flatpak. Para el primero introduce un nombre disponible en PATH o la ruta del ejecutable; para Flatpak, el ID instalado. No introduzcas un comando con argumentos.
4. Pulsa **Guardar y buscar ROMs** para aplicar las rutas y buscar archivos. Puedes usar **Comprobar emulador guardado** después. La comprobación confirma que existe el ejecutable o paquete; no comprueba la carga de un juego ni la configuración de BIOS.
5. Revisa el resumen de archivos encontrados por consola y vuelve a la biblioteca.
6. Abre un juego, entra en **Configuración**, selecciona su ROM entre los archivos detectados o escribe la ruta completa y guarda la asociación.
7. Pulsa **Jugar**. Se invoca el emulador con la ruta de la ROM como argumento separado.

Puedes usar el mismo ejecutable de mGBA para GB, GBC y GBA. El adaptador inicial admite emuladores que aceptan la ROM como argumento posicional, como las interfaces habituales de mGBA, melonDS y Azahar; la apertura real debe verificarse con la versión instalada. No se incluyen ni instalan emuladores, BIOS ni ROMs. Flatpak necesita permiso para acceder a las carpetas elegidas.

El escaneo asocia automáticamente los nombres que coinciden con un único juego y archivo candidato, ignorando etiquetas entre paréntesis y corchetes. Conserva las selecciones existentes. Cuando hay varias versiones o nombres no reconocidos, permite seleccionar la ROM manualmente. Solo los juegos con una ROM asociada y existente aparecen en colección. No se extraen ZIP ni se instalan paquetes CIA. GB/GBC comparten extensiones en el escaneo, por lo que los totales por consola pueden incluir el mismo archivo.

La carpeta opcional de partidas alimenta las sugerencias del visor de Partidas; no cambia dónde guarda el emulador. La lectura requiere preparar el ayudante PKHeX.Core descrito más abajo. Al cerrar el launcher, los emuladores abiertos continúan ejecutándose; la detección de sesiones duplicadas cubre procesos iniciados durante la ejecución actual del servidor.

## Biblioteca visual

- 28 entregas principales, desde Pokémon Red hasta Pokémon Ultra Moon.
- Páginas dedicadas, carátulas locales, información, resumen y configuración por juego.
- Búsqueda, filtros por consola, colección y favoritos, y ordenación.
- Navegación anterior/siguiente según los filtros y regreso a la biblioteca.
- Sección de partidas con selección manual y visor de solo lectura mediante un ayudante PKHeX.Core opcional.

Enlace directo de ejemplo: `http://127.0.0.1:8765/#game=blue`.

## Verificación

Este proyecto de hobby no incorpora nuevos tests automatizados. La verificación se realiza con comprobaciones manuales puntuales: abrir las páginas afectadas, guardar configuración y comprobar el lanzamiento del emulador cuando corresponda. Las reglas de colaboración están en [AGENTS.md](AGENTS.md).

Consulta [PLAN.md](PLAN.md) para las siguientes fases. El servicio automático y el instalador quedan pendientes.

La carpeta raíz no crea ni mueve archivos. Las subcarpetas ausentes se notifican al buscar ROMs. La configuración anterior conserva sus rutas específicas; vacíalas para que esa consola use la raíz general.

El botón **Examinar…** abre el selector nativo de carpetas mediante Zenity (GNOME) o KDialog (KDE), si está instalado. El servidor debe ejecutarse en la sesión gráfica del usuario. Después de seleccionar una carpeta, pulsa **Guardar y buscar ROMs**. Esta acción aplica las rutas y muestra un resumen visual por consola; asocia automáticamente las coincidencias claras al catálogo.

Cada consola incluye **Examinar…** para elegir el ejecutable nativo o AppImage. El archivo debe tener permiso de ejecución. En modo Flatpak se introduce el ID instalado y el selector de archivos se oculta.


## Arquitectura Flask

- `app/__init__.py`: fábrica `create_app`, protección de acceso local y dependencias por instancia.
- `app/pages.py`: Blueprint de páginas y fragmentos Jinja.
- `app/api.py`: Blueprint de acciones JSON; mantiene los endpoints existentes.
- `app/templates/base.html`: estructura compartida con bloques `title`, `content` y `scripts`.
- `app/templates/includes/`: sidebar, cabecera de biblioteca y pie.
- `app/templates/library/`, `games/`, `settings/`: plantillas de cada página.
- `app/services/`: escaneo, emuladores y catálogo; `app/repositories/`: persistencia SQLite.
- `app/static/`: CSS y JavaScript separados en comportamiento común, biblioteca, juego y configuración.
- `data/catalog.json`: fuente única de los 28 juegos y consolas, sin ejecutar JavaScript para leer sus datos.

Waitress sirve la aplicación WSGI en `127.0.0.1`, sin depurador ni recarga automática. La configuración SQLite conserva el formato y directorio anteriores. `--port` también configura la validación de Host y Origin.

`GET /settings/fragment?system=gba` devuelve el formulario Jinja sin el layout; es la base para actualizaciones parciales. La biblioteca conserva sus filtros y tarjetas en JavaScript y la asociación de ROMs sigue siendo un formulario dinámico. Las fichas, sus secciones y los ajustes globales ya tienen sus plantillas propias.

HTMX aportará valor al añadir búsqueda y paginación de Pokédex con fragmentos renderizados por Flask. Alpine.js queda opcional para componentes con estado local. Esta migración conserva JavaScript nativo; todavía no incorpora ninguna de las dos bibliotecas. Si se añaden, se distribuirán localmente para funcionar sin conexión.

Los cores integrados se dejan para una etapa final. «Jugar» sigue abriendo el emulador nativo, AppImage o Flatpak configurado por el usuario.

## Pokédex local — Kanto y datos por edición

Red, Blue, Yellow, FireRed y LeafGreen comparten la Pokédex de Kanto: especies, numeración e ilustraciones se almacenan una sola vez. Sus textos y sprites se relacionan con cada edición y los tipos se guardan por generación.

Abre la pestaña Pokédex de cualquiera de esos juegos:

- Sin contenido local aparece **Descargar Pokédex de Kanto**.
- Si Kanto ya se descargó desde otro juego, el listado y las fichas comunes se pueden consultar inmediatamente.
- **Completar datos de la edición** descarga los recursos que falten, conservando el contenido compartido.
- Red, Blue y Yellow comparten el paquete de primera generación; FireRed y LeafGreen comparten el de tercera generación. Los sprites de Red/Blue se descargan una sola vez, al igual que los de FireRed/LeafGreen.
- Las demás regiones indican su propio nombre y que su paquete todavía no está preparado. Se incorporarán progresivamente.

La descarga muestra progreso y sigue en segundo plano mientras el servidor permanece abierto. Si falla o se cierra el servidor, **Reanudar descarga** reutiliza los JSON e imágenes completados. Un archivo que quedó a medias se descarga de nuevo; la reanudación es por recurso, no por bytes. Completar recursos adicionales de una edición inicia su propio contador.

Contenido de esta etapa: búsqueda por nombre o número, filtro por tipo, ilustraciones, sprites, tipos históricos, altura, peso, descripción por edición e idioma y familiares evolutivos de la Pokédex. Las fichas incluyen estadísticas base históricas, barras en una escala común de 0 a 255 y suma total: cinco estadísticas con Especial en primera generación y seis con Ataque Especial y Defensa Especial desde segunda generación. Se incorporan automáticamente a la SQLite desde los JSON ya descargados al arrancar, sin volver a descargar imágenes o Pokémon. Se aplican los cambios históricos de cada estadística por separado; no se sustituyen por los valores modernos. Encuentros, aprendizaje de movimientos y MT/MO quedan para las siguientes etapas. Los JSON ya descargados se reutilizarán donde contengan información útil para esas funciones.

La Pokédex funciona sin conexión después de descargarla. Si solo existe descripción en inglés para una edición, se indica su idioma. La ilustración es común; los tipos, textos y sprites se muestran según el juego y los recursos disponibles.

Archivos en `<directorio de datos>/pokedex/`:

- `pokedex.sqlite3`: enciclopedia compartida y relaciones por edición/generación.
- `images/artwork/`: ilustraciones comunes.
- `images/sprites/`: sprites por grupo gráfico (`red-blue`, `yellow`, `firered-leafgreen`).
- `cache/`: respuestas de PokéAPI reutilizables para reanudar y ampliar contenido.
- `downloads/`: progreso por paquete; conserva compatibilidad con el antiguo `yellow.json`.

Sin `--data-dir`, la ruta habitual es `~/.local/share/pokelauncher/pokedex/` (respeta `$XDG_DATA_HOME`). Se conservan las descargas anteriores y se preparan las relaciones y tipos de otras ediciones desde la caché local, sin acceso a Internet. Para trasladar el contenido a otro equipo, copia la carpeta `pokedex` completa con el servidor detenido.

Fuentes de descarga: `https://pokeapi.co/api/v2/` y `https://raw.githubusercontent.com/PokeAPI/sprites/`. Descarga el servidor Python; el navegador recibe las imágenes desde el launcher. No se necesitan dependencias adicionales.


## Ficha ampliada de cada Pokémon

La ficha separa automáticamente la información compartida de la especie de la información correspondiente al juego seleccionado. Se genera con los JSON locales, sin escribir contenido manual por Pokémon ni hacer descargas al abrirla.

- **Ficha general:** tipos actuales, tamaño, clasificación y origen; captura, crecimiento, experiencia y amistad base actuales, EV y habilidades generales; crianza, sexo, hábitat, color y forma corporal.
- **En esta edición:** descripción y sprite propios, tipos y estadísticas históricos, habilidades y EV aplicables cuando corresponden, objetos salvajes registrados y defensas por tipo de esa generación.
- **Movimientos:** aprendizaje del grupo de versiones seleccionado, separado por nivel, MT/MO, tutor, crianza y otros métodos presentes. Solo se muestran nombre y nivel conocidos; potencia, precisión, PP y efectos requieren recursos adicionales.
- **Familia evolutiva:** especies y ramificaciones presentes en la Pokédex descargada. Las condiciones de evolución no se muestran mientras no se descargue la cadena detallada.
- **Información desplegable:** nombres por idioma, variedades generales y números en otras Pokédex. Su presencia en el listado general no implica disponibilidad en el juego seleccionado.

Las habilidades y la crianza generales se mantienen visibles incluso entrando desde Yellow. Los datos generales actuales se identifican como tales; no se presentan como valores históricos de Yellow. La sección de la edición usa las relaciones de PokéAPI para seleccionar sus datos. Los nombres de recursos se localizan si sus traducciones están en caché; de lo contrario se conserva el nombre original. Los encuentros y los sonidos no se muestran porque todavía no están descargados.


### Kalos — Pokémon X e Y

En `/games/x?section=pokedex` o `/games/y?section=pokedex` se puede descargar el paquete compartido de Kalos. Incluye sus tres Pokédex: Central, Costa y Montaña, con navegación entre ellas y numeración regional independiente. Los filtros, las fichas y los botones anterior/siguiente conservan la Pokédex seleccionada.

Una sola descarga habilita ambos juegos. Se reutilizan los JSON y las ilustraciones existentes; los tipos y estadísticas se guardan para la generación VI y los textos corresponden a cada edición. El progreso cuenta especies únicas entre las tres listas. Las descargas interrumpidas conservan los archivos completados para reanudarlas. La publicación de las tres listas se realiza al terminar, en una sola transacción.

## Lector de partidas (primera etapa)

La pestaña **Partidas** conserva el panel y los componentes visuales del launcher. Permite elegir una partida disponible, consultar entrenador, ID, tiempo jugado, equipo y cajas, y actualizar la lectura manualmente. Cada Pokémon muestra especie, apodo, nivel, movimientos y objeto cuando el formato lo admite. La ruta queda asociada a ese juego únicamente después de una lectura correcta; se guarda en una tabla independiente de la configuración de ROMs.

### Preparación

Python sigue utilizando el entorno del sistema. El lector opcional es un pequeño programa C# separado y requiere el **SDK de .NET 10** para compilarlo y el runtime de .NET 10 para ejecutarlo. Por defecto restaura el paquete [PKHeX.Core 26.10.18](https://www.nuget.org/packages/PKHeX.Core/26.10.18), fijado en el proyecto. También admite compilar con una DLL local mediante `-p:PKHeXCorePath=/ruta/PKHeX.Core.dll`; la respuesta JSON identifica la versión realmente cargada. Desde la raíz del launcher, con el SDK ya instalado:

```bash
dotnet publish tools/SaveReader/SaveReader.csproj -c Release -o tools/SaveReader/publish
python server.py
```

La compilación predeterminada necesita Internet para restaurar el paquete NuGet. Usando una DLL local compatible y el SDK ya instalado, no es necesario descargar PKHeX.Core. Las lecturas posteriores son locales. Los directorios de compilación se excluyen del control de versiones. Sin el lector, el launcher continúa disponible y Partidas explica que falta prepararlo.

Configura el emulador y su carpeta de partidas en **Configuración**, donde puedes usar **Examinar…** o escribir la ruta. En **Partidas** dentro de cada juego solo se muestra un selector de partidas y **Actualizar**. Si hay una sola partida y aún no hay lectura guardada, se carga automáticamente; si hay varias, elige una para ver sus datos. Al regresar se conserva la última lectura y se renueva únicamente al pulsar **Actualizar** o elegir otra partida. Si no se encuentra ninguna, aparece un enlace a Configuración.

Azahar configurado en Linux permite detectar `main` mediante su estructura SD y el identificador de título de la edición abierta. Se consultan ubicaciones nativas, Flatpak, portable `./user` y la SDMC personalizada de `qt-config.ini`. Las carpetas configuradas también se consultan: para otros formatos se relacionan nombres de guardado con la ROM asociada o los nombres conocidos del juego. Los archivos cuya relación no puede determinarse no se mezclan con las partidas de otras ediciones. Las rutas y detalles de detección no se muestran en el selector del juego.

Puedes seguir jugando: pulsa **Actualizar** cuando quieras renovar la copia del launcher. Si el archivo cambia mientras se copia o la copia no pasa la validación, el launcher reintenta hasta tres veces con dos segundos entre intentos; durante ese proceso se muestra «Cargando».

### Alcance y conservación del original

El contrato JSON del ayudante tiene `schema_version: 1`. Incluye `trainer`, `party`, `boxes` y `dex` (listas de identificadores nacionales `seen` y `caught` cuando el formato dispone de Pokédex). Esas listas representan los registros del juego; la presencia actual de Pokémon se obtiene del equipo y las cajas. La comparación con la enciclopedia local y sus porcentajes pertenece a la segunda etapa; esta implementación no calcula un porcentaje usando el máximo de especies de la generación.

El alcance previsto son los juegos oficiales del catálogo, de Game Boy a 3DS (generaciones I a VII), mediante guardados normales reconocidos por PKHeX.Core: principalmente `.sav`, `.srm`, `.dsv` y `main` extraído y descifrado. La extensión por sí sola no garantiza compatibilidad. No se admiten save states, ROM hacks ni contenedores cifrados de consola. La edición detectada debe corresponder al juego seleccionado; algunos formatos antiguos solo permiten identificar una pareja de ediciones y se avisa de esa ambigüedad.

El servidor abre el original en lectura, limita el tamaño a 16 MiB y entrega al ayudante una copia temporal que se elimina al terminar. El ayudante no expone escritura ni recibe la ruta original. Durante la copia se comparan dos lecturas consecutivas y los metadatos del archivo para detectar cambios. Las sumas de comprobación de PKHeX.Core también deben ser válidas. Una vez obtenida una copia válida, los cambios posteriores del original no invalidan la lectura. El juego puede permanecer abierto; el launcher nunca escribe en la carpeta de partidas.

La ruta, fecha de modificación, fecha de lectura y hash de la copia se incluyen en la respuesta. Se conserva una copia por juego y sus datos en la tabla `save_snapshots` de la base SQLite del launcher. Una actualización válida reemplaza la copia anterior y sus datos en una única transacción; si falla, se mantiene la última lectura válida. Al volver a la pestaña se muestra esa lectura guardada, sin acceder de nuevo al original. Después de la primera carga, la copia se renueva al pulsar Actualizar o al seleccionar otra partida.

**Estado de validación:** instalado SDK .NET 10.0.113 y runtime 10.0.13. Compilado el lector con PKHeX.Core 26.8.26.0 extraído de la AppImage local; la restauración de NuGet está restringida en esta sesión. Lectura real de Pokémon Y correcta: equipo, cajas y registros de Pokédex, con persistencia de la copia en una base temporal y SHA-256 del original idéntico al terminar. El archivo detectado de Rubí Omega no fue reconocido por esa biblioteca y requiere revisión; su SHA-256 también permaneció idéntico. La API confirma que el lector está disponible. La publicación local se encuentra en `tools/SaveReader/publish`. Las demás ediciones y la revisión visual siguen pendientes.

PKHeX.Core es un proyecto de terceros bajo [GPL-3.0](https://github.com/kwsch/PKHeX/blob/26.10.18/LICENSE). Su código y condiciones deben tenerse en cuenta al distribuir el lector.


La detección de Azahar se basa en sus [rutas de usuario](https://github.com/azahar-emu/azahar/blob/master/src/common/file_util.cpp), [configuración de almacenamiento](https://github.com/azahar-emu/azahar/blob/master/src/citra_qt/configuration/config.cpp) y [estructura de guardados SD](https://github.com/azahar-emu/azahar/blob/master/src/core/file_sys/archive_source_sd_savedata.cpp). Se comprobaron ubicaciones temporales nativas y personalizadas, filtrado entre X/Y y respuesta de la API. Se localizaron guardados reales de Azahar nativo para Y y Rubí Omega. Los perfiles Flatpak siguen pendientes de revisión manual. Los emuladores restantes conservan selección manual de carpeta y archivo.


### Inspección de la AppImage local de PKHeX

Se inspeccionó `PKHeX-Avalonia-1.96.6-x86_64.AppImage` sin abrir ni modificar partidas. El ejecutable contiene un bundle .NET con `PKHeX.Core/26.8.26` y runtime `Microsoft.NETCore.App/10.0.14`. Se extrajo `PKHeX.Core.dll` únicamente en `/tmp` para revisión. No aparecen `libcoreclr.so` ni `libhostfxr.so` como bibliotecas separadas; intentar cargar el ejecutable desde Python mediante `ctypes.CDLL` falla porque es un ejecutable PIE. Esto descarta su carga directa como runtime compartido por esa vía, no todas las posibles técnicas de integración. Reutilizar la DLL con Python.NET todavía requiere disponer de un runtime cargable y validar la compatibilidad; esa lectura no se ha conseguido. Después de instalar el SDK del sistema se compiló el ayudante C# reutilizando esta DLL, y se validó la lectura de una copia real de Pokémon Y sin cambios en el original. El runtime utilizado por el ayudante es el del sistema.


### Presentación visual de partidas

El equipo se muestra con ilustraciones locales, tipos y detalles desplegables. Las cajas conservan las posiciones del guardado en una cuadrícula de sprites, con navegación entre cajas y una ficha del Pokémon seleccionado. Los datos del entrenador aparecen en una tarjeta con tiempo jugado y recuentos del equipo y las cajas; no se calcula todavía porcentaje de Pokédex.

Las imágenes se reutilizan de la Pokédex descargada, sin conexiones ni descargas al abrir Partidas. Si faltan, se conserva la lectura con marcadores visuales y un enlace a la Pokédex. Las ilustraciones generales representan la especie y pueden no reproducir una forma o variante variocolor concreta. Los tipos se omiten cuando la forma guardada no puede establecerse con los datos locales. La respuesta de lectura conserva los datos originales y añade imágenes únicamente al servirlos, sin alterar la copia persistida. El ayudante incluye ahora la capacidad de cada caja.

Comprobadas las rutas principales, las imágenes locales y la presentación en Firefox a tamaños de escritorio y móvil mediante una vista temporal de los datos de Y. Los cambios de estilos están limitados al visor de Partidas.


### Cajas disponibles y Caja de Combate en X/Y

El lector diferencia la capacidad máxima del formato de las cajas desbloqueadas en el guardado. Para X/Y y Rubí Omega/Zafiro Alfa consulta `BoxesUnlocked` y lee la `BattleBox` independiente de seis posiciones. Las cajas normales conservan sus nombres; se omiten las no desbloqueadas que estén vacías, manteniendo visibles las que contengan Pokémon aunque sus indicadores sean inconsistentes. La Caja de Combate aparece como sección visual separada y no aumenta el contador de cajas normales.

Comprobado con una copia guardada de Y: siete cajas normales disponibles, 74 Pokémon en ellas y seis en la Caja de Combate. Se conservó el hash de la copia usada para la revisión. Las lecturas antiguas de X/Y se reinterpretan automáticamente con el lector actualizado a partir de los bytes de la copia ya almacenada. Se conservan el estado y las fechas de esa copia, sin volver a abrir el guardado original. Actualizar sigue siendo la acción para obtener un guardado nuevo del emulador. El soporte de Rubí Omega/Zafiro Alfa utiliza las mismas estructuras de PKHeX.Core, pero todavía no se ha validado con un guardado reconocido de esas ediciones.

Referencias de implementación: [BoxLayout6](https://github.com/kwsch/PKHeX/blob/master/PKHeX.Core/Saves/Substructures/Gen6/BoxLayout6.cs) y [BattleBox6](https://github.com/kwsch/PKHeX/blob/master/PKHeX.Core/Saves/Substructures/Gen6/BattleBox6.cs).

Si el servidor se inició sin `--dev`, los cambios de Python requieren detenerlo y ejecutar `python server.py` de nuevo; recargar la página por sí solo no recarga el código del servidor.
