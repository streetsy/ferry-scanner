import os
import time
import requests
from datetime import datetime
from playwright.sync_api import sync_playwright

# ---------- YOUR SETTINGS ----------
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "PUT_YOUR_TOKEN_HERE")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "PUT_YOUR_CHAT_ID_HERE")

TARGET_DAYS = [18, 23, 25]
STATE_FILE = "last_known_state.txt"
MAX_ATTEMPTS = 3
# ------------------------------------


def send_telegram_photo(path, caption):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    try:
        with open(path, "rb") as f:
            requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption},
                          files={"photo": f}, timeout=30)
    except Exception as e:
        print(f"[WARN] Telegram photo send failed: {e}")


def click_add_n_times(counter_locator, n):
    """Clicks '+' until the counter actually shows n, retrying if a click didn't register."""
    for _ in range(n + 3):  # a few spare attempts in case one click is dropped
        current_text = counter_locator.inner_text()
        if str(n) in current_text:
            return True
        counter_locator.get_by_test_id("numberSelectorAdd").click()
        time.sleep(0.6)
    return str(n) in counter_locator.inner_text()


def check_one_date_attempt(day):
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
        page.get_by_role("button", name="September").click()
        page.get_by_role("button", name=f"{day} September 2026", exact=True).click()

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

        shot_path = f"debug_{day}sept.png"
        page.screenshot(path=shot_path, full_page=True)
        page_text = page.inner_text("body").lower().replace("\n", " ")
        browser.close()

        if not dogs_ok:
            return "UNKNOWN_DOG_COUNT_FAILED", shot_path

        pet_blocker_markers = ["no pet accommodation"]
        sold_out_markers = ["sailing full", "sold out", "no availability", "fully booked", "not available"]

        if any(m in page_text for m in pet_blocker_markers):
            return "SOLD_OUT_NO_PET_SPACE", shot_path
        elif any(m in page_text for m in sold_out_markers):
            return "SOLD_OUT", shot_path
        elif "€" in page_text:
            return "AVAILABLE", shot_path
        else:
            return "UNKNOWN", shot_path


def check_one_date(day):
    last_status, last_shot = "UNKNOWN", None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            status, shot = check_one_date_attempt(day)
            if not status.startswith("UNKNOWN"):
                return status, shot
            last_status, last_shot = status, shot
            print(f"  attempt {attempt} for {day} Sept was {status}, retrying...")
        except Exception as e:
            print(f"  attempt {attempt} for {day} Sept failed: {e}")
        time.sleep(3)
    return last_status, last_shot


def load_state():
    if not os.path.exists(STATE_FILE):
        return {}
    state = {}
    with open(STATE_FILE) as f:
        for line in f:
            if "=" in line:
                k, v = line.strip().split("=", 1)
                state[k] = v
    return state


def save_state(state):
    with open(STATE_FILE, "w") as f:
        for k, v in state.items():
            f.write(f"{k}={v}\n")


def main():
    last_state = load_state()
    new_state = {}

    for day in TARGET_DAYS:
        status, shot_path = check_one_date(day)
        new_state[str(day)] = status
        print(f"[{datetime.now()}] {day} Sept -> {status}")

        was_available = last_state.get(str(day)) == "AVAILABLE"
        if status == "AVAILABLE" and not was_available:
            send_telegram_photo(shot_path,
                f"\U0001F6A8 REAL availability found for {day} Sept Rosslare->Bilbao (incl. pet space)! Book now: https://www.brittany-ferries.ie/booking/trip")
        elif status.startswith("UNKNOWN") and shot_path:
            send_telegram_photo(shot_path, f"Scanner unsure about {day} Sept ({status}) - please check")

    save_state(new_state)


if __name__ == "__main__":
    main()
