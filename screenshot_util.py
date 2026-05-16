import asyncio
from playwright.async_api import async_playwright

async def take_screenshot(url, output_path):
    """
    Takes a full-page screenshot of the given URL.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Emulate a typical desktop screen width, and let height expand
        context = await browser.new_context(viewport={'width': 1280, 'height': 800})
        page = await context.new_page()
        
        print(f"Taking screenshot of {url}...")
        try:
            # Go to the URL, wait for network to be idle
            await page.goto(url, wait_until='networkidle', timeout=60000)
            
            # Optional: Hide annoying sticky headers / banners if needed
            # For GitHub, it's usually fine as is.
            
            # Take a full page screenshot
            await page.screenshot(path=output_path, full_page=True)
            print(f"Screenshot saved to {output_path}")
        except Exception as e:
            print(f"Failed to take screenshot: {e}")
            raise
        finally:
            await browser.close()

if __name__ == "__main__":
    # Test script
    asyncio.run(take_screenshot("https://github.com/microsoft/playwright", "test_screenshot.png"))
