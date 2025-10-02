document.addEventListener('DOMContentLoaded', () => {
    // --- State Management ---
    const state = {
        token: localStorage.getItem('access_token'),
        user: null,
        totems: [],
        transactions: [],
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
        },
        totems: {
            tableBody: document.getElementById('totems-table-body'),
            addTotemButton: document.getElementById('add-totem-button'),
        },
        transactions: {
            tableBody: document.getElementById('transactions-table-body'),
        },
        modal: {
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
        } else {
            elements.userInfo.mpStatusBadge.textContent = 'No Conectado';
            elements.userInfo.mpStatusBadge.className = styles.badge.neutral;
            elements.userInfo.connectMpButton.classList.remove('hidden');
            elements.userInfo.disconnectMpButton.classList.add('hidden');
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
        const skeletonRow = document.getElementById('payments-skeleton-row');
        const emptyState = document.getElementById('payments-empty-state');
        const pagination = elements.payments.pagination;

        tableBody.querySelectorAll('tr:not(#payments-skeleton-row):not(#payments-empty-state)').forEach(row => row.remove());

        if (items && items.length > 0) {
            pagination.classList.remove('hidden');
            emptyState.classList.add('hidden');
            items.forEach(payment => {
                const statusBadge = payment.status === 'approved' 
                    ? `<span class="badge ${styles.badge.success}">Aprobado</span>`
                    : `<span class="badge ${styles.badge.neutral}">${payment.status}</span>`;

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

            // Actualizar info de paginación
            const from = (currentPage - 1) * perPage + 1;
            const to = from + items.length - 1;
            elements.payments.info.from.textContent = from;
            elements.payments.info.to.textContent = to;
            // No tenemos el total, así que lo ocultamos por ahora
            // elements.payments.info.total.textContent = total; 

            elements.payments.prevButton.disabled = currentPage === 1;
            elements.payments.nextButton.disabled = items.length < perPage;

        } else if (currentPage === 1) { // Solo mostrar estado vacío en la primera página
            pagination.classList.add('hidden');
            emptyState.classList.remove('hidden');
        }

        skeletonRow.classList.add('hidden');
    }

    const renderSellersTable = () => {
        const tableBody = elements.admin.sellersTableBody;
        const skeleton = elements.admin.sellersSkeleton;
        tableBody.innerHTML = ''; // Limpiar
        tableBody.appendChild(skeleton);

        if (state.sellers.length > 0) {
            state.sellers.forEach(seller => {
                const row = `
                    <tr class="hover:bg-gray-50">
                        <td class="px-6 py-4 whitespace-nowrap">
                            <div class="text-sm font-medium text-gray-900">${seller.name}</div>
                            <div class="text-xs text-gray-500">${seller.id === state.user.id ? '(Tú)' : ''}</div>
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${seller.email}</td>
                        <td class="px-6 py-4 whitespace-nowrap"><span class="badge ${seller.role === 'admin' ? styles.badge.brand : styles.badge.neutral}">${seller.role}</span></td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${seller.totems.length}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                            <button class="btn btn--secondary btn--sm edit-seller" data-id="${seller.id}">Editar</button>
                            <button class="btn btn--danger btn--sm delete-seller" data-id="${seller.id}" ${seller.id === state.user.id ? 'disabled' : ''}>Eliminar</button>
                        </td>
                    </tr>
                `;
                tableBody.insertAdjacentHTML('beforeend', row);
            });
        } else {
            tableBody.innerHTML = `<tr><td colspan="5" class="text-center py-10">No hay otros vendedores registrados.</td></tr>`;
        }
        skeleton.classList.add('hidden');
    };

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

    const sellerModal = {
        open(isEdit = false, seller = null) {
            elements.sellerModal.form.reset();
            elements.sellerModal.idInput.value = '';
            elements.sellerModal.passwordInput.placeholder = isEdit ? 'Dejar en blanco para no cambiar' : 'Requerido';
            elements.sellerModal.passwordInput.required = !isEdit;

            if (isEdit && seller) {
                elements.sellerModal.title.textContent = 'Editar Vendedor';
                elements.sellerModal.idInput.value = seller.id;
                elements.sellerModal.nameInput.value = seller.name;
                elements.sellerModal.emailInput.value = seller.email;
                elements.sellerModal.roleInput.value = seller.role;
            } else {
                elements.sellerModal.title.textContent = 'Añadir Nuevo Vendedor';
            }
            elements.sellerModal.element.classList.remove('hidden');
            elements.sellerModal.nameInput.focus();
        },
        close() {
            elements.sellerModal.element.classList.add('hidden');
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
            owner_id: state.user.id // Crucial for creation
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
            await loadInitialData(); // Recargar todo
        } catch (error) {
            // El error ya se muestra en el toast del apiService
        }
    }

    async function handleDeleteTotem(totemId) {
        if (confirm('¿Estás seguro de que quieres eliminar este tótem?')) {
            try {
                await apiService(`/totems/${totemId}`, 'DELETE');
                showToast('Tótem eliminado con éxito.');
                await loadInitialData();
            } catch (error) {
                // El error ya se muestra en el toast del apiService
            }
        }
    }

    async function loadPayments(page = 1) {
        const perPage = state.payments.perPage;
        const skip = (page - 1) * perPage;
        try {
            const paymentsData = await apiService(`/api/v1/payments/me?skip=${skip}&limit=${perPage}`);
            state.payments.items = paymentsData;
            state.payments.currentPage = page;
            renderPaymentsTable();
        } catch (error) {
            console.error('Error al cargar los pagos:', error);
        }
    }

    // --- Initialization ---
    async function loadInitialData() {
        try {
            state.user = await apiService('/sellers/me');
            state.totems = state.user.totems || [];
            renderUserInfo();
            renderTotemsTable();
            await loadPayments(); // Carga inicial de pagos
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

        elements.totems.addTotemButton.addEventListener('click', () => totemModal.open());
        elements.modal.cancelButton.addEventListener('click', () => totemModal.close());
        elements.modal.backdrop.addEventListener('click', () => totemModal.close());
        elements.modal.form.addEventListener('submit', handleTotemFormSubmit);

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && !elements.modal.element.classList.contains('hidden')) {
                totemModal.close();
            }
        });

        // Delegación de eventos para botones de la tabla
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
            if (state.payments.currentPage > 1) loadPayments(state.payments.currentPage - 1);
        });

        elements.payments.nextButton.addEventListener('click', () => {
            loadPayments(state.payments.currentPage + 1);
        });

        elements.userInfo.disconnectMpButton.addEventListener('click', async () => {
            if (confirm('¿Estás seguro de que quieres desconectar tu cuenta de Mercado Pago?')) {
                await apiService('/mercadopago/disconnect');
                window.location.reload();
            }
        });

        // Listeners para la sección de admin (solo si el usuario es admin)
        if (state.user && state.user.role === 'admin') {
            elements.admin.addSellerButton.addEventListener('click', () => sellerModal.open());
            elements.sellerModal.cancelButton.addEventListener('click', () => sellerModal.close());
            elements.sellerModal.backdrop.addEventListener('click', () => sellerModal.close());
            elements.sellerModal.form.addEventListener('submit', handleSellerFormSubmit);

            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape' && !elements.sellerModal.element.classList.contains('hidden')) {
                    sellerModal.close();
                }
            });

            elements.admin.sellersTableBody.addEventListener('click', (e) => {
                const editButton = e.target.closest('.edit-seller');
                const deleteButton = e.target.closest('.delete-seller');
                if (editButton) {
                    const seller = state.sellers.find(s => s.id == editButton.dataset.id);
                    sellerModal.open(true, seller);
                }
                if (deleteButton) {
                    handleDeleteSeller(deleteButton.dataset.id);
                }
            });
        }
    }

    // --- App Start ---
    loadInitialData();
    setupEventListeners();
});