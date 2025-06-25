# Anime Episode Checker (IVANIME)

NOTA: SOLO FUNCIONA LOCALMENTE, EN GITHUB ACTIONS NO LOGRA PASAR EL BYPASS DE CLOUDFLARE EN OUO.IO

Herramienta automatizada para verificar nuevos episodios de anime en ivanime.com y obtener enlaces de descarga de MEGA.

## 🚀 Características

- **Detección automática de nuevos episodios**: Verifica si hay episodios nuevos comparando con la base de datos local
- **Resolución automática de CAPTCHA**: Bypassa los CAPTCHAs de las páginas intermedias
- **Base de datos SQLite**: Almacena el progreso y contador de episodios
- **Exportación JSON**: Guarda los enlaces de MEGA en un archivo JSON
- **Múltiples animes**: Soporta verificación de varios animes simultáneamente
- **Headless**: Funciona en segundo plano sin abrir ventanas del navegador

## 📋 Requisitos

- Node.js (v14 o superior)
- npm o yarn

## 🛠️ Instalación

1. Clona el repositorio:
```bash
git clone <tu-repositorio>
cd anime-episode-checker
```

2. Instala las dependencias:
```bash
npm install
```

Las dependencias principales son:
- `playwright`: Para automatización del navegador
- `sqlite3`: Base de datos SQLite
- `sqlite`: Wrapper moderno para SQLite

## 📖 Uso

### Configuración inicial

1. Edita el objeto `animeLinks` en el código para agregar tus animes:
```javascript
const animeLinks = {
    'nombre-anime': 'https://www.ivanime.com/paste/ID/',
    'otro-anime': 'https://www.ivanime.com/paste/OTRO-ID/',
};
```

### Ejecución

```bash
node index.js
```

## 📁 Estructura de archivos

```
proyecto/
├── index.js              # Archivo principal
├── anime_data.db         # Base de datos SQLite (se crea automáticamente)
├── mega_links.json       # Enlaces de MEGA exportados
├── package.json
└── README.md
```

## 🗄️ Base de datos

La aplicación crea automáticamente una base de datos SQLite (`anime_data.db`) con la siguiente estructura:

```sql
CREATE TABLE anime_counters (
    url TEXT PRIMARY KEY,
    anime_name TEXT NOT NULL,
    count INTEGER NOT NULL,
    last_checked TEXT
);
```

## 📄 Archivo de salida

Los enlaces de MEGA se guardan en `mega_links.json` con el siguiente formato:

```json
[
  {
    "name": "tobeherox",
    "megaLink": "https://mega.nz/file/...",
    "date": "2024-01-01T12:00:00.000Z",
    "episodeCount": 25
  }
]
```

## 🔧 Funcionamiento

1. **Verificación de episodios**: Busca el div con ID `qlt-1080p` y cuenta los elementos con clase `ep no1`
2. **Comparación**: Compara el contador actual con el almacenado en la base de datos
3. **Detección de nuevos episodios**: Si hay más episodios, procede a obtener el enlace MEGA
4. **Resolución de CAPTCHA**: Navega a la página de MEGA y resuelve automáticamente el CAPTCHA
5. **Actualización**: Actualiza la base de datos y el archivo JSON con la nueva información

## 🎯 Funciones principales

### `getEpisodeData(page)`
Extrae el contador de episodios y el enlace MEGA del último episodio.

### `bypassCaptcha(page, url)`
Resuelve automáticamente los CAPTCHAs de las páginas intermedias.

### `processAnime(db, page, animeName, animeUrl)`
Procesa un anime completo: verifica, compara, actualiza y guarda.

## ⚙️ Configuración

### Modo headless
Por defecto, el navegador funciona en modo headless. Para ver el navegador en acción:
```javascript
const browser = await chromium.launch({ headless: false });
```

### Timeouts
Los timeouts están configurados para manejar páginas lentas:
- Selector CAPTCHA: 15 segundos
- Navegación: 10 segundos

## 🐛 Troubleshooting

### Error de CAPTCHA
Si el CAPTCHA no se resuelve automáticamente:
- Verifica que la página no haya cambiado su estructura
- Aumenta los timeouts si la conexión es lenta

### Error de base de datos
Si hay problemas con SQLite:
- Elimina el archivo `anime_data.db` para regenerarlo
- Verifica los permisos de escritura en el directorio

### Problemas con Playwright
Si Playwright no funciona:
```bash
npx playwright install
```

## 📝 Logs

La aplicación proporciona logs detallados:
- 🔍 Procesando anime
- 📊 Contadores actuales y nuevos
- 🎉 Nuevos episodios encontrados
- 🔗 Enlaces de MEGA obtenidos
- 💾 Actualizaciones de base de datos

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:
1. Fork el repositorio
2. Crea una rama para tu feature
3. Commit tus cambios
4. Push a la rama
5. Abre un Pull Request

## ⚠️ Disclaimer

Esta herramienta es solo para uso educativo. Respeta los términos de servicio de los sitios web que utilices.
