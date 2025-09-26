document.addEventListener("DOMContentLoaded", () => {
  // --- Referencias a elementos del DOM ---
  const menuToggle = document.getElementById("menuToggle")
  const sideNav = document.getElementById("side-nav-table")
  const navOverlay = document.getElementById("navOverlay")
  const searchInput = document.getElementById("searchInput")

  const deleteModal = document.getElementById("deleteModal")
  const deleteButtons = document.querySelectorAll(".btn-action.delete")
  const editButtons = document.querySelectorAll(".btn-action.edit")
  const closeButtons = document.querySelectorAll(".close")
  const cancelDelete = document.getElementById("cancelDelete")
  const confirmDelete = document.getElementById("confirmDelete")

  const doorFormModal = document.getElementById("doorFormModal")
  const permitFormModal = document.getElementById("permitFormModal")

  const cancelFormButtons = document.querySelectorAll(".modal-footer .btn-secondary")
  const saveUserButton = document.getElementById("saveUser")
  const saveDoorButton = document.getElementById("saveDoor")
  const savePermitButton = document.getElementById("savePermit")

  const addDoorButton = document.getElementById("addDoorButton")
  const addPermitButton = document.getElementById("addPermitButton")

  const confirmUserButtons = document.querySelectorAll(".btn-action.confirm")

  // --- Nuevos elementos para filtros ---
  const userRoleFilter = document.getElementById("userRoleFilter")
  const userInsideFilter = document.getElementById("userInsideFilter")
  const exitPermitFilter = document.getElementById("exitPermitFilter")
  const doorStatusFilter = document.getElementById("doorStatusFilter")
  const permitStatusFilter = document.getElementById("permitStatusFilter")
  const permitDoorFilter = document.getElementById("permitDoorFilter")
  const activityFilter = document.getElementById("activityFilter")
  const activityUserFilter = document.getElementById("activityUserFilter")
  const activityDoorFilter = document.getElementById("activityDoorFilter")
  const tempUserStatusFilter = document.getElementById("tempUserStatusFilter")

  // --- Nuevos elementos para modal de permisos (DNI y autocompletado) ---
  const userDNIInput = document.getElementById("userDNI")
  const userNameInput = document.getElementById("userName")
  const userSurnameInput = document.getElementById("userSurname")
  const userSuggestions = document.getElementById("userSuggestions")

  // --- Nuevos elementos para modal de imagen de puerta ---
  const imageDisplayModal = document.getElementById("imageDisplayModal")
  const displayedImage = document.getElementById("displayedImage")
  const closeImageModalButton = document.getElementById("closeImageModalButton")
  const closeImageModalIcon = document.getElementById("closeImageModal")

  let currentRow = null

  // --- Datos de ejemplo (simulados) para autocompletado y filtros ---
  const allUsersData = [
    { dni: "12345678A", name: "Juan", surname: "Pérez", userInside: true, exitPermit: false, role: "admin" },
    { dni: "87654321B", name: "María", surname: "González", userInside: false, exitPermit: true, role: "user" },
    { dni: "23456789C", name: "Carlos", surname: "Rodríguez", userInside: true, exitPermit: true, role: "user" },
    { dni: "34567890D", name: "Ana", surname: "Martínez", userInside: false, exitPermit: false, role: "guest" },
    { dni: "45678901E", name: "Pedro", surname: "Sánchez", userInside: true, exitPermit: false, role: "user" },
    { dni: "98765432Z", name: "Laura", surname: "Gómez", userInside: false, exitPermit: false, role: "guest" }, // Temp user
    { dni: "11223344Y", name: "Roberto", surname: "Fernández", userInside: false, exitPermit: false, role: "guest" }, // Temp user
    { dni: "55667788X", name: "Sofía", surname: "Díaz", userInside: false, exitPermit: false, role: "guest" }, // Temp user
  ]

  const allDoorsData = [
    { id: "puerta1", name: "Principal", status: "active", image: "puerta1.jpg" },
    { id: "puerta2", name: "Secundaria", status: "inactive", image: "puerta2.jpg" },
    { id: "puerta3", name: "Garaje", status: "active", image: "puerta3.jpg" },
  ]

  // --- Funcionalidad del menú lateral ---
  if (menuToggle && sideNav && navOverlay) {
    menuToggle.addEventListener("click", function () {
      this.classList.toggle("active")
      sideNav.classList.toggle("active")
      navOverlay.classList.toggle("active")
    })

    navOverlay.addEventListener("click", function () {
      menuToggle.classList.remove("active")
      sideNav.classList.remove("active")
      this.classList.remove("active")
    })
  }

  // Flag para evitar que applyFilters reinicie la página cuando estamos navegando por paginación
  let isPaginating = false;
  // Tabla objetivo explícita para filtros cuando se navega por paginación
  let currentTableForFilters = null;

  // --- Paginación (Actividad de todos los usuarios) ---
  const ACTIVITY_ITEMS_PER_PAGE = 5;
  let activityCurrentPage = 1;
  const activityTable = document.getElementById("activityTable");
  function getActivityPaginationContainer() {
    if (!activityTable) return null;
    const abmBox = activityTable.closest('.abm-box') || document;
    return abmBox.querySelector('.pagination');
  }

  function countVisibleActivityRows() {
    if (!activityTable) return 0;
    const rows = Array.from(activityTable.querySelectorAll('tbody tr'));
    return rows.filter(r => r.dataset.filterVisible !== '0').length;
  }

  function applyActivityPagination() {
    if (!activityTable) return;
    const rows = Array.from(activityTable.querySelectorAll('tbody tr'));
    let visibleIndex = 0;
    rows.forEach(row => {
      const isVisibleByFilters = row.dataset.filterVisible !== '0';
      if (!isVisibleByFilters) { row.style.display = 'none'; return; }
      const start = (activityCurrentPage - 1) * ACTIVITY_ITEMS_PER_PAGE;
      const end = start + ACTIVITY_ITEMS_PER_PAGE;
      if (visibleIndex >= start && visibleIndex < end) {
        row.style.display = '';
      } else {
        row.style.display = 'none';
      }
      visibleIndex++;
    });
  }

  function renderActivityPagination() {
    const container = getActivityPaginationContainer();
    if (!activityTable || !container) return;
    const totalVisible = countVisibleActivityRows();
    const totalPages = Math.max(1, Math.ceil(totalVisible / ACTIVITY_ITEMS_PER_PAGE));
    if (activityCurrentPage > totalPages) activityCurrentPage = totalPages;

    container.innerHTML = '';

    const createBtn = (label, page, disabled = false, active = false) => {
      const btn = document.createElement('button');
      btn.className = `btn-page ${active ? 'active' : ''}`.trim();
      btn.innerHTML = label;
      btn.disabled = disabled;
      btn.addEventListener('click', () => {
        activityCurrentPage = page;
        // Reaplicar filtros antes de paginar para recalcular filas visibles sin reiniciar a página 1
        try { isPaginating = true; currentTableForFilters = activityTable; applyFilters(); } catch (e) {} finally { isPaginating = false; currentTableForFilters = null; }
        applyActivityPagination();
        renderActivityPagination();
      });
      return btn;
    };

    container.appendChild(createBtn('<i class="fas fa-chevron-left"></i>', Math.max(1, activityCurrentPage - 1), activityCurrentPage === 1));
    for (let i = 1; i <= totalPages; i++) {
      container.appendChild(createBtn(String(i), i, false, i === activityCurrentPage));
    }
    container.appendChild(createBtn('<i class="fas fa-chevron-right"></i>', Math.min(totalPages, activityCurrentPage + 1), activityCurrentPage === totalPages));
  }

  function refreshActivityPagination() {
    if (!activityTable) return;
    activityCurrentPage = 1;
    renderActivityPagination();
    applyActivityPagination();
  }
  // Exponer para que scripts inline puedan invocarlo tras cargar datos
  window.refreshActivityPagination = refreshActivityPagination;

  // --- Paginación (Usuarios) ---
  const USERS_ITEMS_PER_PAGE = 5;
  let usersCurrentPage = 1;
  const usersTable = document.getElementById("usersTable");
  function getUsersPaginationContainer() {
    if (!usersTable) return null;
    const abmBox = usersTable.closest('.abm-box') || document;
    return abmBox.querySelector('.pagination');
  }

  function countVisibleUserRows() {
    if (!usersTable) return 0;
    const rows = Array.from(usersTable.querySelectorAll("tbody tr"));
    return rows.filter(r => r.dataset.filterVisible !== '0').length;
  }

  function applyUsersPagination() {
    if (!usersTable) return;
    const rows = Array.from(usersTable.querySelectorAll("tbody tr"));
    let visibleIndex = 0;
    rows.forEach(row => {
      const isVisibleByFilters = row.dataset.filterVisible !== '0';
      if (!isVisibleByFilters) { row.style.display = 'none'; return; }
      // Determine if this visible row belongs to current page
      const start = (usersCurrentPage - 1) * USERS_ITEMS_PER_PAGE;
      const end = start + USERS_ITEMS_PER_PAGE;
      if (visibleIndex >= start && visibleIndex < end) {
        row.style.display = "";
      } else {
        row.style.display = "none";
      }
      visibleIndex++;
    });
  }

  function renderUsersPagination() {
    if (!usersTable) return;
    // Recompute total pages considering current filters
    const totalVisible = countVisibleUserRows();
    const totalPages = Math.max(1, Math.ceil(totalVisible / USERS_ITEMS_PER_PAGE));
    if (usersCurrentPage > totalPages) usersCurrentPage = totalPages;

    const usersPaginationContainer = getUsersPaginationContainer();
    if (!usersPaginationContainer) return;
    usersPaginationContainer.innerHTML = "";

    const createBtn = (label, page, disabled = false, active = false) => {
      const btn = document.createElement("button");
      btn.className = `btn-page ${active ? "active" : ""}`.trim();
      btn.innerHTML = label;
      btn.disabled = disabled;
      btn.addEventListener("click", () => {
        usersCurrentPage = page;
        // Reaplicar filtros antes de paginar para recalcular filas visibles sin reiniciar a página 1
        try { isPaginating = true; currentTableForFilters = usersTable; applyFilters(); } catch (e) {} finally { isPaginating = false; currentTableForFilters = null; }
        applyUsersPagination();
        renderUsersPagination();
      });
      return btn;
    };

    // Prev
    usersPaginationContainer.appendChild(
      createBtn('<i class="fas fa-chevron-left"></i>', Math.max(1, usersCurrentPage - 1), usersCurrentPage === 1)
    );

    for (let i = 1; i <= totalPages; i++) {
      usersPaginationContainer.appendChild(createBtn(String(i), i, false, i === usersCurrentPage));
    }

    // Next
    usersPaginationContainer.appendChild(
      createBtn('<i class="fas fa-chevron-right"></i>', Math.min(totalPages, usersCurrentPage + 1), usersCurrentPage === totalPages)
    );
  }

  function refreshUsersPagination() {
    if (!usersTable) return;
    // Reset to first page on filter/sort changes
    usersCurrentPage = 1;
    renderUsersPagination();
    applyUsersPagination();
  }

  // --- Paginación (Permisos) ---
  const PERMITS_ITEMS_PER_PAGE = 5;
  let permitsCurrentPage = 1;
  const permitsTable = document.getElementById("permitsTable");
  // Nota: cada vista tiene su propio contenedor .pagination. Seleccionamos el más cercano a la tabla.
  function getPermitsPaginationContainer() {
    if (!permitsTable) return null;
    // Buscar el contenedor .pagination dentro del mismo .abm-box
    const abmBox = permitsTable.closest('.abm-box') || document;
    return abmBox.querySelector('.pagination');
  }

  function countVisiblePermitRows() {
    if (!permitsTable) return 0;
    const rows = Array.from(permitsTable.querySelectorAll("tbody tr"));
    return rows.filter(r => r.dataset.filterVisible !== '0').length;
  }

  function applyPermitsPagination() {
    if (!permitsTable) return;
    const rows = Array.from(permitsTable.querySelectorAll("tbody tr"));
    let visibleIndex = 0;
    rows.forEach(row => {
      const isVisibleByFilters = row.dataset.filterVisible !== '0';
      if (!isVisibleByFilters) { row.style.display = 'none'; return; } // mantener ocultas las filtradas
      const start = (permitsCurrentPage - 1) * PERMITS_ITEMS_PER_PAGE;
      const end = start + PERMITS_ITEMS_PER_PAGE;
      if (visibleIndex >= start && visibleIndex < end) {
        row.style.display = "";
      } else {
        row.style.display = "none";
      }
      visibleIndex++;
    });
  }

  function renderPermitsPagination() {
    const container = getPermitsPaginationContainer();
    if (!permitsTable || !container) return;
    const totalVisible = countVisiblePermitRows();
    const totalPages = Math.max(1, Math.ceil(totalVisible / PERMITS_ITEMS_PER_PAGE));
    if (permitsCurrentPage > totalPages) permitsCurrentPage = totalPages;

    container.innerHTML = "";

    const createBtn = (label, page, disabled = false, active = false) => {
      const btn = document.createElement("button");
      btn.className = `btn-page ${active ? "active" : ""}`.trim();
      btn.innerHTML = label;
      btn.disabled = disabled;
      btn.addEventListener("click", () => {
        permitsCurrentPage = page;
        // Reaplicar filtros antes de paginar para recalcular filas visibles sin reiniciar a página 1
        try { isPaginating = true; currentTableForFilters = permitsTable; applyFilters(); } catch (e) {} finally { isPaginating = false; currentTableForFilters = null; }
        applyPermitsPagination();
        renderPermitsPagination();
      });
      return btn;
    };

    // Prev
    container.appendChild(
      createBtn('<i class="fas fa-chevron-left"></i>', Math.max(1, permitsCurrentPage - 1), permitsCurrentPage === 1)
    );
    // Número de páginas
    for (let i = 1; i <= totalPages; i++) {
      container.appendChild(createBtn(String(i), i, false, i === permitsCurrentPage));
    }
    // Next
    container.appendChild(
      createBtn('<i class="fas fa-chevron-right"></i>', Math.min(totalPages, permitsCurrentPage + 1), permitsCurrentPage === totalPages)
    );
  }

  function refreshPermitsPagination() {
    if (!permitsTable) return;
    permitsCurrentPage = 1;
    renderPermitsPagination();
    applyPermitsPagination();
  }

  // --- Funcionalidad de Filtrado General ---
  const applyFilters = () => {
    const currentTable = currentTableForFilters || document.querySelector(".users-table")
    if (!currentTable) return

    const rows = currentTable.querySelectorAll("tbody tr")
    const searchTerm = searchInput ? searchInput.value.toLowerCase() : ""

    rows.forEach((row) => {
      let isVisible = true
      const rowText = row.textContent.toLowerCase()

      // Search filter
      if (searchTerm && !rowText.includes(searchTerm)) {
        isVisible = false
      }

      // Specific table filters
      const tableId = currentTable.id
      if (tableId === "usersTable") {
        const role = row.cells[0].querySelector(".badge").textContent.toLowerCase()
        const userInside = row.cells[4].textContent.trim().toLowerCase() === "sí"
        const exitPermit = row.cells[5].textContent.trim().toLowerCase() === "sí"

        if (userRoleFilter && userRoleFilter.value !== "all" && role !== userRoleFilter.value) {
          isVisible = false
        }
        if (userInsideFilter && userInsideFilter.value !== "all") {
          const filterValue = userInsideFilter.value === "true"
          if (userInside !== filterValue) {
            isVisible = false
          }
        }
        if (exitPermitFilter && exitPermitFilter.value !== "all") {
          const filterValue = exitPermitFilter.value === "true"
          if (exitPermit !== filterValue) {
            isVisible = false
          }
        }
      } else if (tableId === "doorsTable") {
        const status = row.cells[1].querySelector(".status-badge").textContent.toLowerCase()
        if (doorStatusFilter && doorStatusFilter.value !== "all" && status !== doorStatusFilter.value) {
          isVisible = false
        }
      } else if (tableId === "permitsTable") {
        const status = row.cells[0].querySelector(".status-badge").textContent.toLowerCase()
        const door = row.cells[1].textContent.trim().toLowerCase()
        if (permitStatusFilter && permitStatusFilter.value !== "all" && status !== permitStatusFilter.value) {
          isVisible = false
        }
        if (permitDoorFilter && permitDoorFilter.value !== "all" && door !== permitDoorFilter.value) {
          isVisible = false
        }
      } else if (tableId === "activityTable") {
        const activityType = row.cells[3].querySelector(".activity-badge").textContent.toLowerCase()
        const user = row.cells[0].textContent.trim().toLowerCase()
        const door = row.cells[1].textContent.trim().toLowerCase()
        if (activityFilter && activityFilter.value !== "all" && activityType !== activityFilter.value) {
          isVisible = false
        }
        if (
          activityUserFilter &&
          activityUserFilter.value !== "all" &&
          user !== activityUserFilter.value.toLowerCase()
        ) {
          isVisible = false
        }
        if (
          activityDoorFilter &&
          activityDoorFilter.value !== "all" &&
          door !== activityDoorFilter.value.toLowerCase()
        ) {
          isVisible = false
        }
      } else if (tableId === "temporaryUsersTable") {
        const status = row.cells[3].querySelector(".badge").textContent.toLowerCase()
        if (tempUserStatusFilter && tempUserStatusFilter.value !== "all" && status !== tempUserStatusFilter.value) {
          isVisible = false
        }
      }

      row.style.display = isVisible ? "" : "none"
      // Guardar visibilidad por filtros para que la paginación no la pierda
      row.dataset.filterVisible = isVisible ? '1' : '0'
    })

    // Aplicar paginación sobre el resultado filtrado, pero no reiniciar página si estamos navegando
    if (!isPaginating) {
      if (currentTable.id === "usersTable") {
        refreshUsersPagination();
      } else if (currentTable.id === "permitsTable") {
        refreshPermitsPagination();
      } else if (currentTable.id === "activityTable") {
        refreshActivityPagination();
      }
    } else {
      // Si estamos paginando, solo aplicar la paginación vigente sin resetear a página 1
      if (currentTable.id === "usersTable") {
        applyUsersPagination();
      } else if (currentTable.id === "permitsTable") {
        applyPermitsPagination();
      } else if (currentTable.id === "activityTable") {
        applyActivityPagination();
      }
    }
  }

  // Attach filter event listeners
  if (searchInput) searchInput.addEventListener("input", applyFilters)
  document.querySelectorAll(".select-box select, .filter-select").forEach((select) => {
    select.addEventListener("change", applyFilters)
  })
  document.querySelectorAll(".btn-filter").forEach((button) => {
    button.addEventListener("click", applyFilters)
  })

  // --- Ordenar tabla al hacer clic en los encabezados ---
  const tableHeaders = document.querySelectorAll("th[data-sort]")
  tableHeaders.forEach((header) => {
    header.addEventListener("click", function () {
      const column = this.getAttribute("data-sort")
      const columnIndex = Array.from(this.parentNode.children).indexOf(this)

      const currentDirection = this.getAttribute("data-direction") || "asc"
      const newDirection = currentDirection === "asc" ? "desc" : "asc"

      const currentTableHeaders = this.closest("table").querySelectorAll("th[data-sort]")
      currentTableHeaders.forEach((th) => th.removeAttribute("data-direction"))
      this.setAttribute("data-direction", newDirection)

      currentTableHeaders.forEach((th) => {
        const icon = th.querySelector("i")
        if (icon) {
          icon.className = "fas fa-sort"
        }
      })

      const icon = this.querySelector("i")
      if (icon) {
        icon.className = `fas fa-sort-${newDirection === "asc" ? "up" : "down"}`
      }

      const tbody = this.closest("table").querySelector("tbody")
      const rows = Array.from(tbody.querySelectorAll("tr"))

      rows.sort((a, b) => {
        let aValue, bValue
        const tableId = this.closest("table").id

        if (tableId === "usersTable" && (column === "interno" || column === "permisoSalida")) {
          aValue = a.cells[columnIndex].textContent.trim().toLowerCase() === "sí"
          bValue = b.cells[columnIndex].textContent.trim().toLowerCase() === "sí"
        } else if (tableId === "doorsTable" && column === "status") {
          aValue = a.cells[columnIndex].textContent.includes("Activa")
          bValue = b.cells[columnIndex].textContent.includes("Activa")
        } else if (tableId === "permitsTable" && column === "status") {
          aValue = a.cells[columnIndex].textContent.includes("Activa")
          bValue = b.cells[columnIndex].textContent.includes("Activa")
        } else if (tableId === "temporaryUsersTable" && column === "estado") {
          aValue = a.cells[columnIndex].textContent.includes("Pendiente")
          bValue = b.cells[columnIndex].textContent.includes("Pendiente")
        } else {
          aValue = a.cells[columnIndex].textContent.trim()
          bValue = b.cells[columnIndex].textContent.trim()
        }

        if (aValue < bValue) {
          return newDirection === "asc" ? -1 : 1
        }
        if (aValue > bValue) {
          return newDirection === "asc" ? 1 : -1
        }
        return 0
      })

      rows.forEach((row) => tbody.appendChild(row))

      // Si se ordena en la tabla de usuarios/permisos/actividad, refrescar paginación
      const tableEl = this.closest("table");
      if (tableEl && tableEl.id === "usersTable") {
        refreshUsersPagination();
      } else if (tableEl && tableEl.id === "permitsTable") {
        refreshPermitsPagination();
      } else if (tableEl && tableEl.id === "activityTable") {
        refreshActivityPagination();
      }
    })
  })

  // --- Inicializar la paginación (Usuarios) ---
  if (usersTable && getUsersPaginationContainer()) {
    // Asegurar flags de visibilidad por filtros antes de la primera paginación
    try { isPaginating = true; currentTableForFilters = usersTable; applyFilters(); } catch (e) {} finally { isPaginating = false; currentTableForFilters = null; }
    refreshUsersPagination();
  }

  // --- Inicializar la paginación (Permisos) ---
  if (permitsTable && getPermitsPaginationContainer()) {
    // Asegurar flags de visibilidad por filtros antes de la primera paginación
    try { isPaginating = true; currentTableForFilters = permitsTable; applyFilters(); } catch (e) {} finally { isPaginating = false; currentTableForFilters = null; }
    refreshPermitsPagination();
  }

  // --- Inicializar la paginación (Actividad) ---
  if (activityTable && getActivityPaginationContainer()) {
    // Si las filas se cargan dinámicamente luego, observa cambios y refresca
    const activityBody = activityTable.querySelector('tbody');
    if (activityBody) {
      const mo = new MutationObserver(() => {
        // Asegurar que las filas nuevas tengan flags de visibilidad de filtros
        try { isPaginating = true; applyFilters(); } catch (e) {} finally { isPaginating = false; }
        refreshActivityPagination();
      });
      mo.observe(activityBody, { childList: true });
    }
    // Intento inicial por si ya hay filas
    try { applyFilters(); } catch (e) {}
    refreshActivityPagination();
  }

  // --- Funcionalidad para los modales y botones de acción (Eliminar) ---
  if (deleteButtons.length > 0 && deleteModal) {
    deleteButtons.forEach((button) => {
      button.addEventListener("click", function () {
        currentRow = this.closest("tr")
        deleteModal.style.display = "flex"
      })
    })

    closeButtons.forEach((button) => {
      button.addEventListener("click", function () {
        const modal = this.closest(".modal")
        if (modal) {
          modal.style.display = "none"
        }
      })
    })

    window.addEventListener("click", (event) => {
      if (event.target.classList.contains("modal")) {
        event.target.style.display = "none"
      }
    })

    if (cancelDelete) {
      cancelDelete.addEventListener("click", () => {
        deleteModal.style.display = "none"
      })
    }

    if (confirmDelete) {
      confirmDelete.addEventListener("click", async () => {
        if (currentRow) {
          const userId = currentRow.dataset.userId || currentRow.dataset.id
          
          // Actualizar en el servidor
          await handleDeleteUser(userId, currentRow)
        }
        deleteModal.style.display = "none"
      })
    }
  }

  // --- Funcionalidad para editar (Modificar) ---
  if (editButtons.length > 0) {
    editButtons.forEach((button) => {
      button.addEventListener("click", function () {
        currentRow = this.closest("tr")
        const tableId = this.closest("table").id

        if (tableId === "usersTable" && userFormModal) {
          const cells = currentRow.querySelectorAll("td")
          document.getElementById("role").value = cells[0].querySelector(".badge").textContent.toLowerCase()
          document.getElementById("name").value = cells[1].textContent.trim()
          document.getElementById("surname").value = cells[2].textContent.trim()
          document.getElementById("dni").value = cells[3].textContent.trim()
          document.getElementById("modalTitle").textContent = "Modificar Usuario"
          userFormModal.style.display = "flex"
        } else if (tableId === "doorsTable" && doorFormModal) {
          const cells = currentRow.querySelectorAll("td")
          document.getElementById("doorName").value = cells[0].textContent.trim()
          document.getElementById("modalTitle").textContent = "Modificar Puerta"
          doorFormModal.style.display = "flex"
        } else if (tableId === "permitsTable" && permitFormModal) {
          const cells = currentRow.querySelectorAll("td")
          document.getElementById("doorId").value = cells[1].textContent.trim()
          document.getElementById("timeLimit").value = cells[5].textContent.trim()

          const userFullName = cells[3].textContent.trim()
          const foundUser = allUsersData.find((u) => `${u.name} ${u.surname}` === userFullName)
          if (foundUser) {
            userDNIInput.value = foundUser.dni
            userNameInput.value = foundUser.name
            userSurnameInput.value = foundUser.surname
            userNameInput.readOnly = true
            userSurnameInput.readOnly = true
          } else {
            userDNIInput.value = ""
            userNameInput.value = ""
            userSurnameInput.value = ""
            userNameInput.readOnly = false
            userSurnameInput.readOnly = false
          }

          document.getElementById("modalTitle").textContent = "Modificar Permiso"
          permitFormModal.style.display = "flex"
        }
      })
    })
  }

  // --- Guardar Usuario (para usuarios.html) ---
  if (saveUserButton) {
    saveUserButton.addEventListener("click", async () => {
      const role = document.getElementById("role").value;
      const name = document.getElementById("name").value;
      const surname = document.getElementById("surname").value;
      const dni = document.getElementById("dni").value;

      if (!name || !surname || !dni) {
        alert("Por favor complete todos los campos obligatorios");
        return;
      }

      try {
        if (currentRow) {
          const userId = currentRow.querySelector("[data-user-id]").getAttribute("data-user-id");
          
          // Actualizar en el servidor
          await actualizarUsuarioEnServidor(userId, {
            name,
            surname,
            dni,
            role
          });

          // Actualizar la interfaz
          const cells = currentRow.querySelectorAll("td");
          cells[0].innerHTML = `<span class="badge ${role}">${role.charAt(0).toUpperCase() + role.slice(1)}</span>`;
          cells[1].textContent = name;
          cells[2].textContent = surname;
          cells[3].textContent = dni;

          showNotification("Usuario actualizado correctamente", "success");
          userFormModal.style.display = "none";
        } else {
          // Lógica para añadir nuevo usuario (si se implementa un botón de añadir en usuarios.html)
          const usersTableBody = document.querySelector("#usersTable tbody");
          const newRow = usersTableBody.insertRow();
          newRow.innerHTML = `
            <td><span class="badge ${role}">${role.charAt(0).toUpperCase() + role.slice(1)}</span></td>
            <td>${name}</td>
            <td>${surname}</td>
            <td>${dni}</td>
            <td></td>
            <td class="actions">
                <button class="btn-action delete" title="Eliminar"><i class="fas fa-trash"></i></button>
                <button class="btn-action edit" title="Modificar"><i class="fas fa-edit"></i></button>
            </td>
          `;
          attachTableActionListeners(newRow);
          showNotification("Usuario registrado correctamente", "success");
          userFormModal.style.display = "none";
        }
      } catch (error) {
        console.error("Error al guardar el usuario:", error);
        showNotification("Error al guardar el usuario. Por favor, intente nuevamente.", "error");
      }
    });
  }

  // --- Guardar Puerta (para puerta.html) ---
  if (saveDoorButton) {
    saveDoorButton.addEventListener("click", () => {
      const doorName = document.getElementById("doorName").value
      const doorImgFile = document.getElementById("doorImg").files[0]

      if (!doorName) {
        alert("Por favor complete el nombre de la puerta")
        return
      }

      if (currentRow) {
        const cells = currentRow.querySelectorAll("td")
        cells[0].textContent = doorName
        if (doorImgFile) {
          cells[3].textContent = doorImgFile.name
          cells[3].setAttribute("data-img", doorImgFile.name) // Update data attribute
        }
      } else {
        const newRow = document.createElement("tr")
        const today = new Date().toISOString().split("T")[0]
        const imgFileName = doorImgFile ? doorImgFile.name : "puerta_default.jpg"

        newRow.innerHTML = `
                    <td>${doorName}</td>
                    <td>${today}</td>
                    <td><span class="door-img" data-img="${imgFileName}">${imgFileName}</span></td>
                    <td class="actions">
                        <button class="btn-action delete" title="Eliminar"><i class="fas fa-trash"></i></button>
                        <button class="btn-action edit" title="Modificar"><i class="fas fa-edit"></i></button>
                    </td>
                `
        document.querySelector("#doorsTable tbody").appendChild(newRow)
        attachTableActionListeners(newRow)
      }
      doorFormModal.style.display = "none"
    })
  }

  // --- Guardar Permiso (para permisos.html) - VERSIÓN CON BASE DE DATOS ---
  if (savePermitButton) {
    savePermitButton.addEventListener("click", async () => {
      const doorId = document.getElementById("doorId").value
      const userDNI = userDNIInput.value.trim()
      const userName = userNameInput.value.trim()
      const userSurname = userSurnameInput.value.trim()
      const timeLimit = document.getElementById("timeLimit").value

      if (!doorId || !userDNI || !userName || !userSurname || !timeLimit) {
        showNotification("Por favor complete todos los campos", "error")
        return
      }

      if (!currentUserData) {
        showNotification("Usuario no válido. Busque un usuario existente por DNI.", "error")
        return
      }

      // Mostrar loading
      savePermitButton.disabled = true
      savePermitButton.textContent = "Guardando..."

      try {
        // Handle permanent permission case
        const tiempoMinutos = timeLimit === 'permanent' ? 0 : parseInt(timeLimit);
        console.log('Creating permission with:', { 
          userData: currentUserData, 
          doorId, 
          timeLimit,
          tiempoMinutos
        });
        
        const resultado = await crearPermiso(currentUserData, doorId, tiempoMinutos)
        console.log('Permission creation result:', resultado);
        
        if (resultado.success) {
          showNotification("Permiso creado exitosamente", "success")
          
          // Recargar la página para mostrar el nuevo permiso
          setTimeout(() => {
            window.location.reload()
          }, 1500)
        } else {
          showNotification("Error al crear permiso: " + resultado.error, "error")
        }
      } catch (error) {
        showNotification("Error de conexión al crear permiso", "error")
      } finally {
        savePermitButton.disabled = false
        savePermitButton.textContent = "Guardar"
        permitFormModal.style.display = "none"
      }
    })
  }

  // --- Cancelar formulario (general para todos los modales de formulario) ---
  cancelFormButtons.forEach((button) => {
    button.addEventListener("click", function () {
      const modal = this.closest(".modal")
      if (modal) {
        modal.style.display = "none"
      }
    })
  })

  // --- Abrir modales de registro ---
  if (addDoorButton && doorFormModal) {
    addDoorButton.addEventListener("click", () => {
      currentRow = null
      document.getElementById("doorName").value = ""
      document.getElementById("modalTitle").textContent = "Registrar Puerta"
      doorFormModal.style.display = "flex"
    })
  }

  if (addPermitButton && permitFormModal) {
    addPermitButton.addEventListener("click", async () => {
      currentRow = null
      currentUserData = null
      
      // Limpiar formulario
      userDNIInput.value = ""
      userNameInput.value = ""
      userSurnameInput.value = ""
      userSearchStatus.textContent = ""
      userNameInput.readOnly = true
      userSurnameInput.readOnly = true
      document.getElementById("timeLimit").selectedIndex = 0
      
      // Cargar puertas dinámicamente
      await cargarPuertasDisponibles()
      
      document.getElementById("modalTitle").textContent = "Otorgar Permiso"
      permitFormModal.style.display = "flex"
    })
  }

  // --- Funciones de utilidad ---
  function showNotification(message, type) {
    const notification = document.createElement("div")
    notification.className = `notification ${type}`
    notification.style.cssText = `
      position: fixed;
      top: 20px;
      right: -400px;
      background: ${type === 'success' ? '#4caf50' : type === 'error' ? '#f44336' : '#2196f3'};
      color: white;
      padding: 16px 24px;
      border-radius: 8px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
      z-index: 9999;
      transition: right 0.3s ease;
      max-width: 400px;
    `
    notification.innerHTML = `
      <div class="notification-content" style="display: flex; align-items: center; gap: 12px;">
        <i class="fas ${type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle'}"></i>
        <span>${message}</span>
      </div>
    `
    document.body.appendChild(notification)
    
    setTimeout(() => {
      notification.style.right = "20px"
      setTimeout(() => {
        notification.style.right = "-400px"
        setTimeout(() => {
          notification.remove()
        }, 300)
      }, 3000)
    }, 100)
  }

  // --- Función para manejar la eliminación de usuarios ---
  async function handleDeleteUser(userId, row) {
    try {
      const response = await fetch(`/eliminarUsuario/${userId}`, {
        method: 'DELETE',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        }
      });

      // Verificar si la respuesta es JSON
      const contentType = response.headers.get('content-type');
      let data;
      
      if (contentType && contentType.includes('application/json')) {
        data = await response.json();
      } else {
        // Si la respuesta no es JSON, obtener el texto del error
        const errorText = await response.text();
        console.error('Respuesta inesperada del servidor:', errorText);
        throw new Error('Error en la respuesta del servidor');
      }

      if (response.ok && data.success) {
        // Animación de eliminación
        row.style.backgroundColor = "#ffebee";
        setTimeout(() => {
          row.remove();
          // Mostrar notificación de éxito
          showNotification("Usuario eliminado exitosamente", "success");
        }, 300);
      } else {
        const errorMessage = data.message || 'Error al eliminar el usuario';
        showNotification(errorMessage, "error");
      }
    } catch (error) {
      console.error('Error:', error);
      showNotification(error.message || "Error de conexión al eliminar usuario", "error");
    }
  }

  // --- Función para manejar la eliminación de un permiso ---
  async function handleDeletePermission(permissionId) {
    if (!permissionId) {
      console.error('ID de permiso no proporcionado');
      return;
    }

    if (!confirm('¿Está seguro que desea eliminar este permiso?')) {
      return;
    }

    try {
      const response = await fetch(`/api/permisos/${encodeURIComponent(permissionId)}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
        },
        credentials: 'same-origin'
      });

      // Verificar si la respuesta es JSON
      const contentType = response.headers.get('content-type');
      if (!contentType || !contentType.includes('application/json')) {
        const text = await response.text();
        throw new Error(`Respuesta inesperada del servidor: ${text}`);
      }

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.message || 'Error al eliminar el permiso');
      }

      showNotification('Permiso eliminado correctamente', 'success');
      // Recargar la página para actualizar la tabla
      setTimeout(() => window.location.reload(), 1000);
    } catch (error) {
      console.error('Error al eliminar permiso:', error);
      showNotification(error.message || 'Error al eliminar el permiso', 'error');
    }
  }

  // --- Adjuntar manejadores de eventos a los botones de acción ---
  function attachTableActionListeners(row) {
    // Botón de eliminar permiso (solo para la tabla de permisos)
    const deleteBtn = row.querySelector('.btn-action.delete');
    if (deleteBtn && document.getElementById('permitsTable')) {
      deleteBtn.addEventListener('click', function(e) {
        e.stopPropagation();
        // Obtener el ID del permiso del atributo data-id del botón o de la fila
        const permissionId = this.getAttribute('data-id') || 
                            row.getAttribute('data-permission-id') ||
                            (row.cells[0] ? row.cells[0].textContent.trim() : null);
        
        if (permissionId) {
          handleDeletePermission(permissionId);
        } else {
          console.error('No se pudo encontrar el ID del permiso');
          showNotification('Error: No se pudo identificar el permiso a eliminar', 'error');
        }
      });
    }

    // Resto del código existente para otros tipos de tablas...
    // Botón de eliminar
    const deleteBtnUser = row.querySelector('.btn-action.delete');
    if (deleteBtnUser) {
      deleteBtnUser.addEventListener('click', function(e) {
        e.stopPropagation();
        const userId = row.dataset.userId || row.dataset.id;
        
        // Mostrar el modal de confirmación
        const modal = document.getElementById('deleteModal');
        if (modal) {
          modal.style.display = 'block';
          
          // Configurar el botón de confirmación
          const confirmBtn = modal.querySelector('#confirmDelete');
          if (confirmBtn) {
            // Remover cualquier manejador anterior para evitar duplicados
            const newConfirmBtn = confirmBtn.cloneNode(true);
            confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);
            
            // Agregar el nuevo manejador
            newConfirmBtn.addEventListener('click', async () => {
              modal.style.display = 'none';
              await handleDeleteUser(userId, row);
            });
          }
        }
      });
    }

    // Botón de editar (manejador existente)
    const editBtn = row.querySelector('.btn-action.edit');
    if (editBtn) {
      editBtn.addEventListener('click', function(e) {
        e.stopPropagation();
        // Código existente para edición
      });
    }
  }

  // --- Lógica para el modal de imagen de puerta ---
  if (imageDisplayModal) {
    if (closeImageModalButton) {
      closeImageModalButton.addEventListener("click", () => {
        imageDisplayModal.style.display = "none"
      })
    }
    if (closeImageModalIcon) {
      closeImageModalIcon.addEventListener("click", () => {
        imageDisplayModal.style.display = "none"
      })
    }
    window.addEventListener("click", (event) => {
      if (event.target === imageDisplayModal) {
        imageDisplayModal.style.display = "none"
      }
    })
  }

  // --- Variables para datos dinámicos ---
  let currentUserData = null
  const userSearchStatus = document.getElementById("userSearchStatus")

  // --- Funciones para comunicación con el backend ---
  async function cargarPuertasDisponibles() {
    try {
      const response = await fetch('/api/puertas')
      const data = await response.json()
      
      if (data.success) {
        const doorSelect = document.getElementById("doorId")
        doorSelect.innerHTML = '<option value="">Seleccione una puerta...</option>'
        
        data.puertas.forEach(puerta => {
          const option = document.createElement('option')
          // Soportar tanto {id_puerta, nombre_puerta} como {id, nombre}
          const id = puerta.id_puerta !== undefined ? puerta.id_puerta : puerta.id
          const nombre = puerta.nombre_puerta !== undefined ? puerta.nombre_puerta : puerta.nombre
          option.value = id
          option.textContent = nombre
          doorSelect.appendChild(option)
        })
      } else {
        showNotification("Error al cargar puertas: " + data.error, "error")
      }
    } catch (error) {
      console.error("Error al cargar puertas:", error)
      showNotification("Error de conexión al cargar puertas", "error")
    }
  }

  async function buscarUsuarioPorDNI(dni) {
    try {
      const response = await fetch('/api/buscar-usuario', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dni: dni })
      })
      return await response.json()
    } catch (error) {
      console.error("Error al buscar usuario:", error)
      return { success: false, error: "Error de conexión" }
    }
  }

  async function buscarUsuariosAutocompletar(dniParcial) {
    try {
      const response = await fetch(`/api/buscar-usuarios-autocompletar?search=${encodeURIComponent(dniParcial)}`)
      return await response.json()
    } catch (error) {
      console.error("Error al buscar usuarios para autocompletar:", error)
      return { success: false, error: "Error de conexión" }
    }
  }

  async function crearPermiso(userData, puertaId, tiempoMinutos) {
    try {
      const response = await fetch('/api/crear-permiso', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id_user: userData.id_user,
          id_puerta: puertaId,
          tiempo_minutos: tiempoMinutos
        })
      })
      return await response.json()
    } catch (error) {
      console.error("Error al crear permiso:", error)
      return { success: false, error: "Error de conexión" }
    }
  }

  // --- Función para actualizar un usuario en el servidor ---
  const actualizarUsuarioEnServidor = async (idUsuario, datos) => {
    try {
      const response = await fetch(`/api/usuarios/${idUsuario}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.content || ''
        },
        body: JSON.stringify({
          nombre: datos.name,
          apellido: datos.surname,
          dni: datos.dni,
          rol: datos.role
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.message || 'Error al actualizar el usuario');
      }

      return await response.json();
    } catch (error) {
      console.error('Error:', error);
      throw error;
    }
  };

  // --- Funcionalidad de autocompletado para DNI ---
  if (userDNIInput && userNameInput && userSurnameInput && userSuggestions) {
    let timeoutId = null
    
    // Función para mostrar sugerencias
    function mostrarSugerencias(usuarios) {
      userSuggestions.innerHTML = ""
      
      if (usuarios.length === 0) {
        userSuggestions.style.display = "none"
        return
      }
      
      usuarios.forEach(usuario => {
        const suggestionItem = document.createElement("div")
        suggestionItem.className = "suggestion-item"
        suggestionItem.style.cssText = "padding: 10px; cursor: pointer; border-bottom: 1px solid #eee; hover: background-color: #f5f5f5;"
        suggestionItem.innerHTML = `
          <div style="font-weight: 500;">${usuario.dni}</div>
          <div style="font-size: 12px; color: #666;">${usuario.nombre_completo}</div>
        `
        
        // Hover effects
        suggestionItem.addEventListener("mouseenter", () => {
          suggestionItem.style.backgroundColor = "#f5f5f5"
        })
        suggestionItem.addEventListener("mouseleave", () => {
          suggestionItem.style.backgroundColor = "white"
        })
        
        // Click handler
        suggestionItem.addEventListener("click", () => {
          seleccionarUsuario(usuario)
        })
        
        userSuggestions.appendChild(suggestionItem)
      })
      
      userSuggestions.style.display = "block"
    }
    
    // Función para seleccionar un usuario
    function seleccionarUsuario(usuario) {
      userDNIInput.value = usuario.dni
      userNameInput.value = usuario.nombre
      userSurnameInput.value = usuario.apellido
      userSearchStatus.textContent = "✓ Usuario seleccionado"
      userSearchStatus.style.color = "#28a745"
      currentUserData = usuario
      userSuggestions.style.display = "none"
    }
    
    // Función para ocultar sugerencias
    function ocultarSugerencias() {
      setTimeout(() => {
        userSuggestions.style.display = "none"
      }, 200)
    }
    
    // Event listener para input
    userDNIInput.addEventListener("input", async () => {
      const dni = userDNIInput.value.trim()
      
      // Limpiar timeout anterior
      if (timeoutId) {
        clearTimeout(timeoutId)
      }
      
      if (dni.length < 2) {
        userNameInput.value = ""
        userSurnameInput.value = ""
        userSearchStatus.textContent = ""
        currentUserData = null
        userSuggestions.style.display = "none"
        return
      }

      userSearchStatus.textContent = "Buscando..."
      userSearchStatus.style.color = "#666"

      // Debounce la búsqueda
      timeoutId = setTimeout(async () => {
        const resultado = await buscarUsuariosAutocompletar(dni)
        
        if (resultado.success) {
          if (resultado.usuarios.length > 0) {
            mostrarSugerencias(resultado.usuarios)
            userSearchStatus.textContent = `${resultado.usuarios.length} usuario(s) encontrado(s)`
            userSearchStatus.style.color = "#28a745"
          } else {
            userSuggestions.style.display = "none"
            userSearchStatus.textContent = "No se encontraron usuarios"
            userSearchStatus.style.color = "#dc3545"
          }
        } else {
          userSuggestions.style.display = "none"
          userSearchStatus.textContent = "Error al buscar usuarios"
          userSearchStatus.style.color = "#dc3545"
        }
      }, 300)
    })
    
    // Ocultar sugerencias cuando se hace click fuera
    userDNIInput.addEventListener("blur", ocultarSugerencias)
    
    // Navegación con teclado
    userDNIInput.addEventListener("keydown", (e) => {
      const suggestions = userSuggestions.querySelectorAll(".suggestion-item")
      let selectedIndex = -1
      
      // Encontrar el elemento seleccionado actual
      suggestions.forEach((item, index) => {
        if (item.style.backgroundColor === "rgb(245, 245, 245)") {
          selectedIndex = index
        }
      })
      
      if (e.key === "ArrowDown") {
        e.preventDefault()
        selectedIndex = Math.min(selectedIndex + 1, suggestions.length - 1)
        updateSelection(suggestions, selectedIndex)
      } else if (e.key === "ArrowUp") {
        e.preventDefault()
        selectedIndex = Math.max(selectedIndex - 1, 0)
        updateSelection(suggestions, selectedIndex)
      } else if (e.key === "Enter" && selectedIndex >= 0) {
        e.preventDefault()
        suggestions[selectedIndex].click()
      } else if (e.key === "Escape") {
        userSuggestions.style.display = "none"
      }
    })
    
    function updateSelection(suggestions, selectedIndex) {
      suggestions.forEach((item, index) => {
        item.style.backgroundColor = index === selectedIndex ? "#f5f5f5" : "white"
      })
    }
  }

  // --- Adjuntar listeners a todos los botones de acción existentes al cargar la página ---
  document.querySelectorAll(".users-table tbody tr").forEach((row) => {
    attachTableActionListeners(row)
  })

  // Asegurarse de que los botones de eliminar tengan el ID del permiso
  document.querySelectorAll('.btn-action.delete').forEach(btn => {
    const row = btn.closest('tr');
    if (row) {
      // El ID del permiso está en la primera celda de la fila
      const permissionId = row.cells[0].textContent.trim();
      if (permissionId) {
        btn.setAttribute('data-id', permissionId);
      }
    }
  });

  // Inicializar los botones de eliminar permisos
  document.querySelectorAll('#permitsTable .btn-action.delete').forEach(btn => {
    const row = btn.closest('tr');
    if (row) {
      // Buscar el ID del permiso en la primera celda de la fila
      const permissionId = row.cells[0].textContent.trim();
      if (permissionId) {
        btn.setAttribute('data-id', permissionId);
        row.setAttribute('data-permission-id', permissionId);
      }
    }
  });
})
