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
    await page.goto(url, { waitUntil: 'domcontentloaded' });

    try {
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
        console.log('✅ CAPTCHA resuelto (clic en Get Link")');
        
        // Espera a posibles redirecciones
        await page.waitForNavigation({ timeout: 10000 });
        return page.url();
    } catch (error) {
        console.error('❌ Error al resolver CAPTCHA:', error.message);
        return null;
    }
}

async function processAnime(db, page, animeName, animeUrl) {
    try {
        console.log(`\n🔍 Procesando anime: ${animeName}`);
        
        // Obtener el contador actual de la base de datos
        const currentCount = await getCurrentCount(db, animeUrl);
        console.log(`📊 Contador actual en DB: ${currentCount}`);

        // Obtener el enlace MEGA y el nuevo contador
        await page.goto(animeUrl, { waitUntil: 'domcontentloaded' });
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
                    
                    // Guardar enlace en JSON
                    const animeData = {
                        name: animeName,
                        megaLink: megaUrlFinal,
                        date: new Date().toISOString(),
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
                    
                    return { success: true, animeName, megaUrlFinal };
                }
            } else {
                console.log('⚠️ No se encontró enlace MEGA');
            }
        } else {
            console.log('ℹ️ No hay nuevos episodios disponibles');
        }
        
        return { success: false, animeName };
    } catch (error) {
        console.error(`❌ Error procesando ${animeName}:`, error.message);
        return { success: false, animeName, error: error.message };
    }
}

// Ejecución principal
(async () => {
    // Inicializar base de datos
    const db = await setupDatabase();
    await initializeDatabase(db);

    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();

    // Diccionario con diferentes nombres de anime y enlaces
    const animeLinks = {
        'tobeherox': 'https://www.ivanime.com/paste/2031576/',
        'fireforce': 'https://www.ivanime.com/paste/3031564/',
        // Puedes agregar más animes aquí
    };

    try {
        console.log('🚀 Iniciando verificación de animes...');
        
        const results = [];
        
        // Procesar cada anime en paralelo
        for (const [animeName, animeUrl] of Object.entries(animeLinks)) {
            const result = await processAnime(db, page, animeName, animeUrl);
            results.push(result);
        }
        
        // Mostrar resumen
        console.log('\n📝 Resumen de resultados:');
        const updatedAnimes = results.filter(r => r.success);
        const failedAnimes = results.filter(r => !r.success && r.error);
        
        if (updatedAnimes.length > 0) {
            console.log('✅ Animes actualizados:');
            updatedAnimes.forEach(anime => {
                console.log(`- ${anime.animeName}: ${anime.megaUrlFinal}`);
            });
        }
        
        if (failedAnimes.length > 0) {
            console.log('❌ Animes con errores:');
            failedAnimes.forEach(anime => {
                console.log(`- ${anime.animeName}: ${anime.error}`);
            });
        }
        
        console.log(`\n🎉 Proceso completado. ${updatedAnimes.length} animes actualizados, ${failedAnimes.length} con errores.`);

    } catch (error) {
        console.error('❌ Error general:', error.message);
    } finally {
        await browser.close();
        await db.close();
    }
})();