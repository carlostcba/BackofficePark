document.addEventListener('DOMContentLoaded', () => {
    // --- State Management ---
    const state = {
        token: localStorage.getItem('access_token'),
        user: null,
        totems: [],
        payments: {
            items: [],
            currentPage: 1,
            perPage: 10,
            startDate: null,
            endDate: null,
        },
        sellers: [], // For admin users
    };

    // --- Constants for Styles ---
    const styles = {
        btn: {
            primary: 'bg-brand text-white font-semibold py-2 px-4 rounded-md shadow-sm hover:opacity-90 transition-opacity',
            secondary: 'bg-white text-dark font-semibold py-2 px-4 rounded-md border border-dark hover:bg-neutral-100 transition-colors',
            danger: 'bg-danger text-white font-semibold py-2 px-4 rounded-md shadow-sm hover:opacity-90 transition-opacity',
            sm: 'py-1 px-2 text-sm',
        },
        badge: {
            brand: 'py-1 px-3 text-xs font-bold rounded-full bg-brand text-white',
            neutral: 'py-1 px-3 text-xs font-bold rounded-full bg-medium-gray text-white',
            success: 'py-1 px-3 text-xs font-bold rounded-full bg-green-600 text-white',
        }
    };

    // --- DOM Elements ---
    const elements = {
        logoutButton: document.getElementById('logout-button'),
        userInfo: {
            skeleton: document.getElementById('user-info-skeleton'),
            content: document.getElementById('user-info-content'),
            name: document.getElementById('user-name'),
            mpStatusBadge: document.getElementById('mp-status-badge'),
            connectMpButton: document.getElementById('connect-mp-button'),
            disconnectMpButton: document.getElementById('disconnect-mp-button'),
            mpTokensContainer: document.getElementById('mp-tokens-container'),
            mpAccessToken: document.getElementById('mp-access-token'),
            mpRefreshToken: document.getElementById('mp-refresh-token'),
            toggleAccessTokenBtn: document.getElementById('toggle-access-token'),
            toggleRefreshTokenBtn: document.getElementById('toggle-refresh-token'),
        },
        totems: {
            tableBody: document.getElementById('totems-table-body'),
            addTotemButton: document.getElementById('add-totem-button'),
        },
        payments: {
            tableBody: document.getElementById('payments-table-body'),
            pagination: document.getElementById('payments-pagination'),
            prevButton: document.getElementById('payments-prev-button'),
            nextButton: document.getElementById('payments-next-button'),
            info: {
                from: document.getElementById('payments-from'),
                to: document.getElementById('payments-to'),
                total: document.getElementById('payments-total'),
            },
            startDateFilter: document.getElementById('start-date-filter'),
            endDateFilter: document.getElementById('end-date-filter'),
            skeletonRow: document.getElementById('payments-skeleton-row'),
            emptyState: document.getElementById('payments-empty-state'),
        },
        modal: { // totem modal
            element: document.getElementById('totem-modal'),
            backdrop: document.getElementById('modal-backdrop'),
            form: document.getElementById('totem-form'),
            title: document.getElementById('totem-modal-title'),
            idInput: document.getElementById('totem-id'),
            externalPosIdInput: document.getElementById('external_pos_id'),
            locationInput: document.getElementById('location'),
            isActiveInput: document.getElementById('is_active'),
            cancelButton: document.getElementById('cancel-totem-button'),
        },
        toastContainer: document.getElementById('toast-container'),
    };

    // --- API Service ---
    async function apiService(endpoint, method = 'GET', body = null) {
        const headers = { 'Authorization': `Bearer ${state.token}` };
        if (body) {
            headers['Content-Type'] = 'application/json';
        }
        try {
            const response = await fetch(endpoint, { method, headers, body: body ? JSON.stringify(body) : null });
            if (response.status === 401) {
                localStorage.removeItem('access_token');
                window.location.href = '/';
                return;
            }
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.detail || 'Ocurrió un error en la petición.');
            }
            return data;
        } catch (error) {
            showToast(error.message, 'error');
            throw error;
        }
    }

    // --- UI Rendering ---
    function renderUserInfo() {
        elements.userInfo.skeleton.classList.add('hidden');
        elements.userInfo.content.classList.remove('hidden');
        elements.userInfo.name.textContent = state.user.name || state.user.email;

        if (state.user.mp_access_token) {
            elements.userInfo.mpStatusBadge.textContent = 'Conectado';
            elements.userInfo.mpStatusBadge.className = styles.badge.brand;
            elements.userInfo.connectMpButton.classList.add('hidden');
            elements.userInfo.disconnectMpButton.classList.remove('hidden');
            elements.userInfo.mpTokensContainer.classList.remove('hidden');
            elements.userInfo.mpAccessToken.value = state.user.mp_access_token;
            elements.userInfo.mpRefreshToken.value = state.user.mp_refresh_token;
        } else {
            elements.userInfo.mpStatusBadge.textContent = 'No Conectado';
            elements.userInfo.mpStatusBadge.className = styles.badge.neutral;
            elements.userInfo.connectMpButton.classList.remove('hidden');
            elements.userInfo.disconnectMpButton.classList.add('hidden');
            elements.userInfo.mpTokensContainer.classList.add('hidden');
        }
    }

    function renderTotemsTable() {
        const tableBody = elements.totems.tableBody;
        tableBody.innerHTML = ''; // Clear previous content
        if (state.totems.length === 0) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="4" class="text-center py-10 px-4">
                        <h4 class="text-lg font-medium text-dark">Aún no tienes tótems</h4>
                        <p class="text-sm text-medium-gray mt-1">¡Añade tu primer tótem para empezar a operar!</p>
                        <button class="${styles.btn.primary} mt-4" onclick="document.getElementById('add-totem-button').click()">Añadir Tótem</button>
                    </td>
                </tr>
            `;
            return;
        }
        state.totems.forEach(totem => {
            const row = document.createElement('tr');
            row.className = 'hover:bg-neutral-100';
            row.innerHTML = `
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-dark">${totem.external_pos_id}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-medium-gray">${totem.location || 'N/A'}</td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <span class="${totem.is_active ? styles.badge.brand : styles.badge.neutral}">${totem.is_active ? 'Activo' : 'Inactivo'}</span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                    <button class="${styles.btn.secondary} ${styles.btn.sm} edit-totem" data-id="${totem.id}">Editar</button>
                    <button class="${styles.btn.danger} ${styles.btn.sm} delete-totem" data-id="${totem.id}">Eliminar</button>
                </td>
            `;
            tableBody.appendChild(row);
        });
    }

    const renderPaymentsTable = () => {
        const { items, currentPage, perPage } = state.payments;
        const tableBody = elements.payments.tableBody;
        
        tableBody.querySelectorAll('tr:not(#payments-skeleton-row):not(#payments-empty-state)').forEach(row => row.remove());

        if (items && items.length > 0) {
            elements.payments.pagination.classList.remove('hidden');
            elements.payments.emptyState.classList.add('hidden');
            items.forEach(payment => {
                const statusBadge = payment.status === 'approved' 
                    ? `<span class="py-1 px-3 text-xs font-bold rounded-full bg-green-100 text-green-800">Aprobado</span>`
                    : `<span class="py-1 px-3 text-xs font-bold rounded-full bg-gray-100 text-gray-800">${payment.status}</span>`;

                const row = `
                    <tr class="hover:bg-gray-50">
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-600">${new Date(payment.payment_time).toLocaleString()}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">${payment.ticket_code || 'N/A'}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${payment.external_pos_id || 'N/A'}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-800 text-right font-semibold">$${parseFloat(payment.amount).toFixed(2)}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-center">${statusBadge}</td>
                    </tr>
                `;
                tableBody.insertAdjacentHTML('beforeend', row);
            });

            const from = (currentPage - 1) * perPage + 1;
            const to = from + items.length - 1;
            elements.payments.info.from.textContent = from;
            elements.payments.info.to.textContent = to;
            
            elements.payments.prevButton.disabled = currentPage === 1;
            elements.payments.nextButton.disabled = items.length < perPage;

        } else if (currentPage === 1) {
            elements.payments.pagination.classList.add('hidden');
            elements.payments.emptyState.classList.remove('hidden');
        }

        elements.payments.skeletonRow.classList.add('hidden');
    }

    // --- Components ---
    function showToast(message, type = 'success') {
        const bgColor = type === 'error' ? 'bg-danger' : 'bg-brand';
        const toast = document.createElement('div');
        toast.className = `toast ${bgColor} text-white py-2 px-4 rounded-md shadow-lg`;
        toast.textContent = message;
        elements.toastContainer.appendChild(toast);

        setTimeout(() => toast.classList.add('show'), 10);
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    const totemModal = {
        open(isEdit = false, totem = null) {
            elements.modal.form.reset();
            elements.modal.idInput.value = '';
            if (isEdit && totem) {
                elements.modal.title.textContent = 'Editar Tótem';
                elements.modal.idInput.value = totem.id;
                elements.modal.externalPosIdInput.value = totem.external_pos_id;
                elements.modal.locationInput.value = totem.location;
                elements.modal.isActiveInput.checked = totem.is_active;
            } else {
                elements.modal.title.textContent = 'Añadir Nuevo Tótem';
            }
            elements.modal.element.classList.remove('hidden');
            elements.modal.externalPosIdInput.focus();
        },
        close() {
            elements.modal.element.classList.add('hidden');
        }
    };

    // --- Event Handlers ---
    async function handleTotemFormSubmit(event) {
        event.preventDefault();
        const totemId = elements.modal.idInput.value;
        const payload = {
            external_pos_id: elements.modal.externalPosIdInput.value,
            location: elements.modal.locationInput.value,
            is_active: elements.modal.isActiveInput.checked,
            owner_id: state.user.id
        };

        try {
            if (totemId) {
                await apiService(`/totems/${totemId}`, 'PATCH', payload);
                showToast('Tótem actualizado con éxito.');
            } else {
                await apiService('/totems/', 'POST', payload);
                showToast('Tótem creado con éxito.');
            }
            totemModal.close();
            await loadInitialData(true); // Recargar solo tótems
        } catch (error) {
            // El error ya se muestra en el toast del apiService
        }
    }

    async function handleDeleteTotem(totemId) {
        if (confirm('¿Estás seguro de que quieres eliminar este tótem?')) {
            try {
                await apiService(`/totems/${totemId}`, 'DELETE');
                showToast('Tótem eliminado con éxito.');
                await loadInitialData(true);
            } catch (error) {
                // El error ya se muestra en el toast del apiService
            }
        }
    }

    async function loadPayments(page = 1, keepFilters = false) {
        const perPage = state.payments.perPage;
        const skip = (page - 1) * perPage;

        if (!keepFilters) {
            state.payments.startDate = elements.payments.startDateFilter.value || null;
            state.payments.endDate = elements.payments.endDateFilter.value || null;
        }

        let url = `/api/v1/payments/me?skip=${skip}&limit=${perPage}`;
        if (state.payments.startDate) url += `&start_date=${state.payments.startDate}`;
        if (state.payments.endDate) url += `&end_date=${state.payments.endDate}`;

        try {
            const paymentsData = await apiService(url);
            state.payments.items = paymentsData;
            state.payments.currentPage = page;
            renderPaymentsTable();
        } catch (error) {
            console.error('Error al cargar los pagos:', error);
        }
    }

    // --- Initialization ---
    async function loadInitialData(onlyTotems = false) {
        try {
            if (!onlyTotems) {
                state.user = await apiService('/sellers/me');
                renderUserInfo();
                await loadPayments(); // Carga inicial de pagos
            }
            // Totems are part of the user object, so we need to fetch the user again or have a separate endpoint
            const userWithTotems = await apiService('/sellers/me');
            state.user = userWithTotems;
            state.totems = userWithTotems.totems || [];
            renderTotemsTable();
        } catch (error) {
            console.error('Fallo crítico al cargar los datos iniciales.');
        }
    }

    function setupEventListeners() {
        if (!state.token) {
            window.location.href = '/';
            return;
        }

        elements.logoutButton.addEventListener('click', () => {
            localStorage.removeItem('access_token');
            window.location.href = '/';
        });

        elements.userInfo.connectMpButton.addEventListener('click', async () => {
            try {
                const response = await apiService('/mercadopago/authorize-url');
                if (response && response.authorization_url) {
                    window.location.href = response.authorization_url;
                }
            } catch (error) {
                console.error("Failed to get Mercado Pago authorization URL", error);
            }
        });
        
        elements.userInfo.disconnectMpButton.addEventListener('click', async () => {
            if (confirm('¿Estás seguro de que quieres desconectar tu cuenta de Mercado Pago?')) {
                try {
                    await apiService('/mercadopago/disconnect', 'GET'); // Should be GET or POST as per API
                    showToast('Cuenta de Mercado Pago desconectada.');
                    // Optimistically update UI
                    state.user.mp_access_token = null;
                    renderUserInfo();
                    // Or reload the page
                    // window.location.reload();
                } catch(error) {
                    // Toast is already shown by apiService
                }
            }
        });

        elements.userInfo.toggleAccessTokenBtn.addEventListener('click', () => {
            const input = elements.userInfo.mpAccessToken;
            const button = elements.userInfo.toggleAccessTokenBtn;
            if (input.type === 'password') {
                input.type = 'text';
                button.textContent = 'Ocultar';
            } else {
                input.type = 'password';
                button.textContent = 'Mostrar';
            }
        });

        elements.userInfo.toggleRefreshTokenBtn.addEventListener('click', () => {
            const input = elements.userInfo.mpRefreshToken;
            const button = elements.userInfo.toggleRefreshTokenBtn;
            if (input.type === 'password') {
                input.type = 'text';
                button.textContent = 'Ocultar';
            } else {
                input.type = 'password';
                button.textContent = 'Mostrar';
            }
        });

        elements.totems.addTotemButton.addEventListener('click', () => totemModal.open());
        elements.modal.cancelButton.addEventListener('click', () => totemModal.close());
        elements.modal.backdrop.addEventListener('click', () => totemModal.close());
        elements.modal.form.addEventListener('submit', handleTotemFormSubmit);

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && !elements.modal.element.classList.contains('hidden')) {
                totemModal.close();
            }
        });

        elements.totems.tableBody.addEventListener('click', async (e) => {
            const editButton = e.target.closest('.edit-totem');
            const deleteButton = e.target.closest('.delete-totem');
            if (editButton) {
                const totem = state.totems.find(t => t.id == editButton.dataset.id);
                totemModal.open(true, totem);
            }
            if (deleteButton) {
                handleDeleteTotem(deleteButton.dataset.id);
            }
        });

        elements.payments.prevButton.addEventListener('click', () => {
            if (state.payments.currentPage > 1) loadPayments(state.payments.currentPage - 1, true);
        });

        elements.payments.nextButton.addEventListener('click', () => {
            loadPayments(state.payments.currentPage + 1, true);
        });

        elements.payments.startDateFilter.addEventListener('change', () => {
            loadPayments(1); // Reinicia a la página 1 al cambiar el filtro
        });

        elements.payments.endDateFilter.addEventListener('change', () => {
            loadPayments(1); // Reinicia a la página 1 al cambiar el filtro
        });
    }

    // --- App Start ---
    async function startApp() {
        if (!state.token) {
            window.location.href = '/';
            return;
        }
        await loadInitialData();
        setupEventListeners();
    }

    startApp();
});