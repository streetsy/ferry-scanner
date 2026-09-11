from playwright.sync_api import sync_playwright

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
    page.wait_for_timeout(4000)

    page.screenshot(path="debug_oct9_test.png", full_page=True)
    text = page.inner_text("body").lower()

    sold_out_markers = ["sold out", "no availability", "fully booked", "not available", "no sailings"]
    available_markers = ["select", "book now", "€"]

    if any(m in text for m in sold_out_markers):
        print("RESULT: SOLD_OUT (unexpected - this date should be available!)")
    elif any(m in text for m in available_markers):
        print("RESULT: AVAILABLE (correct!)")
    else:
        print("RESULT: UNKNOWN - check debug_oct9_test.png")

    browser.close()
