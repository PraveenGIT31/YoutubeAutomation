import asyncio
from playwright.async_api import async_playwright

async def take_screenshot(url, output_path):
    """
    Takes a full-page screenshot of the given URL, with retries and robust options.
    """
    max_retries = 3
    retry_delay = 3  # seconds
    
    for attempt in range(1, max_retries + 1):
        print(f"Attempt {attempt}/{max_retries}: Taking screenshot of {url}...")
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                # Configure a standard desktop User-Agent to prevent bot detection blocks
                context = await browser.new_context(
                    viewport={'width': 1280, 'height': 800},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
                )
                page = await context.new_page()
                
                # Go to the URL, wait for standard load event (much faster/less flaky than networkidle)
                await page.goto(url, wait_until='load', timeout=30000)
                
                # Extra brief sleep to let dynamic styles/images render fully
                await page.wait_for_timeout(2000)
                
                # Take a full page screenshot
                await page.screenshot(path=output_path, full_page=True)
                print(f"Screenshot saved successfully to {output_path}")
                await browser.close()
                return  # Success!
        except Exception as e:
            print(f"Attempt {attempt} failed: {e}")
            if attempt < max_retries:
                print(f"Waiting {retry_delay}s before retrying...")
                await asyncio.sleep(retry_delay)
            else:
                print(f"All {max_retries} attempts failed to take screenshot.")
                raise

if __name__ == "__main__":
    # Test script
    asyncio.run(take_screenshot("https://github.com/microsoft/playwright", "test_screenshot.png"))
