"""
=============================================================================
  Selenium Automation — Class 10 Mathematics RAG LLM Accuracy Tester
  Textbook : 10 Mathematics EM 2024-25 (Telangana SCERT)
  Target   : http://192.168.1.121:8521/
=============================================================================

HOW IT WORKS
─────────────────────────────────────────────────────────────────────────────
  1. Script opens Chrome and navigates to the RAG app
  2. It WAITS (up to 10 minutes) for the Chat text field to become ENABLED
     ► During this wait YOU manually:
         a) Click "Upload and Train" in the sidebar
         b) Browse and upload the 10th Maths PDF
         c) Click "Train on Uploaded files"
         d) Wait for training to complete
         e) Click "Chat Interface" in the sidebar
  3. The moment the chat input field becomes active/enabled the script
     AUTOMATICALLY starts asking all 20 questions from the textbook
  4. Each AI response is captured and scored for accuracy
  5. A detailed HTML report + CSV are saved when all tests finish

USAGE
─────────────────────────────────────────────────────────────────────────────
    python test_math_rag_automation.py
    python test_math_rag_automation.py --url http://192.168.1.121:8521/
    python test_math_rag_automation.py --threshold 45
    python test_math_rag_automation.py --out C:/reports
    python test_math_rag_automation.py --ids TC01 TC05 TC14

DEPENDENCIES
─────────────────────────────────────────────────────────────────────────────
    pip install selenium
    Chrome + matching ChromeDriver must be installed and on PATH
"""

# ─────────────────────────────────────────────────────────────────────────────
# Imports
# ─────────────────────────────────────────────────────────────────────────────
import argparse
import csv
import difflib
import os
import re
import sys
import time
import traceback
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# ─────────────────────────────────────────────────────────────────────────────
# Configuration defaults
# ─────────────────────────────────────────────────────────────────────────────

APP_URL               = "http://192.168.1.121:8521/"
PASS_THRESHOLD        = 40      # combined score (%) to mark a test PASS
WAIT_FOR_CHAT_SEC     = 600     # max seconds to wait for the chat input to appear
RESPONSE_WAIT_SEC     = 120     # max seconds to wait for one AI response
INTER_QUESTION_DELAY  = 4       # pause between consecutive questions (s)

# ─────────────────────────────────────────────────────────────────────────────
# 20 Test cases — questions from the Class-10 Maths textbook
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class TestCase:
    id: str
    chapter: str
    question: str
    reference_answer: str
    keywords: List[str]


TEST_CASES: List[TestCase] = [

    # ── Ch-1 : Real Numbers ──────────────────────────────────────────────────
    TestCase(
        id="TC01", chapter="Ch-1: Real Numbers",
        question="Show that 5 minus root 3 is irrational.",
        reference_answer=(
            "Assume 5 minus root 3 is rational. Then coprimes a and b with b not 0 "
            "exist such that 5 minus root 3 equals a divided by b. Rearranging gives "
            "root 3 equals 5b minus a divided by b which is rational. "
            "But root 3 is irrational which is a contradiction. "
            "Therefore 5 minus root 3 is irrational."
        ),
        keywords=["irrational", "rational", "contradiction", "assume", "coprime"],
    ),
    TestCase(
        id="TC02", chapter="Ch-1: Real Numbers",
        question="State the Fundamental Theorem of Arithmetic.",
        reference_answer=(
            "Every composite number can be expressed as a product of primes and "
            "this factorisation is unique apart from the order of prime factors."
        ),
        keywords=["composite", "prime", "factorization", "unique"],
    ),
    TestCase(
        id="TC03", chapter="Ch-1: Real Numbers",
        question="State Euclid's Division Lemma and write its equation.",
        reference_answer=(
            "Given positive integers a and b, there exist unique whole numbers "
            "q and r such that a equals bq plus r where r is between 0 and b."
        ),
        keywords=["bq + r", "remainder", "quotient", "euclid", "unique"],
    ),
    TestCase(
        id="TC04", chapter="Ch-1: Real Numbers",
        question="Find the HCF of 900 and 270 using Euclid's division algorithm.",
        reference_answer=(
            "900 = 270 x 3 + 90. Then 270 = 90 x 3 + 0. "
            "Since remainder is 0, HCF of 900 and 270 is 90."
        ),
        keywords=["90", "HCF", "900", "270"],
    ),
    TestCase(
        id="TC05", chapter="Ch-1: Real Numbers",
        question=(
            "Is the decimal expansion of 16 by 125 terminating "
            "or non-terminating repeating? Give reason."
        ),
        reference_answer=(
            "125 equals 5 cubed. The denominator is of the form 2n times 5m "
            "so the decimal expansion is terminating. 16 by 125 equals 0.128."
        ),
        keywords=["terminating", "125", "prime", "5"],
    ),
    TestCase(
        id="TC06", chapter="Ch-1: Real Numbers",
        question="Show that 3 root 2 is irrational.",
        reference_answer=(
            "Assume 3 root 2 equals a by b for coprimes a and b with b not 0. "
            "Then root 2 equals a by 3b which is rational. "
            "But root 2 is irrational — contradiction. Hence 3 root 2 is irrational."
        ),
        keywords=["irrational", "contradiction", "rational", "root 2"],
    ),

    # ── Ch-2 : Sets ──────────────────────────────────────────────────────────
    TestCase(
        id="TC07", chapter="Ch-2: Sets",
        question="What is a set? Give two examples of number sets in mathematics.",
        reference_answer=(
            "A set is a well-defined collection of distinct objects. "
            "N is the set of natural numbers 1 2 3 and so on. "
            "W is the set of whole numbers 0 1 2 3 and so on."
        ),
        keywords=["set", "collection", "distinct", "natural", "whole"],
    ),

    # ── Ch-3 : Polynomials ───────────────────────────────────────────────────
    TestCase(
        id="TC08", chapter="Ch-3: Polynomials",
        question="Find the zeroes of the polynomial p x equals x squared minus 2x minus 3.",
        reference_answer=(
            "x squared minus 2x minus 3 factors as x minus 3 times x plus 1. "
            "Zeroes are x equals 3 and x equals minus 1."
        ),
        keywords=["3", "-1", "zeroes", "factor"],
    ),
    TestCase(
        id="TC09", chapter="Ch-3: Polynomials",
        question=(
            "For a quadratic polynomial with zeroes alpha and beta, "
            "write the sum and product of zeroes in terms of coefficients."
        ),
        reference_answer=(
            "Sum of zeroes alpha plus beta equals minus b by a. "
            "Product of zeroes alpha times beta equals c by a."
        ),
        keywords=["sum", "product", "zeroes", "-b/a", "c/a"],
    ),

    # ── Ch-4 : Linear Equations ──────────────────────────────────────────────
    TestCase(
        id="TC10", chapter="Ch-4: Linear Equations",
        question=(
            "What are the conditions for a pair of linear equations to have "
            "unique solution, no solution, and infinitely many solutions?"
        ),
        reference_answer=(
            "Unique solution: a1 by a2 not equal to b1 by b2 — lines intersect. "
            "No solution: a1 by a2 equals b1 by b2 not equal to c1 by c2 — lines parallel. "
            "Infinitely many: a1 by a2 equals b1 by b2 equals c1 by c2 — lines coincide."
        ),
        keywords=["unique", "parallel", "coincide", "intersect", "solution"],
    ),

    # ── Ch-5 : Quadratic Equations ───────────────────────────────────────────
    TestCase(
        id="TC11", chapter="Ch-5: Quadratic Equations",
        question="Write the quadratic formula for ax squared plus bx plus c equals 0.",
        reference_answer=(
            "x equals minus b plus or minus square root of b squared minus 4ac "
            "all divided by 2a. b squared minus 4ac is the discriminant."
        ),
        keywords=["discriminant", "b squared", "4ac", "2a", "formula"],
    ),
    TestCase(
        id="TC12", chapter="Ch-5: Quadratic Equations",
        question="What is the nature of roots when discriminant b squared minus 4ac is greater than 0?",
        reference_answer=(
            "When b squared minus 4ac is greater than 0 the equation "
            "has two distinct real roots."
        ),
        keywords=["two distinct", "real roots", "discriminant"],
    ),

    # ── Ch-6 : Progressions ──────────────────────────────────────────────────
    TestCase(
        id="TC13", chapter="Ch-6: Progressions",
        question="Write the formula for the nth term of an Arithmetic Progression.",
        reference_answer=(
            "The nth term of an AP is a sub n equals a plus n minus 1 times d "
            "where a is the first term and d is the common difference."
        ),
        keywords=["nth term", "n-1", "common difference", "arithmetic"],
    ),
    TestCase(
        id="TC14", chapter="Ch-6: Progressions",
        question=(
            "In a GP the 3rd term is 24 and the 6th term is 192. "
            "Find the 10th term."
        ),
        reference_answer=(
            "ar squared equals 24 and ar to the power 5 equals 192. "
            "r cubed equals 8 so r equals 2 and a equals 6. "
            "10th term equals 6 times 2 to the power 9 equals 3072."
        ),
        keywords=["3072", "r = 2", "a = 6", "geometric"],
    ),
    TestCase(
        id="TC15", chapter="Ch-6: Progressions",
        question="Give the formula for sum of first n terms of an AP.",
        reference_answer=(
            "S sub n equals n by 2 times 2a plus n minus 1 times d. "
            "Or n by 2 times a plus l where l is the last term."
        ),
        keywords=["n/2", "2a", "n-1", "sum", "last term"],
    ),

    # ── Ch-7 : Coordinate Geometry ───────────────────────────────────────────
    TestCase(
        id="TC16", chapter="Ch-7: Coordinate Geometry",
        question="State the distance formula between two points P x1 y1 and Q x2 y2.",
        reference_answer=(
            "PQ equals square root of x2 minus x1 whole squared "
            "plus y2 minus y1 whole squared."
        ),
        keywords=["distance", "square root", "x2", "y2"],
    ),
    TestCase(
        id="TC17", chapter="Ch-7: Coordinate Geometry",
        question="Give the section formula for point P dividing AB internally in ratio m1 to m2.",
        reference_answer=(
            "P equals m1 x2 plus m2 x1 divided by m1 plus m2 "
            "and m1 y2 plus m2 y1 divided by m1 plus m2."
        ),
        keywords=["section formula", "m1", "m2", "internally"],
    ),

    # ── Ch-8 : Similar Triangles ─────────────────────────────────────────────
    TestCase(
        id="TC18", chapter="Ch-8: Similar Triangles",
        question="State the Basic Proportionality Theorem also known as Thales Theorem.",
        reference_answer=(
            "If a line is drawn parallel to one side of a triangle and intersects "
            "the other two sides then it divides them in the same ratio. "
            "In triangle ABC if DE is parallel to BC then AD by DB equals AE by EC."
        ),
        keywords=["parallel", "ratio", "proportionality", "triangle", "AD"],
    ),

    # ── Ch-9 : Tangents & Secants ────────────────────────────────────────────
    TestCase(
        id="TC19", chapter="Ch-9: Tangents & Secants",
        question="Is a tangent at any point on a circle perpendicular to the radius at that point?",
        reference_answer=(
            "True. The tangent to a circle at any point is perpendicular to "
            "the radius drawn to the point of tangency."
        ),
        keywords=["tangent", "perpendicular", "radius", "true"],
    ),

    # ── Ch-11 : Trigonometry ──────────────────────────────────────────────────
    TestCase(
        id="TC20", chapter="Ch-11: Trigonometry",
        question="State the fundamental trigonometric identity involving sin theta and cos theta.",
        reference_answer=(
            "sin squared theta plus cos squared theta equals 1. "
            "Also 1 plus tan squared theta equals sec squared theta and "
            "1 plus cot squared theta equals cosec squared theta."
        ),
        keywords=["sin", "cos", "identity", "theta", "1"],
    ),
]

# ─────────────────────────────────────────────────────────────────────────────
# Scoring helpers
# ─────────────────────────────────────────────────────────────────────────────

_STOP = {
    "a","an","the","is","are","was","were","be","been","in","on","at","to",
    "for","of","and","or","but","if","it","this","that","we","you","i","by",
    "as","so","then","also","from","with","which","where","what","how",
    "give","state","show","find","write","let","such","equals","equal",
    "gives","thus","hence","since","its","not",
}

def _seq(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio() * 100

def _f1(ref: str, hyp: str) -> float:
    r = set(re.findall(r'\w+', ref.lower())) - _STOP
    h = set(re.findall(r'\w+', hyp.lower())) - _STOP
    if not r or not h:
        return 0.0
    c = r & h
    p = len(c) / len(h)
    rc = len(c) / len(r)
    d = p + rc
    return round(2 * p * rc / d * 100, 2) if d else 0.0

def _kw(keywords: List[str], response: str) -> float:
    if not keywords:
        return 100.0
    low  = response.lower()
    hits = sum(1 for kw in keywords if kw.lower() in low)
    return round(hits / len(keywords) * 100, 2)

def compute_score(tc: TestCase, response: str) -> dict:
    s   = round(_seq(tc.reference_answer, response), 2)
    f   = _f1(tc.reference_answer, response)
    k   = _kw(tc.keywords, response)
    com = round(0.25 * s + 0.30 * f + 0.45 * k, 2)
    return dict(seq=s, f1=f, kw=k, combined=com)

# ─────────────────────────────────────────────────────────────────────────────
# Result container
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Result:
    tc:      TestCase
    resp:    str
    scores:  dict
    passed:  bool
    error:   Optional[str] = None
    elapsed: float = 0.0

# ─────────────────────────────────────────────────────────────────────────────
# Browser controller
# ─────────────────────────────────────────────────────────────────────────────

class ChatTester:
    """
    Opens the Streamlit RAG app, waits until the chat input is enabled
    (the user trains the model manually), then runs all Q&A tests.
    """

    _SEL_SIDEBAR  = "[data-testid='stSidebar']"
    _SEL_CHAT_IN  = "[data-testid='stChatInputTextArea']"
    _SEL_CHAT_MSG = "[data-testid='stChatMessage']"
    _SEL_MARK_P   = "[data-testid='stMarkdownContainer'] p"

    def __init__(self, url: str, headless: bool, driver_path: str):
        self.url    = url
        self.driver = self._make_driver(headless, driver_path)
        self.wait   = WebDriverWait(self.driver, 45)

    # ── Driver ────────────────────────────────────────────────────────────────

    def _make_driver(self, headless: bool, dp: str) -> webdriver.Chrome:
        opts = ChromeOptions()
        if headless:
            opts.add_argument("--headless=new")
        opts.add_argument("--window-size=1440,900")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--log-level=3")
        opts.add_experimental_option("excludeSwitches", ["enable-logging"])
        svc = Service(executable_path=dp) if dp else Service()
        return webdriver.Chrome(service=svc, options=opts)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _log(self, msg: str):
        print(f"  [{datetime.now().strftime('%H:%M:%S')}] {msg}")

    def _safe_click(self, el):
        try:
            el.click()
        except ElementClickInterceptedException:
            self.driver.execute_script("arguments[0].click();", el)

    # ── STEP 1 : Open app ────────────────────────────────────────────────────

    def open_app(self):
        self._log(f"Opening  {self.url}")
        self.driver.get(self.url)
        self.wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, self._SEL_SIDEBAR)
        ))
        time.sleep(3)
        self._log("App loaded successfully.")

    # ── STEP 2 : Navigate to Chat Interface sidebar item ─────────────────────

    def _click_chat_interface_nav(self):
        """
        Try to click 'Chat Interface' in the sidebar.
        Called automatically before waiting — the user may already be there.
        """
        try:
            paras = self.driver.find_elements(By.CSS_SELECTOR, self._SEL_MARK_P)
            for p in paras:
                if p.text.strip() == "Chat Interface":
                    radio = p.find_element(
                        By.XPATH, "ancestor::label[@data-baseweb='radio']"
                    )
                    self.driver.execute_script("arguments[0].click();", radio)
                    time.sleep(2)
                    return
        except Exception:
            pass  # silently ignore — user may navigate manually

    # ── STEP 3 : Wait for chat input to become ENABLED ───────────────────────

    def wait_for_chat_enabled(self, timeout: int = WAIT_FOR_CHAT_SEC) -> bool:
        """
        Polls every 3 seconds until the chat textarea is present AND not
        disabled.  Prints a live countdown so the user knows to act.

        Returns True when ready, False on timeout.
        """
        print()
        print("  ┌──────────────────────────────────────────────────────────┐")
        print("  │  WAITING FOR YOU TO COMPLETE THE FOLLOWING STEPS:        │")
        print("  │                                                          │")
        print("  │   1.  Click  'Upload and Train'  in the left sidebar     │")
        print("  │   2.  Click  'Browse files'  and select the Maths PDF    │")
        print("  │   3.  Click  'Train on Uploaded files'                   │")
        print("  │   4.  Wait for training to finish                        │")
        print("  │   5.  Click  'Chat Interface'  in the left sidebar       │")
        print("  │                                                          │")
        print("  │  The test will START AUTOMATICALLY once the chat         │")
        print("  │  text field becomes active.                              │")
        print("  └──────────────────────────────────────────────────────────┘")
        print()

        start    = time.time()
        reported = set()

        while time.time() - start < timeout:
            elapsed = int(time.time() - start)
            remaining = timeout - elapsed

            # Print a status line every 15 seconds
            mark = (elapsed // 15) * 15
            if mark not in reported and elapsed > 0:
                reported.add(mark)
                self._log(
                    f"Still waiting … {elapsed}s elapsed  |  "
                    f"{remaining}s remaining  |  "
                    "Complete the manual steps above ☝"
                )

            # Auto-attempt to click Chat Interface (in case user hasn't yet)
            if elapsed > 0 and elapsed % 10 == 0:
                self._click_chat_interface_nav()

            # Check if the chat textarea exists and is enabled
            inputs = self.driver.find_elements(
                By.CSS_SELECTOR, self._SEL_CHAT_IN
            )
            if inputs:
                inp = inputs[0]
                # Streamlit disables the textarea while training
                disabled = inp.get_attribute("disabled")
                aria_disabled = inp.get_attribute("aria-disabled")
                is_enabled = (
                    inp.is_displayed()
                    and disabled is None
                    and aria_disabled != "true"
                )
                if is_enabled:
                    print()
                    self._log(
                        "✅  Chat input is ACTIVE — starting automated tests now!"
                    )
                    time.sleep(1.5)
                    return True

            time.sleep(3)

        self._log("⚠️  Timeout reached. Chat input did not become active.")
        return False

    # ── STEP 4 : Ask one question and return the response ────────────────────

    def _count_ai(self) -> int:
        msgs = self.driver.find_elements(By.CSS_SELECTOR, self._SEL_CHAT_MSG)
        return sum(
            1 for m in msgs
            if "assistant" in (m.get_attribute("aria-label") or "").lower()
        )

    def _latest_ai(self) -> str:
        msgs = self.driver.find_elements(By.CSS_SELECTOR, self._SEL_CHAT_MSG)
        ai = [
            m for m in msgs
            if "assistant" in (m.get_attribute("aria-label") or "").lower()
        ]
        if not ai:
            return ""
        try:
            return ai[-1].find_element(
                By.CSS_SELECTOR, "[data-testid='stChatMessageContent']"
            ).text.strip()
        except NoSuchElementException:
            return ai[-1].text.strip()

    def ask(self, question: str, timeout: int = RESPONSE_WAIT_SEC) -> str:
        prev = self._count_ai()

        # Type the question
        inp = self.wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, self._SEL_CHAT_IN)
        ))
        inp.click()
        inp.send_keys(Keys.CONTROL + "a")
        inp.send_keys(Keys.DELETE)
        time.sleep(0.2)
        inp.send_keys(question)
        time.sleep(0.4)
        inp.send_keys(Keys.RETURN)

        # Wait for response to arrive and streaming to finish
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self._count_ai() > prev:
                time.sleep(2)
                s1 = self._latest_ai()
                time.sleep(2)
                s2 = self._latest_ai()
                if s1 == s2:
                    return s2
            time.sleep(1)

        return self._latest_ai()

    # ── STEP 5 : Run all test cases ───────────────────────────────────────────

    def run_all(self, test_cases: List[TestCase], threshold: float) -> List[Result]:
        results: List[Result] = []
        total = len(test_cases)

        for idx, tc in enumerate(test_cases, 1):
            print(f"\n  {'─'*66}")
            print(f"  [{idx:02d}/{total}]  {tc.id}  |  {tc.chapter}")
            print(f"  {'─'*66}")

            preview = (tc.question[:75] + "…") if len(tc.question) > 75 else tc.question
            self._log(f"Q: {preview}")

            start = time.time()
            resp  = ""
            err   = None

            try:
                resp = self.ask(tc.question)
            except Exception as exc:
                err = f"{type(exc).__name__}: {exc}"
                self._log(f"ERROR — {err}")

            elapsed = round(time.time() - start, 1)
            s       = compute_score(tc, resp)
            passed  = s["combined"] >= threshold and err is None

            tag = "PASS ✅" if passed else "FAIL ❌"
            self._log(
                f"[{tag}]  combined={s['combined']:.1f}%  "
                f"seq={s['seq']:.1f}%  f1={s['f1']:.1f}%  "
                f"kw={s['kw']:.1f}%  time={elapsed}s"
            )

            results.append(Result(
                tc=tc, resp=resp, scores=s,
                passed=passed, error=err, elapsed=elapsed,
            ))

            if idx < total:
                time.sleep(INTER_QUESTION_DELAY)

        return results

    def close(self):
        try:
            self.driver.quit()
        except Exception:
            pass

# ─────────────────────────────────────────────────────────────────────────────
# HTML Report builder
# ─────────────────────────────────────────────────────────────────────────────

_CSS = """
<style>
*{box-sizing:border-box}
body{font-family:'Segoe UI',Arial,sans-serif;margin:0;background:#f0f4fa;color:#222}
.wrap{max-width:1500px;margin:auto;padding:34px 26px}
h1{color:#1a3a6c;margin:0 0 4px}
.sub{color:#777;font-size:.88rem;margin-bottom:30px}
h2{color:#2c5f9e;border-bottom:2px solid #d4e0f7;padding-bottom:7px;margin-top:38px}

/* Instruction banner */
.banner{background:#fff8e1;border-left:5px solid #f39c12;border-radius:6px;
        padding:16px 20px;margin-bottom:28px}
.banner b{color:#b7770d}
.banner ol{margin:10px 0 0 20px;padding:0;font-size:.9rem;line-height:1.8}

/* Cards */
.cards{display:flex;flex-wrap:wrap;gap:14px;margin:18px 0 32px}
.card{background:white;border-radius:10px;padding:18px 24px;
      box-shadow:0 2px 8px rgba(0,0,0,.08);text-align:center;min-width:118px}
.val{font-size:2.1rem;font-weight:700;line-height:1.1}
.lbl{font-size:.72rem;color:#888;margin-top:4px;text-transform:uppercase;letter-spacing:.05em}
.green{color:#1a8a1a}.red{color:#c0392b}.blue{color:#1a5fb4}.orange{color:#d35400}

/* Accuracy metrics row */
.metrics{display:flex;flex-wrap:wrap;gap:12px;margin-bottom:24px}
.met{background:white;border-radius:8px;padding:14px 18px;
     box-shadow:0 1px 5px rgba(0,0,0,.07);flex:1;min-width:170px}
.met-title{font-size:.72rem;color:#aaa;text-transform:uppercase;margin-bottom:5px}
.met-val{font-size:1.55rem;font-weight:700}
.met-desc{font-size:.72rem;color:#bbb;margin-top:2px}

/* Chapter breakdown */
.chapters{display:flex;flex-wrap:wrap;gap:10px;margin-bottom:18px}
.ch{background:white;border-radius:8px;padding:12px 16px;
    box-shadow:0 1px 5px rgba(0,0,0,.07);flex:1;min-width:175px}
.ch-name{font-size:.76rem;font-weight:600;color:#2c5f9e;margin-bottom:5px}
.ch-val{font-size:1.3rem;font-weight:700}
.ch-sub{font-size:.72rem;color:#bbb;margin-top:2px}

/* Table */
table{width:100%;border-collapse:collapse;background:white;border-radius:10px;
      overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.08);font-size:.83rem}
thead{background:#2c5f9e;color:white}
th,td{padding:10px 13px;text-align:left;vertical-align:top}
th{font-size:.77rem;letter-spacing:.04em;white-space:nowrap}
tr:nth-child(even) td{background:#f0f5fb}
td:first-child{font-weight:700;color:#2c5f9e}

.pb{background:#27ae60;color:white;padding:3px 10px;
    border-radius:16px;font-weight:700;font-size:.74rem}
.fb{background:#e74c3c;color:white;padding:3px 10px;
    border-radius:16px;font-weight:700;font-size:.74rem}

.bw{background:#ddd;border-radius:4px;height:8px;
    width:78px;display:inline-block;vertical-align:middle}
.bf{border-radius:4px;height:8px}
.sc{white-space:nowrap}

details summary{cursor:pointer;color:#2c5f9e;font-size:.79rem;
                font-weight:600;padding:3px 0}
pre{background:#f4f6fc;border-radius:5px;padding:9px 11px;
    white-space:pre-wrap;word-break:break-word;
    font-size:.76rem;max-height:160px;overflow-y:auto;margin-top:4px}

.mbox{background:white;border-radius:10px;padding:20px 24px;
      box-shadow:0 2px 8px rgba(0,0,0,.08);margin-top:28px}
.mbox li{margin:6px 0;font-size:.88rem}
</style>
"""

_BANNER = """
<div class="banner">
  <b>📋 Manual Steps Performed Before Automation Began:</b>
  <ol>
    <li>Click <b>Upload and Train</b> in the left sidebar</li>
    <li>Click <b>Browse files</b> and select the <b>10_mathematics_em_2024-25.pdf</b></li>
    <li>Click <b>Train on Uploaded files</b> and wait for training to complete</li>
    <li>Click <b>Chat Interface</b> in the left sidebar</li>
    <li>Once chat input became active, automation took over and asked all questions</li>
  </ol>
</div>
"""

def _bar(val: float) -> str:
    col = "#27ae60" if val >= 60 else "#f39c12" if val >= 40 else "#e74c3c"
    w   = min(int(val), 100)
    return (
        f'<div class="bw"><div class="bf" '
        f'style="width:{w}%;background:{col}"></div></div>&nbsp;{val:.1f}%'
    )

def _chapter_section(results: List[Result]) -> str:
    by: dict = {}
    for r in results:
        by.setdefault(r.tc.chapter, []).append(r.scores["combined"])
    html = ""
    for ch, vals in sorted(by.items()):
        avg = sum(vals) / len(vals)
        col = "green" if avg >= 60 else "orange" if avg >= 40 else "red"
        html += (
            f'<div class="ch">'
            f'<div class="ch-name">{ch}</div>'
            f'<div class="ch-val {col}">{avg:.1f}%</div>'
            f'<div class="ch-sub">{len(vals)} question(s)</div></div>'
        )
    return f'<div class="chapters">{html}</div>'

def build_html(results: List[Result], threshold: float,
               run_ts: str, url: str) -> str:
    passed   = sum(1 for r in results if r.passed)
    total    = len(results)
    avg_comb = sum(r.scores["combined"] for r in results) / total if total else 0
    avg_kw   = sum(r.scores["kw"]       for r in results) / total if total else 0
    avg_f1   = sum(r.scores["f1"]       for r in results) / total if total else 0
    avg_seq  = sum(r.scores["seq"]      for r in results) / total if total else 0
    avg_time = sum(r.elapsed            for r in results) / total if total else 0
    pass_pct = passed / total * 100 if total else 0

    col_pass = "green" if pass_pct >= 60 else "orange" if pass_pct >= 40 else "red"

    rows = ""
    for r in results:
        badge = f'<span class="pb">PASS</span>' if r.passed else f'<span class="fb">FAIL</span>'
        err   = f"<br><small style='color:red'>⚠ {r.error}</small>" if r.error else ""
        rows += f"""
<tr>
  <td>{r.tc.id}</td>
  <td style="min-width:120px">{r.tc.chapter}</td>
  <td style="max-width:180px">{r.tc.question}</td>
  <td><details><summary>Show reference</summary>
      <pre>{r.tc.reference_answer}</pre></details></td>
  <td><details><summary>Show AI response</summary>
      <pre>{r.resp or "(no response captured)"}</pre></details>{err}</td>
  <td class="sc">{_bar(r.scores['seq'])}</td>
  <td class="sc">{_bar(r.scores['f1'])}</td>
  <td class="sc">{_bar(r.scores['kw'])}</td>
  <td class="sc"><strong>{_bar(r.scores['combined'])}</strong></td>
  <td>{badge}</td>
  <td>{r.elapsed}s</td>
</tr>"""

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>Class-10 Maths RAG — Accuracy Report</title>{_CSS}</head>
<body><div class="wrap">

<h1>📐 Class-10 Mathematics RAG LLM — Accuracy &amp; Frequency Report</h1>
<p class="sub">
  <b>Textbook:</b> 10 Mathematics EM 2024-25 (Telangana SCERT) &nbsp;|&nbsp;
  <b>App:</b> {url} &nbsp;|&nbsp;
  <b>Run:</b> {run_ts} &nbsp;|&nbsp;
  <b>Pass threshold:</b> {threshold}%
</p>

{_BANNER}

<h2>Overall Accuracy &amp; Frequency</h2>
<div class="metrics">
  <div class="met">
    <div class="met-title">Pass Rate</div>
    <div class="met-val {col_pass}">{pass_pct:.1f}%</div>
    <div class="met-desc">{passed} of {total} tests passed</div>
  </div>
  <div class="met">
    <div class="met-title">Combined Accuracy</div>
    <div class="met-val blue">{avg_comb:.1f}%</div>
    <div class="met-desc">Weighted average of 3 metrics</div>
  </div>
  <div class="met">
    <div class="met-title">Keyword Accuracy</div>
    <div class="met-val blue">{avg_kw:.1f}%</div>
    <div class="met-desc">Key concepts mentioned correctly</div>
  </div>
  <div class="met">
    <div class="met-title">Token F1 Score</div>
    <div class="met-val blue">{avg_f1:.1f}%</div>
    <div class="met-desc">Word-level precision / recall</div>
  </div>
  <div class="met">
    <div class="met-title">Sequence Match</div>
    <div class="met-val blue">{avg_seq:.1f}%</div>
    <div class="met-desc">Character-level similarity</div>
  </div>
  <div class="met">
    <div class="met-title">Avg Response Time</div>
    <div class="met-val blue">{avg_time:.1f}s</div>
    <div class="met-desc">Per question incl. streaming</div>
  </div>
</div>

<h2>Accuracy by Chapter</h2>
{_chapter_section(results)}

<h2>Summary</h2>
<div class="cards">
  <div class="card"><div class="val">{total}</div><div class="lbl">Total Tests</div></div>
  <div class="card"><div class="val green">{passed}</div><div class="lbl">Passed</div></div>
  <div class="card"><div class="val red">{total - passed}</div><div class="lbl">Failed</div></div>
  <div class="card"><div class="val {col_pass}">{pass_pct:.1f}%</div><div class="lbl">Pass Rate</div></div>
  <div class="card"><div class="val orange">{avg_comb:.1f}%</div><div class="lbl">Avg Combined</div></div>
  <div class="card"><div class="val blue">{avg_time:.1f}s</div><div class="lbl">Avg Time</div></div>
</div>

<h2>Detailed Question-by-Question Results</h2>
<table>
<thead>
  <tr>
    <th>ID</th><th>Chapter</th><th>Question</th>
    <th>Reference Answer</th><th>AI Response</th>
    <th>Seq Sim</th><th>Token F1</th><th>KW Hit</th>
    <th>Combined</th><th>Status</th><th>Time</th>
  </tr>
</thead>
<tbody>{rows}</tbody>
</table>

<div class="mbox">
  <h2 style="margin-top:0">Scoring Methodology</h2>
  <ul>
    <li><b>Sequence Similarity (25%)</b> — Character-level overlap between
        the textbook reference answer and the AI response (Python difflib).</li>
    <li><b>Token F1 Score (30%)</b> — Word-level precision/recall F1;
        common stop-words excluded for fair comparison.</li>
    <li><b>Keyword Hit-Rate (45%)</b> — Percentage of essential concept
        keywords present in the AI response. Weighted highest as it most
        reliably captures factual accuracy.</li>
    <li><b>Combined Score</b> = 0.25 × Seq + 0.30 × F1 + 0.45 × KW</li>
    <li>A test <b>PASSES</b> when Combined Score ≥ {threshold}%
        and no Selenium error occurred.</li>
  </ul>
</div>

</div></body></html>"""

# ─────────────────────────────────────────────────────────────────────────────
# CSV
# ─────────────────────────────────────────────────────────────────────────────

def save_csv(results: List[Result], path: str):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "ID", "Chapter", "Question",
            "Seq_Sim_%", "Token_F1_%", "KW_Hit_%", "Combined_%",
            "Status", "Elapsed_s", "Error",
        ])
        for r in results:
            w.writerow([
                r.tc.id, r.tc.chapter, r.tc.question,
                r.scores["seq"], r.scores["f1"],
                r.scores["kw"], r.scores["combined"],
                "PASS" if r.passed else "FAIL",
                r.elapsed, r.error or "",
            ])

# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(
        description=(
            "Opens the RAG app, WAITS for you to upload+train the model, "
            "then auto-runs 20 maths Q&A accuracy tests."
        )
    )
    p.add_argument("--url",       default=APP_URL,
                   help=f"Streamlit app URL  [default: {APP_URL}]")
    p.add_argument("--headless",  action="store_true",
                   help="Run Chrome headlessly (manual steps won't be visible)")
    p.add_argument("--threshold", type=float, default=PASS_THRESHOLD,
                   help=f"Minimum combined score (%%) to PASS  [default: {PASS_THRESHOLD}]")
    p.add_argument("--driver",    default=os.environ.get("CHROME_DRIVER_PATH", ""),
                   help="Path to chromedriver binary  [optional]")
    p.add_argument("--ids",       nargs="*",
                   help="Run only specific test IDs  e.g. --ids TC01 TC05 TC14")
    p.add_argument("--wait",      type=int, default=WAIT_FOR_CHAT_SEC,
                   help=f"Max seconds to wait for chat to activate  [default: {WAIT_FOR_CHAT_SEC}]")
    p.add_argument("--out",       default=".",
                   help="Output directory for reports  [default: current dir]")
    return p.parse_args()

# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    args = parse_args()

    tests = TEST_CASES
    if args.ids:
        ids_up = {x.upper() for x in args.ids}
        tests  = [tc for tc in TEST_CASES if tc.id in ids_up]
        if not tests:
            print(f"[ERROR] No test cases match: {args.ids}")
            sys.exit(1)

    run_ts  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ts_file = datetime.now().strftime("%Y%m%d_%H%M%S")

    print("\n" + "═"*68)
    print("  📐  Class-10 Maths RAG — Accuracy & Frequency Test Suite")
    print("═"*68)
    print(f"  App URL    : {args.url}")
    print(f"  Headless   : {args.headless}")
    print(f"  Threshold  : {args.threshold}%")
    print(f"  Tests      : {len(tests)}")
    print(f"  Chat wait  : up to {args.wait}s")
    print(f"  Run at     : {run_ts}")
    print("═"*68)

    tester:  Optional[ChatTester] = None
    results: List[Result]         = []

    try:
        tester = ChatTester(
            url=args.url,
            headless=args.headless,
            driver_path=args.driver,
        )

        # STEP 1 — Open the app
        tester.open_app()

        # STEP 2 — Wait for user to upload, train, and open chat
        chat_ready = tester.wait_for_chat_enabled(timeout=args.wait)
        if not chat_ready:
            print("\n[ERROR] Chat input did not become active within the timeout.")
            print("        Please retry or increase --wait value.")
            sys.exit(1)

        # STEP 3 — Run all tests automatically
        print("\n" + "─"*68)
        print("  PHASE — Automated Q&A Accuracy Tests (20 questions)")
        print("─"*68)
        results = tester.run_all(tests, args.threshold)

    except KeyboardInterrupt:
        print("\n[Interrupted] Saving partial results …")
    except Exception as exc:
        print(f"\n[FATAL] {exc}")
        traceback.print_exc()
    finally:
        if tester:
            tester.close()

    # ── Console summary ───────────────────────────────────────────────────────
    if not results:
        print("[WARN] No results captured.")
        sys.exit(1)

    passed   = sum(1 for r in results if r.passed)
    total    = len(results)
    avg_comb = sum(r.scores["combined"] for r in results) / total
    avg_kw   = sum(r.scores["kw"]       for r in results) / total
    avg_f1   = sum(r.scores["f1"]       for r in results) / total
    avg_time = sum(r.elapsed            for r in results) / total

    print("\n" + "═"*68)
    print("  ACCURACY & FREQUENCY REPORT")
    print("═"*68)
    print(f"  Total Tests        : {total}")
    print(f"  Passed             : {passed}  ({passed/total*100:.1f}%)")
    print(f"  Failed             : {total - passed}")
    print(f"  Avg Combined Score : {avg_comb:.1f}%")
    print(f"  Avg Keyword Hit    : {avg_kw:.1f}%")
    print(f"  Avg Token F1       : {avg_f1:.1f}%")
    print(f"  Avg Response Time  : {avg_time:.1f}s")
    print("─"*68)
    for r in results:
        tag = "PASS ✅" if r.passed else "FAIL ❌"
        print(
            f"  [{tag}] {r.tc.id:5s} | {r.tc.chapter:28s} | "
            f"combined={r.scores['combined']:5.1f}% | "
            f"kw={r.scores['kw']:5.1f}%"
        )
    print("═"*68)

    # ── Save reports ──────────────────────────────────────────────────────────
    os.makedirs(args.out, exist_ok=True)
    html_path = os.path.join(args.out, f"accuracy_report_{ts_file}.html")
    csv_path  = os.path.join(args.out, f"accuracy_report_{ts_file}.csv")

    with open(html_path, "w", encoding="utf-8") as fh:
        fh.write(build_html(results, args.threshold, run_ts, args.url))
    save_csv(results, csv_path)

    print(f"\n  HTML Report : {html_path}")
    print(f"  CSV  Report : {csv_path}\n")

    sys.exit(sum(1 for r in results if not r.passed))


if __name__ == "__main__":
    main()