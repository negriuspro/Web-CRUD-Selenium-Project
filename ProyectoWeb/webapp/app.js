
const passwordInput = document.getElementById('passwordUser');
const toggleBtn = document.getElementById('togglePassword');
let editId = -1;

const deleteConfirmDiv = document.getElementById('deleteConfirm');
const deleteMsgSpan = document.getElementById('deleteMsg');
const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
const cancelDeleteBtn = document.getElementById('cancelDeleteBtn');
let userToDelete = null;


if (toggleBtn && passwordInput) {
    toggleBtn.addEventListener('click', () => {
        const isPassword = passwordInput.type === 'password';
        passwordInput.type = isPassword ? 'text' : 'password';
        toggleBtn.textContent = isPassword ? 'Ocultar' : 'Mostrar';
    });
}


async function checkAuth() {
    try {
        const res = await fetch('/api/check_session');
        if (!res.ok) window.location.href = 'index.html';
    } catch (err) {
        console.error(err);
        window.location.href = 'index.html';
    }
}

async function handleLogin(event) {
    event.preventDefault();
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    mostrarErrorLogin('', 0); 

    if (!email || !password) {
        mostrarErrorLogin('Por favor ingrese email y contraseña');
        return;
    }

    try {
        const res = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        const data = await res.json();
        if (res.ok) {
            window.location.href = 'dashboard.html';
        } else {
            mostrarErrorLogin(data.message || 'Credenciales incorrectas');
        }
    } catch (err) {
        mostrarErrorLogin('Error de conexión');
        console.error(err);
    }
}

async function logout() {
    try { await fetch('/api/logout', { method: 'POST' }); }
    catch (err) { console.error(err); }
    finally { window.location.href = 'index.html'; }
}


async function cargarUsuarios() {
    try {
        const res = await fetch('/api/users');
        if (!res.ok) throw new Error("Error al cargar usuarios");
        const usuarios = await res.json();

        const tbody = document.getElementById('userTableBody');
        if (!tbody) return;
        tbody.innerHTML = '';

        usuarios.forEach(user => {
            const tr = document.createElement('tr');
            tr.setAttribute('data-email', user.email);
            tr.innerHTML = `
                <td>${escapeHtml(user.username)}</td>
                <td>${escapeHtml(user.email)}</td>
                <td>
                    <button type="button" onclick="editarUsuario(${user.id})" class="secondary">Editar</button>
                    <button type="button" onclick="eliminarUsuario(${user.id}, '${escapeHtml(user.username)}')" class="deleteBtn danger">Eliminar</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        mostrarErrorDashboard('Error al cargar usuarios');
        console.error(err);
    }
}

async function guardarUsuario(event) {
    event.preventDefault();
    const username = document.getElementById('nombre').value.trim();
    const email = document.getElementById('correo').value.trim();
    const password = document.getElementById('passwordUser').value;

    if (!username || !email) {
        mostrarErrorDashboard("Por favor complete los campos de nombre y correo");
        return;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        mostrarErrorDashboard("Formato de correo inválido");
        return;
    }

    try {
        const method = editId === -1 ? 'POST' : 'PUT';
        const url = editId === -1 ? '/api/users' : `/api/users/${editId}`;
        const payload = { username, email };
        if (password) payload.password = password;

        const res = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (res.ok) {
            document.getElementById('userForm').reset();
            editId = -1;
            document.getElementById('submitBtn').textContent = 'Crear Usuario';
            await cargarUsuarios();
            mostrarExitoDashboard('Usuario guardado correctamente');
        } else {
            mostrarErrorDashboard(data.message || "Error al guardar usuario");
        }
    } catch (err) {
        mostrarErrorDashboard(`Error: ${err}`);
        console.error(err);
    }
}

async function editarUsuario(id) {
    try {
        const res = await fetch(`/api/users/${id}`);
        const data = await res.json();
        if (!res.ok) throw new Error(data.message || "No se pudo cargar el usuario");

        document.getElementById('nombre').value = data.username;
        document.getElementById('correo').value = data.email;
        document.getElementById('passwordUser').value = data.password;

        editId = id;
        document.getElementById('submitBtn').textContent = 'Actualizar Usuario';
    } catch (err) {
        mostrarErrorDashboard(`Error: ${err}`);
        console.error(err);
    }
}


function eliminarUsuario(id, username) {
    userToDelete = id;
    deleteMsgSpan.textContent = `¿Desea eliminar al usuario "${username}"?`;
    deleteConfirmDiv.style.display = 'block';
}

if (confirmDeleteBtn) {
    confirmDeleteBtn.addEventListener('click', async () => {
        if (!userToDelete) return;
        try {
            const res = await fetch(`/api/users/${userToDelete}`, { method: 'DELETE' });
            const data = await res.json();
            if (!res.ok) throw new Error(data.message || 'Error al eliminar usuario');
            await cargarUsuarios();
            mostrarExitoDashboard(`Usuario eliminado correctamente`);
        } catch (err) {
            mostrarErrorDashboard(`Error: ${err}`);
        } finally {
            deleteConfirmDiv.style.display = 'none';
            userToDelete = null;
        }
    });
}

if (cancelDeleteBtn) {
    cancelDeleteBtn.addEventListener('click', () => {
        deleteConfirmDiv.style.display = 'none';
        userToDelete = null;
    });
}

// ----------------------------
// --- Utils ---
// ----------------------------
function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/[&<>"'`=\/]/g, s => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': '&quot;', "'": '&#39;', "/": '&#x2F;', "`": '&#x60;', "=": '&#x3D;' }[s]));
}

function mostrarErrorLogin(msg, timeout = 0) {
    const errorDiv = document.getElementById('errorMsg');
    if (!errorDiv) { alert(msg); return; }
    errorDiv.style.display = msg ? 'inline-block' : 'none';
    errorDiv.textContent = msg || '';

    if (timeout > 0 && msg) {
        setTimeout(() => {
            errorDiv.style.display = 'none';
            errorDiv.textContent = '';
        }, timeout);
    }
}


function mostrarErrorDashboard(msg, timeout = 3000) {
    const errorDiv = document.getElementById('crudErrorMsg');
    if (!errorDiv) { alert(msg); return; }
    errorDiv.style.display = 'block';
    errorDiv.textContent = msg;
    if (timeout > 0) setTimeout(() => { errorDiv.style.display = 'none'; errorDiv.textContent = ''; }, timeout);
}

function mostrarExitoDashboard(msg, timeout = 3000) {
    const successDiv = document.getElementById('crudSuccessMsg');
    if (!successDiv) { alert(msg); return; }
    successDiv.style.display = 'block';
    successDiv.textContent = msg;
    if (timeout > 0) setTimeout(() => { successDiv.style.display = 'none'; successDiv.textContent = ''; }, timeout);
}


document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    if (loginForm) loginForm.addEventListener('submit', handleLogin);

    const userForm = document.getElementById('userForm');
    if (userForm) {
        checkAuth().then(() => cargarUsuarios());
        userForm.addEventListener('submit', guardarUsuario);

        const logoutBtn = document.getElementById('logoutBtn');
        if (logoutBtn) logoutBtn.addEventListener('click', logout);
    }
});
