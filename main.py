import aiohttp
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import asyncio
import os
from datetime import datetime

async def get_episode_data_async(url):
    """Obtiene el contador de episodios y el enlace MEGA de la página"""
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
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
        
    except aiohttp.ClientError as e:
        print(f"Error de conexión: {str(e)}")
        return {'count': 0, 'megaLink': None}
    except Exception as e:
        print(f"Error inesperado al obtener datos: {str(e)}")
        return {'count': 0, 'megaLink': None}



async def take_screenshot_async(mega_url, screenshot_path="screenshot.png"):
    """Toma una captura de pantalla del enlace MEGA con ventana visible"""
    if not mega_url:
        print("No hay enlace MEGA disponible")
        return False
    
    browser = None
    try:
        async with async_playwright() as p:
            # Configuración con ventana visible (headless=False)
            browser = await p.chromium.launch(
                headless=False,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
                    '--start-maximized'
                ],
                slow_mo=500  # Mayor tiempo entre acciones
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                # Desactivar detección de automation
                bypass_csp=True,
                java_script_enabled=True,
                locale='en-US',
                timezone_id='America/New_York'
            )
            
            page = await context.new_page()
            
            try:
                print(f"Navegando a: {mega_url}")
                # Intentar con diferentes estrategias de carga
                try:
                    await page.goto(mega_url, wait_until='load', timeout=120000)  # 120 segundos
                except:
                    await page.goto(mega_url, wait_until='domcontentloaded', timeout=120000)
                
                # Esperar a que ciertos elementos críticos estén presentes
                try:
                    await page.wait_for_selector('body', state='attached', timeout=30000)
                except:
                    print("Advertencia: No se pudo verificar el cuerpo de la página")
                
                # Manejo de Cloudflare u otras protecciones
                if await page.title() in ["Just a moment, please...", "Verification"]:
                    print("Detectada protección. Esperando bypass manual...")
                    try:
                        await page.wait_for_selector('text=Verify you are human', timeout=10000)
                        print("Por favor completa el captcha manualmente...")
                        await page.wait_for_timeout(60000)  # 60 segundos para completar manualmente
                    except:
                        print("Continuando sin interacción manual...")
                
                # Esperar adicional para asegurar carga completa
                await page.wait_for_timeout(5000)
                
                print("Tomando captura de pantalla...")
                await page.screenshot(path=screenshot_path, full_page=True)
                print(f"Captura guardada exitosamente en: {screenshot_path}")
                return True
                
            except Exception as page_error:
                print(f"Error durante la navegación: {str(page_error)}")
                # Intentar capturar aunque haya error
                try:
                    await page.screenshot(path=f"error_{screenshot_path}", full_page=True)
                    print("Se guardó captura del estado de error")
                except:
                    pass
                return False
                
    except Exception as e:
        print(f"Error al iniciar el navegador: {str(e)}")
        return False
    finally:
        if browser:
            await browser.close()








async def process_url_with_screenshot_async(url, screenshot_dir="screenshots"):
    """Procesa una URL y toma captura de pantalla con manejo robusto de errores"""
    try:
        os.makedirs(screenshot_dir, exist_ok=True)
        
        print("\nObteniendo datos del episodio...")
        result = await get_episode_data_async(url)
        
        if not result['megaLink']:
            print("No se encontró enlace MEGA disponible")
            return result
        
        print(f"Enlace MEGA encontrado. Total de episodios: {result['count']}")
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        screenshot_path = os.path.join(screenshot_dir, f"mega_screenshot_{timestamp}.png")
        
        print("\nIniciando captura de pantalla...")
        success = await take_screenshot_async(result['megaLink'], screenshot_path)
        
        if success:
            print("\nProceso completado exitosamente")
        else:
            print("\nError durante el proceso de captura")
        
        return result
        
    except Exception as e:
        print(f"\nError crítico en el proceso principal: {str(e)}")
        return {'count': 0, 'megaLink': None}

async def main():
    try:
        url = 'https://www.ivanime.com/paste/2031576/'
        print("Iniciando proceso...")
        result = await process_url_with_screenshot_async(url)
        print(f"\nResultado final: {result}")
    except KeyboardInterrupt:
        print("\nProceso interrumpido por el usuario")
    except Exception as e:
        print(f"\nError inesperado en la ejecución principal: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())