import time
from playwright.sync_api import sync_playwright

def click_add_n_times(counter_locator, n):
    for _ in range(n + 3):
        if str(n) in counter_locator.inner_text():
            return True
        counter_locator.get_by_test_id("numberSelectorAdd").click()
        time.sleep(0.6)
    return str(n) in counter_locator.inner_text()

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://www.brittany-ferries.ie/booking/trip", wait_until="networkidle")

    page.get_by_role("button", name="Yes, I accept!").click()
    page.get_by_role("radio", name="One way").check()
    page.locator("#mat-select-value-0").click()
    page.locator("span").filter(has_text="Rosslarearrow_right_altBilbao").first.click()
    page.locator(".mat-mdc-form-field.pb-0 > .mat-mdc-text-field-wrapper > .mat-mdc-form-field-flex > .mat-mdc-form-field-infix").click()
    page.get_by_role("button", name="October").click()
    page.get_by_role("button", name="9 October 2026", exact=True).click()

    page.locator("#mat-select-1 > .mat-mdc-select-trigger > .mat-mdc-select-arrow-wrapper").click()
    adults = page.get_by_test_id("adultsPassengers")
    click_add_n_times(adults, 2)
    page.get_by_test_id("selectWrapper").get_by_test_id("submit").click()

    page.locator("#mat-select-4 > .mat-mdc-select-trigger > .mat-mdc-select-arrow-wrapper").click()
    page.locator("span").filter(has_text="Minibus/Motorhome").first.click()
    page.locator(".mat-mdc-checkbox-touch-target").first.click()
    page.get_by_test_id("vehicleDetailsSubmit").click()

    page.locator("#mat-select-6 > .mat-mdc-select-trigger > .mat-mdc-select-arrow-wrapper").click()
    dogs = page.get_by_test_id("smallDogs")
    dogs_ok = click_add_n_times(dogs, 2)
    page.get_by_test_id("selectWrapper").get_by_test_id("submit").click()

    page.get_by_test_id("submit").click()
    page.wait_for_timeout(4000)

    page.screenshot(path="debug_oct9_final.png", full_page=True)
    text = page.inner_text("body").lower().replace("\n", " ")

    print(f"dogs_ok = {dogs_ok}")
    if "no pet accommodation" in text:
        print("RESULT: SOLD_OUT_NO_PET_SPACE")
    elif any(m in text for m in ["sailing full", "sold out", "no availability", "fully booked", "not available"]):
        print("RESULT: SOLD_OUT")
    elif "€" in text:
        print("RESULT: AVAILABLE (correct - this date should have space)")
    else:
        print("RESULT: UNKNOWN")

    browser.close()
