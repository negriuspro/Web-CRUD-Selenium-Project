import os
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


@pytest.fixture(scope="session")
def driver():
    driver_path = os.path.join(os.path.dirname(__file__), "drivers", "chromedriver.exe")
    service = Service(driver_path)
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(service=service, options=options)
    driver.maximize_window()
    yield driver
    driver.quit()


BASE_URL = "http://127.0.0.1:5000"
ADMIN_EMAIL = "admin@test.com"
ADMIN_PASSWORD = "admin123"

@pytest.fixture
def logged_in_driver(driver):
    driver.get(f"{BASE_URL}/index.html")
    driver.find_element(By.ID, "email").send_keys(ADMIN_EMAIL)
    driver.find_element(By.ID, "password").send_keys(ADMIN_PASSWORD)
    driver.find_element(By.CSS_SELECTOR, "#loginForm button").click()
    WebDriverWait(driver, 10).until(EC.url_contains("dashboard.html"))
    yield driver


TEST_NAMES_ES = {
    "test_login_empty_fields": "login_campos_vacios",
    "test_login_success": "login_exitoso",
    "test_login_invalid_credentials": "login_credenciales_invalidas",
    "test_view_users_table": "ver_tabla_usuarios",
    "test_create_user_success": "crear_usuario_exitoso",
    "test_create_user_empty_fields": "crear_usuario_campos_vacios",
    "test_create_user_reject_duplicate": "crear_usuario_duplicado",
    "test_edit_user_success": "editar_usuario_exitoso",
    "test_delete_user_success": "eliminar_usuario_exitoso",
    "test_delete_user_cancel": "eliminar_usuario_cancelar",
    "test_dashboard_blocked_without_login": "acceso_denegado_sin_login",
    "test_logout_success": "cerrar_sesion_exitoso"
}


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()

    if rep.when == "call":
        driver = item.funcargs.get("driver") or item.funcargs.get("logged_in_driver")
        if driver:
            screenshots_dir = os.path.join(os.getcwd(), "screenshots")
            os.makedirs(screenshots_dir, exist_ok=True)
            
            
            clean_name = item.name
            if clean_name in TEST_NAMES_ES:
                file_name = f"{TEST_NAMES_ES[clean_name]}.png"
            else:
                file_name = f"{clean_name}.png".replace("::", "_").replace("/", "_").replace("\\", "_").replace(":", "_")
            
            path = os.path.join(screenshots_dir, file_name)
            
            try:
                driver.save_screenshot(path)
                
                pytest_html = item.config.pluginmanager.getplugin("html")
                if pytest_html:
                    extra = getattr(rep, "extra", [])
                    relative_path = os.path.join("screenshots", file_name)
                    html = f'<div><img src="{relative_path}" alt="screenshot" style="width:400px;" onclick="window.open(this.src)" /></div>'
                    extra.append(pytest_html.extras.html(html))
                    rep.extra = extra
            except Exception as e:
                print(f"Error al capturar screenshot: {e}")
