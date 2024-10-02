import argparse
import logging
from pathlib import Path

from playwright.sync_api import sync_playwright


def run(playwright, sdk_name, sdk_url):
    browser = playwright.firefox.launch(headless=True)
    context = browser.new_context(bypass_csp=True)
    page = context.new_page()
    try:
        page.goto(sdk_url)
        page.wait_for_load_state("networkidle")
    except Exception:
        logging.error(f"{sdk_name} failed")
        return
    # 获取页面 HTML
    html_content = page.content()
    with open(f"./htmls/{sdk_name}.html", "w", encoding="utf-8") as fout:
        fout.write(html_content)
    # print(html_content)
    # 关闭浏览器
    context.close()
    browser.close()


def main():
    logging.basicConfig(
        format='%(asctime)s [%(levelname)s] %(message)s', level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--sdkName", help="Sdk Name")
    parser.add_argument("-u", "--sdkURL", help="Sdk URL")
    args = parser.parse_args()
    sdk_name = Path(args.sdkName)
    sdk_url = Path(args.sdkURL)
    with sync_playwright() as playwright:
        run(playwright, sdk_name, sdk_url)


if __name__ == "__main__":
    main()
