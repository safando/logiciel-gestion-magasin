/*!
 * Color mode toggler for Bootstrap's docs (https://getbootstrap.com/)
 * Copyright 2011-2024 The Bootstrap Authors
 * Licensed under the Creative Commons Attribution 3.0 Unported License.
 */

(() => {
    'use strict'
  
    const getStoredTheme = () => localStorage.getItem('theme')
    const setStoredTheme = theme => localStorage.setItem('theme', theme)
  
    const getPreferredTheme = () => {
      const storedTheme = getStoredTheme()
      if (storedTheme) {
        return storedTheme
      }
  
      return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
    }
  
    const setTheme = theme => {
      if (theme === 'auto' && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        document.documentElement.setAttribute('data-bs-theme', 'dark')
      } else {
        document.documentElement.setAttribute('data-bs-theme', theme)
      }
    }
  
    setTheme(getPreferredTheme())
  
    const showActiveTheme = (theme, focus = false) => {
      const themeSwitcher = document.querySelector('#bd-theme')
  
      if (!themeSwitcher) {
        return
      }
  
      const themeSwitcherText = document.querySelector('#bd-theme-text')
      const activeThemeIcon = document.querySelector('.theme-icon-active')
      const btnToActive = document.querySelector(`[data-bs-theme-value="${theme}"]`)
      const iconOfActiveBtn = btnToActive.querySelector('i').className
  
      document.querySelectorAll('[data-bs-theme-value]').forEach(element => {
        element.classList.remove('active')
        element.setAttribute('aria-pressed', 'false')
      })
  
      btnToActive.classList.add('active')
      btnToActive.setAttribute('aria-pressed', 'true')
      activeThemeIcon.className = iconOfActiveBtn
  
      if (focus) {
        themeSwitcher.focus()
      }
    }
  
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
      const storedTheme = getStoredTheme()
      if (storedTheme !== 'light' && storedTheme !== 'dark') {
        setTheme(getPreferredTheme())
      }
    })
  
    window.addEventListener('DOMContentLoaded', () => {
      showActiveTheme(getPreferredTheme())
  
      document.querySelectorAll('[data-bs-theme-value]')
        .forEach(toggle => {
          toggle.addEventListener('click', () => {
            const theme = toggle.getAttribute('data-bs-theme-value')
            setStoredTheme(theme)
            setTheme(theme)
            showActiveTheme(theme, true)
          })
        })
    })
  })()
  

// =============================================================================
// Logique de l'application
// =============================================================================
document.addEventListener('DOMContentLoaded', () => {
    const loginScreen = document.getElementById('login-screen');
    const appContent = document.getElementById('app-content');
    const loginForm = document.getElementById('login-form');
    const logoutButton = document.getElementById('logout-button');
    const mainContent = document.getElementById('main-content');
    const navLinks = document.querySelectorAll('#sidebar .nav-link');

    let authToken = null;

    // --- GESTION DE L'AUTHENTIFICATION ---

    async function handleLogin(event) {
        event.preventDefault();
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
                body: formData
            });

            if (response.ok) {
                const data = await response.json();
                authToken = data.access_token;
                showApp();
            } else {
                loginError.textContent = 'Nom d\'utilisateur ou mot de passe incorrect.';
                loginError.style.display = 'block';
            }
        } catch (error) {
            loginError.textContent = 'Erreur de connexion au serveur.';
            loginError.style.display = 'block';
        }
    }

    function handleLogout() {
        authToken = null;
        showLogin();
    }

    function showLogin() {
        loginScreen.style.display = 'block';
        appContent.style.display = 'none';
    }

    function showApp() {
        loginScreen.style.display = 'none';
        appContent.style.display = 'block';
        // Activer le premier onglet et charger son contenu
        navLinks.forEach(l => l.classList.remove('active'));
        const firstLink = document.querySelector('#sidebar .nav-link[data-tab="dashboard"]');
        firstLink.classList.add('active');
        loadTabContent('dashboard');
    }

    // Fonction fetch sécurisée qui ajoute le token
    async function secureFetch(url, options = {}) {
        const headers = { ...options.headers, 'Authorization': `Bearer ${authToken}` };
        const response = await fetch(url, { ...options, headers });

        if (response.status === 401) { // Non autorisé
            handleLogout();
            throw new Error('Session expirée. Veuillez vous reconnecter.');
        }
        return response;
    }

    loginForm.addEventListener('submit', handleLogin);
    logoutButton.addEventListener('click', handleLogout);

    // --- LOGIQUE DE L'APPLICATION PRINCIPALE ---

    // Fonction pour charger le contenu d'un onglet
    async function loadTabContent(tabName) {
        mainContent.innerHTML = '<div class="d-flex justify-content-center align-items-center" style="height: 80vh;"><div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div></div>'; // Vider et afficher un spinner

        try {
            switch (tabName) {
                case 'dashboard': await loadDashboardTab(); break;
                case 'stock': await loadStockTab(); break;
                case 'ventes': await loadVentesTab(); break;
                case 'pertes': await loadPertesTab(); break;
                case 'analyse': await loadAnalyseTab(); break;
            }
        } catch (error) {
            mainContent.innerHTML = `<div class="alert alert-danger">${error.message}</div>`;
        }
    }

    // --- Logique pour l'onglet TABLEAU DE BORD ---
    async function loadDashboardTab() {
        const response = await secureFetch('/api/dashboard');
        const kpis = await response.json();

        let topVentesHtml = kpis.top_ventes_today.map(item => `<li class="list-group-item d-flex justify-content-between align-items-center">${item.nom} <span class="badge bg-primary rounded-pill">${item.quantite_vendue}</span></li>`).join('');
        if (!topVentesHtml) topVentesHtml = "<p class='list-group-item text-muted'>Aucune vente enregistrée aujourd'hui.</p>";

        let lowStockHtml = kpis.low_stock_produits.map(item => `<li class="list-group-item d-flex justify-content-between align-items-center">${item.nom} <span class="badge bg-danger rounded-pill">${item.quantite}</span></li>`).join('');
        if (!lowStockHtml) lowStockHtml = "<p class='list-group-item text-muted'>Aucun produit en stock faible.</p>";

        let stockParProduitHtml = kpis.stock_par_produit.map(item => `<li class="list-group-item d-flex justify-content-between align-items-center">${item.nom} <span class="badge bg-secondary rounded-pill">${item.quantite}</span></li>`).join('');
        if (!stockParProduitHtml) stockParProduitHtml = "<p class='list-group-item text-muted'>Aucun produit en stock.</p>";

        mainContent.innerHTML = `
            <div class="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pt-3 pb-2 mb-3 border-bottom">
                <h1 class="h2">Tableau de Bord</h1>
            </div>
            <div class="row">
                <div class="col-md-3 mb-3">
                    <div class="card text-white bg-primary">
                        <div class="card-header">Chiffre d'Affaires (Aujourd'hui)</div>
                        <div class="card-body">
                            <h5 class="card-title">${kpis.ca_today.toFixed(2)} €</h5>
                        </div>
                    </div>
                </div>
                <div class="col-md-3 mb-3">
                    <div class="card text-white bg-success">
                        <div class="card-header">Nombre de Ventes (Aujourd'hui)</div>
                        <div class="card-body">
                            <h5 class="card-title">${kpis.ventes_today}</h5>
                        </div>
                    </div>
                </div>
                <div class="col-md-3 mb-3">
                    <div class="card text-dark bg-light">
                        <div class="card-header">Quantité Totale en Stock</div>
                        <div class="card-body">
                            <h5 class="card-title">${kpis.total_stock_quantite} unités</h5>
                        </div>
                    </div>
                </div>
                <div class="col-md-3 mb-3">
                    <div class="card text-dark bg-warning">
                        <div class="card-header">Valeur Totale du Stock</div>
                        <div class="card-body">
                            <h5 class="card-title">${kpis.total_stock_valeur.toFixed(2)} €</h5>
                        </div>
                    </div>
                </div>
            </div>

            <div class="row mt-4">
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-header">
                            <i class="bi bi-graph-up"></i> Ventes du Jour par Produit
                        </div>
                        <ul class="list-group list-group-flush">
                            ${topVentesHtml}
                        </ul>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-header text-white bg-danger">
                            <i class="bi bi-exclamation-triangle-fill"></i> Alerte Stock Faible (Moins de 5 unités)
                        </div>
                        <ul class="list-group list-group-flush">
                            ${lowStockHtml}
                        </ul>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-header">
                            <i class="bi bi-box-seam"></i> Inventaire par Produit
                        </div>
                        <ul class="list-group list-group-flush">
                            ${stockParProduitHtml}
                        </ul>
                    </div>
                </div>
            </div>
        `;
    }

    // --- Logique pour l'onglet GESTION STOCK ---
    async function loadStockTab() {
        mainContent.innerHTML = `
            <div class="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pt-3 pb-2 mb-3 border-bottom">
                <h1 class="h2">Gestion du Stock</h1>
                <div class="btn-toolbar mb-2 mb-md-0">
                    <button type="button" class="btn btn-sm btn-outline-primary" id="add-produit-btn">
                        <i class="bi bi-plus-circle"></i>
                        Ajouter un produit
                    </button>
                    <div class="btn-group ms-2">
                        <button type="button" class="btn btn-sm btn-outline-secondary dropdown-toggle" data-bs-toggle="dropdown">
                            <i class="bi bi-download"></i> Export
                        </button>
                        <ul class="dropdown-menu">
                            <li><a class="dropdown-item export-btn" href="#" data-type="stock" data-format="excel">Excel</a></li>
                            <li><a class="dropdown-item export-btn" href="#" data-type="stock" data-format="pdf">PDF</a></li>
                        </ul>
                    </div>
                </div>
            </div>
            <div class="table-responsive">
                <table class="table table-striped table-sm" id="stock-table">
                    <thead>
                        <tr>
                            <th>Nom</th>
                            <th>Prix d'achat</th>
                            <th>Prix de vente</th>
                            <th>Quantité</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        <!-- Les lignes du tableau seront insérées ici -->
                    </tbody>
                </table>
            </div>
        `;

        const response = await secureFetch('/api/produits');
        const produits = await response.json();
        const tableBody = document.querySelector('#stock-table tbody');
        tableBody.innerHTML = '';
        produits.forEach(p => {
            const row = tableBody.insertRow();
            row.innerHTML = `
                <td>${p.nom}</td>
                <td>${p.prix_achat.toFixed(2)} €</td>
                <td>${p.prix_vente.toFixed(2)} €</td>
                <td>${p.quantite}</td>
                <td>
                    <button class="btn btn-sm btn-warning edit-btn" data-id="${p.id}"><i class="bi bi-pencil-square"></i></button>
                    <button class="btn btn-sm btn-danger delete-btn" data-id="${p.id}"><i class="bi bi-trash"></i></button>
                </td>
            `;
        });
    }

    // --- Modale et logique pour AJOUTER/MODIFIER un produit ---
    function openProduitModal(produit = null) {
        const modalHTML = `
        <div class="modal fade" id="produit-modal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">${produit ? 'Modifier le produit' : 'Ajouter un produit'}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <form id="produit-form">
                            <input type="hidden" id="produit-id" value="${produit ? produit.id : ''}">
                            <div class="mb-3">
                                <label for="produit-nom" class="form-label">Nom du produit</label>
                                <input type="text" class="form-control" id="produit-nom" required value="${produit ? produit.nom : ''}">
                            </div>
                            <div class="mb-3">
                                <label for="produit-prix-achat" class="form-label">Prix d'achat (€)</label>
                                <input type="number" class="form-control" id="produit-prix-achat" required step="0.01" value="${produit ? produit.prix_achat : ''}">
                            </div>
                            <div class="mb-3">
                                <label for="produit-prix-vente" class="form-label">Prix de vente (€)</label>
                                <input type="number" class="form-control" id="produit-prix-vente" required step="0.01" value="${produit ? produit.prix_vente : ''}">
                            </div>
                            <div class="mb-3">
                                <label for="produit-quantite" class="form-label">Quantité</label>
                                <input type="number" class="form-control" id="produit-quantite" required value="${produit ? produit.quantite : '1'}">
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Annuler</button>
                        <button type="button" class="btn btn-primary" id="save-produit-btn">Enregistrer</button>
                    </div>
                </div>
            </div>
        </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        const modal = new bootstrap.Modal(document.getElementById('produit-modal'));
        modal.show();
        const modalElement = document.getElementById('produit-modal');
        modalElement.addEventListener('hidden.bs.modal', () => {
            modalElement.remove();
        });
    }

    // --- Logique pour l'onglet GESTION VENTES ---
    async function loadVentesTab() {
        const produitsResponse = await secureFetch('/api/produits');
        const produits = await produitsResponse.json();
        let options = produits.filter(p => p.quantite > 0).map(p => `<option value="${p.id}">${p.nom} (Stock: ${p.quantite})</option>`).join('');

        mainContent.innerHTML = `
            <div class="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pt-3 pb-2 mb-3 border-bottom">
                <h1 class="h2">Gestion des Ventes</h1>
            </div>
            <div class="card mb-4">
                <div class="card-header">Enregistrer une nouvelle vente</div>
                <div class="card-body">
                    <form id="vente-form">
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label for="vente-produit-id" class="form-label">Produit</label>
                                <select class="form-select" id="vente-produit-id" required>
                                    <option value="" disabled selected>Choisir un produit...</option>
                                    ${options}
                                </select>
                            </div>
                            <div class="col-md-4 mb-3">
                                <label for="vente-quantite" class="form-label">Quantité</label>
                                <input type="number" class="form-control" id="vente-quantite" value="1" min="1" required>
                            </div>
                            <div class="col-md-2 d-flex align-items-end">
                                <button type="submit" class="btn btn-primary w-100">Enregistrer</button>
                            </div>
                        </div>
                    </form>
                </div>
            </div>
            <div class="d-flex justify-content-between align-items-center">
                <h2 class="h3">Historique des Ventes</h2>
                <div class="btn-group">
                    <button type="button" class="btn btn-sm btn-outline-secondary dropdown-toggle" data-bs-toggle="dropdown">
                        <i class="bi bi-download"></i> Export
                    </button>
                    <ul class="dropdown-menu dropdown-menu-end">
                        <li><a class="dropdown-item export-btn" href="#" data-type="ventes" data-format="excel">Excel</a></li>
                        <li><a class="dropdown-item export-btn" href="#" data-type="ventes" data-format="pdf">PDF</a></li>
                    </ul>
                </div>
            </div>
            <div class="table-responsive">
                <table class="table table-striped table-sm" id="ventes-table">
                    <thead>
                        <tr>
                            <th>Produit</th>
                            <th>Quantité</th>
                            <th>Prix Total</th>
                            <th>Date</th>
                        </tr>
                    </thead>
                    <tbody></tbody>
                </table>
            </div>
        `;

        const ventesResponse = await secureFetch('/api/ventes');
        const ventes = await ventesResponse.json();
        const tableBody = document.querySelector('#ventes-table tbody');
        tableBody.innerHTML = '';
        ventes.forEach(v => {
            const row = tableBody.insertRow();
            row.innerHTML = `
                <td>${v.produit_nom}</td>
                <td>${v.quantite}</td>
                <td>${v.prix_total.toFixed(2)} €</td>
                <td>${new Date(v.date).toLocaleString('fr-FR')}</td>
            `;
        });
    }

    // --- Logique pour l'onglet GESTION PERTES ---
    async function loadPertesTab() {
        const produitsResponse = await secureFetch('/api/produits');
        const produits = await produitsResponse.json();
        let options = produits.filter(p => p.quantite > 0).map(p => `<option value="${p.id}">${p.nom} (Stock: ${p.quantite})</option>`).join('');

        mainContent.innerHTML = `
            <div class="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pt-3 pb-2 mb-3 border-bottom">
                <h1 class="h2">Gestion des Pertes</h1>
            </div>
            <div class="card mb-4">
                <div class="card-header">Enregistrer une nouvelle perte</div>
                <div class="card-body">
                    <form id="perte-form">
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label for="perte-produit-id" class="form-label">Produit</label>
                                <select class="form-select" id="perte-produit-id" required>
                                    <option value="" disabled selected>Choisir un produit...</option>
                                    ${options}
                                </select>
                            </div>
                            <div class="col-md-4 mb-3">
                                <label for="perte-quantite" class="form-label">Quantité Perdue</label>
                                <input type="number" class="form-control" id="perte-quantite" value="1" min="1" required>
                            </div>
                            <div class="col-md-2 d-flex align-items-end">
                                <button type="submit" class="btn btn-danger w-100">Enregistrer</button>
                            </div>
                        </div>
                    </form>
                </div>
            </div>
            <div class="d-flex justify-content-between align-items-center">
                <h2 class="h3">Historique des Pertes</h2>
                <div class="btn-group">
                    <button type="button" class="btn btn-sm btn-outline-secondary dropdown-toggle" data-bs-toggle="dropdown">
                        <i class="bi bi-download"></i> Export
                    </button>
                    <ul class="dropdown-menu dropdown-menu-end">
                        <li><a class="dropdown-item export-btn" href="#" data-type="pertes" data-format="excel">Excel</a></li>
                        <li><a class="dropdown-item export-btn" href="#" data-type="pertes" data-format="pdf">PDF</a></li>
                    </ul>
                </div>
            </div>
            <div class="table-responsive">
                <table class="table table-striped table-sm" id="pertes-table">
                    <thead>
                        <tr>
                            <th>Produit</th>
                            <th>Quantité</th>
                            <th>Date</th>
                        </tr>
                    </thead>
                    <tbody></tbody>
                </table>
            </div>
        `;

        const pertesResponse = await secureFetch('/api/pertes');
        const pertes = await pertesResponse.json();
        const tableBody = document.querySelector('#pertes-table tbody');
        tableBody.innerHTML = '';
        pertes.forEach(p => {
            const row = tableBody.insertRow();
            row.innerHTML = `
                <td>${p.produit_nom}</td>
                <td>${p.quantite}</td>
                <td>${new Date(p.date).toLocaleString('fr-FR')}</td>
            `;
        });
    }

    // --- Logique pour l'onglet ANALYSE FINANCIÈRE ---
    async function loadAnalyseTab() {
        mainContent.innerHTML = `
            <div class="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pt-3 pb-2 mb-3 border-bottom">
                <h1 class="h2">Analyse Financière</h1>
            </div>
            <div class="card mb-4">
                <div class="card-header">Sélectionner une période</div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-5">
                            <label for="start-date" class="form-label">Date de début</label>
                            <input type="date" id="start-date" class="form-control">
                        </div>
                        <div class="col-md-5">
                            <label for="end-date" class="form-label">Date de fin</label>
                            <input type="date" id="end-date" class="form-control">
                        </div>
                        <div class="col-md-2 d-flex align-items-end">
                            <button id="run-analysis" class="btn btn-primary w-100">Analyser</button>
                        </div>
                    </div>
                </div>
            </div>

            <div class="row">
                <div class="col-md-4">
                    <div class="card text-white bg-primary mb-3">
                        <div class="card-header">Chiffre d'Affaires</div>
                        <div class="card-body">
                            <h5 class="card-title" id="ca-value">0.00 €</h5>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card text-white bg-warning mb-3">
                        <div class="card-header">Coût des Ventes</div>
                        <div class="card-body">
                            <h5 class="card-title" id="cogs-value">0.00 €</h5>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card text-white bg-success mb-3">
                        <div class="card-header">Bénéfice Brut</div>
                        <div class="card-body">
                            <h5 class="card-title" id="benefice-value">0.00 €</h5>
                        </div>
                    </div>
                </div>
            </div>

            <div class="card">
                <div class="card-header">Évolution du Chiffre d'Affaires</div>
                <div class="card-body">
                    <canvas id="ca-chart"></canvas>
                </div>
            </div>
        `;

        const today = new Date().toISOString().split('T')[0];
        const firstDayOfMonth = new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().split('T')[0];
        document.getElementById('start-date').value = firstDayOfMonth;
        document.getElementById('end-date').value = today;

        let chart = null;

        async function runAnalysis() {
            const startDate = document.getElementById('start-date').value;
            const endDate = document.getElementById('end-date').value;
            if (!startDate || !endDate) return;

            const response = await secureFetch(`/api/analyse?start_date=${startDate}&end_date=${endDate}`);
            const data = await response.json();

            document.getElementById('ca-value').textContent = `${data.chiffre_affaires.toFixed(2)} €`;
            document.getElementById('cogs-value').textContent = `${data.cogs.toFixed(2)} €`;
            document.getElementById('benefice-value').textContent = `${data.benefice.toFixed(2)} €`;

            const ctx = document.getElementById('ca-chart').getContext('2d');
            if(chart) chart.destroy();
            chart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.graph_data.map(d => d.jour),
                    datasets: [{
                        label: 'Chiffre Affaires par Jour',
                        data: data.graph_data.map(d => d.ca_jour),
                        backgroundColor: 'rgba(54, 162, 235, 0.6)',
                        borderColor: 'rgba(54, 162, 235, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }

        document.getElementById('run-analysis').addEventListener('click', runAnalysis);
        runAnalysis();
    }

    // Écouteur d'événement global pour les clics (délégation d'événements)
    document.addEventListener('click', async (event) => {
        // Clic sur un onglet de navigation
        if (event.target.matches('#sidebar .nav-link')) {
            event.preventDefault();
            navLinks.forEach(l => l.classList.remove('active'));
            event.target.classList.add('active');
            const tab = event.target.getAttribute('data-tab');
            loadTabContent(tab);
        }

        // Bouton "Ajouter un produit"
        if (event.target.closest('#add-produit-btn')) {
            openProduitModal();
        }

        // Bouton "Enregistrer" dans la modale produit
        if (event.target.id === 'save-produit-btn') {
            const id = document.getElementById('produit-id').value;
            const produitData = {
                nom: document.getElementById('produit-nom').value,
                prix_achat: parseFloat(document.getElementById('produit-prix-achat').value),
                prix_vente: parseFloat(document.getElementById('produit-prix-vente').value),
                quantite: parseInt(document.getElementById('produit-quantite').value)
            };

            if (id) produitData.id = parseInt(id);

            const response = await secureFetch('/api/produits', {
                method: id ? 'PUT' : 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(produitData)
            });

            if (response.ok) {
                bootstrap.Modal.getInstance(document.getElementById('produit-modal')).hide();
                loadStockTab();
            } else {
                const error = await response.json();
                alert(`Erreur: ${error.detail}`);
            }
        }

        // Bouton "Supprimer" un produit
        if (event.target.closest('.delete-btn')) {
            const id = event.target.closest('.delete-btn').dataset.id;
            if (confirm("Êtes-vous sûr de vouloir supprimer ce produit ?")) {
                const response = await secureFetch(`/api/produits/${id}`, { method: 'DELETE' });
                if (response.ok) loadStockTab();
            }
        }

        // Bouton "Modifier" un produit
        if (event.target.closest('.edit-btn')) {
            const id = event.target.closest('.edit-btn').dataset.id;
            const response = await secureFetch('/api/produits');
            const produits = await response.json();
            const produit = produits.find(p => p.id == id);
            openProduitModal(produit);
        }

        // Formulaire pour ajouter une vente
        if (event.target.closest('#vente-form')) {
            event.preventDefault();
            const venteData = {
                produit_id: parseInt(document.getElementById('vente-produit-id').value),
                quantite: parseInt(document.getElementById('vente-quantite').value)
            };
            const response = await secureFetch('/api/ventes', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(venteData)
            });
            if (response.ok) loadVentesTab();
            else { const error = await response.json(); alert(`Erreur: ${error.detail}`); }
        }

        // Formulaire pour ajouter une perte
        if (event.target.closest('#perte-form')) {
            event.preventDefault();
            const perteData = {
                produit_id: parseInt(document.getElementById('perte-produit-id').value),
                quantite: parseInt(document.getElementById('perte-quantite').value)
            };
            const response = await secureFetch('/api/pertes', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(perteData)
            });
            if (response.ok) loadPertesTab();
            else { const error = await response.json(); alert(`Erreur: ${error.detail}`); }
        }

        // Boutons "Export"
        if (event.target.matches('.export-btn')) {
            event.preventDefault();
            const dataType = event.target.dataset.type;
            const fileFormat = event.target.dataset.format;
            const response = await secureFetch(`/api/export?data_type=${dataType}&file_format=${fileFormat}`);
            if(response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download = `export_${dataType}.${fileFormat === 'excel' ? 'xlsx' : 'pdf'}`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
            }
        }
    });

    // Initialisation : Montrer l'écran de connexion
    showLogin();
});