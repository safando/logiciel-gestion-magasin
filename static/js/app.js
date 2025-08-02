
document.addEventListener('DOMContentLoaded', () => {
    const app = document.getElementById('app');
    let authToken = localStorage.getItem('token');

    const showToast = (message, type = 'success') => {
        // Une fonction simple pour les notifications. Vous pouvez la remplacer par une bibliothèque comme Toastify.js
        alert(message);
    };

    const renderLogin = () => {
        app.innerHTML = `
            <div class="container">
                <div class="row justify-content-center align-items-center vh-100">
                    <div class="col-md-4">
                        <div class="card shadow">
                            <div class="card-body p-4">
                                <h3 class="card-title text-center mb-4">Connexion</h3>
                                <form id="login-form">
                                    <div class="mb-3">
                                        <label for="username" class="form-label">Nom d'utilisateur</label>
                                        <input type="text" class="form-control" id="username" required>
                                    </div>
                                    <div class="mb-3">
                                        <label for="password" class="form-label">Mot de passe</label>
                                        <input type="password" class="form-control" id="password" required>
                                    </div>
                                    <button type="submit" class="btn btn-primary w-100">Se connecter</button>
                                    <div id="login-error" class="text-danger mt-2" style="display: none;"></div>
                                </form>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        const loginForm = document.getElementById('login-form');
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            const loginError = document.getElementById('login-error');

            const formData = new URLSearchParams();
            formData.append('username', username);
            formData.append('password', password);

            try {
                const response = await fetch('/token', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: formData,
                });

                if (response.ok) {
                    const data = await response.json();
                    authToken = data.access_token;
                    localStorage.setItem('token', authToken);
                    renderApp();
                } else {
                    loginError.textContent = 'Nom d\'utilisateur ou mot de passe incorrect.';
                    loginError.style.display = 'block';
                }
            } catch (error) {
                loginError.textContent = 'Erreur de connexion au serveur.';
                loginError.style.display = 'block';
            }
        });
    };

    const renderApp = async () => {
        if (!authToken) {
            renderLogin();
            return;
        }

        app.innerHTML = `
            <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
                <div class="container-fluid">
                    <a class="navbar-brand" href="#">Gestion de Magasin</a>
                    <button id="logout-button" class="btn btn-outline-light">Déconnexion</button>
                </div>
            </nav>
            <div class="container mt-4">
                <h1>Tableau de bord</h1>
                <p>Bienvenue ! Vous êtes connecté.</p>
                <!-- Le contenu principal de l'application ira ici -->
            </div>
        `;

        const logoutButton = document.getElementById('logout-button');
        logoutButton.addEventListener('click', () => {
            authToken = null;
            localStorage.removeItem('token');
            renderLogin();
        });
    };

    // Point d'entrée de l'application
    renderApp();
});
