import os

def save_screenshot(driver, name):
    screenshot_dir = os.path.join(os.path.dirname(__file__), "screenshots")
    if not os.path.exists(screenshot_dir):
        os.makedirs(screenshot_dir)
    driver.save_screenshot(os.path.join(screenshot_dir, name))
