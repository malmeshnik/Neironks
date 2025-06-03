from playwright.sync_api import sync_playwright

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state="state.json")
        page = context.new_page()
        page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                window.chrome = { runtime: {} };
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3],
                });
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['ru-RU', 'ru'],
                });
                Object.defineProperty(navigator, 'platform', {
                    get: () => 'Win32',
                });
            """)

        page = browser.new_page()
        page.goto("https://freelancehunt.com/profile/login?_gl=1*12xjmeb*_up*MQ..*_gs*MQ..&gclid=Cj0KCQjwzYLABhD4ARIsALySuCQ95fvA3deLv9zZw3nP0hW5L0_WPHwzUilou64ZdsjYBuSdl83HkCoaAkvMEALw_wcB", referer="https://www.google.com")
        #page.goto("https://www.google.com")
        print("📄 URL now:", page.url)
        print("🔍 Title:", page.title()) 
       	#print("✅ Content:", page.content()[:1000])
        #page.fill("textarea[name='q']", "freelancehunt")
#        page.fill("input[name='q']", "freelancehunt")
        #page.keyboard.press("Enter")
        #page.wait_for_timeout(2000)
        #page.click("text=Freelancehunt")
        #print("✅ Страница загружена")
        #print("⏳ Ждём появления ссылки на Freelancehunt...")
#        page.wait_for_selector("h3.LC20lb", timeout=10000)
 #       page.click("h3.LC20lb:has-text('Freelancehunt — the best freelance marketplace')")
        html_content = page.content()
        print("✅ Код страницы:")
        print(html_content)
        browser.close()

if __name__ == "__main__":
    main()
