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
        loadTabContent('dashboard'); // Charger le premier onglet
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
        mainContent.innerHTML = ''; // Vider le contenu précédent

        try {
            switch (tabName) {
                case 'dashboard': await loadDashboardTab(); break;
                case 'stock': await loadStockTab(); break;
                case 'ventes': await loadVentesTab(); break;
                case 'pertes': await loadPertesTab(); break;
                case 'analyse': await loadAnalyseTab(); break;
            }
        } catch (error) {
            alert(error.message);
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
            <!-- ... (le reste du HTML du tableau de bord) ... -->
        `;
    }

    // --- Logique pour l'onglet GESTION STOCK ---
    async function loadStockTab() {
        mainContent.innerHTML = `
            <div class="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pt-3 pb-2 mb-3 border-bottom">
                <h1 class="h2">Gestion du Stock</h1>
                <div class="btn-toolbar mb-2 mb-md-0">
                    <button type="button" class="btn btn-sm btn-outline-primary" id="add-produit-btn">
                        <i class="bi bi-plus-circle"></i> Ajouter un produit
                    </button>
                    <!-- ... (boutons d'export) ... -->
                </div>
            </div>
            <div class="table-responsive">
                <table class="table table-striped table-sm" id="stock-table">...</table>
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
    function openProduitModal(produit = null) { /* ... même logique qu'avant ... */ }

    // Écouteur d'événement global pour les clics
    document.addEventListener('click', async (event) => {
        // Bouton "Enregistrer" dans la modale
        if (event.target && event.target.id === 'save-produit-btn') {
            const id = document.getElementById('produit-id').value;
            const produitData = { /* ... */ };
            const method = id ? 'PUT' : 'POST';
            const response = await secureFetch('/api/produits', {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(produitData)
            });
            if (response.ok) {
                bootstrap.Modal.getInstance(document.getElementById('produit-modal')).hide();
                loadStockTab();
            }
        }

        // Bouton "Supprimer"
        if (event.target && event.target.classList.contains('delete-btn')) {
            const id = event.target.dataset.id;
            if (confirm("Êtes-vous sûr de vouloir supprimer ce produit ?")) {
                const response = await secureFetch(`/api/produits/${id}`, { method: 'DELETE' });
                if (response.ok) loadStockTab();
            }
        }

        // Bouton "Modifier"
        if (event.target && event.target.classList.contains('edit-btn')) {
            const id = event.target.dataset.id;
            const response = await secureFetch('/api/produits');
            const produits = await response.json();
            const produit = produits.find(p => p.id == id);
            openProduitModal(produit);
        }

        // Boutons "Export"
        if (event.target && event.target.classList.contains('export-btn')) {
            event.preventDefault();
            const dataType = event.target.dataset.type;
            const fileFormat = event.target.dataset.format;
            // L'export via redirection ne fonctionnera plus à cause de l'authentification.
            // Il faut fetch les données et les télécharger manuellement.
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

    // --- Logique pour les autres onglets (Ventes, Pertes, Analyse) ---
    // ... Il faudrait adapter toutes les fonctions `load...Tab` et les formulaires
    // pour utiliser `secureFetch` au lieu de `fetch`.

    // Gestion du clic sur les onglets
    navLinks.forEach(link => {
        link.addEventListener('click', (event) => {
            event.preventDefault();
            navLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');
            const tab = link.getAttribute('data-tab');
            loadTabContent(tab);
        });
    });

    // Initialisation : Montrer l'écran de connexion
    showLogin();
});
