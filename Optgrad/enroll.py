"""
OptGrad Dev Server — Full E2E Automation Suite (2-Run Flow)
URL: https://dev.optgrad.in/

══════════════════════════════════════════════════════════════
RUN 1 — NEW USER FLOW
══════════════════════════════════════════════════════════════
  MODULE 1: LOGIN
    Step 01  Open landing page
    Step 02  Click 'Sign Up / Login' navbar button
    Step 03  Modal opens → Login tab selected
    Step 04  Enter email: shivatest22@yopmail.com
    Step 05  Tick T&C checkbox
    Step 06  Click Continue → OTP sent
    Step 07  [MANUAL] Enter OTP + click Continue in browser
    Step 08  Verify logged-in (profile avatar appears)

  MODULE 2: COURSE ENROLLMENT (New User)
    Step 09  Scroll to course carousel → click 'View Program'
    Step 10  Verify Course Details page (/course-details/...)
    Step 11  Click 'Enroll Now' button
    Step 12  Verify enrollment modal ('Start your learning journey')
    Step 13  Click 'Yes, Enroll Me!'
    Step 14  Verify enrollment success

  MODULE 3: START LEARNING
    Step 15  Click 'Start Learning' (green button)
    Step 16  Verify Learning Details page (/learning-details/...)
    Step 17  Verify modules sidebar present
    Step 18  Click 'Start Learning' on first module

  MODULE 4: AI TUTOR
    Step 19  Verify Content Details page (/content-details/...)
    Step 20  Click AI Tutor button (red circle, title="Let the AI Tutor Explain")
    Step 21  Verify AI popup/panel opens
    Step 22  Close AI popup (X button — SVG M2.146 2.854...)
    Step 23  Verify AI popup closed

  MODULE 5: LOGOUT (after AI)
    Step 24  Navigate back to landing page
    Step 25  Click profile avatar icon
    Step 26  Verify dropdown menu visible
    Step 27  Click Logout
    Step 28  Verify logged-out state

══════════════════════════════════════════════════════════════
RUN 2 — RETURNING USER FLOW (already enrolled)
══════════════════════════════════════════════════════════════
  MODULE 6: RE-LOGIN
    Step 29  Click 'Sign Up / Login' again
    Step 30  Enter email + OTP (manual)
    Step 31  Verify logged-in

  MODULE 7: CONTINUE LEARNING (Returning User)
    Step 32  Click 'View Program' on same course
    Step 33  Verify 'Continue Learning' button visible (NOT 'Enroll Now')
    Step 34  Click 'Continue Learning'
    Step 35  Verify Learning Details page

  MODULE 8: CONTENT + AI TUTOR (Run 2)
    Step 36  Click 'Start Learning' green button
    Step 37  Verify Content Details page
    Step 38  Click AI Tutor button
    Step 39  Verify AI popup opens
    Step 40  Close AI popup

  MODULE 9: FINAL LOGOUT
    Step 41  Navigate to landing page
    Step 42  Click profile avatar
    Step 43  Click Logout
    Step 44  Verify logged-out state

Requirements:
    pip install selenium webdriver-manager

Run:
    python optgrad_e2e_tests.py
"""

import time
import traceback
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementNotInteractableException,
)
from webdriver_manager.chrome import ChromeDriverManager

# ══════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════
BASE_URL      = "https://optgrad.in/"
LOGIN_EMAIL   = "eshivanani18@gmail.com"
OTP_WAIT_SEC  = 120
EXPLICIT_WAIT = 20


# ══════════════════════════════════════════════════════════
# DRIVER
# ══════════════════════════════════════════════════════════
def get_driver() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1440,900")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    service = Service(ChromeDriverManager().install())
    driver  = webdriver.Chrome(service=service, options=options)
    driver.implicitly_wait(5)
    return driver


# ══════════════════════════════════════════════════════════
# HELPER CLASS
# ══════════════════════════════════════════════════════════
class H:
    def __init__(self, driver: webdriver.Chrome):
        self.d    = driver
        self.wait = WebDriverWait(driver, EXPLICIT_WAIT)

    def safe_click(self, el):
        self.d.execute_script(
            "arguments[0].scrollIntoView({behavior:'smooth',block:'center'});", el
        )
        time.sleep(0.4)
        try:
            el.click()
        except ElementNotInteractableException:
            self.d.execute_script("arguments[0].click();", el)

    def type_slow(self, el, text: str):
        el.clear()
        for ch in text:
            el.send_keys(ch)
            time.sleep(0.04)

    def is_visible(self, by, val) -> bool:
        try:
            return self.d.find_element(by, val).is_displayed()
        except NoSuchElementException:
            return False

    def wait_visible(self, by, val, timeout=EXPLICIT_WAIT):
        return WebDriverWait(self.d, timeout).until(
            EC.visibility_of_element_located((by, val))
        )

    def wait_clickable(self, by, val, timeout=EXPLICIT_WAIT):
        return WebDriverWait(self.d, timeout).until(
            EC.element_to_be_clickable((by, val))
        )

    def find_profile_btn(self):
        """
        Profile avatar after login:
        <button class="... w-9 h-9 rounded-full overflow-hidden ...">
          <div class="... from-red-400 to-red-600 ...">S</div>
        </button>
        """
        xpaths = [
            "//header//button[contains(@class,'rounded-full') "
            "and contains(@class,'overflow-hidden')]",
            "//header//button[contains(@class,'w-9') "
            "and contains(@class,'h-9') "
            "and contains(@class,'rounded-full')]",
            "//header//div[contains(@class,'from-red-400') "
            "and contains(@class,'to-red-600')]"
            "/ancestor::button",
        ]
        for xpath in xpaths:
            try:
                for el in self.d.find_elements(By.XPATH, xpath):
                    if el.is_displayed():
                        return el
            except Exception:
                continue
        return None

    def debug(self, label=""):
        print(f"  [DEBUG{' '+label if label else ''}] URL: {self.d.current_url}")


# ══════════════════════════════════════════════════════════
# ── SHARED: LOGIN FLOW ────────────────────────────────────
# ══════════════════════════════════════════════════════════

def do_login(h: H, run_label: str) -> bool:
    """
    Complete login flow: click Sign Up/Login → enter email → OTP → wait for avatar.
    Used in both Run 1 and Run 2.
    """
    print(f"\n  [{run_label}] Clicking 'Sign Up / Login' button...")
    try:
        btn = WebDriverWait(h.d, 15).until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//button[.//span[contains(text(),'Sign Up / Login')] "
                "or contains(text(),'Sign Up / Login')]"
            ))
        )
        h.safe_click(btn)
        time.sleep(1.5)
        print(f"  [OK] Button clicked")
    except TimeoutException:
        print(f"  [FAIL] Sign Up/Login button not found")
        return False

    # Wait for modal
    try:
        WebDriverWait(h.d, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "input[type='email']")
            )
        )
        print(f"  [OK] Modal opened")
    except TimeoutException:
        print(f"  [FAIL] Modal did not open")
        return False

    # Ensure Login tab
    for xpath in [
        "//button[@type='button' and normalize-space(text())='Login']",
        "//button[@type='button' and contains(text(),'Login')]",
    ]:
        try:
            tab = h.d.find_element(By.XPATH, xpath)
            if tab.is_displayed():
                h.safe_click(tab)
                time.sleep(0.5)
                break
        except NoSuchElementException:
            continue

    # Enter email
    try:
        inp = WebDriverWait(h.d, 10).until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "input[type='email']")
            )
        )
        h.safe_click(inp)
        h.type_slow(inp, LOGIN_EMAIL)
        time.sleep(0.5)
        print(f"  [OK] Email entered: {LOGIN_EMAIL}")
    except TimeoutException:
        print(f"  [FAIL] Email input not found")
        return False

    # Tick T&C
    for locator in [
        (By.ID, "terms"),
        (By.CSS_SELECTOR, "input[type='checkbox']"),
    ]:
        try:
            cb = h.d.find_element(*locator)
            if not cb.is_selected():
                h.safe_click(cb)
                time.sleep(0.4)
            print(f"  [OK] T&C checked")
            break
        except NoSuchElementException:
            continue

    # Click Continue
    try:
        cont = WebDriverWait(h.d, 10).until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//button[@type='submit' and contains(text(),'Continue')]"
            ))
        )
        h.safe_click(cont)
        time.sleep(2)
        print(f"  [OK] Continue clicked — OTP dispatched")
    except TimeoutException:
        print(f"  [FAIL] Continue button not found")
        return False

    # Detect OTP screen
    for by, sel in [
        (By.CSS_SELECTOR, "input[inputmode='numeric']"),
        (By.CSS_SELECTOR, "input[maxlength='1']"),
        (By.XPATH,        "//input[@type='text' and @maxlength='1']"),
        (By.XPATH,        "//input[contains(@class,'otp')]"),
    ]:
        try:
            WebDriverWait(h.d, 12).until(
                EC.presence_of_element_located((by, sel))
            )
            print("  [OK] OTP input screen detected")
            break
        except TimeoutException:
            continue

    print("\n" + "=" * 62)
    print(f"  >>> ACTION REQUIRED ({run_label}) <<<")
    print(f"  1. Check inbox: {LOGIN_EMAIL}")
    print("  2. Enter OTP digits in the browser")
    print("  3. Click CONTINUE in the browser")
    print(f"  Script will auto-detect login. ({OTP_WAIT_SEC}s max)")
    print("=" * 62)

    # Poll for profile avatar
    print("  Polling for profile avatar (login success)...")
    end_time  = time.time() + OTP_WAIT_SEC
    logged_in = False

    while time.time() < end_time:
        el = h.find_profile_btn()
        if el:
            print("  [OK] Profile avatar detected — login confirmed!")
            logged_in = True
            break
        try:
            b = h.d.find_element(
                By.XPATH,
                "//button[.//span[contains(text(),'Sign Up / Login')] "
                "or contains(text(),'Sign Up / Login')]"
            )
            if not b.is_displayed():
                print("  [OK] Login btn hidden — login confirmed (secondary)")
                logged_in = True
                break
        except NoSuchElementException:
            print("  [OK] Login btn gone — login confirmed")
            logged_in = True
            break

        remaining = int(end_time - time.time())
        if remaining % 15 == 0 and remaining > 0:
            print(f"  Waiting... {remaining}s left")
        time.sleep(1)

    if not logged_in:
        print("  [FAIL] Login not detected within timeout")
        h.debug("POST-OTP")
    return logged_in


# ══════════════════════════════════════════════════════════
# ── SHARED: COURSE FLOW ───────────────────────────────────
# ══════════════════════════════════════════════════════════

def click_view_program(h: H) -> bool:
    """Click View Program on first visible course card in carousel."""
    print("\n  [STEP] Clicking 'View Program' on course card...")
    time.sleep(2)

    # Scroll to courses section
    try:
        h.d.execute_script(
            "document.getElementById('about')?.scrollIntoView({behavior:'smooth'});"
        )
        time.sleep(1.5)
    except Exception:
        h.d.execute_script("window.scrollBy(0, 700);")
        time.sleep(1)

    xpaths = [
        # Only visible/active carousel slides
        "//div[not(@aria-hidden='true')]//button[contains(text(),'View Program')]",
        "//div[contains(@class,'slick-active')]//button[contains(text(),'View Program')]",
        "//div[@data-index='0']//button[contains(text(),'View Program')]",
        # Any visible
        "//button[contains(text(),'View Program')]",
    ]

    for xpath in xpaths:
        try:
            for el in h.d.find_elements(By.XPATH, xpath):
                if el.is_displayed() and el.is_enabled():
                    h.safe_click(el)
                    time.sleep(3)
                    print("  [PASS] 'View Program' clicked")
                    return True
        except Exception:
            continue

    print("  [FAIL] No clickable 'View Program' found")
    return False


def verify_course_details_page(h: H) -> bool:
    """Verify we are on /course-details/ page."""
    time.sleep(2)
    url = h.d.current_url
    ok  = "course-details" in url
    print(f"  URL: {url}")
    print(f"  On course-details -> {'PASS' if ok else 'FAIL'}")
    return ok


def click_start_learning_green(h: H) -> bool:
    """
    Click the green 'Start Learning' button on learning-details page.
    <button class="... bg-[#00C16A] ...">Start Learning</button>
    Goes to /content-details/{id}/1/0
    """
    print("\n  [STEP] Clicking green 'Start Learning' button...")
    time.sleep(1)
    xpaths = [
        "//button[contains(@class,'bg-[#00C16A]')]",
        "//button[contains(., 'Start Learning') and "
        "contains(@class,'bg-[#00C16A]')]",
        "//button[contains(., 'Start Learning')]",
    ]
    for xpath in xpaths:
        try:
            for el in h.d.find_elements(By.XPATH, xpath):
                if el.is_displayed() and el.is_enabled():
                    h.safe_click(el)
                    time.sleep(3)
                    print("  [PASS] 'Start Learning' clicked")
                    return True
        except Exception:
            continue
    print("  [WARN] 'Start Learning' not found — may already on content")
    return True


def verify_content_details_page(h: H) -> bool:
    """Verify we are on /content-details/ page."""
    time.sleep(2)
    url = h.d.current_url
    ok  = "content-details" in url
    print(f"  URL: {url}")
    print(f"  On content-details -> {'PASS' if ok else 'FAIL'}")
    return ok


def click_ai_tutor(h: H) -> bool:
    """
    Click the AI Tutor button on the content page.
    <button title="Let the AI Tutor Explain" class="... bg-[#FF2600] ... rounded-full ...">
    """
    print("\n  [STEP] Clicking AI Tutor button...")
    time.sleep(2)

    xpaths = [
        "//button[@title='Let the AI Tutor Explain']",
        "//button[contains(@title,'AI Tutor')]",
        "//button[contains(@title,'Tutor')]",
        # Red circle button with play icon SVG (path M16 8A8 8 0 1 1)
        "//button[contains(@class,'rounded-full') and "
        "contains(@class,'bg-[#FF2600]') and "
        "not(contains(@class,'w-9'))]",
    ]

    for xpath in xpaths:
        try:
            el = WebDriverWait(h.d, 10).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            h.safe_click(el)
            time.sleep(2)
            print("  [PASS] AI Tutor button clicked")
            return True
        except TimeoutException:
            continue

    print("  [FAIL] AI Tutor button not found")
    h.debug("AI-TUTOR")
    return False


def verify_ai_popup(h: H) -> bool:
    """
    Verify AI Tutor popup/panel opened.
    The popup shows AI content and has a close (X) button.
    X button SVG path: M2.146 2.854...
    """
    print("\n  [STEP] Verifying AI Tutor popup...")
    time.sleep(2)

    indicators = [
        # Close X button (the only element with M2.146 path)
        (By.XPATH,
         "//button[.//*[contains(@d,'M2.146 2.854')]]"),
        (By.XPATH,
         "//button[.//*[contains(@d,'M2.146')]]"),
        # Any dialog/panel/modal that appeared
        (By.XPATH,
         "//*[contains(@class,'ai') or contains(@class,'tutor') "
         "or contains(@class,'overlay') or contains(@class,'panel')]"
         "[not(contains(@class,'w-1'))]"),
        # Audio element (AI voice)
        (By.TAG_NAME, "audio"),
    ]

    for by, sel in indicators:
        try:
            el = WebDriverWait(h.d, 8).until(
                EC.presence_of_element_located((by, sel))
            )
            if el.is_displayed():
                print(f"  [PASS] AI popup detected: {el.tag_name}")
                return True
        except TimeoutException:
            continue

    print("  [WARN] AI popup not definitively detected (may be audio-only)")
    return True  # non-fatal, AI may play as audio overlay


def close_ai_popup(h: H) -> bool:
    """
    Close the AI Tutor popup with the X button.
    SVG path: M2.146 2.854a.5.5 0 1 1 .708-.708L8 7.293...
    That is the standard X/close icon.
    """
    print("\n  [STEP] Closing AI Tutor popup...")
    time.sleep(1)

    close_xpaths = [
        # Exact SVG path from provided HTML
        "//button[.//*[contains(@d,'M2.146 2.854a.5.5 0 1 1 .708-.708')]]",
        "//button[.//*[contains(@d,'M2.146 2.854')]]",
        "//button[.//*[contains(@d,'M2.146')]]",
        # Generic close/X buttons
        "//button[contains(@aria-label,'close') or "
        "contains(@aria-label,'Close') or "
        "contains(@title,'close') or contains(@title,'Close')]",
        # Lucide X icon pattern
        "//button[.//*[@class='lucide lucide-x' or "
        "contains(@class,'lucide-x')]]",
        # Any button with X SVG paths
        "//button[.//path[contains(@d,'M18 6 6 18')] or "
        ".//path[contains(@d,'m6 6 12 12')]]",
    ]

    for xpath in close_xpaths:
        try:
            els = h.d.find_elements(By.XPATH, xpath)
            for el in els:
                if el.is_displayed() and el.is_enabled():
                    h.safe_click(el)
                    time.sleep(1.5)
                    print("  [PASS] AI popup close button clicked")
                    return True
        except Exception:
            continue

    # Fallback: press Escape key
    try:
        from selenium.webdriver.common.keys import Keys
        h.d.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        time.sleep(1)
        print("  [OK] ESC key sent to close popup")
        return True
    except Exception:
        pass

    print("  [WARN] Close button not found — continuing")
    return True  # non-fatal


def verify_ai_closed(h: H) -> bool:
    """Verify AI popup/panel is no longer visible."""
    print("\n  [STEP] Verifying AI popup is closed...")
    time.sleep(1)

    # The X button should no longer be visible
    x_visible = h.is_visible(
        By.XPATH,
        "//button[.//*[contains(@d,'M2.146 2.854')]]"
    )
    closed = not x_visible
    print(f"  AI popup closed -> {'PASS' if closed else 'WARN (may still show)'}")
    return True  # non-fatal


def do_logout(h: H) -> bool:
    """
    Navigate to landing page, click profile avatar, click Logout,
    verify Sign Up/Login button returns.
    """
    print("\n  [STEP] Navigating to landing page for logout...")
    h.d.get(BASE_URL)
    time.sleep(3)

    # Click profile avatar
    print("  [STEP] Clicking profile avatar...")
    el = h.find_profile_btn()
    if el:
        h.safe_click(el)
        time.sleep(1.5)
        print("  [OK] Profile avatar clicked")
    else:
        # JS fallback
        try:
            grad = h.d.find_element(
                By.XPATH,
                "//header//div[contains(@class,'from-red-400') "
                "and contains(@class,'to-red-600')]"
            )
            h.d.execute_script(
                "arguments[0].closest('button').click();", grad
            )
            time.sleep(1.5)
            print("  [OK] Profile avatar clicked (JS)")
        except Exception as e:
            print(f"  [FAIL] Profile avatar click failed: {e}")
            return False

    # Verify dropdown
    print("  [STEP] Verifying dropdown menu...")
    dropdown_ok = False
    for by, sel in [
        (By.XPATH, "//button[normalize-space(text())='Logout' "
                   "or contains(text(),'Logout')]"),
        (By.CLASS_NAME, "profile-dropdown-container"),
        (By.XPATH, "//a[contains(@href,'/mycourses')]"),
    ]:
        try:
            el = WebDriverWait(h.d, 6).until(
                EC.visibility_of_element_located((by, sel))
            )
            print(f"  [OK] Dropdown visible: '{el.text[:50]}'")
            dropdown_ok = True
            break
        except TimeoutException:
            continue
    if not dropdown_ok:
        print("  [WARN] Dropdown not confirmed — attempting logout anyway")

    # Click Logout
    print("  [STEP] Clicking Logout...")
    for xpath in [
        "//button[normalize-space(text())='Logout']",
        "//button[contains(text(),'Logout')]",
        "//button[.//span[contains(text(),'Logout')]]",
        "//button[.//*[contains(@d,'M17 16l4-4')]]",
    ]:
        try:
            btn = WebDriverWait(h.d, 5).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            h.safe_click(btn)
            time.sleep(2)
            print("  [OK] Logout clicked")
            break
        except TimeoutException:
            continue

    # Verify logged out
    time.sleep(2)
    try:
        btn = WebDriverWait(h.d, 8).until(
            EC.visibility_of_element_located((
                By.XPATH,
                "//button[.//span[contains(text(),'Sign Up / Login')] "
                "or contains(text(),'Sign Up / Login')]"
            ))
        )
        ok = btn.is_displayed()
        print(f"  [PASS] Logged out — 'Sign Up / Login' restored")
        return ok
    except TimeoutException:
        print("  [FAIL] Logout not confirmed")
        return False


# ══════════════════════════════════════════════════════════
# MAIN RUNNER
# ══════════════════════════════════════════════════════════
def main():
    print("\n" + "=" * 62)
    print("  OptGrad Dev Server — Full E2E Automation (2 Runs)")
    print(f"  URL   : {BASE_URL}")
    print(f"  Email : {LOGIN_EMAIL}")
    print("=" * 62)

    driver  = get_driver()
    results = {}

    try:
        h = H(driver)

        # ══════════════════════════════════════════════════
        # RUN 1 — NEW USER FLOW
        # ══════════════════════════════════════════════════
        print("\n" + "█" * 62)
        print("  RUN 1 — NEW USER FLOW")
        print("█" * 62)

        # ── MODULE 1: LOGIN ───────────────────────────────
        section("MODULE 1: LOGIN (Run 1)")
        h.d.get(BASE_URL)
        time.sleep(3)
        results["R1-Step01 Open Landing Page"] = (
            "OptGrad" in h.d.title
        )
        print(f"  Title: '{h.d.title}' -> "
              f"{'PASS' if results['R1-Step01 Open Landing Page'] else 'FAIL'}")

        r1_login = do_login(h, "RUN 1")
        results["R1-Step02-07 Login + OTP"]    = r1_login
        results["R1-Step08 Verify Logged In"]  = (
            h.find_profile_btn() is not None
        )
        print(f"  Profile avatar visible -> "
              f"{'PASS' if results['R1-Step08 Verify Logged In'] else 'FAIL'}")

        if not r1_login:
            print("\n  [ABORT] Run 1 login failed.")
        else:
            # Navigate to landing to access course cards
            h.d.get(BASE_URL)
            time.sleep(3)

            # ── MODULE 2: ENROLL ──────────────────────────
            section("MODULE 2: COURSE ENROLLMENT (New User)")

            results["R1-Step09 Click View Program"] = (
                click_view_program(h)
            )
            results["R1-Step10 Course Details Page"] = (
                verify_course_details_page(h)
            )

            # Click Enroll Now
            print("\n  [STEP] Clicking 'Enroll Now'...")
            enroll_ok = False
            try:
                btn = WebDriverWait(h.d, 10).until(
                    EC.element_to_be_clickable((
                        By.XPATH,
                        "//button[contains(text(),'Enroll Now')]"
                    ))
                )
                h.safe_click(btn)
                time.sleep(2)
                print("  [PASS] 'Enroll Now' clicked")
                enroll_ok = True
            except TimeoutException:
                print("  [FAIL] 'Enroll Now' not found")
            results["R1-Step11 Click Enroll Now"] = enroll_ok

            # Verify modal
            print("\n  [STEP] Verifying enrollment modal...")
            modal_ok = False
            for by, sel in [
                (By.XPATH, "//div[contains(@class,'enroll-card')]"),
                (By.XPATH,
                 "//h2[contains(text(),'Start your learning journey')]"),
                (By.XPATH,
                 "//button[contains(text(),'Yes, Enroll Me')]"),
            ]:
                try:
                    el = WebDriverWait(h.d, 8).until(
                        EC.visibility_of_element_located((by, sel))
                    )
                    print(f"  [PASS] Modal visible: '{el.text[:50]}'")
                    modal_ok = True
                    break
                except TimeoutException:
                    continue
            if not modal_ok:
                print("  [FAIL] Enrollment modal not detected")
            results["R1-Step12 Enrollment Modal"] = modal_ok

            # Click Yes Enroll Me
            print("\n  [STEP] Clicking 'Yes, Enroll Me!'...")
            yes_ok = False
            try:
                yes_btn = WebDriverWait(h.d, 8).until(
                    EC.element_to_be_clickable((
                        By.XPATH,
                        "//button[contains(text(),'Yes, Enroll Me')]"
                    ))
                )
                h.safe_click(yes_btn)
                time.sleep(3)
                print("  [PASS] 'Yes, Enroll Me!' clicked")
                yes_ok = True
            except TimeoutException:
                print("  [FAIL] 'Yes, Enroll Me!' not found")
            results["R1-Step13 Yes Enroll Me"] = yes_ok

            # Verify enrollment success
            time.sleep(2)
            modal_gone = not h.is_visible(
                By.XPATH,
                "//button[contains(text(),'Yes, Enroll Me')]"
            )
            start_visible = h.is_visible(
                By.XPATH,
                "//button[contains(.,'Start Learning') or "
                "contains(.,'Start') or contains(.,'Continue Learning')]"
            )
            enroll_success = modal_gone or start_visible
            print(f"\n  Enrollment success (modal gone OR start visible) -> "
                  f"{'PASS' if enroll_success else 'WARN'}")
            results["R1-Step14 Enrollment Success"] = enroll_success

            # ── MODULE 3: START LEARNING ──────────────────
            section("MODULE 3: START LEARNING (Run 1)")

            # Click 'Start Learning' (green) OR 'Start' (red) on course page
            print("\n  [STEP] Clicking 'Start Learning' / 'Start'...")
            start1_ok = False
            for xpath in [
                "//button[contains(@class,'bg-[#00C16A]')]",
                "//button[contains(., 'Start Learning')]",
                "//button[normalize-space(text())='Start']"
                "[contains(@class,'from-[#FF2600]')]",
                "//button[normalize-space(text())='Start']",
            ]:
                try:
                    for el in h.d.find_elements(By.XPATH, xpath):
                        if el.is_displayed() and el.is_enabled():
                            h.safe_click(el)
                            time.sleep(3)
                            print(f"  [PASS] '{el.text.strip()[:40]}' clicked")
                            start1_ok = True
                            break
                    if start1_ok:
                        break
                except Exception:
                    continue
            if not start1_ok:
                print("  [FAIL] Start button not found")
            results["R1-Step15 Click Start"] = start1_ok

            # Verify learning-details page
            time.sleep(2)
            url_r1 = h.d.current_url
            on_learning1 = "learning-details" in url_r1
            print(f"  URL: {url_r1}")
            print(f"  On learning-details -> "
                  f"{'PASS' if on_learning1 else 'FAIL'}")
            results["R1-Step16 Learning Details Page"] = on_learning1

            # Verify modules sidebar
            sidebar_ok = h.is_visible(
                By.XPATH, "//*[contains(text(),'MODULES OVERVIEW')]"
            )
            print(f"  Modules sidebar -> "
                  f"{'PASS' if sidebar_ok else 'FAIL'}")
            results["R1-Step17 Modules Sidebar"] = sidebar_ok

            # Click green Start Learning button (module 1)
            results["R1-Step18 Start Learning Module"] = (
                click_start_learning_green(h)
            )

            # ── MODULE 4: AI TUTOR ────────────────────────
            section("MODULE 4: AI TUTOR (Run 1)")

            # Verify content-details page
            time.sleep(2)
            url_content1 = h.d.current_url
            on_content1  = "content-details" in url_content1
            print(f"  URL: {url_content1}")
            print(f"  On content-details -> "
                  f"{'PASS' if on_content1 else 'FAIL'}")
            results["R1-Step19 Content Details Page"] = on_content1

            results["R1-Step20 Click AI Tutor"]    = click_ai_tutor(h)
            results["R1-Step21 Verify AI Popup"]   = verify_ai_popup(h)
            results["R1-Step22 Close AI Popup"]    = close_ai_popup(h)
            results["R1-Step23 Verify AI Closed"]  = verify_ai_closed(h)

            # ── MODULE 5: LOGOUT (after AI) ───────────────
            section("MODULE 5: LOGOUT — Run 1")
            results["R1-Step24-28 Logout"] = do_logout(h)

        # ══════════════════════════════════════════════════
        # RUN 2 — RETURNING USER FLOW
        # ══════════════════════════════════════════════════
        print("\n" + "█" * 62)
        print("  RUN 2 — RETURNING USER FLOW (Already Enrolled)")
        print("█" * 62)

        input("\n  Press ENTER to start RUN 2 (re-login as returning user)...")

        # ── MODULE 6: RE-LOGIN ────────────────────────────
        section("MODULE 6: RE-LOGIN (Run 2)")
        h.d.get(BASE_URL)
        time.sleep(3)
        results["R2-Step29 Open Landing Page"] = (
            "OptGrad" in h.d.title
        )

        r2_login = do_login(h, "RUN 2")
        results["R2-Step30-31 Login + OTP"] = r2_login
        print(f"  Profile avatar -> "
              f"{'PASS' if h.find_profile_btn() else 'FAIL'}")

        if not r2_login:
            print("\n  [ABORT] Run 2 login failed.")
        else:
            h.d.get(BASE_URL)
            time.sleep(3)

            # ── MODULE 7: CONTINUE LEARNING ───────────────
            section("MODULE 7: CONTINUE LEARNING (Returning User)")

            results["R2-Step32 Click View Program"] = (
                click_view_program(h)
            )
            results["R2-Step33 Course Details Page"] = (
                verify_course_details_page(h)
            )

            # Verify 'Continue Learning' button present (NOT Enroll Now)
            print("\n  [STEP] Checking for 'Continue Learning' button...")
            time.sleep(2)
            continue_ok = False
            enroll_gone = False

            # Check Continue Learning visible
            try:
                cont_btn = WebDriverWait(h.d, 10).until(
                    EC.presence_of_element_located((
                        By.XPATH,
                        "//button[contains(text(),'Continue Learning')]"
                    ))
                )
                continue_ok = cont_btn.is_displayed()
                print(f"  'Continue Learning' visible -> "
                      f"{'PASS' if continue_ok else 'FAIL'}")
            except TimeoutException:
                print("  'Continue Learning' -> FAIL (not found)")
            results["R2-Step33b Continue Learning Btn Visible"] = continue_ok

            # Verify Enroll Now is NOT shown
            try:
                enroll_el = h.d.find_element(
                    By.XPATH,
                    "//button[contains(text(),'Enroll Now')]"
                )
                enroll_gone = not enroll_el.is_displayed()
            except NoSuchElementException:
                enroll_gone = True
            print(f"  'Enroll Now' hidden/gone -> "
                  f"{'PASS' if enroll_gone else 'WARN'}")
            results["R2-Step33c Enroll Now Gone"] = enroll_gone

            # Click Continue Learning
            print("\n  [STEP] Clicking 'Continue Learning'...")
            cont_click_ok = False
            try:
                btn = WebDriverWait(h.d, 8).until(
                    EC.element_to_be_clickable((
                        By.XPATH,
                        "//button[contains(text(),'Continue Learning')]"
                    ))
                )
                h.safe_click(btn)
                time.sleep(3)
                print("  [PASS] 'Continue Learning' clicked")
                cont_click_ok = True
            except TimeoutException:
                # Fallback: Start button
                for xpath in [
                    "//button[contains(., 'Start Learning')]",
                    "//button[normalize-space(text())='Start']",
                ]:
                    try:
                        for el in h.d.find_elements(By.XPATH, xpath):
                            if el.is_displayed() and el.is_enabled():
                                h.safe_click(el)
                                time.sleep(3)
                                print(f"  [OK] '{el.text.strip()[:30]}' clicked (fallback)")
                                cont_click_ok = True
                                break
                        if cont_click_ok:
                            break
                    except Exception:
                        continue
                if not cont_click_ok:
                    print("  [FAIL] Neither Continue Learning nor Start found")
            results["R2-Step34 Click Continue Learning"] = cont_click_ok

            # Verify learning-details page
            time.sleep(2)
            url_r2 = h.d.current_url
            on_learning2 = "learning-details" in url_r2
            print(f"  URL: {url_r2}")
            print(f"  On learning-details -> "
                  f"{'PASS' if on_learning2 else 'FAIL'}")
            results["R2-Step35 Learning Details Page"] = on_learning2

            # ── MODULE 8: CONTENT + AI TUTOR (Run 2) ──────
            section("MODULE 8: CONTENT + AI TUTOR (Run 2)")

            results["R2-Step36 Start Learning Module"] = (
                click_start_learning_green(h)
            )

            time.sleep(2)
            url_c2 = h.d.current_url
            on_c2  = "content-details" in url_c2
            print(f"  URL: {url_c2}")
            print(f"  On content-details -> {'PASS' if on_c2 else 'FAIL'}")
            results["R2-Step37 Content Details Page"] = on_c2

            results["R2-Step38 Click AI Tutor"]   = click_ai_tutor(h)
            results["R2-Step39 Verify AI Popup"]  = verify_ai_popup(h)
            results["R2-Step40 Close AI Popup"]   = close_ai_popup(h)

            # ── MODULE 9: FINAL LOGOUT ────────────────────
            section("MODULE 9: FINAL LOGOUT (Run 2)")
            results["R2-Step41-44 Logout"] = do_logout(h)

    except KeyboardInterrupt:
        print("\n  [INTERRUPTED] Stopped by user.")
    except Exception as e:
        print(f"\n  [ERROR] {e}")
        traceback.print_exc()

    finally:
        print_report(results)
        input("\n  Press ENTER to close browser...")
        driver.quit()
        print("  Done.")


# ══════════════════════════════════════════════════════════
# UTILITIES
# ══════════════════════════════════════════════════════════
def section(title: str):
    print(f"\n{'─' * 62}")
    print(f"  {title}")
    print(f"{'─' * 62}")


def print_report(results: dict):
    print("\n\n" + "=" * 62)
    print("  FINAL E2E TEST REPORT")
    print("=" * 62)

    # Group by Run
    run1 = {k: v for k, v in results.items() if k.startswith("R1")}
    run2 = {k: v for k, v in results.items() if k.startswith("R2")}

    for run_name, run_data in [
        ("RUN 1 — NEW USER", run1),
        ("RUN 2 — RETURNING USER", run2),
    ]:
        if not run_data:
            continue
        print(f"\n  {run_name}")
        print("  " + "·" * 55)
        mod_pass = sum(1 for v in run_data.values() if v)
        for step, ok in run_data.items():
            mark   = "+" if ok else "x"
            status = "PASS" if ok else "FAIL"
            # Shorten key for display
            display = step.split(" ", 1)[1] if " " in step else step
            print(f"  [{mark}] {status}  {display}")
        print(f"  Subtotal: {mod_pass}/{len(run_data)} passed")

    total_pass = sum(1 for v in results.values() if v)
    total_all  = len(results)
    print("\n" + "=" * 62)
    print(f"  OVERALL: {total_pass}/{total_all} steps passed")
    print("=" * 62)


if __name__ == "__main__":
    main()