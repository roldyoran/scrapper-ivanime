import aiohttp
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import asyncio
import os
from datetime import datetime
import random
import time

class CloudflareBypasser:
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        ]
    
    async def get_episode_data_async(self, url):
        """Obtiene el contador de episodios y el enlace MEGA de la página"""
        try:
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers=headers
            ) as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    html_content = await response.text()
            
            soup = BeautifulSoup(html_content, 'html.parser')
            qlt_div = soup.find('div', id='qlt-1080p')
            
            if not qlt_div:
                print("No se encontró el div de calidad 1080p")
                return {'count': 0, 'megaLink': None}
            
            episodios_div = qlt_div.find('div', class_='episodios drv')
            episodios = episodios_div.find_all('div', class_='ep no1') if episodios_div else []
            
            mega_link = None
            if episodios:
                mega_element = episodios[-1].find('a', class_='mega')
                mega_link = mega_element.get('href') if mega_element else None
            
            return {'count': len(episodios), 'megaLink': mega_link}
            
        except Exception as e:
            print(f"Error al obtener datos: {str(e)}")
            return {'count': 0, 'megaLink': None}

    async def wait_for_cloudflare_bypass(self, page, timeout=60000):
        """Espera hasta que Cloudflare permita el acceso"""
        start_time = time.time()
        
        while time.time() - start_time < timeout / 1000:
            try:
                title = await page.title()
                url = page.url
                
                # Verificar si ya pasamos Cloudflare
                if not any(keyword in title.lower() for keyword in ['just a moment', 'verify you are human', 'checking', 'please wait']):
                    # Verificar que no estemos en una página de error
                    if 'error' not in url.lower() and 'blocked' not in url.lower():
                        print("✅ Cloudflare bypasseado exitosamente")
                        return True
                
                # Esperar un poco antes de verificar de nuevo
                await page.wait_for_timeout(2000)
                
            except Exception as e:
                print(f"Error durante el bypass: {e}")
                await page.wait_for_timeout(1000)
        
        print("❌ Timeout esperando bypass de Cloudflare")
        return False

    async def solve_turnstile(self, page):
        """Intenta resolver automáticamente el challenge de Turnstile"""
        try:
            # Buscar el iframe de Turnstile
            turnstile_frame = None
            frames = page.frames
            
            for frame in frames:
                if 'turnstile' in frame.url or 'challenges.cloudflare.com' in frame.url:
                    turnstile_frame = frame
                    break
            
            if turnstile_frame:
                print("🔍 Challenge de Turnstile detectado")
                
                # Esperar a que aparezca el checkbox
                try:
                    await turnstile_frame.wait_for_selector('input[type="checkbox"]', timeout=10000)
                    checkbox = await turnstile_frame.query_selector('input[type="checkbox"]')
                    
                    if checkbox:
                        print("🖱️ Haciendo clic en el checkbox de Turnstile")
                        await checkbox.click()
                        await page.wait_for_timeout(3000)
                        return True
                        
                except Exception as e:
                    print(f"No se pudo interactuar con el checkbox: {e}")
            
            return False
            
        except Exception as e:
            print(f"Error al resolver Turnstile: {e}")
            return False

    async def take_screenshot_with_bypass(self, mega_url, screenshot_path="screenshot.png"):
        """Toma captura de pantalla con bypass avanzado de Cloudflare"""
        if not mega_url:
            print("❌ No hay enlace MEGA disponible")
            return False
        
        browser = None
        try:
            async with async_playwright() as p:
                print("🚀 Iniciando navegador...")
                
                # Configuración del navegador para evadir detección
                browser = await p.chromium.launch(
                    headless=True,  # Cambiar a True si no quieres ver el navegador
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-features=VizDisplayCompositor',
                        '--disable-features=IsolateOrigins,site-per-process',
                        '--disable-ipc-flooding-protection',
                        '--disable-renderer-backgrounding',
                        '--disable-backgrounding-occluded-windows',
                        '--disable-background-timer-throttling',
                        '--force-fieldtrials=*BackgroundTracing/default/',
                        '--no-sandbox',
                        '--disable-web-security',
                        '--disable-dev-shm-usage',
                        '--disable-extensions',
                        '--no-first-run',
                        '--no-default-browser-check',
                        '--disable-default-apps',
                        '--disable-popup-blocking',
                        '--disable-translate',
                        '--disable-background-networking',
                        '--disable-sync',
                        '--metrics-recording-only',
                        '--disable-features=TranslateUI',
                        '--disable-features=BlinkGenPropertyTrees',
                        '--disable-component-extensions-with-background-pages',
                    ]
                )
                
                # Contexto del navegador con configuración anti-detección
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent=random.choice(self.user_agents),
                    locale='en-US',
                    timezone_id='America/New_York',
                    permissions=['geolocation'],
                    extra_http_headers={
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Cache-Control': 'no-cache',
                        'Pragma': 'no-cache',
                        'Sec-Fetch-Dest': 'document',
                        'Sec-Fetch-Mode': 'navigate',
                        'Sec-Fetch-Site': 'none',
                        'Upgrade-Insecure-Requests': '1'
                    }
                )
                
                # Inyectar scripts para evadir detección
                await context.add_init_script("""
                    // Eliminar propiedades que delatan automation
                    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                    
                    // Sobrescribir plugins
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [
                            {name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer'},
                            {name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai'},
                            {name: 'Native Client', filename: 'internal-nacl-plugin'}
                        ]
                    });
                    
                    // Simular interacción humana
                    ['mousedown', 'mouseup', 'mousemove', 'keydown', 'keyup'].forEach(event => {
                        window.addEventListener(event, () => {}, true);
                    });
                    
                    // Randomizar propiedades del canvas
                    const getContext = HTMLCanvasElement.prototype.getContext;
                    HTMLCanvasElement.prototype.getContext = function(type) {
                        const context = getContext.call(this, type);
                        if (type === '2d') {
                            const originalFillText = context.fillText;
                            context.fillText = function(...args) {
                                return originalFillText.apply(this, args);
                            };
                        }
                        return context;
                    };
                """)
                
                page = await context.new_page()
                
                print(f"🌐 Navegando a: {mega_url}")
                
                # Estrategia de navegación en múltiples pasos
                try:
                    # Primero ir a la página principal para establecer cookies
                    await page.goto('https://mega.nz', wait_until='domcontentloaded', timeout=30000)
                    await page.wait_for_timeout(random.randint(2000, 4000))
                    
                    # Simular movimiento del mouse
                    await page.mouse.move(random.randint(100, 500), random.randint(100, 500))
                    await page.wait_for_timeout(random.randint(1000, 2000))
                    
                    # Ahora ir a la URL objetivo
                    await page.goto(mega_url, wait_until='load', timeout=120000)
                    
                except Exception as nav_error:
                    print(f"⚠️ Error en navegación inicial: {nav_error}")
                    try:
                        await page.goto(mega_url, wait_until='domcontentloaded', timeout=60000)
                    except Exception as final_nav_error:
                        print(f"❌ Error final de navegación: {final_nav_error}")
                        return False
                
                # Verificar si hay protección de Cloudflare
                title = await page.title()
                if any(keyword in title.lower() for keyword in ['just a moment', 'verify you are human']):
                    print("🛡️ Cloudflare detectado. Iniciando bypass...")
                    
                    # Intentar resolver Turnstile si está presente
                    await self.solve_turnstile(page)
                    
                    # Esperar el bypass automático
                    if not await self.wait_for_cloudflare_bypass(page, timeout=120000):
                        print("❌ No se pudo bypasear Cloudflare automáticamente")
                        print("💡 Tip: Completa manualmente el captcha si aparece")
                        await page.wait_for_timeout(30000)  # Dar tiempo para intervención manual
                
                # Esperar a que la página cargue completamente
                await page.wait_for_timeout(5000)
                
                # Verificar que estamos en MEGA
                current_url = page.url
                if 'mega.nz' not in current_url and 'mega.co.nz' not in current_url:
                    print(f"⚠️ URL inesperada: {current_url}")
                
                print("📸 Tomando captura de pantalla...")
                await page.screenshot(path=screenshot_path, full_page=True)
                print(f"✅ Captura guardada en: {screenshot_path}")
                
                # Guardar contenido HTML para debugging
                content = await page.content()
                with open("mega_content.html", "w", encoding="utf-8") as f:
                    f.write(content)
                    print("📄 Contenido HTML guardado en mega_content.html")
                
                return True
                
        except Exception as e:
            print(f"❌ Error crítico: {str(e)}")
            return False
        finally:
            if browser:
                await browser.close()

    async def process_url_complete(self, url, screenshot_dir="screenshots"):
        """Proceso completo: obtener datos y captura con bypass"""
        try:
            os.makedirs(screenshot_dir, exist_ok=True)
            
            print("🔍 Obteniendo datos del episodio...")
            result = await self.get_episode_data_async(url)
            
            if not result['megaLink']:
                print("❌ No se encontró enlace MEGA")
                return result
            
            print(f"📺 Enlace MEGA encontrado. Episodios: {result['count']}")
            print(f"🔗 MEGA URL: {result['megaLink']}")
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot_path = os.path.join(screenshot_dir, f"mega_{timestamp}.png")
            
            print("\n🚀 Iniciando captura con bypass...")
            success = await self.take_screenshot_with_bypass(result['megaLink'], screenshot_path)
            
            if success:
                print("✅ Proceso completado exitosamente")
            else:
                print("❌ Error en el proceso de captura")
            
            return result
            
        except Exception as e:
            print(f"❌ Error crítico: {str(e)}")
            return {'count': 0, 'megaLink': None}

async def main():
    bypasser = CloudflareBypasser()
    
    try:
        url = 'https://www.ivanime.com/paste/2031576/'
        print("🎬 Iniciando scraper con bypass de Cloudflare...")
        print("=" * 50)
        
        result = await bypasser.process_url_complete(url)
        
        print("\n" + "=" * 50)
        print(f"📊 Resultado final:")
        print(f"   Episodios encontrados: {result['count']}")
        print(f"   MEGA Link: {result['megaLink']}")
        
    except KeyboardInterrupt:
        print("\n⏹️ Proceso interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ Error inesperado: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())