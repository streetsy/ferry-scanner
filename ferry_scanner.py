import os
import time
import requests
from datetime import datetime
from playwright.sync_api import sync_playwright

# ---------- YOUR SETTINGS ----------
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "PUT_YOUR_TOKEN_HERE")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "PUT_YOUR_CHAT_ID_HERE")

TARGET_DAYS = [18, 23, 25]
TEST_DATES = [(9, "October")]  # TEMPORARY - for confirming GitHub -> Telegram works
STATE_FILE = "last_known_state.txt"
MAX_ATTEMPTS = 3
# ------------------------------------


def send_telegram_text(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": message}, timeout=15)
    except Exception as e:
        print(f"[WARN] Telegram text send failed: {e}")


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


def check_one_date_attempt(day, month, browser):
    context = browser.new_context()
    page = context.new_page()
    page.set_default_timeout(30000)
    shot_path = f"debug_{day}sept.png"

    try:
        page.goto("https://www.brittany-ferries.ie/booking/trip", wait_until="domcontentloaded", timeout=30000)

        # Sometimes the page loads with raw translation keys still showing
        # (e.g. "booking.trip.oneWay" instead of "One way") - a refresh
        # usually fixes this. Try up to 3 times.
        for reload_attempt in range(3):
            page.wait_for_timeout(2000)
            if "booking.trip.oneWay" not in page.inner_text("body"):
                break
            print(f"  translations stuck, reloading (attempt {reload_attempt + 1})...")
            page.reload(wait_until="domcontentloaded", timeout=30000)

        page.wait_for_selector("text=Yes, I accept!", timeout=15000)
        _run_booking_flow(page, day, month)
    except Exception as e:
        # Always grab a screenshot of wherever it got stuck, so we can
        # actually see the problem instead of failing silently.
        try:
            page.screenshot(path=shot_path, full_page=True)
        except Exception:
            pass
        context.close()
        return f"UNKNOWN_STEP_FAILED: {e}", shot_path

    page_text = page.inner_text("body").lower().replace("\n", " ")
    page.screenshot(path=shot_path, full_page=True)
    context.close()

    return _classify(page_text), shot_path


def _run_booking_flow(page, day, month):
    page.get_by_role("button", name="Yes, I accept!").click()
    page.get_by_role("radio", name="One way").check()
    page.locator("#mat-select-value-0").click()
    page.locator("span").filter(has_text="Rosslarearrow_right_altBilbao").first.click()
    page.locator(".mat-mdc-form-field.pb-0 > .mat-mdc-text-field-wrapper > .mat-mdc-form-field-flex > .mat-mdc-form-field-infix").click()
    page.get_by_role("button", name=month).click()
    page.get_by_role("button", name=f"{day} {month} 2026", exact=True).click()

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

    if not dogs_ok:
        raise RuntimeError("dog count never reached 2")

    try:
        page.wait_for_function(
            """() => {
                const t = document.body.innerText.toLowerCase();
                return t.includes('sailing full') || t.includes('no pet accommodation') ||
                       t.includes('sold out') || t.includes('no availability') ||
                       t.includes('fully booked') || t.includes('not available') ||
                       t.includes('€');
            }""",
            timeout=20000
        )
    except Exception as e:
        print(f"[WARN] result marker wait timed out: {e}")


def _classify(page_text):
    pet_blocker_markers = ["no pet accommodation"]
    sold_out_markers = ["sailing full", "sold out", "no availability", "fully booked", "not available"]

    if any(m in page_text for m in pet_blocker_markers):
        return "SOLD_OUT_NO_PET_SPACE"
    elif any(m in page_text for m in sold_out_markers):
        return "SOLD_OUT"
    elif "€" in page_text:
        return "AVAILABLE"
    else:
        return "UNKNOWN"


def check_one_date(day, month, browser):
    last_status, last_shot = "UNKNOWN", None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            status, shot = check_one_date_attempt(day, month, browser)
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

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for day in TARGET_DAYS:
            status, shot_path = check_one_date(day, "September", browser)
            new_state[str(day)] = status
            print(f"[{datetime.now()}] {day} Sept -> {status}")

            was_available = last_state.get(str(day)) == "AVAILABLE"
            if status == "AVAILABLE" and not was_available:
                send_telegram_photo(shot_path,
                    f"\U0001F6A8 REAL availability found for {day} Sept Rosslare->Bilbao (incl. pet space)! Book now: https://www.brittany-ferries.ie/booking/trip")
            elif status.startswith("UNKNOWN"):
                if shot_path and os.path.exists(shot_path):
                    send_telegram_photo(shot_path, f"Scanner unsure about {day} Sept ({status}) - please check")
                else:
                    send_telegram_text(f"Scanner unsure about {day} Sept ({status}) - no screenshot available")

        browser.close()

    save_state(new_state)


if __name__ == "__main__":
    main()
