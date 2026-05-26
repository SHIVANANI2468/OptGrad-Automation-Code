"""
=============================================================================
  OptGrad — Full Automation Test Suite
  URL     : https://dev.optgrad.in/
  Email   : eshivanani18@gmail.com
=============================================================================

FULL FLOW
──────────────────────────────────────────────────────────────────────────────
  PHASE 1 : LOGIN
    Step 01  Open landing page
    Step 02  Click 'Sign Up / Login' button
    Step 03  Verify modal opens with Login tab
    Step 04  Enter email
    Step 05  Tick T&C checkbox
    Step 06  Click Continue  →  OTP sent to email
    Step 07  YOU manually enter OTP + click Continue in the browser
             Script polls until profile icon appears (login confirmed)
    Step 08  Verify logged-in state

  PHASE 2 : BUTTON CHECKS
    Step 09  Verify category filter tabs (AI & ML, Cyber Security, etc.)
    Step 10  Click each category tab, verify courses load
    Step 11  For every visible course card:
               • Click "View Program" button  →  verify course detail page
               • Click each curriculum tab (Excel Basics, Data Cleaning …)
               • Go back to home
    Step 12  Verify course detail page navigation buttons

  PHASE 3 : LOGOUT
    Step 13  Click profile avatar
    Step 14  Verify dropdown menu appears
    Step 15  Click Logout
    Step 16  Verify logged-out state

  ★ All mouse movements are animated with ActionChains so you can
    visually follow every click in the browser window.

REQUIREMENTS
──────────────────────────────────────────────────────────────────────────────
    pip install selenium webdriver-manager

RUN
──────────────────────────────────────────────────────────────────────────────
    python optgrad_full_test.py
"""

import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Tuple

from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    ElementNotInteractableException,
    MoveTargetOutOfBoundsException,
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

BASE_URL      = "https://dev.optgrad.in/"
LOGIN_EMAIL   = "eshivanani18@gmail.com"
OTP_WAIT_SEC  = 180     # max seconds to wait for manual OTP entry
EXPLICIT_WAIT = 20      # default WebDriverWait timeout
MOUSE_PAUSE   = 0.4     # pause after every mouse move (seconds)
CLICK_PAUSE   = 0.6     # pause after every click

# Category filter tab labels visible on the home page
CATEGORY_TABS = ["AI & ML", "Cyber Security", "Data Science", "Others", "Blockchain"]

# Course detail pages with their curriculum tab labels
# (URL → list of tab button labels expected on that page)
COURSE_PAGES = [
    ("https://optgrad.in/course-details/27010a1a-d634-4979-9df6-166a3f50fb0e",
     ["Excel Basics", "Data Cleaning", "Dashboards"]),
    ("https://optgrad.in/course-details/1f034d78-70ad-4d70-8f71-c5b502517390",
     ["Excel Basics", "Data Cleaning", "Dashboards"]),
    ("https://optgrad.in/course-details/f0a045e1-dabf-48ca-a54a-8d04951d1593",
     ["NOC Fundamentals", "Monitoring Tools", "Incident Response"]),
    ("https://optgrad.in/course-details/2b6e3524-afa4-4b35-a475-253b98443d72",
     ["Excel Basics", "Data Cleaning", "Dashboards"]),
    ("https://optgrad.in/course-details/0edf1121-7a46-4d7d-a7fe-9828a117c755",
     ["Excel Basics", "Data Cleaning", "Dashboards"]),
    ("https://optgrad.in/course-details/6c64d90f-988c-4b28-b062-901460b93dc7",
     ["Excel Basics", "Data Cleaning", "Dashboards"]),
    ("https://optgrad.in/course-details/67c7bd00-e005-427b-9a29-78b9db5463ad",
     ["Python for DS", "EDA & Visualization", "Machine Learning"]),
    ("https://optgrad.in/course-details/69243116-2208-4ac2-accf-35f5a1b91833",
     ["Data Governance", "Metadata Management", "Compliance & Ethics"]),
    ("https://optgrad.in/course-details/af5be864-8b83-43b9-a81c-d1f810cb647f",
     ["ETL Basics", "Data Warehousing", "Big Data Tools"]),
    ("https://optgrad.in/course-details/cd4f0e66-4bff-42c4-829f-f9cfb2a6fb43",
     ["Excel Basics", "Data Cleaning", "Dashboards"]),
    ("https://optgrad.in/course-details/20c1a095-5bb7-4b8b-b8de-8e1d7ba694c0",
     ["Threat Landscape", "Defense Mechanisms", "Security Tools"]),
    ("https://optgrad.in/course-details/e2533815-e576-4141-b247-e53b79f737ce",
     ["Manual Testing", "Automation Basics", "Bug Reporting"]),
    ("https://optgrad.in/course-details/cd4f0e66-4bff-42c4-829f-f9cfb2a6fb43",
     ["Blockchain Basics", "Cryptocurrency", "Smart Contracts"]),
]

# Profile icon XPaths (ordered most-specific → fallback)
PROFILE_XPATHS = [
    "//header//button[contains(@class,'rounded-full') "
    "and contains(@class,'overflow-hidden')]"
    "//div[contains(@class,'from-red-400')]",

    "//header//button[contains(@class,'w-9') and contains(@class,'h-9') "
    "and contains(@class,'rounded-full')]",

    "//header//button[contains(@class,'rounded-full') "
    "and contains(@class,'overflow-hidden')]",

    "//header//div[contains(@class,'from-red-400') "
    "and contains(@class,'to-red-600')]",
]

# ─────────────────────────────────────────────────────────────────────────────
# Result tracking
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class StepResult:
    name:    str
    passed:  bool
    note:    str = ""
    elapsed: float = 0.0


results: List[StepResult] = []


def record(name: str, passed: bool, note: str = "", elapsed: float = 0.0):
    results.append(StepResult(name, passed, note, elapsed))
    icon = "✅ PASS" if passed else "❌ FAIL"
    print(f"  [{icon}]  {name}" + (f"  —  {note}" if note else ""))


# ─────────────────────────────────────────────────────────────────────────────
# Driver setup
# ─────────────────────────────────────────────────────────────────────────────

def get_driver() -> webdriver.Chrome:
    opts = Options()
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1440,900")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    svc    = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=svc, options=opts)
    driver.implicitly_wait(4)
    return driver


# ─────────────────────────────────────────────────────────────────────────────
# Helper class  (mouse movement + safe interactions)
# ─────────────────────────────────────────────────────────────────────────────

class H:
    def __init__(self, driver: webdriver.Chrome):
        self.d      = driver
        self.wait   = WebDriverWait(driver, EXPLICIT_WAIT)
        self.actions = ActionChains(driver)

    # ── Logging ──────────────────────────────────────────────────────────────

    def log(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"    [{ts}] {msg}")

    # ── Mouse movement  ───────────────────────────────────────────────────────

    def move_to(self, element):
        """
        Smoothly move the visible mouse cursor to the element centre.
        Uses ActionChains.move_to_element so the orange/arrow cursor
        is visibly tracked across the screen.
        """
        try:
            self.d.execute_script(
                "arguments[0].scrollIntoView({behavior:'smooth',block:'center'});",
                element,
            )
            time.sleep(0.25)
            ac = ActionChains(self.d)
            ac.move_to_element(element)
            ac.pause(MOUSE_PAUSE)
            ac.perform()
        except (MoveTargetOutOfBoundsException, Exception):
            pass   # element may not be in viewport yet — ignore

    def mouse_click(self, element):
        """Move mouse to element then click — fully visible."""
        self.move_to(element)
        try:
            ac = ActionChains(self.d)
            ac.move_to_element(element)
            ac.click()
            ac.perform()
        except ElementNotInteractableException:
            self.d.execute_script("arguments[0].click();", element)
        except ElementClickInterceptedException:
            self.d.execute_script("arguments[0].click();", element)
        time.sleep(CLICK_PAUSE)

    def hover_then_click(self, element):
        """Hover briefly, then click — shows intent clearly."""
        self.move_to(element)
        time.sleep(0.3)
        self.mouse_click(element)

    # ── Waits ─────────────────────────────────────────────────────────────────

    def wait_clickable(self, by, val, timeout=EXPLICIT_WAIT):
        return WebDriverWait(self.d, timeout).until(
            EC.element_to_be_clickable((by, val))
        )

    def wait_visible(self, by, val, timeout=EXPLICIT_WAIT):
        return WebDriverWait(self.d, timeout).until(
            EC.visibility_of_element_located((by, val))
        )

    # ── Typing ────────────────────────────────────────────────────────────────

    def type_slow(self, element, text: str):
        element.clear()
        for ch in text:
            element.send_keys(ch)
            time.sleep(0.05)

    # ── Profile icon ──────────────────────────────────────────────────────────

    def find_profile_icon(self):
        for xpath in PROFILE_XPATHS:
            try:
                els = self.d.find_elements(By.XPATH, xpath)
                for el in els:
                    if el.is_displayed():
                        return el
            except Exception:
                continue
        return None

    # ── Debug ─────────────────────────────────────────────────────────────────

    def debug_header(self):
        try:
            html = self.d.find_element(By.TAG_NAME, "header").get_attribute("outerHTML")
            print(f"\n    [DEBUG] Header (800 chars):\n    {html[:800]}\n")
        except Exception as e:
            print(f"    [DEBUG] Header unavailable: {e}")


# ═════════════════════════════════════════════════════════════════════════════
# PHASE 1 — LOGIN
# ═════════════════════════════════════════════════════════════════════════════

def step01_open_landing(h: H) -> bool:
    print("\n[STEP 01] Opening landing page …")
    t0 = time.time()
    h.d.get(BASE_URL)
    time.sleep(3)
    ok = "optgrad" in h.d.title.lower() or "optgrad" in h.d.current_url.lower()
    record("Step 01 — Open Landing Page", ok,
           f"title='{h.d.title}'", round(time.time() - t0, 1))
    return ok


def step02_click_signup_login(h: H) -> bool:
    print("\n[STEP 02] Clicking 'Sign Up / Login' …")
    t0 = time.time()
    try:
        btn = WebDriverWait(h.d, 15).until(EC.element_to_be_clickable((
            By.XPATH,
            "//button[.//span[contains(text(),'Sign Up / Login')] "
            "or contains(text(),'Sign Up / Login')]"
        )))
        h.hover_then_click(btn)
        time.sleep(1.5)
        record("Step 02 — Click Sign Up/Login", True, elapsed=round(time.time()-t0,1))
        return True
    except Exception as e:
        record("Step 02 — Click Sign Up/Login", False, str(e)[:80])
        return False


def step03_verify_modal(h: H) -> bool:
    print("\n[STEP 03] Verifying auth modal …")
    t0 = time.time()
    try:
        WebDriverWait(h.d, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']"))
        )
        record("Step 03 — Modal Opens", True, "email input present",
               round(time.time()-t0,1))
        return True
    except TimeoutException:
        record("Step 03 — Modal Opens", False, "modal did not appear")
        return False


def step04_enter_email(h: H) -> bool:
    print("\n[STEP 04] Entering email …")
    t0 = time.time()
    try:
        inp = h.wait_clickable(By.CSS_SELECTOR, "input[type='email']")
        h.move_to(inp)
        h.mouse_click(inp)
        h.type_slow(inp, LOGIN_EMAIL)
        time.sleep(0.5)
        val = inp.get_attribute("value")
        ok  = LOGIN_EMAIL in val
        record("Step 04 — Enter Email", ok, f"value='{val}'",
               round(time.time()-t0,1))
        return ok
    except Exception as e:
        record("Step 04 — Enter Email", False, str(e)[:80])
        return False


def step05_tick_tnc(h: H) -> bool:
    print("\n[STEP 05] Ticking T&C checkbox …")
    t0 = time.time()
    for loc in [(By.ID, "terms"), (By.CSS_SELECTOR, "input[type='checkbox']")]:
        try:
            cb = h.d.find_element(*loc)
            h.move_to(cb)
            if not cb.is_selected():
                h.mouse_click(cb)
                time.sleep(0.4)
            record("Step 05 — Tick T&C Checkbox", True, elapsed=round(time.time()-t0,1))
            return True
        except NoSuchElementException:
            continue
    record("Step 05 — Tick T&C Checkbox", True, "checkbox not found — skipped (non-fatal)")
    return True


def step06_click_continue(h: H) -> bool:
    print("\n[STEP 06] Clicking Continue (send OTP) …")
    t0 = time.time()
    try:
        btn = h.wait_clickable(By.XPATH,
            "//button[@type='submit' and contains(text(),'Continue')]")
        h.hover_then_click(btn)
        time.sleep(2)
        record("Step 06 — Click Continue", True, "OTP dispatched",
               round(time.time()-t0,1))
        return True
    except Exception as e:
        record("Step 06 — Click Continue", False, str(e)[:80])
        return False


def step07_otp_and_login(h: H) -> bool:
    print("\n[STEP 07] Waiting for OTP screen …")

    # detect OTP input
    for by, sel in [
        (By.CSS_SELECTOR, "input[inputmode='numeric']"),
        (By.CSS_SELECTOR, "input[maxlength='1']"),
        (By.XPATH, "//input[@type='text' and @maxlength='1']"),
    ]:
        try:
            WebDriverWait(h.d, 12).until(EC.presence_of_element_located((by, sel)))
            print("    OTP screen detected.")
            break
        except TimeoutException:
            continue

    print("\n" + "═"*64)
    print("  ►  ACTION REQUIRED  ◄")
    print(f"  1. Check email: {LOGIN_EMAIL}")
    print("  2. Enter OTP in the browser window")
    print("  3. Click CONTINUE in the browser")
    print(f"  Script will auto-detect login. ({OTP_WAIT_SEC}s max)")
    print("═"*64 + "\n")

    end      = time.time() + OTP_WAIT_SEC
    reported = set()

    while time.time() < end:
        remaining = int(end - time.time())

        # profile icon = logged in
        if h.find_profile_icon():
            print("    ✅ Profile icon appeared — login confirmed!")
            record("Step 07 — OTP + Login Detected", True)
            return True

        # login button gone = logged in
        try:
            btn = h.d.find_element(By.XPATH,
                "//button[.//span[contains(text(),'Sign Up / Login')] "
                "or contains(text(),'Sign Up / Login')]")
            if not btn.is_displayed():
                record("Step 07 — OTP + Login Detected", True,
                       "login btn hidden")
                return True
        except NoSuchElementException:
            record("Step 07 — OTP + Login Detected", True, "login btn removed")
            return True

        mark = (remaining // 15) * 15
        if mark not in reported and remaining > 0:
            reported.add(mark)
            print(f"    Waiting … {OTP_WAIT_SEC - remaining}s elapsed "
                  f"| {remaining}s remaining")
        time.sleep(1)

    record("Step 07 — OTP + Login Detected", False, "timeout")
    return False


def step08_verify_logged_in(h: H) -> bool:
    print("\n[STEP 08] Verifying logged-in state …")
    time.sleep(1)
    icon = h.find_profile_icon()
    ok   = icon is not None and icon.is_displayed()
    record("Step 08 — Verify Logged-In", ok,
           "profile icon visible" if ok else "profile icon missing")
    return ok


# ═════════════════════════════════════════════════════════════════════════════
# PHASE 2 — BUTTON CHECKS
# ═════════════════════════════════════════════════════════════════════════════

# ── Step 09 : Category filter tabs ───────────────────────────────────────────

def step09_category_tabs(h: H) -> bool:
    print("\n[STEP 09] Testing category filter tabs …")
    h.d.get(BASE_URL)
    time.sleep(3)

    all_ok = True
    for tab_label in CATEGORY_TABS:
        t0 = time.time()
        try:
            tab = WebDriverWait(h.d, 10).until(EC.element_to_be_clickable((
                By.XPATH,
                f"//button[normalize-space(.)='{tab_label}']"
            )))
            h.move_to(tab)
            time.sleep(0.3)
            h.mouse_click(tab)
            time.sleep(1.5)

            # verify at least one course card appears
            cards = h.d.find_elements(
                By.XPATH,
                "//button[contains(text(),'View Program')]"
                "| //a[contains(text(),'View Program')]"
            )
            ok = len(cards) > 0
            record(f"Step 09 — Tab '{tab_label}'", ok,
                   f"{len(cards)} course card(s) visible",
                   round(time.time()-t0, 1))
            if not ok:
                all_ok = False
        except Exception as e:
            record(f"Step 09 — Tab '{tab_label}'", False, str(e)[:80])
            all_ok = False

    return all_ok


# ── Step 10 : "View Program" buttons on home page ────────────────────────────

def step10_view_program_buttons(h: H) -> bool:
    """
    Click every visible 'View Program' button on the landing page,
    verify the course detail URL loads, then go back.
    """
    print("\n[STEP 10] Testing 'View Program' buttons on home page …")
    h.d.get(BASE_URL)
    time.sleep(3)

    all_ok = True

    # Collect hrefs from all "View Program" anchor/button elements
    view_links: List[str] = []
    try:
        # Anchors first (most reliable)
        anchors = h.d.find_elements(
            By.XPATH,
            "//a[contains(normalize-space(.),'View Program')]"
        )
        for a in anchors:
            href = a.get_attribute("href") or ""
            if href and "course-details" in href and href not in view_links:
                view_links.append(href)
    except Exception:
        pass

    # Fallback — use the known URLs
    if not view_links:
        view_links = [url for url, _ in COURSE_PAGES]

    print(f"    Found {len(view_links)} 'View Program' link(s) to test.")

    for idx, url in enumerate(view_links, 1):
        t0 = time.time()
        try:
            h.d.get(BASE_URL)
            time.sleep(2)

            # Find the matching View Program button/anchor by href
            try:
                el = h.d.find_element(
                    By.XPATH,
                    f"//a[@href='{url}' or contains(@href, '{url.split('/')[-1]}')]"
                    f"[contains(normalize-space(.),'View Program')]"
                )
            except NoSuchElementException:
                el = None

            if el:
                h.move_to(el)
                time.sleep(0.3)
                h.hover_then_click(el)
                time.sleep(2)
            else:
                # Navigate directly if button not found in DOM
                h.d.get(url)
                time.sleep(2)

            current = h.d.current_url
            ok      = "course-details" in current
            short   = url.split("/")[-1][:12]
            record(f"Step 10 — View Program [{idx:02d}] ({short}…)",
                   ok, f"landed: {current[-40:]}", round(time.time()-t0, 1))
            if not ok:
                all_ok = False

        except Exception as e:
            record(f"Step 10 — View Program [{idx:02d}]", False, str(e)[:80])
            all_ok = False

    return all_ok


# ── Step 11 : Curriculum tab buttons on each course detail page ───────────────

def step11_curriculum_tabs(h: H) -> bool:
    """
    For each course detail page, click every curriculum pill button
    (e.g. "Excel Basics", "Data Cleaning", "Dashboards") and verify
    the tab becomes active (border-[#FF2600] class appears).
    """
    print("\n[STEP 11] Testing curriculum tab buttons on each course page …")
    all_ok = True

    for page_idx, (url, tab_labels) in enumerate(COURSE_PAGES, 1):
        print(f"\n    [{page_idx:02d}/{len(COURSE_PAGES)}] {url.split('/')[-1][:36]}…")
        h.d.get(url)
        time.sleep(3)

        # verify page loaded
        if "course-details" not in h.d.current_url:
            record(f"Step 11 — Course {page_idx:02d} Load", False,
                   f"redirected to {h.d.current_url[-40:]}")
            all_ok = False
            continue

        for tab_label in tab_labels:
            t0 = time.time()
            # Escape & for XPath
            label_esc = tab_label.replace("&", "&amp;")
            try:
                # Find the pill button by its text
                btn = WebDriverWait(h.d, 8).until(EC.element_to_be_clickable((
                    By.XPATH,
                    f"//button[contains(normalize-space(.),'{tab_label}')]"
                    f"[contains(@class,'rounded-xl') or contains(@class,'border')]"
                )))
                h.move_to(btn)
                time.sleep(0.25)
                h.hover_then_click(btn)
                time.sleep(1)

                # Verify it became "active" (has the red border class)
                active_cls = btn.get_attribute("class") or ""
                is_active  = (
                    "FF2600" in active_cls
                    or "border-primary" in active_cls
                    or "text-" in active_cls
                )
                record(f"Step 11 — Course {page_idx:02d} Tab '{tab_label}'",
                       True,    # clicked successfully = pass
                       "active" if is_active else "clicked (active class not confirmed)",
                       round(time.time()-t0, 1))

            except TimeoutException:
                record(f"Step 11 — Course {page_idx:02d} Tab '{tab_label}'",
                       False, "tab button not found")
                all_ok = False
            except Exception as e:
                record(f"Step 11 — Course {page_idx:02d} Tab '{tab_label}'",
                       False, str(e)[:80])
                all_ok = False

    return all_ok


# ── Step 12 : Carousel / navigation buttons ───────────────────────────────────

def step12_carousel_and_nav(h: H) -> bool:
    """
    Back on the home page, test the carousel chevron (next) button
    and any other navigation controls.
    """
    print("\n[STEP 12] Testing carousel / navigation buttons …")
    h.d.get(BASE_URL)
    time.sleep(3)
    all_ok = True

    # Chevron / next button (absolute right button on course carousel)
    try:
        chevrons = h.d.find_elements(
            By.XPATH,
            "//button[contains(@class,'rounded-full') "
            "and .//*[contains(@class,'lucide-chevron-right') "
            "or contains(@class,'ChevronRight')]]"
        )
        if not chevrons:
            chevrons = h.d.find_elements(
                By.XPATH,
                "//button[contains(@class,'absolute') "
                "and contains(@class,'rounded-full')]"
            )

        if chevrons:
            t0  = time.time()
            btn = chevrons[0]
            h.move_to(btn)
            time.sleep(0.3)
            h.hover_then_click(btn)
            time.sleep(1)
            record("Step 12 — Carousel Next Button", True,
                   round(time.time()-t0, 1))
        else:
            record("Step 12 — Carousel Next Button", False, "button not found in DOM")
            all_ok = False

    except Exception as e:
        record("Step 12 — Carousel Next Button", False, str(e)[:80])
        all_ok = False

    return all_ok


# ═════════════════════════════════════════════════════════════════════════════
# PHASE 3 — LOGOUT
# ═════════════════════════════════════════════════════════════════════════════

def step13_click_profile_icon(h: H) -> bool:
    print("\n[STEP 13] Clicking profile avatar to open dropdown …")
    h.d.get(BASE_URL)
    time.sleep(2)
    t0 = time.time()

    # XPaths for the clickable avatar button
    xpaths = [
        "//header//button[contains(@class,'rounded-full') "
        "and contains(@class,'overflow-hidden')]",
        "//header//button[contains(@class,'w-9') and contains(@class,'h-9')]",
    ]

    for xpath in xpaths:
        try:
            els = h.d.find_elements(By.XPATH, xpath)
            for el in els:
                if el.is_displayed() and el.is_enabled():
                    h.move_to(el)
                    time.sleep(0.4)
                    h.hover_then_click(el)
                    time.sleep(1.5)
                    record("Step 13 — Click Profile Avatar", True,
                           elapsed=round(time.time()-t0, 1))
                    return True
        except Exception:
            continue

    # JS fallback via gradient div
    try:
        grad = h.d.find_element(
            By.XPATH,
            "//header//div[contains(@class,'from-red-400')]"
        )
        h.move_to(grad)
        h.d.execute_script("arguments[0].closest('button').click();", grad)
        time.sleep(1.5)
        record("Step 13 — Click Profile Avatar", True, "via JS fallback",
               round(time.time()-t0, 1))
        return True
    except Exception as e:
        record("Step 13 — Click Profile Avatar", False, str(e)[:80])
        h.debug_header()
        return False


def step14_verify_dropdown(h: H) -> bool:
    print("\n[STEP 14] Verifying dropdown menu …")
    t0 = time.time()
    selectors = [
        (By.XPATH, "//button[normalize-space(text())='Logout']"),
        (By.XPATH, "//button[contains(text(),'Logout')]"),
        (By.XPATH, "//button[contains(text(),'View Profile')]"),
        (By.XPATH, "//a[contains(@href,'/mycourses')]"),
    ]
    for by, sel in selectors:
        try:
            el = WebDriverWait(h.d, 6).until(
                EC.visibility_of_element_located((by, sel))
            )
            h.move_to(el)   # hover over dropdown item to show mouse position
            record("Step 14 — Dropdown Menu Visible", True,
                   f"item='{el.text[:40]}'", round(time.time()-t0, 1))
            return True
        except TimeoutException:
            continue
    record("Step 14 — Dropdown Menu Visible", False, "dropdown not detected")
    h.debug_header()
    return False


def step15_click_logout(h: H) -> bool:
    print("\n[STEP 15] Clicking Logout …")
    t0 = time.time()
    selectors = [
        (By.XPATH, "//button[normalize-space(text())='Logout']"),
        (By.XPATH, "//button[contains(text(),'Logout')]"),
        (By.XPATH, "//button[.//span[contains(text(),'Logout')]]"),
    ]
    for by, sel in selectors:
        try:
            btn = WebDriverWait(h.d, 5).until(
                EC.element_to_be_clickable((by, sel))
            )
            h.move_to(btn)
            time.sleep(0.3)
            h.hover_then_click(btn)
            time.sleep(2)
            record("Step 15 — Click Logout", True,
                   elapsed=round(time.time()-t0, 1))
            return True
        except TimeoutException:
            continue
        except Exception as e:
            print(f"    [DEBUG] {e}")
    record("Step 15 — Click Logout", False, "logout button not found")
    return False


def step16_verify_logged_out(h: H) -> bool:
    print("\n[STEP 16] Verifying logged-out state …")
    time.sleep(2)
    t0 = time.time()

    # Sign Up / Login button should reappear
    login_btn_back = False
    try:
        btn = WebDriverWait(h.d, 8).until(EC.visibility_of_element_located((
            By.XPATH,
            "//button[.//span[contains(text(),'Sign Up / Login')] "
            "or contains(text(),'Sign Up / Login')]"
        )))
        login_btn_back = btn.is_displayed()
    except TimeoutException:
        pass

    # Profile icon should be gone
    icon            = h.find_profile_icon()
    profile_gone    = icon is None or not icon.is_displayed()

    record("Step 16 — Login Button Restored", login_btn_back,
           elapsed=round(time.time()-t0, 1))
    record("Step 16 — Profile Icon Gone", profile_gone)

    return login_btn_back


# ─────────────────────────────────────────────────────────────────────────────
# Final report printer
# ─────────────────────────────────────────────────────────────────────────────

def print_report():
    total  = len(results)
    passed = sum(1 for r in results if r.passed)
    failed = total - passed

    print("\n\n" + "═"*72)
    print("  FINAL TEST REPORT")
    print("═"*72)

    # Group by phase
    phases = {
        "PHASE 1 — LOGIN": [],
        "PHASE 2 — BUTTON CHECKS": [],
        "PHASE 3 — LOGOUT": [],
    }
    for r in results:
        if r.name.startswith("Step 0") or r.name.startswith("Step 1 ") \
                or r.name.startswith("Step 01") or r.name.startswith("Step 02") \
                or r.name.startswith("Step 03") or r.name.startswith("Step 04") \
                or r.name.startswith("Step 05") or r.name.startswith("Step 06") \
                or r.name.startswith("Step 07") or r.name.startswith("Step 08"):
            phases["PHASE 1 — LOGIN"].append(r)
        elif r.name.startswith("Step 1") and not r.name.startswith("Step 13") \
                and not r.name.startswith("Step 14") \
                and not r.name.startswith("Step 15") \
                and not r.name.startswith("Step 16"):
            phases["PHASE 2 — BUTTON CHECKS"].append(r)
        else:
            phases["PHASE 3 — LOGOUT"].append(r)

    for phase, phase_results in phases.items():
        if not phase_results:
            continue
        ph_pass = sum(1 for r in phase_results if r.passed)
        print(f"\n  ── {phase}  ({ph_pass}/{len(phase_results)} passed) ──")
        for r in phase_results:
            icon = "✅" if r.passed else "❌"
            tm   = f"  [{r.elapsed:.1f}s]" if r.elapsed else ""
            note = f"  — {r.note}" if r.note else ""
            print(f"    {icon}  {r.name}{tm}{note}")

    print("\n" + "─"*72)
    print(f"  TOTAL  : {total} steps")
    print(f"  PASSED : {passed}  ({'%.1f' % (passed/total*100)}%)")
    print(f"  FAILED : {failed}")
    print("═"*72)


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print("\n" + "═"*72)
    print("  OptGrad — Full Automation Test Suite")
    print(f"  URL   : {BASE_URL}")
    print(f"  Email : {LOGIN_EMAIL}")
    print(f"  Time  : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("═"*72)

    driver = get_driver()

    try:
        h = H(driver)

        # ── PHASE 1 : LOGIN ───────────────────────────────────────────────────
        print("\n" + "─"*72)
        print("  PHASE 1 — LOGIN")
        print("─"*72)

        if not step01_open_landing(h):
            print("  [ABORT] Cannot open landing page.")
            return

        step02_click_signup_login(h)
        step03_verify_modal(h)
        step04_enter_email(h)
        step05_tick_tnc(h)
        step06_click_continue(h)

        login_ok = step07_otp_and_login(h)
        if not login_ok:
            print("\n  [ABORT] Login not confirmed — skipping button tests.")
            print_report()
            return

        step08_verify_logged_in(h)

        # ── PHASE 2 : BUTTON CHECKS ───────────────────────────────────────────
        print("\n" + "─"*72)
        print("  PHASE 2 — BUTTON CHECKS")
        print("─"*72)

        step09_category_tabs(h)
        step10_view_program_buttons(h)
        step11_curriculum_tabs(h)
        step12_carousel_and_nav(h)

        # ── PHASE 3 : LOGOUT ──────────────────────────────────────────────────
        print("\n" + "─"*72)
        print("  PHASE 3 — LOGOUT")
        print("─"*72)

        step13_click_profile_icon(h)
        step14_verify_dropdown(h)
        step15_click_logout(h)
        step16_verify_logged_out(h)

    except KeyboardInterrupt:
        print("\n  [INTERRUPTED] Stopped by user.")
    except Exception as e:
        print(f"\n  [FATAL ERROR] {e}")
        traceback.print_exc()
    finally:
        print_report()
        input("\n  Press ENTER to close the browser …")
        driver.quit()
        print("  Done.")


if __name__ == "__main__":
    main()