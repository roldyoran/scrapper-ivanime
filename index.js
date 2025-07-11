const { chromium } = require('playwright');
const sqlite3 = require('sqlite3').verbose();
const { open } = require('sqlite');
const fs = require('fs');

async function setupDatabase() {
    return open({
        filename: './anime_data.db',
        driver: sqlite3.Database
    });
}

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

async function getCurrentCount(db, url) {
    const result = await db.get('SELECT count FROM anime_counters WHERE url = ?', [url]);
    return result ? result.count : 0;
}

async function updateCount(db, url, animeName, newCount) {
    const now = new Date().toISOString();
    await db.run(`
        INSERT OR REPLACE INTO anime_counters (url, anime_name, count, last_checked)
        VALUES (?, ?, ?, ?)
    `, [url, animeName, newCount, now]);
}

async function getEpisodeData(page) {
    await page.waitForLoadState('load');
    const qltDiv = await page.$('div#qlt-1080p');
    if (!qltDiv) return { count: 0, megaLink: null };
    const episodiosDiv = await qltDiv.$('div.episodios.drv');
    if (!episodiosDiv) return { count: 0, megaLink: null };
    const episodios = await episodiosDiv.$$('div.ep.no1');
    const count = episodios.length;
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

async function bypassCaptcha(page, url, attempt = 1, maxAttempts = 2) {
    console.log(`🔄 Intentando resolver CAPTCHA OUO.IO (Intento ${attempt}/${maxAttempts})`);

    await page.mouse.move(100, 100);
    await page.waitForTimeout(1000);
    await page.mouse.wheel(0, 300); // deltaX = 0, deltaY = 300
    await page.waitForTimeout(500);

    try {
        await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
        await page.waitForLoadState('load', { timeout: 60000 });

        const title = await page.title();
        if (title.includes("Just a moment") || title.includes("Un momento")) {
            console.log("🛡️ Página protegida por Cloudflare.");
            await page.waitForTimeout(24000);
            await page.context().clearCookies();
        }

        // Función para buscar el botón correcto y hacer click esperando navegación
        async function clickCaptchaButton() {
            // Primero intenta con id #btn-main
            let btn = page.locator('#btn-main');
            try {
                await btn.waitFor({ state: 'visible', timeout: 5000 });
            } catch {
                // Si no está visible, intenta con clase .btn.btn-main
                btn = page.locator('button.btn.btn-main');
                await btn.waitFor({ state: 'visible', timeout: 15000 }); // un poco más de tiempo
            }

            await Promise.all([
                page.waitForNavigation({ waitUntil: 'load', timeout: 60000 }),
                btn.click()
            ]);
        }



        await clickCaptchaButton();
        console.log('✅ CAPTCHA resuelto (clic en botón I M HUMAN)');
        await page.waitForLoadState('load', { timeout: 60000 });
        await clickCaptchaButton();
        console.log('✅ CAPTCHA resuelto (clic en botón GET LINK)');

        const finalUrl = page.url();
        console.log(`✅ URL final tras los 2 CAPTCHA: ${finalUrl}`);
        return finalUrl;

    } catch (error) {
        console.error(`❌ Error en CAPTCHA (Intento ${attempt}):`, error.message);
        await page.screenshot({ path: `error_captcha_attempt_${attempt}.png` });
        console.log(await page.title());
        console.log(await page.content());

        if (attempt < maxAttempts) {
            console.log('🔄 Reintentando en 5 segundos...');
            await page.waitForTimeout(5000);
            return await bypassCaptcha(page, url, attempt + 1, maxAttempts);
        }
        return null;
    }
}

async function processAnime(db, page, animeName, animeUrl, attempt = 1, maxAttempts = 2) {
    try {
        console.log(`\n🔍 Procesando anime: ${animeName} (Intento ${attempt}/${maxAttempts})`);
        const currentCount = await getCurrentCount(db, animeUrl);
        console.log(`📊 Contador actual: ${currentCount}`);

        await page.goto(animeUrl, { waitUntil: 'domcontentloaded', timeout: 60000 });
        await page.waitForTimeout(2000);

        const { count: newCount, megaLink } = await getEpisodeData(page);
        console.log(`📊 Episodios encontrados: ${newCount}`);

        if (newCount > currentCount) {
            console.log('🎉 Nuevos episodios encontrados');
            if (megaLink) {
                console.log('🔄 Navegando a MEGA para resolver CAPTCHA...');
                const megaUrlFinal = await bypassCaptcha(page, megaLink);
                if (megaUrlFinal) {
                    await updateCount(db, animeUrl, animeName, newCount);
                    console.log('💾 Base de datos actualizada');

                    const fechaFormateada = new Date().toLocaleDateString('es-ES').replace(/\//g, '-');
                    const animeData = {
                        name: animeName,
                        megaLink: megaUrlFinal,
                        date: fechaFormateada,
                        episodeCount: newCount
                    };

                    let allLinks = [];
                    try {
                        const content = fs.readFileSync('./mega_links.json', 'utf8');
                        allLinks = content ? JSON.parse(content) : [];
                        if (!Array.isArray(allLinks)) allLinks = [];
                    } catch {
                        allLinks = [];
                    }

                    const existingIndex = allLinks.findIndex(item => item.name === animeName);
                    if (existingIndex !== -1) allLinks[existingIndex] = animeData;
                    else allLinks.push(animeData);

                    fs.writeFileSync('./mega_links.json', JSON.stringify(allLinks, null, 2));
                    console.log('📄 mega_links.json actualizado');
                    return { success: true, animeName, megaUrlFinal, attempts: attempt };
                } else {
                    console.log('⚠️ No se pudo resolver el CAPTCHA');
                }
            } else {
                console.log('⚠️ No se encontró enlace MEGA');
            }
        } else {
            console.log('ℹ️ No hay nuevos episodios');
        }
        return { success: false, animeName, attempts: attempt };
    } catch (error) {
        console.error(`❌ Error procesando ${animeName} (Intento ${attempt}):`, error.message);
        if (attempt < maxAttempts) {
            console.log('🔄 Reintentando en 3 segundos...');
            await page.waitForTimeout(3000);
            return await processAnime(db, page, animeName, animeUrl, attempt + 1, maxAttempts);
        }
        return { success: false, animeName, error: error.message, attempts: attempt };
    }
}

(async () => {
    const db = await setupDatabase();
    await initializeDatabase(db);

    // Verificar si storage.json es válido
    let storageState = undefined;
    try {
        const content = fs.readFileSync('storage.json', 'utf8');
        if (content.trim()) {
            JSON.parse(content); // validación
            storageState = 'storage.json';
        }
    } catch {
        console.log('⚠️ Archivo storage.json no válido, se ignorará esta sesión.');
    }

    const browser = await chromium.launch({
        headless: true,
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--single-process',
            '--no-zygote',
            '--disable-blink-features=AutomationControlled',
            '--disable-features=IsolateOrigins,site-per-process',
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        ]
    });

    const context = await browser.newContext({
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        viewport: { width: 1920, height: 1080 },
        locale: 'es-ES',
        timezoneId: 'America/Guatemala',
        storageState,
        extraHTTPHeaders: {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'https://www.ivanime.com/'
        }
    });

    const page = await context.newPage();

    const animeLinks = {
        'tobeherox': 'https://www.ivanime.com/paste/2031576/',
        // Agrega más animes aquí
    };

    try {
        console.log('🚀 Iniciando verificación de animes...');
        const results = [];
        for (const [animeName, animeUrl] of Object.entries(animeLinks)) {
            const result = await processAnime(db, page, animeName, animeUrl);
            results.push(result);
            await page.waitForTimeout(1000);
        }

        console.log('\n📝 Resumen de resultados:');
        const updatedAnimes = results.filter(r => r.success);
        const failedAnimes = results.filter(r => !r.success && r.error);
        const noNewEpisodes = results.filter(r => !r.success && !r.error);

        if (updatedAnimes.length) {
            console.log('✅ Animes actualizados:');
            updatedAnimes.forEach(a =>
                console.log(`- ${a.animeName}: ${a.megaUrlFinal} (${a.attempts} intento${a.attempts > 1 ? 's' : ''})`)
            );
        }

        if (failedAnimes.length) {
            console.log('❌ Animes con errores:');
            failedAnimes.forEach(a =>
                console.log(`- ${a.animeName}: ${a.error} (${a.attempts} intento${a.attempts > 1 ? 's' : ''})`)
            );
        }

        if (noNewEpisodes.length) {
            console.log('ℹ️ Animes sin nuevos episodios:');
            noNewEpisodes.forEach(a =>
                console.log(`- ${a.animeName} (${a.attempts} intento${a.attempts > 1 ? 's' : ''})`)
            );
        }

        await context.storageState({ path: 'storage.json' });
        console.log(`\n🎉 Proceso completado. ${updatedAnimes.length} actualizados, ${failedAnimes.length} con errores, ${noNewEpisodes.length} sin nuevos episodios.`);
    } catch (error) {
        console.error('❌ Error general:', error.message);
    } finally {
        await browser.close();
        await db.close();
    }
})();
