from playwright.sync_api import Page, expect

def test_basic_functionality(page: Page, app):
    """
    Tests basic functionality of the application by:
    1. Pressing floor 3 button in elevator 1
    2. Verifying elevator moves to floor 3
    3. Verifying doors open and close automatically
    4. Verifying button state changes appropriately
    """
    app_url = app  # Get the URL from the fixture

    print(f"Navigating to {app_url}")
    page.goto(app_url, wait_until="networkidle")

    # Select floor 3 in elevator 1
    print("=== Test Step 1: Clicking floor 3 button in elevator 1 ===")
    
    # Find and click the floor 3 button in elevator 1 control panel
    floor_3_button = page.locator('#panel-1 .floor-buttons button:has-text("3")')
    expect(floor_3_button).to_be_visible()
    floor_3_button.click()
    
    print("Floor 3 button clicked, waiting for elevator to respond...")
    
    # Wait for button to become active (highlighted)
    expect(floor_3_button).to_have_class("active", timeout=5000)
    print("✓ Floor 3 button is now active (highlighted)")
    
    # === Test Step 2: Verify elevator movement ===
    print("=== Test Step 2: Verifying elevator movement ===")
    
    # Wait for elevator to start moving (status should change to MOVING_UP)
    elevator_status = page.locator('#elevator-1-status')
    expect(elevator_status).to_have_text("MOVING_UP", timeout=10000)
    print("✓ Elevator 1 is now moving up")
    
    # Wait for elevator to reach floor 3 (status should change to IDLE)
    expect(elevator_status).to_have_text("IDLE", timeout=15000)
    print("✓ Elevator 1 has reached destination and is now idle")
    
    # Check that the elevator is at floor 3
    elevator_floor = page.locator('#elevator-1-floor')
    expect(elevator_floor).to_have_text("3", timeout=5000)
    print("✓ Elevator 1 is at floor 3")
    
    # === Test Step 3: Verify automatic door operations ===
    print("=== Test Step 3: Verifying automatic door operations ===")
    
    # Check that doors are opening/open
    elevator_door = page.locator('#elevator-1-door')
    
    # Wait for door to be opening or open
    print("Waiting for doors to open...")
    page.wait_for_function(
        'document.querySelector("#elevator-1-door").textContent === "OPENING" || '
        'document.querySelector("#elevator-1-door").textContent === "OPEN"',
        timeout=10000
    )
    
    door_state = elevator_door.text_content()
    print(f"Door state: {door_state}")
    
    # Wait for doors to be fully open
    expect(elevator_door).to_have_text("OPEN", timeout=10000)
    print("✓ Doors are now fully open")
    
    # Wait for doors to automatically close (should happen after timeout ~3 seconds)
    print("Waiting for doors to automatically close...")
    expect(elevator_door).to_have_text("CLOSING", timeout=10000)
    print("✓ Doors are now closing automatically")
    
    # Wait for doors to be fully closed
    expect(elevator_door).to_have_text("CLOSED", timeout=10000)
    print("✓ Doors are now fully closed")
    
    # === Test Step 4: Verify button state reset ===
    print("=== Test Step 4: Verifying button state reset ===")
    
    # Verify the floor 3 button is no longer active (deactivated after reaching destination)
    expect(floor_3_button).not_to_have_class("active", timeout=5000)
    print("✓ Floor 3 button is no longer active (request completed)")
    
    # Final verification: elevator is still at floor 3
    expect(elevator_floor).to_have_text("3")
    expect(elevator_status).to_have_text("IDLE")
    print("✓ Elevator remains at floor 3 in IDLE state")
    
    print("=== Test completed successfully! ===")
    print("Summary:")
    print("  - Floor 3 button press: ✓")
    print("  - Elevator movement to floor 3: ✓")
    print("  - Automatic door opening: ✓")
    print("  - Automatic door closing: ✓")
    print("  - Button state reset: ✓")
