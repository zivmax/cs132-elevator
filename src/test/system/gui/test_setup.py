from playwright.sync_api import Page, expect


def test_app_loads_and_has_correct_title(page: Page, app):
    """
    Tests if the application loads in headless mode and has the correct title.
    """
    app_url = app  # Get the URL from the fixture

    print(f"Navigating to {app_url}")
    page.goto(
        app_url, wait_until="networkidle"
    )  # wait_until can be 'load', 'domcontentloaded', 'networkidle'

    # Check the title of the page
    expected_title = "Elevator Simulation"
    expect(page).to_have_title(expected_title)
    print(f'Page title is: "{page.title()}". Expected: "{expected_title}"')
