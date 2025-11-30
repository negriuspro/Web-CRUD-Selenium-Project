import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os


BASE_URL = "http://127.0.0.1:5000"
URL_LOGIN = f"{BASE_URL}/index.html"
URL_DASHBOARD = f"{BASE_URL}/dashboard.html"


ADMIN_EMAIL = "admin@test.com"
ADMIN_PASSWORD = "admin123"


@pytest.fixture
def temp_user():
    import requests

    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    if r.status_code != 200:
        pytest.fail(f"No se pudo loguear admin: {r.status_code}, {r.text}")

    user = {"username": "TempUser", "email": "temp@test.com", "password": "1234"}

   
    r = s.get(f"{BASE_URL}/api/users")
    users = r.json()
    if isinstance(users, dict):
        users = users.get("users", [])
    for u in users:
        if u.get("email") == user["email"]:
            try:
                s.delete(f"{BASE_URL}/api/users/{u['id']}")
            except Exception:
                pass

    
    r = s.post(f"{BASE_URL}/api/users", json=user)
    if r.status_code not in [200, 201]:
        pytest.fail(f"No se pudo crear usuario temporal: {r.status_code}, {r.text}")
    user_data = r.json()
    user["id"] = user_data.get("id")

    yield user

    r
    try:
        s.delete(f"{BASE_URL}/api/users/{user['id']}")
    except Exception as e:
        print(f"No se pudo eliminar usuario temporal: {e}")

@pytest.fixture
def logged_in_driver(driver):
    driver.get(URL_LOGIN)
    driver.find_element(By.ID, "email").clear()
    driver.find_element(By.ID, "email").send_keys(ADMIN_EMAIL)
    driver.find_element(By.ID, "password").clear()
    driver.find_element(By.ID, "password").send_keys(ADMIN_PASSWORD)
    driver.find_element(By.CSS_SELECTOR, "#loginForm button").click()
    WebDriverWait(driver, 10).until(EC.url_contains("dashboard.html"))
    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "[data-email]"))
    )
    yield driver





def test_login_empty_fields(driver):
    driver.get(URL_LOGIN)

   
    driver.find_element(By.ID, "email").clear()
    driver.find_element(By.ID, "password").clear()

    driver.find_element(By.CSS_SELECTOR, "#loginForm button").click()

    error_text = WebDriverWait(driver, 5).until(
        lambda d: d.find_element(By.ID, "errorMsg").text.strip() != ''
    )

    
    final_text = driver.find_element(By.ID, "errorMsg").text.lower()
    assert "correo" in final_text or "contraseña" in final_text


def test_login_success(driver):
    driver.get(URL_LOGIN)
    driver.find_element(By.ID, "email").clear()
    driver.find_element(By.ID, "email").send_keys(ADMIN_EMAIL)
    driver.find_element(By.ID, "password").clear()
    driver.find_element(By.ID, "password").send_keys(ADMIN_PASSWORD)
    driver.find_element(By.CSS_SELECTOR, "#loginForm button").click()
    
    WebDriverWait(driver, 10).until(EC.url_contains("dashboard.html"))
    assert "dashboard.html" in driver.current_url, "No se redirigió al dashboard"
   
    header = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.TAG_NAME, "h1"))
    )
    assert "Panel de Usuarios" in header.text, "No se encontró el título 'Panel de Usuarios' en el dashboard"

  
    driver.execute_script("""
        var msg = document.createElement('div');
        msg.innerText = 'Inicio de sesión correcto';
        msg.style.position = 'fixed';
        msg.style.top = '20px';
        msg.style.right = '20px';
        msg.style.backgroundColor = '#28a745';
        msg.style.color = 'white';
        msg.style.padding = '15px 25px';
        msg.style.borderRadius = '8px';
        msg.style.zIndex = '99999';
        msg.style.fontSize = '18px';
        msg.style.fontWeight = 'bold';
        msg.style.boxShadow = '0 4px 6px rgba(0,0,0,0.1)';
        document.body.appendChild(msg);
    """)

def test_dashboard_blocked_without_login(driver):
    
    driver.get(BASE_URL) 
    driver.delete_all_cookies()
    
    driver.get(URL_DASHBOARD)
    WebDriverWait(driver, 10).until(EC.url_contains("index.html"))
    assert "index.html" in driver.current_url, "No se redirigió al login al intentar acceder sin sesión"
    
   
    header = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.TAG_NAME, "h2"))
    )
    assert "Iniciar Sesión" in header.text, "No se encontró el título 'Iniciar Sesión' tras la redirección"

def test_view_users_table(logged_in_driver):
    driver = logged_in_driver
    
    headers = driver.find_elements(By.CSS_SELECTOR, "#usersTable th")
    header_texts = [h.text for h in headers]
    assert "Nombre" in header_texts
    assert "Email" in header_texts
    assert "Acciones" in header_texts
    
    
    rows = driver.find_elements(By.CSS_SELECTOR, "#userTableBody tr")
    if len(rows) > 0:
        assert driver.find_element(By.CSS_SELECTOR, ".secondary").is_displayed()
        assert driver.find_element(By.CSS_SELECTOR, ".deleteBtn").is_displayed()

def test_create_user_success(logged_in_driver):
    driver = logged_in_driver
    import time
    unique_suffix = int(time.time())
    new_email = f"newuser{unique_suffix}@test.com"
    
    driver.find_element(By.ID, "nombre").clear()
    driver.find_element(By.ID, "nombre").send_keys("New User")
    driver.find_element(By.ID, "correo").clear()
    driver.find_element(By.ID, "correo").send_keys(new_email)
    driver.find_element(By.ID, "passwordUser").clear()
    driver.find_element(By.ID, "passwordUser").send_keys("1234")
    driver.find_element(By.ID, "submitBtn").click()
    
  
    success_msg = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, "crudSuccessMsg"))
    )
    assert "guardado" in success_msg.text.lower()
    
    
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, f"[data-email='{new_email}']"))
    )
    
   
    try:
        row = driver.find_element(By.CSS_SELECTOR, f"[data-email='{new_email}']")
        row.find_element(By.ClassName, "deleteBtn").click()
        WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.ID, "confirmDeleteBtn")))
        driver.find_element(By.ID, "confirmDeleteBtn").click()
        WebDriverWait(driver, 5).until(EC.invisibility_of_element_located((By.ID, "confirmDeleteBtn")))
    except:
        pass

def test_create_user_empty_fields(logged_in_driver):
    driver = logged_in_driver
    driver.find_element(By.ID, "nombre").clear()
    driver.find_element(By.ID, "correo").clear()
    driver.find_element(By.ID, "passwordUser").clear()
    
    
    driver.execute_script("document.getElementById('userForm').setAttribute('novalidate', true);")
    driver.find_element(By.ID, "submitBtn").click()
    driver.find_element(By.ID, "passwordUser").clear()
    driver.find_element(By.ID, "nombre").send_keys("Usuario Duplicado")
    driver.find_element(By.ID, "correo").send_keys("juan@test.com")
    driver.find_element(By.ID, "passwordUser").send_keys("1234")
    driver.find_element(By.ID, "submitBtn").click()
    error_msg = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, "crudErrorMsg"))
    )
    
    assert "email" in error_msg.text.lower() and "existe" in error_msg.text.lower()

def test_edit_user_success(logged_in_driver, temp_user):
    driver = logged_in_driver
    driver.get(URL_DASHBOARD)
    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-email='{temp_user['email']}']"))
    )
    driver.find_element(By.CSS_SELECTOR, f"[data-email='{temp_user['email']}'] .secondary").click()
    nombre_input = driver.find_element(By.ID, "nombre")
    nombre_input.clear()
    nombre_input.send_keys("TempUserEdited")
    driver.find_element(By.ID, "submitBtn").click()
    success_msg = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, "crudSuccessMsg"))
    )
    assert "guardado" in success_msg.text.lower() or "actualizado" in success_msg.text.lower()

def test_delete_user_success(logged_in_driver, temp_user):
    driver = logged_in_driver
    driver.get(URL_DASHBOARD)
    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-email='{temp_user['email']}']"))
    )
    driver.find_element(By.CSS_SELECTOR, f"[data-email='{temp_user['email']}'] .deleteBtn").click()
    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, "confirmDeleteBtn"))
    )
    driver.find_element(By.ID, "confirmDeleteBtn").click()
    success_msg = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, "crudSuccessMsg"))
    )
    assert "eliminado" in success_msg.text.lower()

def test_delete_user_cancel(logged_in_driver, temp_user):
    driver = logged_in_driver
    driver.get(URL_DASHBOARD)
    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-email='{temp_user['email']}']"))
    )
    driver.find_element(By.CSS_SELECTOR, f"[data-email='{temp_user['email']}'] .deleteBtn").click()
    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, "cancelDeleteBtn"))
    )
    driver.find_element(By.ID, "cancelDeleteBtn").click()
    
    assert driver.find_element(By.CSS_SELECTOR, f"[data-email='{temp_user['email']}']") is not None

def test_logout_success(logged_in_driver):
    driver = logged_in_driver
    driver.find_element(By.ID, "logoutBtn").click()
    
    WebDriverWait(driver, 10).until(EC.url_contains("index.html"))
    assert "index.html" in driver.current_url
    
   
    header = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.TAG_NAME, "h2"))
    )
    assert "Iniciar Sesión" in header.text

    
    driver.execute_script("""
        var msg = document.createElement('div');
        msg.innerText = 'Sesión cerrada';
        msg.style.position = 'fixed';
        msg.style.top = '20px';
        msg.style.right = '20px';
        msg.style.backgroundColor = '#dc3545';
        msg.style.color = 'white';
        msg.style.padding = '15px 25px';
        msg.style.borderRadius = '8px';
        msg.style.zIndex = '99999';
        msg.style.fontSize = '18px';
        msg.style.fontWeight = 'bold';
        msg.style.boxShadow = '0 4px 6px rgba(0,0,0,0.1)';
        document.body.appendChild(msg);
    """)
    import time
    time.sleep(1) 