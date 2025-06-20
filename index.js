const { chromium } = require('playwright');
const sqlite3 = require('sqlite3').verbose();
const { open } = require('sqlite');
const fs = require('fs');

// Configuración de la base de datos
async function setupDatabase() {
    return open({
        filename: './anime_data.db',
        driver: sqlite3.Database
    });
}

// Función para inicializar la tabla
async function initializeDatabase(db) {
    await db.exec(`
        CREATE TABLE IF NOT EXISTS anime_counters (
            url TEXT PRIMARY KEY,
            anime_name TEXT NOT NULL,
            count INTEGER NOT NULL,
            last_checked TEXT
        )
    `);
}

// Función para obtener el contador actual de la base de datos
async function getCurrentCount(db, url) {
    const result = await db.get('SELECT count FROM anime_counters WHERE url = ?', [url]);
    return result ? result.count : 0;
}

// Función para actualizar o insertar el contador en la base de datos
async function updateCount(db, url, animeName, newCount) {
    const now = new Date().toISOString();
    await db.run(`
        INSERT OR REPLACE INTO anime_counters (url, anime_name, count, last_checked)
        VALUES (?, ?, ?, ?)
    `, [url, animeName, newCount, now]);
}

async function getEpisodeData(page) {
    // Esperar a que el contenido dinámico se cargue
    await page.waitForLoadState('networkidle');
    
    // Busca el div con id "qlt-1080p"
    const qltDiv = await page.$('div#qlt-1080p');
    if (!qltDiv) return { count: 0, megaLink: null };

    // Dentro de ese div, busca el div con clase "episodios drv"
    const episodiosDiv = await qltDiv.$('div.episodios.drv');
    if (!episodiosDiv) return { count: 0, megaLink: null };

    // Obtiene todos los divs con clase "ep no1"
    const episodios = await episodiosDiv.$$('div.ep.no1');
    const count = episodios.length;

    // Extrae el enlace MEGA del ÚLTIMO episodio
    let megaLink = null;
    if (count > 0) {
        const lastEpisode = episodios[count - 1];
        const megaElement = await lastEpisode.$('a.mega');
        if (megaElement) {
            megaLink = await megaElement.getAttribute('href');
        }
    }

    return { count, megaLink };
}

async function bypassCaptcha(page, url) {
    // Navega a la URL de MEGA
    await page.goto(url, { 
        waitUntil: 'domcontentloaded',
        timeout: 30000
    });

    try {
        // Esperar a que la página se cargue completamente
        await page.waitForLoadState('networkidle');
        
        // Espera y haz clic en el botón CAPTCHA
        await page.waitForSelector('#btn-main', { state: 'visible', timeout: 15000 });
        await page.click('#btn-main');
        console.log('✅ CAPTCHA resuelto (clic en "I\'m a human")');
        
        // Espera a posibles redirecciones
        await page.waitForNavigation({ timeout: 10000 });
    } catch (error) {
        console.error('❌ Error al resolver CAPTCHA:', error.message);
    }

    // Espera a que la página cargue completamente
    await page.waitForLoadState('networkidle');
    try {
        // Espera y haz clic en el botón CAPTCHA
        await page.waitForSelector('#btn-main', { state: 'visible', timeout: 15000 });
        await page.click('#btn-main');
        console.log('✅ CAPTCHA resuelto (clic en "Get Link")');
        
        // Espera a posibles redirecciones
        await page.waitForNavigation({ timeout: 10000 });
        return page.url();
    } catch (error) {
        console.error('❌ Error al resolver CAPTCHA:', error.message);
        return null;
    }
}

async function processAnime(db, page, animeName, animeUrl, attempt = 1, maxAttempts = 2) {
    try {
        console.log(`\n🔍 Procesando anime: ${animeName}${attempt > 1 ? ` (Intento ${attempt}/${maxAttempts})` : ''}`);
        
        // Obtener el contador actual de la base de datos
        const currentCount = await getCurrentCount(db, animeUrl);
        console.log(`📊 Contador actual en DB: ${currentCount}`);

        // Obtener el enlace MEGA y el nuevo contador
        await page.goto(animeUrl, { 
            waitUntil: 'domcontentloaded',
            timeout: 30000
        });
        
        // Esperar contenido dinámico
        await page.waitForTimeout(2000);
        
        const { count: newCount, megaLink } = await getEpisodeData(page);
        console.log(`📊 Episodios encontrados: ${newCount}`);

        // Verificar si hay nuevos episodios
        if (newCount > currentCount) {
            console.log('🎉 ¡Nuevos episodios encontrados!');
            
            if (megaLink) {
                console.log('🔄 Navegando a MEGA para resolver CAPTCHA...');
                const megaUrlFinal = await bypassCaptcha(page, megaLink);
                
                if (megaUrlFinal) {
                    console.log(`🔗 Enlace final de MEGA: ${megaUrlFinal}`);
                    
                    // Actualizar la base de datos
                    await updateCount(db, animeUrl, animeName, newCount);
                    console.log('💾 Base de datos actualizada');
                    
                    const fecha = new Date();
                    const fechaFormateada = fecha.toLocaleDateString('es-ES', {
                        day: '2-digit',
                        month: '2-digit',
                        year: 'numeric'
                    }).replace(/\//g, '-');

                    // Guardar enlace en JSON
                    const animeData = {
                        name: animeName,
                        megaLink: megaUrlFinal,
                        date: fechaFormateada,
                        episodeCount: newCount
                    };

                    // Leer archivo existente o crear uno nuevo
                    let allLinks = [];
                    try {
                        allLinks = JSON.parse(fs.readFileSync('./mega_links.json', 'utf8'));
                        if (!Array.isArray(allLinks)) {
                            allLinks = [];
                        }
                    } catch (e) {
                        allLinks = [];
                    }

                    // Buscar si ya existe un elemento con el mismo nombre
                    const existingIndex = allLinks.findIndex(item => item.name === animeName);

                    if (existingIndex !== -1) {
                        // Reemplazar el elemento existente
                        allLinks[existingIndex] = animeData;
                        console.log('📄 Enlace MEGA actualizado en mega_links.json');
                    } else {
                        // Agregar nuevo enlace
                        allLinks.push(animeData);
                        console.log('📄 Enlace MEGA agregado a mega_links.json');
                    }

                    // Guardar los cambios
                    fs.writeFileSync('./mega_links.json', JSON.stringify(allLinks, null, 2));
                    
                    return { success: true, animeName, megaUrlFinal, attempts: attempt };
                }
            } else {
                console.log('⚠️ No se encontró enlace MEGA');
            }
        } else {
            console.log('ℹ️ No hay nuevos episodios disponibles');
        }
        
        return { success: false, animeName, attempts: attempt };
    } catch (error) {
        console.error(`❌ Error procesando ${animeName} (Intento ${attempt}/${maxAttempts}):`, error.message);
        
        // Si falla y aún quedan intentos, reintenta
        if (attempt < maxAttempts) {
            console.log(`🔄 Reintentando ${animeName} en 3 segundos...`);
            await page.waitForTimeout(3000); // Pausa de 3 segundos antes del retry
            return await processAnime(db, page, animeName, animeUrl, attempt + 1, maxAttempts);
        }
        
        return { success: false, animeName, error: error.message, attempts: attempt };
    }
}

// Ejecución principal
(async () => {
    // Inicializar base de datos
    const db = await setupDatabase();
    await initializeDatabase(db);

    // Configuración optimizada para headless con soporte JavaScript dinámico
    const browser = await chromium.launch({ 
        headless: true,
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--no-first-run',
            '--no-zygote',
            '--disable-gpu',
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding',
            '--disable-features=TranslateUI',
            '--disable-ipc-flooding-protection',
            '--disable-extensions',
            '--disable-default-apps',
            '--disable-sync',
            '--disable-translate',
            '--hide-scrollbars',
            '--mute-audio',
            '--no-default-browser-check',
            '--disable-web-security',
            '--disable-features=VizDisplayCompositor',
            '--disable-blink-features=AutomationControlled'
        ]
    });

    const context = await browser.newContext({
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        viewport: { width: 1920, height: 1080 },
        locale: 'es-ES',
        timezoneId: 'America/Guatemala',
        extraHTTPHeaders: {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1'
        }
    });

    const page = await context.newPage();

    // Configuraciones adicionales para JavaScript dinámico
    await page.setExtraHTTPHeaders({
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
    });

    // Interceptar y modificar requests si es necesario
    await page.route('**/*', (route) => {
        const request = route.request();
        const headers = {
            ...request.headers(),
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        };
        route.continue({ headers });
    });

    // Diccionario con diferentes nombres de anime y enlaces
    const animeLinks = {
        'tobeherox': 'https://www.ivanime.com/paste/2031576/',
        'fireforce': 'https://www.ivanime.com/paste/3031564/',
        // Puedes agregar más animes aquí
    };

    try {
        console.log('🚀 Iniciando verificación de animes...');
        
        const results = [];
        
        // Procesar cada anime secuencialmente para evitar problemas
        for (const [animeName, animeUrl] of Object.entries(animeLinks)) {
            const result = await processAnime(db, page, animeName, animeUrl);
            results.push(result);
            
            // Pequeña pausa entre requests para ser más amigable
            await page.waitForTimeout(1000);
        }
        
        // Mostrar resumen
        console.log('\n📝 Resumen de resultados:');
        const updatedAnimes = results.filter(r => r.success);
        const failedAnimes = results.filter(r => !r.success && r.error);
        const noNewEpisodes = results.filter(r => !r.success && !r.error);
        
        if (updatedAnimes.length > 0) {
            console.log('✅ Animes actualizados:');
            updatedAnimes.forEach(anime => {
                console.log(`- ${anime.animeName}: ${anime.megaUrlFinal} (${anime.attempts} intento${anime.attempts > 1 ? 's' : ''})`);
            });
        }
        
        if (failedAnimes.length > 0) {
            console.log('❌ Animes con errores:');
            failedAnimes.forEach(anime => {
                console.log(`- ${anime.animeName}: ${anime.error} (${anime.attempts} intento${anime.attempts > 1 ? 's' : ''})`);
            });
        }
        
        if (noNewEpisodes.length > 0) {
            console.log('ℹ️ Animes sin nuevos episodios:');
            noNewEpisodes.forEach(anime => {
                console.log(`- ${anime.animeName} (${anime.attempts} intento${anime.attempts > 1 ? 's' : ''})`);
            });
        }
        
        console.log(`\n🎉 Proceso completado. ${updatedAnimes.length} animes actualizados, ${failedAnimes.length} con errores, ${noNewEpisodes.length} sin nuevos episodios.`);

    } catch (error) {
        console.error('❌ Error general:', error.message);
    } finally {
        await browser.close();
        await db.close();
    }
})();