import re
from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://www.brittany-ferries.ie/booking/trip")
    page.get_by_role("button", name="Yes, I accept!").click()
    page.get_by_role("radio", name="One way").check()
    page.locator("#mat-select-value-0").click()
    page.locator("span").filter(has_text="Rosslarearrow_right_altBilbao").first.click()
    page.locator(".mat-mdc-form-field.pb-0 > .mat-mdc-text-field-wrapper > .mat-mdc-form-field-flex > .mat-mdc-form-field-infix").click()
    page.get_by_role("button", name="September").click()
    page.get_by_role("button", name="18 September").click()
    page.locator("#mat-select-1 > .mat-mdc-select-trigger > .mat-mdc-select-arrow-wrapper").click()
    page.get_by_test_id("adultsPassengers").get_by_test_id("numberSelectorAdd").click()
    page.get_by_test_id("adultsPassengers").get_by_test_id("numberSelectorAdd").click()
    page.get_by_test_id("selectWrapper").get_by_test_id("submit").click()
    page.locator("#mat-select-4 > .mat-mdc-select-trigger > .mat-mdc-select-arrow-wrapper").click()
    page.locator("span").filter(has_text="Minibus/Motorhome").first.click()
    page.locator(".mat-mdc-checkbox-touch-target").first.click()
    page.get_by_test_id("vehicleDetailsSubmit").click()
    page.locator("#mat-select-6 > .mat-mdc-select-trigger > .mat-mdc-select-arrow-wrapper").click()
    page.get_by_test_id("smallDogs").get_by_test_id("numberSelectorAdd").click()
    page.get_by_test_id("smallDogs").get_by_test_id("numberSelectorAdd").click()
    page.get_by_test_id("selectWrapper").get_by_test_id("submit").click()
    page.get_by_test_id("submit").click()
    page.close()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
