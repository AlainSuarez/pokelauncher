# PokéLauncher

Tu colección de Pokémon, en un solo lugar.

PokéLauncher es una aplicación local para Linux que reúne tus juegos de Pokémon en una biblioteca visual. Explora las entregas de Game Boy a Nintendo 3DS, abre tus ROMs con el emulador que prefieras y consulta información de los juegos, su Pokédex y tus partidas desde una misma interfaz.

Funciona en el navegador y se ejecuta en tu propio equipo. No necesitas Node.js ni una cuenta para usarlo.

## Un vistazo

### Tu biblioteca

Carátulas, búsqueda y filtros para recorrer los 28 juegos del catálogo, desde Pokémon Red hasta Pokémon Ultra Moon. Organiza tus favoritos y consulta los juegos de tu colección.

![Biblioteca de PokéLauncher con carátulas y filtros por consola](docs/screenshots/biblioteca.png)

### Cada juego tiene su espacio

Abre una ficha para consultar su resumen, acceder a la Pokédex, revisar partidas o elegir la ROM y el emulador con el que jugar.

![Ficha de Pokémon Blue en PokéLauncher](docs/screenshots/juego.png)

### Configuración a tu medida

Elige tus carpetas de ROMs y configura emuladores nativos, AppImage o Flatpak para cada consola.

![Configuración de carpetas y emuladores](docs/screenshots/configuracion.png)

Las capturas muestran la aplicación con una configuración nueva, sin ROMs ni partidas personales.

## Qué puedes hacer

- **Explorar tu colección:** buscar por nombre, filtrar por consola, ordenar los juegos y guardar favoritos.
- **Lanzar tus juegos:** localizar ROMs en tus carpetas, asociarlas al catálogo y abrirlas con un emulador externo.
- **Consultar la Pokédex:** descargar los paquetes disponibles y después consultar sus fichas sin conexión, con ilustraciones, tipos, estadísticas y movimientos según la edición.
- **Ver tus partidas:** consultar entrenador, equipo y cajas mediante el lector opcional basado en PKHeX.Core. La lectura utiliza una copia y conserva el archivo original.

## Empezar

Necesitas **Linux con sesión gráfica** y **Python 3.10 o posterior**. Para jugar también necesitas tus propias ROMs y un emulador compatible instalado.

Desde la carpeta del proyecto, instala las dependencias y arranca la aplicación con el Python del sistema:

```bash
python -m pip install -r requirements.txt
python server.py
```

Si tu distribución administra Python y bloquea la instalación con `pip`, instala Flask y Waitress mediante su gestor de paquetes.

Abre **[http://127.0.0.1:8765](http://127.0.0.1:8765)** en tu navegador. Mantén la terminal abierta mientras usas el launcher; para detenerlo, pulsa `Ctrl+C`.

### Preparar tu colección

1. Abre **Configuración** y elige la carpeta raíz de tus ROMs. Organízalas en subcarpetas `gb`, `gbc`, `gba`, `nds` y `3ds`, o indica una ruta diferente para cada consola.
2. Configura el ejecutable o el ID de Flatpak del emulador para cada consola.
3. Pulsa **Guardar y buscar ROMs**. Las coincidencias claras se asocian automáticamente; puedes elegir las demás desde la configuración de cada juego.
4. Abre un juego y pulsa **Jugar**.

Se admiten emuladores que reciben la ruta de la ROM como argumento, como mGBA, melonDS o Azahar. En Flatpak, el emulador necesita permiso para acceder a tus carpetas. Los archivos ZIP y los paquetes CIA no se extraen ni instalan desde el launcher.

### Activar el visor de partidas

El visor requiere el **SDK de .NET 10** para preparar su lector opcional:

```bash
dotnet publish tools/SaveReader/SaveReader.csproj -c Release -o tools/SaveReader/publish
```

Después, inicia el launcher, configura la carpeta de partidas del emulador y abre la pestaña **Partidas** del juego. La compilación inicial necesita conexión para descargar PKHeX.Core.

## Estado del proyecto

PokéLauncher es un proyecto personal de hobby en desarrollo. La biblioteca y el lanzamiento mediante emuladores externos están disponibles. La Pokédex ofrece paquetes de Kanto y Kalos; el resto de regiones se incorporará progresivamente. El visor de partidas es experimental: se ha comprobado con Pokémon Y y la compatibilidad con las demás ediciones sigue pendiente de validación.

La aplicación se sirve únicamente en tu equipo. La biblioteca y la configuración funcionan sin conexión; la Pokédex necesita Internet para descargar sus recursos por primera vez.

Los ajustes se guardan en `~/.local/share/pokelauncher/` o en la ubicación definida por `XDG_DATA_HOME`. Puedes elegir otra carpeta con `python server.py --data-dir /ruta/a/datos`.

Para más detalles, consulta las [notas técnicas y de desarrollo](docs/notas-desarrollo.md) y el [plan del proyecto](PLAN.md).

## Créditos

Los datos y sprites de la Pokédex proceden de [PokéAPI](https://pokeapi.co/) y [PokeAPI/sprites](https://github.com/PokeAPI/sprites). El lector de partidas utiliza [PKHeX.Core](https://github.com/kwsch/PKHeX), sujeto a su licencia GPL-3.0.

PokéLauncher no incluye ROMs, BIOS, emuladores ni partidas. Pokémon, los nombres y las imágenes de los juegos pertenecen a sus respectivos titulares. Este proyecto no está afiliado a Nintendo, Game Freak ni The Pokémon Company.
