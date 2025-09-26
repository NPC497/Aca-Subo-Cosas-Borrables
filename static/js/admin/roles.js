document.addEventListener("DOMContentLoaded", () => {
  // Variables para datos reales desde la base de datos
  let roles = []
  let users = []
  let doors = []
  let roleToAssignUser = null; // Add this line to track the selected role
  let isNewRoleCreationFlow = false;
  let currentTemporaryRole = null;
  let editingRole = null
  let roleToDelete = null
  let tempAdminPermissionChangeState = false
  let selectedDoorIds = []

  const ITEMS_PER_PAGE = 5
  let currentPage = 1
  let searchTerm = ""
  let sortColumn = "name"
  let sortDirection = "asc"

  // --- Global State for Modals (NO SE REINICIAN) ---

  // --- DOM Elements ---
  const rolesTableBody = document.querySelector("#rolesTable tbody")
  const searchInput = document.getElementById("searchInput")
  const addNewRoleBtn = document.getElementById("addNewRoleBtn")
  const assignExistingRoleBtn = document.getElementById("assignExistingRoleBtn")

  // Modals
  const deleteRoleModal = document.getElementById("deleteRoleModal")
  const closeDeleteRoleModal = document.getElementById("closeDeleteRoleModal")
  const cancelDeleteRoleBtn = document.getElementById("cancelDeleteRole")
  const confirmDeleteRoleBtn = document.getElementById("confirmDeleteRole")
  const deleteRoleMessage = document.getElementById("deleteRoleMessage")

  const roleFormModal = document.getElementById("roleFormModal")
  const closeRoleFormModal = document.getElementById("closeRoleFormModal")
  const cancelRoleFormBtn = document.getElementById("cancelRoleForm")
  const saveRoleBtn = document.getElementById("saveRole")
  const roleModalTitle = document.getElementById("roleModalTitle")
  const roleNameInput = document.getElementById("roleName")
  const accessAllDoorsYes = document.getElementById("accessAllDoorsYes")
  const accessAllDoorsNo = document.getElementById("accessAllDoorsNo")
  const assignPermissionsToUsersYes = document.getElementById("assignPermissionsToUsersYes")
  const assignPermissionsToUsersNo = document.getElementById("assignPermissionsToUsersNo")

  // Door access elements
  const doorAccessGroup = document.getElementById("doorAccessGroup")
  const doorSearchInput = document.getElementById("doorSearchInput")
  const doorSearchResults = document.getElementById("doorSearchResults")
  const selectedDoorsList = document.getElementById("selectedDoorsList")

  const assignUserModal = document.getElementById("assignUserModal")
  const closeAssignUserModal = document.getElementById("closeAssignUserModal")
  const cancelAssignUserBtn = document.getElementById("cancelAssignUser")
  const assignUserModalTitle = document.getElementById("assignUserModalTitle")
  const existingRoleSelectGroup = document.getElementById("existingRoleSelectGroup")
  const userSearchInput = document.getElementById("userSearchInput")
  const userSearchResults = document.getElementById("userSearchResults")
  const assignUserMessage = document.getElementById("assignUserMessage")

  const adminPermissionChangeConfirmationModal = document.getElementById("adminPermissionChangeConfirmationModal")
  const closeAdminPermissionChangeConfirmationModal = document.getElementById(
    "closeAdminPermissionChangeConfirmationModal",
  )
  const cancelAdminPermissionChangeBtn = document.getElementById("cancelAdminPermissionChange")
  const confirmAdminPermissionChangeBtn = document.getElementById("confirmAdminPermissionChange")
  const roleNameForAdminConfirm = document.getElementById("roleNameForAdminConfirm")

  const reassignOrRemoveUsersModal = document.getElementById("reassignOrRemoveUsersModal")
  const closeReassignOrRemoveUsersModal = document.getElementById("closeReassignOrRemoveUsersModal")
  const roleNameForReassign = document.getElementById("roleNameForReassign")
  const affectedUsersList = document.getElementById("affectedUsersList")
  const newRoleForAffectedUsers = document.getElementById("newRoleForAffectedUsers")
  const cancelReassignOrRemoveUsers = document.getElementById("cancelReassignOrRemoveUsers")
  const removeRoleFromAllAffected = document.getElementById("removeRoleFromAllAffected")
  const reassignRoleToAffected = document.getElementById("reassignRoleToAffected")

  // Confirmation modal
  const confirmationModal = document.getElementById("confirmationModal")
  const closeConfirmationModal = document.getElementById("closeConfirmationModal")
  const confirmationTitle = document.getElementById("confirmationTitle")
  const confirmationMessage = document.getElementById("confirmationMessage")
  const confirmationIcon = document.getElementById("confirmationIcon")
  const cancelConfirmation = document.getElementById("cancelConfirmation")
  const acceptConfirmation = document.getElementById("acceptConfirmation")

  // Tooltip
  const tooltip = document.getElementById("tooltip")

  // Pagination
  const paginationContainer = document.querySelector(".pagination")

  // Sidebar elements
  const menuToggle = document.getElementById("menuToggle")
  const sideNav = document.getElementById("side-nav-table")
  const navOverlay = document.getElementById("navOverlay")

  // --- Helper Functions ---
  function openModal(modal) {
    modal.classList.add("active")
    document.body.classList.add("modal-open")
  }

  function closeModal(modal) {
    modal.classList.remove("active")
    document.body.classList.remove("modal-open")
  }

  function showMessage(container, message, type = "info") {
    container.textContent = message
    container.className = `message-container ${type}`
    container.style.display = "block"

    setTimeout(() => {
      container.style.display = "none"
    }, 5000)
  }

  function showCustomConfirmation(title, message, iconClass = "fas fa-question-circle", confirmText = "Aceptar", cancelText = "Cancelar") {
    return new Promise((resolve) => {
      confirmationTitle.textContent = title
      confirmationMessage.textContent = message
      confirmationIcon.className = `${iconClass} warning-icon`
      acceptConfirmation.textContent = confirmText
      cancelConfirmation.textContent = cancelText

      const handleAccept = () => {
        closeModal(confirmationModal)
        acceptConfirmation.removeEventListener("click", handleAccept)
        cancelConfirmation.removeEventListener("click", handleCancel)
        resolve(true)
      }

      const handleCancel = () => {
        closeModal(confirmationModal)
        acceptConfirmation.removeEventListener("click", handleAccept)
        cancelConfirmation.removeEventListener("click", handleCancel)
        resolve(false)
      }

      acceptConfirmation.addEventListener("click", handleAccept)
      cancelConfirmation.addEventListener("click", handleCancel)

      openModal(confirmationModal)
    })
  }

  // FUNCIÓN PARA LIMPIAR SOLO LOS CAMPOS NECESARIOS (NO REINICIA EL MODAL)
  function clearRoleFormFields() {
    roleNameInput.value = ""
    accessAllDoorsNo.checked = true
    assignPermissionsToUsersNo.checked = true
    selectedDoorIds = []
    updateSelectedDoorsDisplay()
    doorAccessGroup.style.display = "block" // Mostrar por defecto
    doorSearchInput.value = ""
    doorSearchResults.innerHTML = ""
  }

  // FUNCIÓN PARA LIMPIAR SOLO LOS CAMPOS DEL MODAL DE ASIGNACIÓN (NO REINICIA)
  function updateSelectedRoleDisplay(role) {
    const selectedRoleInfo = document.getElementById("selectedRoleInfo");
    const selectedRoleDisplay = document.getElementById("selectedRoleDisplay");
    
    if (role) {
      selectedRoleInfo.innerHTML = `
        <div class="selected-role">
          <strong>${role.name}</strong>
          ${role.description ? `<p>${role.description}</p>` : ''}
        </div>
      `;
      selectedRoleDisplay.style.display = 'block';
    } else {
      selectedRoleInfo.innerHTML = '';
      selectedRoleDisplay.style.display = 'none';
    }
  }

  function clearAssignUserFields() {
    userSearchInput.value = ""
    userSearchResults.innerHTML = ""
    assignUserMessage.style.display = "none"

    // Solo limpiar campos de búsqueda de rol si están visibles
    const roleSearchInput = document.getElementById("roleSearchInput")
    const roleSearchResults = document.getElementById("roleSearchResults")
    if (roleSearchInput) roleSearchInput.value = ""
    if (roleSearchResults) roleSearchResults.classList.remove("show")

    // Solo resetear la selección de rol si no es un flujo de creación nuevo
    if (!isNewRoleCreationFlow) {
      // updateSelectedRoleDisplay(null)
      // roleToAssignUser = null
    }
  }

  function updateSelectedDoorsDisplay() {
    selectedDoorsList.innerHTML = ""
    selectedDoorIds.forEach((doorId) => {
      const door = doors.find((d) => d.id === doorId)
      if (door) {
        const tag = document.createElement("div")
        tag.className = "selected-door-tag"
        tag.innerHTML = `
          ${door.name}
          <button type="button" class="remove-door-btn" data-door-id="${doorId}">
            <i class="fas fa-times"></i>
          </button>
        `
        selectedDoorsList.appendChild(tag)
      }
    })
  }

  function renderDoorSearchResults(searchTerm) {
    const filteredDoors = doors.filter(
      (door) =>
        !selectedDoorIds.includes(door.id) &&
        (door.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          door.location.toLowerCase().includes(searchTerm.toLowerCase()) ||
          door.description.toLowerCase().includes(searchTerm.toLowerCase())),
    )

    if (filteredDoors.length === 0) {
      doorSearchResults.innerHTML = `<p style="text-align: center; padding: 15px; color: #666;">No se encontraron puertas.</p>`
      doorSearchResults.classList.add("show")
      return
    }

    const ul = document.createElement("ul")
    filteredDoors.forEach((door) => {
      const li = document.createElement("li")
      li.innerHTML = `
        <div class="door-info">
          <strong>${door.name}</strong>
        </div>
        <button type="button" class="select-door-btn" data-door-id="${door.id}">Seleccionar</button>
      `
      ul.appendChild(li)
    })
    doorSearchResults.innerHTML = ""
    doorSearchResults.appendChild(ul)
    doorSearchResults.classList.add("show")
  }

  // Busca puertas desde el backend y actualiza la lista local `doors`
  async function searchDoorsRemote(term) {
    try {
      const params = new URLSearchParams({ q: term, limit: "10" })
      const res = await fetch(`/api/doors/search?${params.toString()}`, { credentials: "same-origin" })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      if (!data.success) throw new Error(data.message || "Error buscando puertas")

      const fetched = (data.doors || []).map((d) => ({
        id: String(d.id),
        name: d.nombre || "",
        location: d.ubicacion || "",
        description: d.descripcion || "",
      }))

      const byId = new Map(doors.map((d) => [d.id, d]))
      for (const f of fetched) {
        byId.set(f.id, { ...(byId.get(f.id) || {}), ...f })
      }
      doors = Array.from(byId.values())

      renderDoorSearchResults(term)
    } catch (err) {
      console.error("searchDoorsRemote error:", err)
      doorSearchResults.innerHTML = `<p style="text-align: center; padding: 15px; color: #e74c3c;">Error al buscar puertas.</p>`
      doorSearchResults.classList.add("show")
    }
  }

  function renderRolesTable() {
    let filteredAndSortedRoles = [...roles]

    // Filter
    if (searchTerm) {
      filteredAndSortedRoles = filteredAndSortedRoles.filter((role) =>
        role.name.toLowerCase().includes(searchTerm.toLowerCase()),
      )
    }

    // Sort
    filteredAndSortedRoles.sort((a, b) => {
      const aValue = a[sortColumn]
      const bValue = b[sortColumn]

      if (typeof aValue === "string" && typeof bValue === "string") {
        return sortDirection === "asc" ? aValue.localeCompare(bValue) : bValue.localeCompare(aValue)
      }
      return 0
    })

    const totalPages = Math.ceil(filteredAndSortedRoles.length / ITEMS_PER_PAGE)
    const startIndex = (currentPage - 1) * ITEMS_PER_PAGE
    const endIndex = startIndex + ITEMS_PER_PAGE
    const paginatedRoles = filteredAndSortedRoles.slice(startIndex, endIndex)

    rolesTableBody.innerHTML = ""

    if (paginatedRoles.length === 0) {
      rolesTableBody.innerHTML = `<tr><td colspan="5" class="py-6 text-center text-gray-500">No se encontraron roles.</td></tr>`
      renderPagination(totalPages)
      return
    }

    paginatedRoles.forEach((role) => {
      const row = rolesTableBody.insertRow()
      row.className = "border-b border-gray-200 hover:bg-gray-50"

      // Get the count of assigned users
      const assignedUsersCount = role.assignedUserIds?.length || 0
      const assignedUsersText = assignedUsersCount > 0 ? `${assignedUsersCount} usuario(s)` : "Ninguno"

      row.innerHTML = `
        <td class="py-3 px-6 text-left whitespace-nowrap">${role.name}</td>
        <td class="py-3 px-6 text-left"><span class="status-badge ${role.accessAllDoors ? "yes" : "no"}">${
          role.accessAllDoors ? "Sí" : "No"
        }</span></td>
        <td class="py-3 px-6 text-left"><span class="status-badge ${
          role.assignPermissionsToUsers ? "yes" : "no"
        }">${role.assignPermissionsToUsers ? "Sí" : "No"}</span></td>
        <td class="py-3 px-6 text-left">${assignedUsersText}</td>
        <td class="py-3 px-6 text-center">
          <div class="flex item-center justify-center space-x-2">
            <button type="button" class="btn-action edit" data-action="edit" data-role-id="${role.id}" aria-label="Editar rol">
              <i class="fas fa-edit"></i>
            </button>
            <button type="button" class="btn-action delete" data-action="delete" data-role-id="${role.id}" aria-label="Eliminar rol">
              <i class="fas fa-trash-alt"></i>
            </button>
          </div>
        </td>
      `
    })

    renderPagination(totalPages)
  }

  function renderPagination(totalPages) {
    paginationContainer.innerHTML = ""

    const createButton = (text, page, isDisabled, isActive = false) => {
      const button = document.createElement("button")
      button.className = `btn-page px-3 py-1 rounded-md ${
        isActive ? "bg-gray-800 text-white" : "bg-gray-200 hover:bg-gray-300 text-gray-700"
      }`
      button.innerHTML = text
      button.disabled = isDisabled
      button.addEventListener("click", () => {
        currentPage = page
        renderRolesTable()
      })
      return button
    }

    paginationContainer.appendChild(
      createButton('<i class="fas fa-chevron-left"></i>', currentPage - 1, currentPage === 1),
    )

    for (let i = 1; i <= totalPages; i++) {
      paginationContainer.appendChild(createButton(i, i, false, i === currentPage))
    }

    paginationContainer.appendChild(
      createButton('<i class="fas fa-chevron-right"></i>', currentPage + 1, currentPage === totalPages),
    )
  }

  function renderRoleSearchResults(searchTerm) {
    console.log('renderRoleSearchResults called with term:', searchTerm);
    console.log('Current roles array:', roles);
    
    const roleSearchResults = document.getElementById("roleSearchResults");
    console.log('Search results container:', roleSearchResults);
    
    if (!roleSearchResults) {
      console.error('roleSearchResults element not found!');
      return;
    }

    if (!searchTerm || searchTerm.trim() === "") {
      roleSearchResults.innerHTML = "";
      roleSearchResults.classList.remove("show");
      return;
    }

    const filteredRoles = roles.filter(
      (role) =>
        role.name.toLowerCase().includes(searchTerm.toLowerCase())
    );

    if (filteredRoles.length === 0) {
      roleSearchResults.innerHTML = "<li class='p-3 text-gray-500'>No se encontraron roles.</li>";
      roleSearchResults.classList.add("show");
      return;
    }

    // Get the selected role ID from session storage
    const selectedRoleId = sessionStorage.getItem('selectedRoleId');
    
    const html = document.createElement("ul");
    filteredRoles.forEach((role) => {
      const isSelected = selectedRoleId === role.id;
      
      const li = document.createElement("li");
      li.className = 'py-2 px-3 hover:bg-gray-50 cursor-pointer';
      li.innerHTML = `
        <div class="user-info">
          <div>${role.name}</div>
        </div>
        <button type="button" class="select-role-btn bg-blue-500 text-white px-3 py-1 rounded hover:bg-blue-600" 
                data-role-id="${role.id}" data-role-name="${role.name}">
          ${isSelected ? 'Seleccionado' : 'Seleccionar'}
        </button>
      `;
      
      // Add click handler to select the role
      li.addEventListener('click', (e) => {
        if (!e.target.closest('.select-role-btn')) {
          const roleId = li.querySelector('.select-role-btn').dataset.roleId;
          const roleName = li.querySelector('.select-role-btn').dataset.roleName;
          roleToAssignUser = { id: roleId, name: roleName };
          updateSelectedRoleDisplay(roleToAssignUser);
          document.getElementById('roleSearchResults').classList.remove('show');
        }
      });
      
      html.appendChild(li);
    });
    
    roleSearchResults.innerHTML = '';
    roleSearchResults.appendChild(html);
    roleSearchResults.classList.add("show");
  }

  function clearSelectedRole() {
    roleToAssignUser = null
    updateSelectedRoleDisplay(null)
    document.getElementById("roleSearchInput").value = ""
    document.getElementById("roleSearchResults").classList.remove("show")
    showMessage(assignUserMessage, "Seleccione un rol para continuar con la asignación.", "info")
  }

  async function assignRoleToUser(user, role) {
    try {
      // Get the current user data with their current role
      const currentUser = users.find(u => u.id === user.id);
      const currentRoleId = currentUser ? currentUser.roleId : null;

      // Check if the user is already assigned to this role
      if (currentRoleId === role.id) {
        showMessage(assignUserMessage, `El usuario ${user.name} ${user.surname} ya está asignado a este rol.`, "info");
        return false;
      }

      // Admin warning check
      const currentRole = roles.find((r) => r.id === currentRoleId);
      if (currentRole && currentRole.isAdminRole && !role.isAdminRole) {
        const confirmed = await showCustomConfirmation(
          "Confirmar Cambio de Permisos",
          `Estás a punto de quitarle los permisos de administrador al usuario ${user.name} ${user.surname}. ¿Deseas continuar?`,
          "fas fa-exclamation-triangle",
        )
        if (!confirmed) {
          return false;
        }
      } else if (role.isAdminRole && currentRole && currentRole.isAdminRole) {
        showMessage(assignUserMessage, `Este usuario ${user.name} ${user.surname} ya es administrador.`, "info");
        return false;
      }

      // Show loading state
      const assignButton = document.querySelector("#assignUserModal .modal-footer button:last-child");
      const originalButtonText = assignButton.innerHTML;
      assignButton.disabled = true;
      assignButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Asignando...';

      try {
        // Send the update to the server
        const response = await fetch(`/api/usuarios/${user.id}/actualizar-rol`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            id_rol: role.id
          })
        });

        const result = await response.json();

        if (response.ok && result.success) {
          // Update local state only after successful server update
          if (currentRoleId) {
            // Remove user from old role's assigned users
            roles = roles.map(r => 
              r.id === currentRoleId 
                ? { ...r, assignedUserIds: r.assignedUserIds.filter(id => id !== user.id) } 
                : r
            );
          }

          // Add user to new role's assigned users
          roles = roles.map(r => 
            r.id === role.id
              ? { 
                  ...r, 
                  assignedUserIds: Array.isArray(r.assignedUserIds) 
                    ? [...r.assignedUserIds, user.id] 
                    : [user.id] 
                }
              : r
          );

          // Update user's role in the users array
          users = users.map(u => 
            u.id === user.id 
              ? { ...u, roleId: role.id }
              : u
          );

          // Show success message
          showMessage(
            assignUserMessage,
            `Rol "${role.name}" asignado a ${user.name} ${user.surname}.`,
            "success"
          );
          
          // Clear the search input and results
          userSearchInput.value = "";
          userSearchResults.innerHTML = "";
          
          // Re-render the table to show updated roles
          renderRolesTable();
          
          return true;
        } else {
          // Show error message
          const errorMessage = result.message || 'Error al asignar el rol';
          showMessage(assignUserMessage, errorMessage, "error");
          return false;
        }
      } catch (error) {
        console.error('Error al asignar rol:', error);
        showMessage(assignUserMessage, `Error al asignar el rol: ${error.message}`, "error");
        return false;
      } finally {
        // Reset button state
        assignButton.disabled = false;
        assignButton.innerHTML = originalButtonText;
      }
    } catch (error) {
      console.error('Error during assignment:', error);
      showMessage(assignUserMessage, `Error al asignar el rol: ${error.message}`, "error");
      return false;
    }
  }

  // Debounce function for search input
  const debounce = (func, delay) => {
    let timeout
    return function (...args) {
      clearTimeout(timeout)
      timeout = setTimeout(() => func.apply(this, args), delay)
    }
  }

  // --- Event Listeners ---

  // Sidebar Toggle
  if (menuToggle && sideNav && navOverlay) {
    menuToggle.addEventListener("click", () => {
      sideNav.classList.toggle("active")
      menuToggle.classList.toggle("active")
      navOverlay.classList.toggle("active")
    })
    navOverlay.addEventListener("click", () => {
      sideNav.classList.remove("active")
      menuToggle.classList.remove("active")
      navOverlay.classList.remove("active")
    })
  }

  // Handle active nav link based on current page
  const currentPath = window.location.pathname.split("/").pop()
  const navLinks = document.querySelectorAll(".nav-link")
  navLinks.forEach((link) => {
    const linkHref = link.getAttribute("href").split("/").pop()
    if (linkHref === currentPath) {
      link.classList.add("active")
    } else {
      link.classList.remove("active")
    }
  })

  // Search
  searchInput.addEventListener("input", (e) => {
    searchTerm = e.target.value
    currentPage = 1
    renderRolesTable()
  })

  // Sort
  document.querySelector("#rolesTable th:nth-child(1)").addEventListener("click", () => {
    if (sortColumn === "name") {
      sortDirection = sortDirection === "asc" ? "desc" : "asc"
    } else {
      sortColumn = "name"
      sortDirection = "asc"
    }
    renderRolesTable()
  })

  // Add New Role Button - NO REINICIA EL MODAL
  addNewRoleBtn.addEventListener("click", () => {
    editingRole = null
    isNewRoleCreationFlow = true
    roleModalTitle.textContent = "Registrar Nuevo Rol"
    clearRoleFormFields() // Solo limpia campos, no reinicia
    openModal(roleFormModal)
  })

  // Assign Existing Role Button
  assignExistingRoleBtn.addEventListener("click", () => {
    isNewRoleCreationFlow = false;
    assignUserModalTitle.textContent = "Asignar Rol Existente a Usuario";
    existingRoleSelectGroup.style.display = "block";
    clearAssignUserFields();
    openModal(assignUserModal);
  })

  // Access All Doors radio button change
  accessAllDoorsYes.addEventListener("change", () => {
    if (accessAllDoorsYes.checked) {
      doorAccessGroup.style.display = "none"
      selectedDoorIds = []
      updateSelectedDoorsDisplay()
    }
  })

  accessAllDoorsNo.addEventListener("change", () => {
    if (accessAllDoorsNo.checked) {
      doorAccessGroup.style.display = "block"
    }
  })

  // Door search functionality (autocomplete desde backend)
  doorSearchInput.addEventListener(
    "input",
    debounce((e) => {
      const term = e.target.value.trim()
      if (term.length >= 2) {
        searchDoorsRemote(term)
      } else {
        doorSearchResults.innerHTML = ""
        doorSearchResults.classList.remove('show')
      }
    }, 300),
  )

  // Door selection
  doorSearchResults.addEventListener("click", (e) => {
    const selectBtn = e.target.closest(".select-door-btn")
    if (!selectBtn) return

    const doorId = selectBtn.dataset.doorId
    if (!selectedDoorIds.includes(doorId)) {
      selectedDoorIds.push(doorId)
      updateSelectedDoorsDisplay()
      renderDoorSearchResults(doorSearchInput.value)
    }
  })

  // Door removal
  selectedDoorsList.addEventListener("click", (e) => {
    const removeBtn = e.target.closest(".remove-door-btn")
    if (!removeBtn) return

    const doorId = removeBtn.dataset.doorId
    selectedDoorIds = selectedDoorIds.filter((id) => id !== doorId)
    updateSelectedDoorsDisplay()
    if (doorSearchInput.value.trim().length >= 2) {
      renderDoorSearchResults(doorSearchInput.value)
    }
  })

  // Role search functionality
  const roleSearchInput = document.getElementById("roleSearchInput")
  if (roleSearchInput) {
    roleSearchInput.addEventListener(
      "input",
      debounce((e) => {
        const searchTerm = e.target.value.trim()
        if (searchTerm.length >= 1) {
          renderRoleSearchResults(searchTerm)
        } else {
          document.getElementById("roleSearchResults").classList.remove("show")
        }
      }, 300),
    )
  }

  // Role selection - Use event delegation on the document level
  console.log('Setting up role selection...');
  
  document.addEventListener('click', (e) => {
    // Check if the click is on a select-role-btn or its children
    const selectBtn = e.target.closest(".select-role-btn");
    if (!selectBtn) return;
    
    console.log('Select button clicked:', selectBtn);
    
    const roleId = selectBtn.dataset.roleId;
    console.log('Role ID from button:', roleId);
    
    const selectedRole = roles.find((r) => r.id === roleId);
    console.log('Found role in roles array:', selectedRole);

    if (selectedRole) {
      console.log('Updating UI for selected role:', selectedRole.name);
      // Update UI to show selected role
      document.querySelectorAll('.role-search-result').forEach(el => {
        el.classList.remove('selected', 'bg-blue-50');
        const btn = el.querySelector('.select-role-btn');
        if (btn) {
          btn.textContent = 'Seleccionar';
          btn.classList.remove('bg-green-500');
          btn.classList.add('bg-blue-500');
        }
      });
      
      const roleItem = selectBtn.closest('.role-search-result');
      if (roleItem) {
        roleItem.classList.add('selected', 'bg-blue-50');
        selectBtn.textContent = 'Seleccionado';
        selectBtn.classList.remove('bg-blue-500');
        selectBtn.classList.add('bg-green-500');
      }
      
      // Update role selection
      roleToAssignUser = selectedRole;
      console.log('Role assigned to roleToAssignUser:', roleToAssignUser);
      updateSelectedRoleDisplay(selectedRole);
      assignUserMessage.style.display = "none";
    } else {
      console.log('No role found with ID:', roleId);
    }
  });

  // Role Form Modal (Add/Edit) - NO REINICIA
  closeRoleFormModal.addEventListener("click", () => closeModal(roleFormModal))
  cancelRoleFormBtn.addEventListener("click", () => closeModal(roleFormModal))

  saveRoleBtn.addEventListener("click", async () => {
    const name = roleNameInput.value.trim()
    const accessAllDoors = accessAllDoorsYes.checked
    const assignPermissionsToUsers = assignPermissionsToUsersYes.checked
    const isAdminRole = assignPermissionsToUsers
    const doorIds = accessAllDoors ? [] : [...selectedDoorIds]

    if (!name) {
      await showCustomConfirmation("Error", "El nombre del rol no puede estar vacío.", "fas fa-exclamation-circle")
      return
    }

    if (!accessAllDoors && doorIds.length === 0) {
      await showCustomConfirmation(
        "Error",
        "Debe seleccionar al menos una puerta o permitir acceso a todas las puertas.",
        "fas fa-exclamation-circle",
      )
      return
    }

    try {
      let response;
      if (editingRole) {
        // Update existing role
        response = await fetch(`/roles/${editingRole.id}/actualizar`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
          },
          body: JSON.stringify({
            nombre: name,
            acceso_todas_puertas: accessAllDoors,
            asignar_permisos_usuarios: assignPermissionsToUsers,
            puertas: doorIds
          })
        });
      } else {
        // Create new role
        response = await fetch('/roles/nuevo', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
          },
          body: JSON.stringify({
            nombre: name,
            acceso_todas_puertas: accessAllDoors,
            asignar_permisos_usuarios: assignPermissionsToUsers,
            puertas: doorIds
          })
        });
      }

      const result = await response.json();

      if (response.ok && result.success) {
        // Close role form modal
        closeModal(roleFormModal);
        
        if (!editingRole) {
          // Handle new role creation flow
          const newRole = {
            id: result.roleId || String(Date()),
            name,
            accessAllDoors,
            assignPermissionsToUsers,
            isAdminRole,
            doorIds
          };
          
          // Add the new role to the roles array
          roles.push(newRole);
          
          // Set the role to assign
          roleToAssignUser = newRole;
          currentTemporaryRole = newRole;
          
          // Show assignment modal
          assignUserModalTitle.textContent = `Asignar Rol "${name}" a Usuario`;
          existingRoleSelectGroup.style.display = "none";
          clearAssignUserFields();
          openModal(assignUserModal);
        } else {
          // Update the existing role in the roles array
          const updatedRole = {
            ...editingRole,
            name,
            accessAllDoors,
            assignPermissionsToUsers,
            isAdminRole,
            doorIds
          };
          
          const roleIndex = roles.findIndex(r => r.id === editingRole.id);
          if (roleIndex !== -1) {
            roles[roleIndex] = updatedRole;
          }
          
          // Show success message
          await showCustomConfirmation(
            "Éxito",
            `El rol "${name}" ha sido actualizado correctamente.`,
            "fas fa-check-circle"
          );
          
          // Refresh the roles table
          renderRolesTable();
        }
      } else {
        // Show error message
        const errorMessage = result.message || (editingRole ? 'Error al actualizar el rol' : 'Error al crear el rol');
        await showCustomConfirmation(
          "Error",
          errorMessage,
          "fas fa-exclamation-circle"
        );
      }
    } catch (error) {
      console.error('Error:', error);
      await showCustomConfirmation(
        "Error",
        `Ocurrió un error al intentar ${editingRole ? 'actualizar' : 'crear'} el rol. Por favor, intente nuevamente.`,
        "fas fa-exclamation-circle"
      );
    } finally {
      // Reset editing state
      if (editingRole) {
        editingRole = null;
      }
    }
  });

  // Delegate events for table actions (Edit, Delete)
  rolesTableBody.addEventListener("click", (e) => {
    const targetButton = e.target.closest("button[data-action]")
    if (!targetButton) return

    const roleId = targetButton.dataset.roleId
    const role = roles.find((r) => r.id === roleId)

    if (!role) return

    const action = targetButton.dataset.action

    if (action === "edit") {
      editingRole = role
      isNewRoleCreationFlow = false
      roleModalTitle.textContent = "Editar Rol"

      // CARGAR DATOS SIN REINICIAR EL MODAL
      roleNameInput.value = role.name
      accessAllDoorsYes.checked = role.accessAllDoors
      accessAllDoorsNo.checked = !role.accessAllDoors
      assignPermissionsToUsersYes.checked = role.assignPermissionsToUsers
      assignPermissionsToUsersNo.checked = !role.assignPermissionsToUsers

      selectedDoorIds = [...(role.doorIds || [])]
      updateSelectedDoorsDisplay()
      doorAccessGroup.style.display = role.accessAllDoors ? "none" : "block"

      openModal(roleFormModal)
    } else if (action === "delete") {
      roleToDelete = role
      deleteRoleMessage.textContent = ""
      const usersAssignedToRole = users.filter((user) => user.roleId === roleToDelete.id)

      if (usersAssignedToRole.length > 0) {
        closeModal(deleteRoleModal)
        roleNameForReassign.textContent = roleToDelete.name
        affectedUsersList.innerHTML = ""
        usersAssignedToRole.forEach((user) => {
          const li = document.createElement("li")
          li.innerHTML = `<div class="user-info"><strong>${user.name} ${user.surname}</strong><span>${user.email}</span></div>`
          affectedUsersList.appendChild(li)
        })
        newRoleForAffectedUsers.innerHTML = '<option value="">-- Seleccionar --</option>'
        roles
          .filter((r) => r.id !== roleToDelete.id)
          .forEach((r) => {
            const option = document.createElement("option")
            option.value = r.id
            option.textContent = r.name
            newRoleForAffectedUsers.appendChild(option)
          })
        openModal(reassignOrRemoveUsersModal)
      } else {
        openModal(deleteRoleModal)
      }
    }
  })

  // Delete Role Modal
  closeDeleteRoleModal.addEventListener("click", () => closeModal(deleteRoleModal))
  cancelDeleteRoleBtn.addEventListener("click", () => closeModal(deleteRoleModal))
  confirmDeleteRoleBtn.addEventListener("click", async () => {
    if (!roleToDelete) {
      closeModal(deleteRoleModal);
      return;
    }

    // Disable buttons and show loading state
    const originalText = confirmDeleteRoleBtn.innerHTML;
    confirmDeleteRoleBtn.disabled = true;
    confirmDeleteRoleBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Eliminando...';
    cancelDeleteRoleBtn.disabled = true;
    closeDeleteRoleModal.style.pointerEvents = 'none';

    try {
      // First, try to delete the role
      const response = await fetch(`/api/roles/${roleToDelete.id}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      const errorData = await response.json();

      if (!response.ok) {
        if (errorData.code === 'USERS_ASSIGNED' || errorData.message === 'existen_usuarios') {
          // Show confirmation dialog for role with users
          const confirm = await showCustomConfirmation(
            'Usuarios asignados',
            `Hay usuarios asignados a este rol. ¿Desea eliminarlo de todos modos?\n\nLos usuarios serán reasignados al rol de usuario por defecto.`,
            'fas fa-exclamation-triangle',
            'Eliminar de todos modos',
            'Cancelar'
          );

          if (confirm) {
            // Show loading state for force delete
            confirmDeleteRoleBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Reasignando usuarios...';
            
            try {
              const forceResponse = await fetch(`/api/roles/${roleToDelete.id}?force=true`, {
                method: 'DELETE',
                headers: {
                  'Content-Type': 'application/json',
                },
              });

              const forceResult = await forceResponse.json();

              if (forceResponse.ok) {
                showMessage(deleteRoleMessage, forceResult.message || 'Rol eliminado exitosamente', 'success');
                closeModal(deleteRoleModal);
                // Refresh the roles list after a short delay to show the success message
                setTimeout(() => {
                  loadRoles();
                }, 1000);
              } else {
                throw new Error(forceResult.message || 'Error al eliminar el rol');
              }
            } catch (error) {
              console.error('Error al forzar eliminación:', error);
              showMessage(deleteRoleMessage, error.message || 'Error al procesar la solicitud', 'error');
              resetDeleteButton(confirmDeleteRoleBtn, originalText);
            }
          } else {
            resetDeleteButton(confirmDeleteRoleBtn, originalText);
          }
          return;
        } else {
          // Show other errors
          throw new Error(errorData.message || 'Error al eliminar el rol');
        }
      }

      // If we get here, the deletion was successful
      showMessage(deleteRoleMessage, 'Rol eliminado exitosamente', 'success');
      closeModal(deleteRoleModal);
      
      // Reload roles after a short delay to show the success message
      setTimeout(() => {
        loadRoles();
      }, 1000);
      
    } catch (error) {
      console.error('Error al eliminar el rol:', error);
      showMessage(deleteRoleMessage, error.message || 'Error al procesar la solicitud', 'error');
    } finally {
      // Reset button state if not in force delete flow
      if (confirmDeleteRoleBtn.innerHTML.includes('Eliminando')) {
        resetDeleteButton(confirmDeleteRoleBtn, originalText);
      }
    }
  });

  // Helper function to reset delete button state
  function resetDeleteButton(button, originalText) {
    button.disabled = false;
    button.innerHTML = originalText;
    cancelDeleteRoleBtn.disabled = false;
    closeDeleteRoleModal.style.pointerEvents = 'auto';
    roleToDelete = null;
  }

  // Assign User Modal
  closeAssignUserModal.addEventListener("click", () => {
    closeModal(assignUserModal);
    // Recargar la página si se acaba de crear un rol
    if (isNewRoleCreationFlow) {
      window.location.reload();
    }
  });
  
  cancelAssignUserBtn.addEventListener("click", () => {
    closeModal(assignUserModal);
    // Recargar la página si se acaba de crear un rol
    if (isNewRoleCreationFlow) {
      window.location.reload();
    }
  });

  // Search user within assign user modal with debounce
  userSearchInput.addEventListener(
    "input",
    debounce(async () => {
      const identifier = userSearchInput.value.trim()
      userSearchResults.innerHTML = ""
      assignUserMessage.style.display = "none"

      if (identifier.length < 2) {
        return
      }

      try {
        // Show loading state
        userSearchResults.innerHTML = '<p class="text-center py-3">Buscando usuarios...</p>';
        
        // Fetch users from the backend with the search term
        const response = await fetch(`/api/buscar-usuarios-autocompletar?search=${encodeURIComponent(identifier)}`)
        const result = await response.json()
        
        if (result.success) {
          const matchingUsers = result.usuarios || []
          
          if (matchingUsers.length > 0) {
            const ul = document.createElement("ul")
            matchingUsers.forEach((user) => {
              const li = document.createElement("li")
              li.className = 'py-2 px-3 hover:bg-gray-50 cursor-pointer';
              li.innerHTML = `
                <div class="user-info">
                  <strong>${user.nombre || ''} ${user.apellido || ''}</strong>
                  <div class="text-sm text-gray-600">
                    ${user.dni ? `DNI: ${user.dni} | ` : ''}${user.email || ''}
                  </div>
                </div>
                <button type="button" class="assign-user-btn bg-blue-500 text-white px-3 py-1 rounded hover:bg-blue-600" 
                        data-user-id="${user.id_user}" data-user-name="${user.nombre} ${user.apellido}">
                  Asignar
                </button>
              `
              ul.appendChild(li)
            })
            userSearchResults.innerHTML = ''
            userSearchResults.appendChild(ul)
          } else {
            userSearchResults.innerHTML = `<p class="text-center text-gray-500 py-3">No se encontraron usuarios.</p>`
          }
        } else {
          console.error('Error en la búsqueda de usuarios:', result.error)
          userSearchResults.innerHTML = `<p class="text-center text-red-500 py-3">Error al buscar usuarios. Intente nuevamente.</p>`
        }
      } catch (error) {
        console.error('Error al buscar usuarios:', error)
        userSearchResults.innerHTML = `<p class="text-center text-red-500 py-3">Error de conexión al servidor.</p>`
      }
    }, 500),
  )

  // Delegate click for "Asignar" buttons in search results
  userSearchResults.addEventListener("click", async (e) => {
    const assignButton = e.target.closest(".assign-user-btn");
    if (!assignButton) return;

    const userId = assignButton.dataset.userId;
    const userName = assignButton.dataset.userName;
    
    // Create a user object from the data attributes
    const user = {
      id: userId,
      name: userName.split(' ')[0],
      surname: userName.split(' ').slice(1).join(' '),
      roleId: null
    };

    // Get the current role to use
    let roleToUse = roleToAssignUser; // Use the globally tracked role

    if (!roleToUse) {
      showMessage(assignUserMessage, "Error: Por favor, seleccione un rol antes de asignar.", "error");
      return;
    }

    // Disable the button to prevent double-clicks
    assignButton.disabled = true;
    const originalButtonText = assignButton.innerHTML;
    assignButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Asignando...';

    try {
      const assignedSuccessfully = await assignRoleToUser(user, roleToUse);
      
      if (assignedSuccessfully) {
        // If it's a new role creation flow and the role hasn't been added yet
        if (isNewRoleCreationFlow && !roles.some((r) => r.id === currentTemporaryRole.id)) {
          roles.push(currentTemporaryRole);
          isNewRoleCreationFlow = false;
          currentTemporaryRole = null;
        }

        // Clear the search input and results but keep the role selection
        userSearchInput.value = "";
        userSearchResults.innerHTML = "";
        
        // Show success message
        showMessage(
          assignUserMessage,
          `Rol "${roleToUse.name}" asignado exitosamente a ${user.name} ${user.surname}.`,
          "success"
        );
        
        // Re-render the table to show updated roles
        renderRolesTable();
      }
    } catch (error) {
      console.error('Error during assignment:', error);
      showMessage(assignUserMessage, `Error al asignar el rol: ${error.message}`, "error");
    } finally {
      // Re-enable the button
      assignButton.disabled = false;
      assignButton.innerHTML = originalButtonText;
    }
  });

  // Admin Permission Change Confirmation Modal
  closeAdminPermissionChangeConfirmationModal.addEventListener("click", () => {
    closeModal(adminPermissionChangeConfirmationModal)
    if (editingRole) {
      assignPermissionsToUsersYes.checked = editingRole.assignPermissionsToUsers
      assignPermissionsToUsersNo.checked = !editingRole.assignPermissionsToUsers
    }
  })

  cancelAdminPermissionChangeBtn.addEventListener("click", () => {
    closeModal(adminPermissionChangeConfirmationModal)
    if (editingRole) {
      assignPermissionsToUsersYes.checked = editingRole.assignPermissionsToUsers
      assignPermissionsToUsersNo.checked = !editingRole.assignPermissionsToUsers
    }
  })

  confirmAdminPermissionChangeBtn.addEventListener("click", () => {
    if (editingRole) {
      editingRole.assignPermissionsToUsers = tempAdminPermissionChangeState
      editingRole.isAdminRole = tempAdminPermissionChangeState
      roles = roles.map((r) =>
        r.id === editingRole.id
          ? {
              ...r,
              assignPermissionsToUsers: tempAdminPermissionChangeState,
              isAdminRole: tempAdminPermissionChangeState,
            }
          : r,
      )
    }
    closeModal(adminPermissionChangeConfirmationModal)
    closeModal(roleFormModal)
    renderRolesTable()
  })

  // Reassign or Remove Users Modal
  closeReassignOrRemoveUsersModal.addEventListener("click", () => closeModal(reassignOrRemoveUsersModal))
  cancelReassignOrRemoveUsers.addEventListener("click", () => closeModal(reassignOrRemoveUsersModal))

  // Handle role reassignment
  reassignRoleToAffected.addEventListener("click", async () => {
    if (!roleToDelete) {
      closeModal(reassignOrRemoveUsersModal);
      return;
    }

    const newRoleId = newRoleForAffectedUsers.value;
    if (!newRoleId) {
      showMessage(affectedUsersList, "Por favor seleccione un rol para reasignar los usuarios.", "error");
      return;
    }

    try {
      const response = await fetch(`/roles/${roleToDelete.id}/reasignar`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({
          nuevo_rol_id: parseInt(newRoleId)
        })
      });

      const result = await response.json();

      if (response.ok && result.success) {
        // Remove the role from the local state
        roles = roles.filter((r) => r.id !== roleToDelete.id);
        
        // Update users in the local state
        users = users.map(user => 
          user.roleId === roleToDelete.id 
            ? { ...user, roleId: parseInt(newRoleId) } 
            : user
        );

        closeModal(reassignOrRemoveUsersModal);
        renderRolesTable();
        
        // Show success message
        const newRoleName = roles.find(r => r.id === parseInt(newRoleId))?.name || 'el rol seleccionado';
        await showCustomConfirmation(
          "Éxito",
          `Usuarios reasignados a ${newRoleName} y rol eliminado correctamente.`,
          "fas fa-check-circle"
        );
      } else {
        const errorMessage = result.message || 'Error al reasignar usuarios';
        showMessage(affectedUsersList, errorMessage, "error");
      }
    } catch (error) {
      console.error('Error reassigning users:', error);
      showMessage(affectedUsersList, 'Error al procesar la solicitud. Intente nuevamente.', "error");
    }
  });

  // Handle role removal without reassignment
  removeRoleFromAllAffected.addEventListener("click", async () => {
    if (!roleToDelete) {
      closeModal(reassignOrRemoveUsersModal);
      return;
    }

    try {
      const response = await fetch(`/roles/${roleToDelete.id}/eliminar`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({
          forzar_eliminacion: true
        })
      });

      const result = await response.json();

      if (response.ok && result.success) {
        // Remove the role from the local state
        roles = roles.filter((r) => r.id !== roleToDelete.id);
        
        // Remove the role from users in the local state
        users = users.map(user => 
          user.roleId === roleToDelete.id 
            ? { ...user, roleId: null } 
            : user
        );

        closeModal(reassignOrRemoveUsersModal);
        renderRolesTable();
        
        // Show success message
        await showCustomConfirmation(
          "Éxito",
          `Rol eliminado y usuarios desvinculados correctamente.`,
          "fas fa-check-circle"
        );
      } else {
        const errorMessage = result.message || 'Error al eliminar el rol';
        showMessage(affectedUsersList, errorMessage, "error");
      }
    } catch (error) {
      console.error('Error removing role:', error);
      showMessage(affectedUsersList, 'Error al procesar la solicitud. Intente nuevamente.', "error");
    }
  });

  // Confirmation modal
  closeConfirmationModal.addEventListener("click", () => closeModal(confirmationModal))

  // Tooltip functionality with better positioning for modals
  document.addEventListener("mouseover", (e) => {
    const element = e.target.closest("[data-tooltip]")
    if (element) {
      const tooltipText = element.getAttribute("data-tooltip")
      tooltip.textContent = tooltipText
      tooltip.classList.add("show")

      const rect = element.getBoundingClientRect()

      let left = rect.left + rect.width / 2 - tooltip.offsetWidth / 2
      let top = rect.top - tooltip.offsetHeight - 10

      if (left < 10) left = 10
      if (left + tooltip.offsetWidth > window.innerWidth - 10) {
        left = window.innerWidth - tooltip.offsetWidth - 10
      }
      if (top < 10) {
        top = rect.bottom + 10
      }

      tooltip.style.left = left + "px"
      tooltip.style.top = top + "px"
    }
  })

  document.addEventListener("mouseout", (e) => {
    const element = e.target.closest("[data-tooltip]")
    if (element) {
      tooltip.classList.remove("show")
    }
  })

  // Make clearSelectedRole globally available
  window.clearSelectedRole = clearSelectedRole

  // Cargar datos reales desde el backend
  async function loadRoles() {
    try {
      const response = await fetch('/roles/lista')
      const result = await response.json()
      
      if (result.success) {
        roles = result.data.map(role => ({
          id: role.id.toString(),
          name: role.nombre,
          accessAllDoors: Boolean(role.acceso_todas_puertas),
          assignPermissionsToUsers: Boolean(role.asignar_permisos_usuarios),
          assignedUserIds: Array(parseInt(role.usuarios_asignados || 0)).fill(''), // Create array with length = user count
          isAdminRole: Boolean(role.asignar_permisos_usuarios),
          doorIds: []
        }))
        renderRolesTable()
      } else {
        console.error('Error al cargar roles:', result.message)
        rolesTableBody.innerHTML = `<tr><td colspan="5" class="py-6 text-center text-gray-500">Error al cargar roles: ${result.message}</td></tr>`
      }
    } catch (error) {
      console.error('Error al conectar con el servidor:', error)
      rolesTableBody.innerHTML = `<tr><td colspan="5" class="py-6 text-center text-gray-500">Error de conexión al servidor</td></tr>`
    }
  }

  // Cargar datos reales al iniciar
  loadRoles()
})
