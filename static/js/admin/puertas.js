// Funciones para el ABM de puertas sin hardcodear

// Variables globales
let puertasData = [];
let puertaActual = null;

// --- Paginación (Puertas) ---
const DOORS_ITEMS_PER_PAGE = 10;
let doorsCurrentPage = 1;
function getDoorsTable() { return document.getElementById('doorsTable'); }
function getDoorsPaginationContainer() { return document.querySelector('.pagination'); }

function countVisibleDoorRows() {
    const table = getDoorsTable();
    if (!table) return 0;
    const rows = Array.from(table.querySelectorAll('tbody tr'));
    return rows.filter(r => r.style.display !== 'none').length;
}

function applyDoorsPagination() {
    const table = getDoorsTable();
    if (!table) return;
    const rows = Array.from(table.querySelectorAll('tbody tr'));
    let visibleIndex = 0;
    rows.forEach(row => {
        const isVisibleByFilters = row.style.display !== 'none';
        if (!isVisibleByFilters) return; // mantener ocultas las filtradas
        const start = (doorsCurrentPage - 1) * DOORS_ITEMS_PER_PAGE;
        const end = start + DOORS_ITEMS_PER_PAGE;
        if (visibleIndex >= start && visibleIndex < end) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
        visibleIndex++;
    });

// Exponer para que otras partes (ordenamiento genérico) puedan refrescar paginación si lo necesitan
window.refreshDoorsPagination = refreshDoorsPagination;
}

function renderDoorsPagination() {
    const container = getDoorsPaginationContainer();
    const table = getDoorsTable();
    if (!container || !table) return;
    const totalVisible = countVisibleDoorRows();
    const totalPages = Math.max(1, Math.ceil(totalVisible / DOORS_ITEMS_PER_PAGE));
    if (doorsCurrentPage > totalPages) doorsCurrentPage = totalPages;

    container.innerHTML = '';

    const createBtn = (label, page, disabled = false, active = false) => {
        const btn = document.createElement('button');
        btn.className = `btn-page ${active ? 'active' : ''}`.trim();
        btn.innerHTML = label;
        btn.disabled = disabled;
        btn.addEventListener('click', () => {
            doorsCurrentPage = page;
            applyDoorsPagination();
            renderDoorsPagination();
        });
        return btn;
    };

    // Prev
    container.appendChild(createBtn('<i class="fas fa-chevron-left"></i>', Math.max(1, doorsCurrentPage - 1), doorsCurrentPage === 1));
    // Numbered pages
    for (let i = 1; i <= totalPages; i++) {
        container.appendChild(createBtn(String(i), i, false, i === doorsCurrentPage));
    }
    // Next
    container.appendChild(createBtn('<i class="fas fa-chevron-right"></i>', Math.min(totalPages, doorsCurrentPage + 1), doorsCurrentPage === totalPages));
}

function refreshDoorsPagination() {
    const table = getDoorsTable();
    const container = getDoorsPaginationContainer();
    if (!table || !container) return;
    doorsCurrentPage = 1;
    renderDoorsPagination();
    applyDoorsPagination();
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    inicializarPuertas();
    // Construir paginación inicial en base a las filas presentes (server o cliente)
    setTimeout(refreshDoorsPagination, 0);
});

// Función para inicializar la tabla de puertas
async function inicializarPuertas() {
    await cargarPuertas();
    configurarEventos();
}

// Cargar todas las puertas desde el servidor
async function cargarPuertas() {
    try {
        const response = await fetch('/api/puertas');
        if (!response.ok) throw new Error('Error al cargar puertas');
        
        const data = await response.json();
        // Aceptar tanto {success, puertas} como un array plano
        if (Array.isArray(data)) {
            puertasData = data;
        } else if (data && Array.isArray(data.puertas)) {
            puertasData = data.puertas;
        } else {
            puertasData = [];
            console.error('Respuesta inesperada de /api/puertas:', data);
        }
        renderizarTablaPuertas();
    } catch (error) {
        console.error('Error:', error);
        alert('Error al cargar las puertas');
    }
}

// Renderizar la tabla de puertas
function renderizarTablaPuertas() {
    const tbody = document.querySelector('#doorsTable tbody');
    if (!tbody) {
        console.error('No se encontró el tbody de la tabla de puertas');
        return;
    }
    
    // No hacemos nada si ya hay datos renderizados por el servidor
    if (document.querySelectorAll('#doorsTable tbody tr').length > 0) {
        // Aun así, asegurar paginación inicial
        refreshDoorsPagination();
        return;
    }
    
    // Solo renderizamos si no hay filas en la tabla
    if (puertasData.length > 0) {
        tbody.innerHTML = '';
        puertasData.forEach(puerta => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${puerta.nombre || ''}</td>
                <td>
                    <span class="status-badge ${puerta.estado === 'activa' ? 'active' : 'inactive'}">
                        ${puerta.estado === 'activa' ? 'Activa' : 'Inactiva'}
                    </span>
                </td>
                <td>${formatearFecha(puerta.fecha_creacion || '')}</td>
                <td>
                    ${puerta.imagen ? 
                        `<img src="${puerta.imagen}" alt="${puerta.nombre || ''}" class="door-image" onclick="verImagen('${puerta.imagen}', '${puerta.nombre || ''}')">` : 
                        '<i class="fas fa-door-open" style="font-size: 24px; color: #666;"></i>'
                    }
                </td>
                <td>
                    <div class="action-buttons">
                        <button class="btn-edit" onclick="editarPuerta(${puerta.id})" title="Editar">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn-delete" onclick="confirmarEliminar(${puerta.id})" title="Eliminar">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            `;
            tbody.appendChild(tr);
        });
        // Aplicar paginación tras renderizar
        refreshDoorsPagination();
    }
}

// Formatear fecha para mostrar
function formatearFecha(fecha) {
    const date = new Date(fecha);
    return date.toLocaleDateString('es-ES', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    });
}

// Configurar eventos de los botones
function configurarEventos() {
    // Botón agregar puerta
    document.getElementById('addDoorButton').addEventListener('click', abrirModalAgregar);
    
    // Botones del modal
    document.getElementById('cancelForm').addEventListener('click', cerrarModal);
    document.getElementById('saveDoor').addEventListener('click', guardarPuerta);
    
    // Cerrar modales al hacer clic en la X
    document.querySelectorAll('.close').forEach(closeBtn => {
        closeBtn.addEventListener('click', cerrarModal);
    });
    
    // Búsqueda en tiempo real
    document.getElementById('searchInput').addEventListener('input', filtrarPuertas);
    
    // Filtro de estado
    document.getElementById('permitDoorFilter').addEventListener('change', filtrarPuertas);
}

// Abrir modal para agregar nueva puerta
function abrirModalAgregar() {
    puertaActual = null;
    document.getElementById('modalTitle').textContent = 'Registrar Nueva Puerta';
    document.getElementById('doorForm').reset();
    document.getElementById('doorFormModal').style.display = 'block';
}

// Abrir modal para editar puerta
async function editarPuerta(id) {
    puertaActual = puertasData.find(p => p.id === id);
    if (!puertaActual) return;
    
    document.getElementById('modalTitle').textContent = 'Editar Puerta';
    document.getElementById('doorName').value = puertaActual.nombre;
    
    // Limpiar el input de archivo
    document.getElementById('doorImg').value = '';
    
    document.getElementById('doorFormModal').style.display = 'block';
}

// Cerrar modal
function cerrarModal() {
    document.getElementById('doorFormModal').style.display = 'none';
    document.getElementById('deleteModal').style.display = 'none';
    document.getElementById('imageDisplayModal').style.display = 'none';
}

// Guardar o actualizar puerta
async function guardarPuerta() {
    const form = document.getElementById('doorForm');
    const formData = new FormData(form);
    const btnGuardar = document.getElementById('saveDoor');
    
    // Validar campos requeridos
    const nombre = formData.get('nombre');
    if (!nombre) {
        showAlert('El nombre es requerido', 'error');
        return;
    }
    
    // Mostrar indicador de carga
    btnGuardar.disabled = true;
    btnGuardar.textContent = 'Guardando...';
    
    try {
        let response;
        if (puertaActual) {
            // Actualizar puerta existente
            // Si hay un archivo, usamos FormData, de lo contrario usamos JSON
            const tieneArchivo = formData.get('imagen')?.size > 0;
            
            if (tieneArchivo) {
                // Para actualizar con archivo, usamos FormData
                response = await fetch(`/api/puertas/${puertaActual.id}`, {
                    method: 'PUT',
                    body: formData
                });
            } else {
                // Para actualizar sin archivo, usamos JSON
                const datos = Object.fromEntries(formData);
                // Eliminar la imagen del objeto si no hay archivo nuevo
                if (!datos.imagen) delete datos.imagen;
                
                response = await fetch(`/api/puertas/${puertaActual.id}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(datos)
                });
            }
        } else {
            // Crear nueva puerta
            response = await fetch('/api/puertas', {
                method: 'POST',
                body: formData
            });
        }

        const data = await response.json();
        
        if (data.success) {
            // Cerrar el modal
            document.getElementById('doorFormModal').style.display = 'none';
            
            // Mostrar mensaje de éxito
            showAlert(puertaActual ? 'Puerta actualizada correctamente' : 'Puerta creada correctamente', 'success');
            
            // Recargar la lista de puertas
            await cargarPuertas();
            
            // Limpiar la puerta actual
            puertaActual = null;
        } else {
            throw new Error(data.message || 'Error al guardar la puerta');
        }
    } catch (error) {
        console.error('Error:', error);
        showAlert(error.message || 'Error al guardar la puerta', 'error');
    } finally {
        // Restaurar el botón
        btnGuardar.disabled = false;
        btnGuardar.textContent = 'Guardar';
    }
}

// Confirmar eliminación de puerta
function confirmarEliminar(id) {
    puertaActual = puertasData.find(p => p.id === id);
    if (!puertaActual) return;
    
    document.getElementById('deleteModal').style.display = 'block';
}

// Eliminar puerta
async function eliminarPuerta() {
    if (!puertaActual) return;
    
    try {
        const response = await fetch(`/api/puertas/${puertaActual.id}`, {
            method: 'DELETE',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        });
        
        // Verificar si la respuesta es JSON
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.error || 'Error al eliminar la puerta');
            }
            cerrarModal();
            await cargarPuertas();
            showNotification('Puerta eliminada correctamente', 'success');
        } else {
            // Si la respuesta no es JSON, probablemente es un error de autenticación/permisos
            const text = await response.text();
            console.error('Respuesta inesperada del servidor:', text);
            throw new Error('Error de autenticación o permisos insuficientes');
        }
        
    } catch (error) {
        console.error('Error:', error);
        showNotification(error.message || 'Error al eliminar la puerta', 'error');
    }
}

// Ver imagen en modal
function verImagen(src, nombre) {
    document.getElementById('imageModalTitle').textContent = `Imagen: ${nombre}`;
    document.getElementById('displayedImage').src = src;
    document.getElementById('imageDisplayModal').style.display = 'block';
}

// Filtrar puertas por búsqueda y estado
function filtrarPuertas() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const estadoFiltro = document.getElementById('permitDoorFilter').value;
    
    const puertasFiltradas = puertasData.filter(puerta => {
        const coincideNombre = puerta.nombre.toLowerCase().includes(searchTerm);
        const coincideEstado = estadoFiltro === 'all' || 
                              (estadoFiltro === 'puerta1' && puerta.estado === 'activa') ||
                              (estadoFiltro === 'puerta2' && puerta.estado === 'inactiva');
        
        return coincideNombre && coincideEstado;
    });
    
    renderizarPuertasFiltradas(puertasFiltradas);
}

// Renderizar puertas filtradas
function renderizarPuertasFiltradas(puertas) {
    const tbody = document.querySelector('#doorsTable tbody');
    if (!tbody) {
        console.error('No se encontró el tbody de la tabla de puertas');
        return;
    }
    
    // Limpiar el tbody
    tbody.innerHTML = '';
    
    // Si no hay puertas, mostrar mensaje
    if (puertas.length === 0) {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td colspan="5" class="no-results">
                No se encontraron puertas que coincidan con la búsqueda
            </td>
        `;
        tbody.appendChild(tr);
        return;
    }
    
    // Renderizar las puertas filtradas
    puertas.forEach(puerta => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${puerta.nombre || ''}</td>
            <td>
                <span class="status-badge ${puerta.estado === 'activa' ? 'active' : 'inactive'}">
                    ${puerta.estado === 'activa' ? 'Activa' : 'Inactiva'}
                </span>
            </td>
            <td>${formatearFecha(puerta.fecha_creacion || '')}</td>
            <td>
                ${puerta.imagen ? 
                    `<img src="${puerta.imagen}" alt="${puerta.nombre || ''}" class="door-image" onclick="verImagen('${puerta.imagen}', '${puerta.nombre || ''}')">` : 
                    '<i class="fas fa-door-open" style="font-size: 24px; color: #666;"></i>'
                }
            </td>
            <td>
                <div class="action-buttons">
                    <button class="btn-edit" onclick="editarPuerta(${puerta.id})" title="Editar">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn-delete" onclick="confirmarEliminar(${puerta.id})" title="Eliminar">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        `;
        tbody.appendChild(tr);
    });
    // Aplicar paginación sobre el resultado filtrado
    refreshDoorsPagination();
}

// Configurar eventos adicionales cuando se carga el DOM
document.addEventListener('DOMContentLoaded', function() {
    // Configurar botón de confirmar eliminación
    document.getElementById('confirmDelete').addEventListener('click', eliminarPuerta);
    
    // Configurar botón de cancelar eliminación
    document.getElementById('cancelDelete').addEventListener('click', cerrarModal);
    
    // Cerrar modales al hacer clic fuera
    window.addEventListener('click', function(event) {
        if (event.target.classList.contains('modal')) {
            cerrarModal();
        }
    });
});
