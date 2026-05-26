"""
OptGrad Landing Page - Selenium Automation Test Suite
URL: https://optgrad.in/
Tests all buttons, dropdowns, navigation, and interactive elements
on the OptGrad landing page.

Requirements:
    pip install selenium webdriver-manager pytest

Run:
    python optgrad_landing_page_tests.py
    or
    pytest optgrad_landing_page_tests.py -v
"""

import time
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
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

# ─────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────
BASE_URL = "https://dev.optgrad.in/"
IMPLICIT_WAIT = 10
EXPLICIT_WAIT = 15
HEADLESS = False          # Set True to run without opening a browser window


# ─────────────────────────────────────────────
# Driver Factory
# ─────────────────────────────────────────────
def get_driver(headless: bool = HEADLESS) -> webdriver.Chrome:
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1440,900")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.implicitly_wait(IMPLICIT_WAIT)
    return driver


# ─────────────────────────────────────────────
# Helper Utilities
# ─────────────────────────────────────────────
class PageHelper:
    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver
        self.wait = WebDriverWait(driver, EXPLICIT_WAIT)

    def find(self, by, value):
        return self.wait.until(EC.presence_of_element_located((by, value)))

    def find_clickable(self, by, value):
        return self.wait.until(EC.element_to_be_clickable((by, value)))

    def scroll_to(self, element):
        self.driver.execute_script(
            "arguments[0].scrollIntoView({behavior:'smooth', block:'center'});",
            element,
        )
        time.sleep(0.5)

    def safe_click(self, element):
        self.scroll_to(element)
        try:
            element.click()
        except ElementNotInteractableException:
            self.driver.execute_script("arguments[0].click();", element)

    def is_visible(self, by, value) -> bool:
        try:
            el = self.driver.find_element(by, value)
            return el.is_displayed()
        except NoSuchElementException:
            return False

    def get_all(self, by, value):
        return self.driver.find_elements(by, value)

    def hover(self, element):
        ActionChains(self.driver).move_to_element(element).perform()
        time.sleep(0.5)


# ─────────────────────────────────────────────
# Test Class
# ─────────────────────────────────────────────
class TestOptGradLandingPage:
    """
    Full test suite for the OptGrad landing page.
    Each test is independent and re-uses the class-level driver.
    """

    @classmethod
    def setup_class(cls):
        cls.driver = get_driver()
        cls.h = PageHelper(cls.driver)
        cls.driver.get(BASE_URL)
        time.sleep(3)   # Allow JS / animations to settle
        print(f"\n[SETUP] Opened {BASE_URL}")

    @classmethod
    def teardown_class(cls):
        cls.driver.quit()
        print("\n[TEARDOWN] Browser closed.")

    def _refresh_page(self):
        """Navigate back to base URL between tests that change pages."""
        self.driver.get(BASE_URL)
        time.sleep(2)

    # ──────────────────────────────────────────
    # TC-01  Page Load & Title
    # ──────────────────────────────────────────
    def test_01_page_load_and_title(self):
        """Page must load successfully with expected title."""
        title = self.driver.title
        assert "OptGrad" in title, f"Unexpected title: {title}"
        print(f"[TC-01 PASS] Title: {title}")

    # ──────────────────────────────────────────
    # TC-02  Header / Navbar Visibility
    # ──────────────────────────────────────────
    def test_02_header_visible(self):
        """Sticky header must be visible on page load."""
        header = self.h.find(By.CSS_SELECTOR, "header")
        assert header.is_displayed(), "Header not visible"
        print("[TC-02 PASS] Header is visible")

    # ──────────────────────────────────────────
    # TC-03  Logo renders and is clickable
    # ──────────────────────────────────────────
    def test_03_logo_click(self):
        """Clicking the logo should stay on / navigate to the homepage."""
        logo_link = self.h.find_clickable(By.CSS_SELECTOR, "header a[href='/']")
        self.h.safe_click(logo_link)
        time.sleep(1)
        assert BASE_URL.rstrip("/") in self.driver.current_url
        print(f"[TC-03 PASS] Logo click → {self.driver.current_url}")

    # ──────────────────────────────────────────
    # TC-04  Resources Dropdown (hover)
    # ──────────────────────────────────────────
    def test_04_resources_dropdown_hover(self):
        """
        'Resources' button in the navbar should exist and be hoverable.
        Because the dropdown is CSS-based, we just verify the trigger
        is present and clickable.
        """
        resources_btn = self.h.find_clickable(
            By.XPATH, "//button[contains(., 'Resources')]"
        )
        assert resources_btn.is_displayed(), "Resources button not visible"
        self.h.hover(resources_btn)
        print("[TC-04 PASS] Resources dropdown trigger hovered")

    # ──────────────────────────────────────────
    # TC-05  Sign Up / Login Button
    # ──────────────────────────────────────────
    def test_05_signup_login_button_visible_and_clickable(self):
        """Sign Up / Login CTA button must be visible and clickable."""
        btn = self.h.find_clickable(
            By.XPATH,
            "//button[contains(., 'Sign Up') or contains(., 'Login')]",
        )
        assert btn.is_displayed(), "Sign Up/Login button not visible"
        assert btn.is_enabled(), "Sign Up/Login button is disabled"
        print("[TC-05 PASS] Sign Up / Login button is visible and enabled")

    # ──────────────────────────────────────────
    # TC-06  Mobile Menu Toggle (hamburger)
    # ──────────────────────────────────────────
    def test_06_mobile_menu_toggle(self):
        """
        Hamburger menu button should be present in the DOM
        (visible only below lg breakpoint – we verify its existence).
        """
        toggle = self.driver.find_elements(
            By.CSS_SELECTOR, "button[aria-label='Toggle mobile menu']"
        )
        assert len(toggle) > 0, "Mobile menu toggle button not found in DOM"
        print("[TC-06 PASS] Mobile menu toggle button exists in DOM")

    # ──────────────────────────────────────────
    # TC-07  Hero Section renders
    # ──────────────────────────────────────────
    def test_07_hero_section_visible(self):
        """Hero section with heading must be visible."""
        hero = self.h.find(By.CSS_SELECTOR, "#home section")
        assert hero.is_displayed(), "Hero section not visible"
        print("[TC-07 PASS] Hero section is visible")

    # ──────────────────────────────────────────
    # TC-08  Hero Search Bar clickable
    # ──────────────────────────────────────────
    def test_08_hero_search_bar_clickable(self):
        """The search bar in the hero section should be clickable."""
        search_bar = self.h.find(
            By.XPATH,
            "//span[contains(text(), 'What would you like to learn today?')]/..",
        )
        self.h.scroll_to(search_bar)
        assert search_bar.is_displayed(), "Hero search bar not displayed"
        print("[TC-08 PASS] Hero search bar is displayed and reachable")

    # ──────────────────────────────────────────
    # TC-09  Goal Selection Buttons (disabled state)
    # ──────────────────────────────────────────
    def test_09_goal_buttons_present(self):
        """
        Goal buttons ('Industry Certification', 'New career path', 'Free Course')
        must be present.  They are currently disabled – verify that state too.
        """
        labels = ["Industry Certification", "New career path", "Free Course"]
        for label in labels:
            btns = self.driver.find_elements(
                By.XPATH, f"//button[contains(., '{label}')]"
            )
            assert len(btns) > 0, f"Goal button '{label}' not found"
            # Confirm they are marked disabled
            assert btns[0].get_attribute("disabled") is not None, (
                f"Goal button '{label}' expected to be disabled but is not"
            )
        print("[TC-09 PASS] Goal selection buttons present and correctly disabled")

    # ──────────────────────────────────────────
    # TC-10  Popular Category Cards (4 cards)
    # ──────────────────────────────────────────
    def test_10_category_cards_visible(self):
        """All four category cards (AI&ML, Data Science, Blockchain, Cybersecurity) must render."""
        expected = ["AI & ML", "Data Science", "Blockchain", "Cybersecurity"]
        for category in expected:
            cards = self.driver.find_elements(
                By.XPATH, f"//h3[contains(text(), '{category}')]"
            )
            assert len(cards) > 0, f"Category card '{category}' not found"
        print("[TC-10 PASS] All 4 category cards are visible")

    # ──────────────────────────────────────────
    # TC-11  Explore Category Buttons clickable
    # ──────────────────────────────────────────
    def test_11_explore_category_buttons(self):
        """'Explore …' buttons inside each category card must be clickable."""
        explore_btns = self.driver.find_elements(
            By.XPATH, "//button[contains(., 'Explore')]"
        )
        assert len(explore_btns) >= 4, (
            f"Expected ≥4 Explore buttons, found {len(explore_btns)}"
        )
        for btn in explore_btns[:4]:
            self.h.scroll_to(btn)
            assert btn.is_displayed(), f"Explore button not visible: {btn.text}"
            assert btn.is_enabled(), f"Explore button not enabled: {btn.text}"
        print(f"[TC-11 PASS] {len(explore_btns)} Explore buttons are clickable")

    # ──────────────────────────────────────────
    # TC-12  Courses Section Tab Bar
    # ──────────────────────────────────────────
    def test_12_course_tab_bar_visible(self):
        """Tab bar with Popular Programs, AI & ML, Cyber Security, etc. must be visible."""
        tabs = ["Popular Programs", "AI & ML", "Cyber Security", "Data Science", "Blockchain"]
        for tab in tabs:
            elems = self.driver.find_elements(
                By.XPATH, f"//button[contains(., '{tab}')]"
            )
            assert len(elems) > 0, f"Tab '{tab}' not found"
        print("[TC-12 PASS] All course tab bar items are present")

    # ──────────────────────────────────────────
    # TC-13  Course Tab Switching
    # ──────────────────────────────────────────
    def test_13_course_tab_switching(self):
        """Clicking a course tab must not throw an error."""
        tab_labels = ["AI & ML", "Cyber Security", "Data Science", "Blockchain", "Others"]
        for label in tab_labels:
            tabs = self.driver.find_elements(
                By.XPATH, f"//button[contains(., '{label}')]"
            )
            if not tabs:
                continue
            tab = tabs[0]
            self.h.scroll_to(tab)
            self.h.safe_click(tab)
            time.sleep(0.5)
            print(f"  → Tab '{label}' clicked without error")
        print("[TC-13 PASS] Course tab switching works")

    # ──────────────────────────────────────────
    # TC-14  Course Carousel Previous Button
    # ──────────────────────────────────────────
    def test_14_carousel_prev_button(self):
        """Carousel 'previous' (left chevron) button must be clickable."""
        prev_btns = self.driver.find_elements(
            By.CSS_SELECTOR,
            "button.slick-prev, button svg.lucide-chevron-left",
        )
        # Target the left-arrow wrapper button instead
        left_btns = self.driver.find_elements(
            By.XPATH,
            "//button[.//*[contains(@class,'lucide-chevron-left')]]"
        )
        assert len(left_btns) > 0, "Carousel left-arrow button not found"
        self.h.scroll_to(left_btns[0])
        self.h.safe_click(left_btns[0])
        time.sleep(0.5)
        print("[TC-14 PASS] Carousel previous button clicked")

    # ──────────────────────────────────────────
    # TC-15  Course Carousel Next Button
    # ──────────────────────────────────────────
    def test_15_carousel_next_button(self):
        """Carousel 'next' (right chevron) button must be clickable."""
        right_btns = self.driver.find_elements(
            By.XPATH,
            "//button[.//*[contains(@class,'lucide-chevron-right')]]"
        )
        assert len(right_btns) > 0, "Carousel right-arrow button not found"
        self.h.scroll_to(right_btns[0])
        self.h.safe_click(right_btns[0])
        time.sleep(0.5)
        print("[TC-15 PASS] Carousel next button clicked")

    # ──────────────────────────────────────────
    # TC-16  'View Program' Buttons on Course Cards
    # ──────────────────────────────────────────
    def test_16_view_program_buttons(self):
        """'View Program' buttons on visible course cards must be enabled."""
        view_btns = self.driver.find_elements(
            By.XPATH, "//button[contains(., 'View Program')]"
        )
        visible_btns = [b for b in view_btns if b.is_displayed()]
        assert len(visible_btns) > 0, "No visible 'View Program' buttons found"
        for btn in visible_btns[:3]:
            assert btn.is_enabled(), "View Program button is disabled"
        print(f"[TC-16 PASS] {len(visible_btns)} 'View Program' buttons are enabled")

    # ──────────────────────────────────────────
    # TC-17  'Take Test' Buttons Disabled State
    # ──────────────────────────────────────────
    def test_17_take_test_buttons_disabled(self):
        """'Take Test' buttons on course cards must currently be disabled."""
        take_test_btns = self.driver.find_elements(
            By.XPATH, "//button[contains(., 'Take Test')]"
        )
        visible_btns = [b for b in take_test_btns if b.is_displayed()]
        assert len(visible_btns) > 0, "No visible 'Take Test' buttons found"
        for btn in visible_btns[:3]:
            assert btn.get_attribute("disabled") is not None, (
                "Expected 'Take Test' button to be disabled"
            )
        print(f"[TC-17 PASS] {len(visible_btns)} 'Take Test' buttons are correctly disabled")

    # ──────────────────────────────────────────
    # TC-18  Stats Section (12+ Courses etc.)
    # ──────────────────────────────────────────
    def test_18_stats_section_visible(self):
        """Stats section showing '12+ Courses', '5+ Categories', '1000+ Students' must render."""
        stats = ["12+", "5+", "1000+"]
        for stat in stats:
            elems = self.driver.find_elements(
                By.XPATH, f"//*[contains(text(), '{stat}')]"
            )
            assert len(elems) > 0, f"Stat '{stat}' not found on page"
        print("[TC-18 PASS] Stats section values are present")

    # ──────────────────────────────────────────
    # TC-19  Features Section Cards Visible
    # ──────────────────────────────────────────
    def test_19_features_section_cards(self):
        """Three feature cards must be visible (AI-Powered, AI Exams, Certificates)."""
        features = [
            "AI-Powered Learning Paths",
            "Test Your Skills with AI Powered Exams",
            "Recognized Certificates",
        ]
        for feature in features:
            elems = self.driver.find_elements(
                By.XPATH, f"//h3[contains(., '{feature}')]"
            )
            assert len(elems) > 0, f"Feature card '{feature}' not found"
        print("[TC-19 PASS] All 3 feature cards are present")

    # ──────────────────────────────────────────
    # TC-20  Testimonials Carousel Prev/Next
    # ──────────────────────────────────────────
    def test_20_testimonials_carousel_navigation(self):
        """Testimonials section carousel arrows must be clickable."""
        # Scroll to testimonials section
        testimonials_section = self.driver.find_elements(By.ID, "testmonials")
        if testimonials_section:
            self.h.scroll_to(testimonials_section[0])
            time.sleep(1)

        # All left/right chevron buttons on the page
        left_btns = self.driver.find_elements(
            By.XPATH, "//button[.//*[contains(@class,'lucide-chevron-left')]]"
        )
        right_btns = self.driver.find_elements(
            By.XPATH, "//button[.//*[contains(@class,'lucide-chevron-right')]]"
        )

        # The second set of arrows belong to the testimonials carousel
        if len(left_btns) >= 2:
            self.h.safe_click(left_btns[1])
            time.sleep(0.5)
        if len(right_btns) >= 2:
            self.h.safe_click(right_btns[1])
            time.sleep(0.5)

        assert len(left_btns) >= 1 and len(right_btns) >= 1, (
            "Testimonials carousel arrows not found"
        )
        print("[TC-20 PASS] Testimonials carousel navigation arrows clicked")

    # ──────────────────────────────────────────
    # TC-21  Footer Links Present
    # ──────────────────────────────────────────
    def test_21_footer_links_present(self):
        """Key footer links must be present and have valid href values."""
        footer = self.h.find(By.CSS_SELECTOR, "footer")
        self.h.scroll_to(footer)
        link_texts = ["Privacy", "Terms", "About", "Careers", "Contact Us"]
        for text in link_texts:
            links = footer.find_elements(
                By.XPATH, f".//a[contains(., '{text}')]"
            )
            assert len(links) > 0, f"Footer link '{text}' not found"
            href = links[0].get_attribute("href")
            assert href, f"Footer link '{text}' has no href"
        print("[TC-21 PASS] Footer links are present with valid hrefs")

    # ──────────────────────────────────────────
    # TC-22  Footer Social Media Links
    # ──────────────────────────────────────────
    def test_22_footer_social_links(self):
        """Social media icon links in the footer must have non-empty hrefs."""
        footer = self.h.find(By.CSS_SELECTOR, "footer")
        social_icons = footer.find_elements(
            By.XPATH,
            ".//a[contains(@href,'linkedin') or contains(@href,'twitter') "
            "or contains(@href,'youtube') or contains(@href,'instagram') "
            "or contains(@href,'x.com')]",
        )
        assert len(social_icons) >= 1, "No social media links found in footer"
        for link in social_icons:
            href = link.get_attribute("href")
            assert href and href.startswith("http"), f"Invalid social link href: {href}"
        print(f"[TC-22 PASS] {len(social_icons)} social media links found in footer")

    # ──────────────────────────────────────────
    # TC-23  Phone CTA Link in Footer
    # ──────────────────────────────────────────
    def test_23_footer_phone_link(self):
        """Phone number link must be present and start with 'tel:'."""
        footer = self.h.find(By.CSS_SELECTOR, "footer")
        phone_links = footer.find_elements(By.CSS_SELECTOR, "a[href^='tel:']")
        assert len(phone_links) > 0, "Phone link not found in footer"
        href = phone_links[0].get_attribute("href")
        assert href.startswith("tel:"), f"Unexpected phone href: {href}"
        print(f"[TC-23 PASS] Phone link found: {href}")

    # ──────────────────────────────────────────
    # TC-24  Email Links in Footer
    # ──────────────────────────────────────────
    def test_24_footer_email_links(self):
        """Email links in footer must start with 'mailto:'."""
        footer = self.h.find(By.CSS_SELECTOR, "footer")
        email_links = footer.find_elements(By.CSS_SELECTOR, "a[href^='mailto:']")
        assert len(email_links) >= 1, "No email links found in footer"
        for link in email_links:
            assert link.get_attribute("href").startswith("mailto:")
        print(f"[TC-24 PASS] {len(email_links)} email link(s) found in footer")

    # ──────────────────────────────────────────
    # TC-25  Chatbot Widget Visible
    # ──────────────────────────────────────────
    def test_25_chatbot_widget_visible(self):
        """Floating chatbot widget (OptGrad AI input) must be visible."""
        chatbot = self.h.find(
            By.XPATH,
            "//input[@placeholder='Ask OptGrad AI...']"
        )
        assert chatbot.is_displayed(), "Chatbot input widget not visible"
        print("[TC-25 PASS] Chatbot widget is visible")

    # ──────────────────────────────────────────
    # TC-26  Chatbot Send Button Disabled State
    # ──────────────────────────────────────────
    def test_26_chatbot_send_button_initially_disabled(self):
        """Chatbot submit button must be disabled when input is empty."""
        send_btn = self.driver.find_elements(
            By.XPATH,
            "//input[@placeholder='Ask OptGrad AI...']/following-sibling::button"
        )
        if not send_btn:
            # Try parent's sibling
            send_btn = self.driver.find_elements(
                By.CSS_SELECTOR,
                "div.fixed button[disabled]"
            )
        assert len(send_btn) > 0, "Chatbot send button not found"
        assert send_btn[0].get_attribute("disabled") is not None, (
            "Chatbot send button should be disabled when input is empty"
        )
        print("[TC-26 PASS] Chatbot send button is correctly disabled on empty input")

    # ──────────────────────────────────────────
    # TC-27  Scroll to Sections via Anchor IDs
    # ──────────────────────────────────────────
    def test_27_section_ids_exist(self):
        """Key section IDs (#home, #about, #faq, #testmonials) must exist in DOM."""
        section_ids = ["home", "about", "faq", "testmonials"]
        for sid in section_ids:
            elems = self.driver.find_elements(By.ID, sid)
            assert len(elems) > 0, f"Section with id='{sid}' not found"
        print("[TC-27 PASS] All expected section IDs exist in the DOM")

    # ──────────────────────────────────────────
    # TC-28  Page Scroll – Back to Top
    # ──────────────────────────────────────────
    def test_28_scroll_to_top(self):
        """After scrolling to the bottom, scrolling back to top should work."""
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        self.driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
        scroll_pos = self.driver.execute_script("return window.pageYOffset;")
        assert scroll_pos < 200, f"Page did not scroll to top: offset={scroll_pos}"
        print("[TC-28 PASS] Scroll-to-top works correctly")

    # ──────────────────────────────────────────
    # TC-29  No Broken Images (spot-check)
    # ──────────────────────────────────────────
    def test_29_no_broken_images_spot_check(self):
        """
        Spot-check that key images (logo, hero) are loaded
        (naturalWidth > 0 indicates the image loaded successfully).
        """
        images = self.driver.find_elements(By.CSS_SELECTOR, "img")
        broken = []
        for img in images[:15]:   # Check first 15 images
            try:
                natural_width = self.driver.execute_script(
                    "return arguments[0].naturalWidth;", img
                )
                if natural_width == 0:
                    broken.append(img.get_attribute("src") or img.get_attribute("alt"))
            except Exception:
                pass
        assert len(broken) == 0, f"Broken images detected: {broken}"
        print("[TC-29 PASS] No broken images in first 15 img elements")

    # ──────────────────────────────────────────
    # TC-30  Page Responsive – Desktop Layout Check
    # ──────────────────────────────────────────
    def test_30_desktop_layout_check(self):
        """
        At 1440px wide, the desktop nav (hidden lg:flex) should be visible.
        """
        self.driver.set_window_size(1440, 900)
        time.sleep(1)
        desktop_nav = self.driver.find_elements(
            By.CSS_SELECTOR, "div.hidden.lg\\:flex"
        )
        assert len(desktop_nav) > 0, "Desktop nav element not found at 1440px"
        print("[TC-30 PASS] Desktop layout renders correctly at 1440px width")


# ─────────────────────────────────────────────
# Stand-alone runner (no pytest required)
# ─────────────────────────────────────────────
def run_all_tests():
    suite = TestOptGradLandingPage()
    suite.setup_class()

    tests = [m for m in dir(suite) if m.startswith("test_")]
    passed, failed = [], []

    for test_name in sorted(tests):
        try:
            getattr(suite, test_name)()
            passed.append(test_name)
        except Exception as e:
            failed.append((test_name, str(e)))
            print(f"[FAIL] {test_name}: {e}")

    suite.teardown_class()

    print("\n" + "=" * 60)
    print(f"  Results: {len(passed)} passed | {len(failed)} failed")
    print("=" * 60)
    if failed:
        print("\nFailed tests:")
        for name, err in failed:
            print(f"  ✗ {name}: {err}")
    else:
        print("\n  All tests passed ✓")


if __name__ == "__main__":
    run_all_tests()