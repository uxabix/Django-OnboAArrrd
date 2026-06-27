"""Capture UI screenshots for README documentation (requires running app on :8000)."""

from pathlib import Path

from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:8000"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "docs" / "screenshots"

ACCOUNTS = {
    "student": ("student.ola@onboard.local", "DemoStudent123!"),
    "mentor": ("mentor.piotr@onboard.local", "DemoMentor123!"),
    "hr": ("hr.demo@onboard.local", "DemoHr123!"),
}

PUBLIC_PAGES = [
    ("home", "/"),
    ("login", "/accounts/login/"),
]

ROLE_PAGES = {
    "student": [
        ("student-dashboard", "/accounts/logged/"),
        ("student-tasks", "/onboarding/tasks/?filter=all"),
        ("student-paths", "/onboarding/paths/"),
        ("student-calendar", "/onboarding/tasks/calendar/"),
        ("student-profile", "/accounts/profile/"),
        ("student-chat", "/chat/"),
        ("mentor-ranking", "/ranking-mentorow/"),
    ],
    "mentor": [
        ("mentor-dashboard", "/accounts/logged/"),
        ("mentor-task-management", "/mentor/tasks/"),
        ("mentor-chat", "/chat/"),
    ],
    "hr": [
        ("hr-dashboard", "/hr/"),
    ],
}


def login(page, email: str, password: str) -> None:
    page.goto(f"{BASE_URL}/accounts/login/")
    page.fill('input[name="username"], input[name="email"]', email)
    page.fill('input[name="password"]', password)
    page.click('button[type="submit"]')
    page.wait_for_load_state("networkidle")
    if email not in page.content():
        raise RuntimeError(f"Login failed for {email}")


def capture(page, name: str, path: str) -> None:
    page.goto(f"{BASE_URL}{path}")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(500)
    outfile = OUTPUT_DIR / f"{name}.png"
    page.screenshot(path=str(outfile), full_page=True)
    print(f"  saved {outfile.name}")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch()

        print("Public pages:")
        public_context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = public_context.new_page()
        for name, path in PUBLIC_PAGES:
            capture(page, name, path)
        public_context.close()

        for role, pages in ROLE_PAGES.items():
            email, password = ACCOUNTS[role]
            print(f"\n{role.title()} pages ({email}):")
            context = browser.new_context(viewport={"width": 1280, "height": 800})
            page = context.new_page()
            login(page, email, password)
            for name, path in pages:
                capture(page, name, path)
            context.close()

        browser.close()

    print(f"\nDone — {len(list(OUTPUT_DIR.glob('*.png')))} screenshots in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
