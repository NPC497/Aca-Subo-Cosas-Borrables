document.addEventListener("DOMContentLoaded", () => {
  // --- Referencias a elementos del DOM ---
  const menuToggle = document.getElementById("menuToggle")
  const sideNav = document.getElementById("side-nav-table")
  const navOverlay = document.getElementById("navOverlay")
  const searchInput = document.getElementById("searchInput")

  const deleteModal = document.getElementById("deleteModal")
  const closeButtons = document.querySelectorAll(".close")
  const cancelDelete = document.getElementById("cancelDelete")
  const confirmDelete = document.getElementById("confirmDelete")

  // NFC Confirmation Modal elements
  const nfcConfirmModal = document.getElementById("nfcConfirmModal")
  const nfcConfirmYes = document.getElementById("nfcConfirmYes")
  const nfcConfirmNo = document.getElementById("nfcConfirmNo")
  const closeNfcConfirmModal = document.getElementById("closeNfcConfirmModal")

  // Filter for temporary users table
  const tempUserStatusFilter = document.getElementById("tempUserStatusFilter")

  let currentRow = null

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

  // --- Paginación (Usuarios Temporarios) ---
  const TEMP_ITEMS_PER_PAGE = 10;
  let tempCurrentPage = 1;
  const temporaryUsersTable = document.getElementById("temporaryUsersTable");
  const tempPaginationContainer = document.querySelector(".pagination");

  function countVisibleTempRows() {
    if (!temporaryUsersTable) return 0;
    const rows = Array.from(temporaryUsersTable.querySelectorAll("tbody tr"));
    return rows.filter(r => r.style.display !== "none").length;
  }

  function applyTempPagination() {
    if (!temporaryUsersTable) return;
    const rows = Array.from(temporaryUsersTable.querySelectorAll("tbody tr"));
    let visibleIndex = 0;
    rows.forEach(row => {
      const isVisibleByFilters = row.style.display !== "none";
      if (!isVisibleByFilters) return; // keep hidden
      const start = (tempCurrentPage - 1) * TEMP_ITEMS_PER_PAGE;
      const end = start + TEMP_ITEMS_PER_PAGE;
      if (visibleIndex >= start && visibleIndex < end) {
        row.style.display = "";
      } else {
        row.style.display = "none";
      }
      visibleIndex++;
    });
  }

  function renderTempPagination() {
    if (!temporaryUsersTable || !tempPaginationContainer) return;
    const totalVisible = countVisibleTempRows();
    const totalPages = Math.max(1, Math.ceil(totalVisible / TEMP_ITEMS_PER_PAGE));
    if (tempCurrentPage > totalPages) tempCurrentPage = totalPages;

    tempPaginationContainer.innerHTML = "";

    const createBtn = (label, page, disabled = false, active = false) => {
      const btn = document.createElement("button");
      btn.className = `btn-page ${active ? "active" : ""}`.trim();
      btn.innerHTML = label;
      btn.disabled = disabled;
      btn.addEventListener("click", () => {
        tempCurrentPage = page;
        applyTempPagination();
        renderTempPagination();
      });
      return btn;
    };

    tempPaginationContainer.appendChild(
      createBtn('<i class="fas fa-chevron-left"></i>', Math.max(1, tempCurrentPage - 1), tempCurrentPage === 1)
    );
    for (let i = 1; i <= totalPages; i++) {
      tempPaginationContainer.appendChild(createBtn(String(i), i, false, i === tempCurrentPage));
    }
    tempPaginationContainer.appendChild(
      createBtn('<i class="fas fa-chevron-right"></i>', Math.min(totalPages, tempCurrentPage + 1), tempCurrentPage === totalPages)
    );
  }

  function refreshTempPagination() {
    if (!temporaryUsersTable) return;
    tempCurrentPage = 1;
    renderTempPagination();
    applyTempPagination();
  }

  // --- Funcionalidad de Filtrado ---
  const applyFilters = () => {
    if (!temporaryUsersTable) return

    const rows = temporaryUsersTable.querySelectorAll("tbody tr")
    const searchTerm = searchInput ? searchInput.value.toLowerCase() : ""
    const statusFilterValue = tempUserStatusFilter ? tempUserStatusFilter.value : "all"

    rows.forEach((row) => {
      let isVisible = true
      const rowText = row.textContent.toLowerCase()

      if (searchTerm && !rowText.includes(searchTerm)) {
        isVisible = false
      }

      const statusCell = row.cells[3]
      if (statusCell) {
        const status = statusCell.querySelector(".badge").textContent.toLowerCase()
        if (statusFilterValue !== "all" && status !== statusFilterValue) {
          isVisible = false
        }
      }

      row.style.display = isVisible ? "" : "none"
    })

    // Aplicar paginación sobre el resultado filtrado
    refreshTempPagination();
  }

  // Attach filter event listeners
  if (searchInput) searchInput.addEventListener("input", applyFilters)
  if (tempUserStatusFilter) tempUserStatusFilter.addEventListener("change", applyFilters)

  // --- Ordenar tabla ---
  const tableHeaders = document.querySelectorAll("#temporaryUsersTable th[data-sort]")
  tableHeaders.forEach((header) => {
    header.addEventListener("click", function () {
      const columnIndex = Array.from(this.parentNode.children).indexOf(this)
      const currentDirection = this.getAttribute("data-direction") || "asc"
      const newDirection = currentDirection === "asc" ? "desc" : "asc"

      tableHeaders.forEach((th) => th.removeAttribute("data-direction"))
      this.setAttribute("data-direction", newDirection)

      const tbody = this.closest("table").querySelector("tbody")
      const rows = Array.from(tbody.querySelectorAll("tr"))

      rows.sort((a, b) => {
        let aValue = a.cells[columnIndex].textContent.trim()
        let bValue = b.cells[columnIndex].textContent.trim()

        if (aValue < bValue) {
          return newDirection === "asc" ? -1 : 1
        }
        if (aValue > bValue) {
          return newDirection === "asc" ? 1 : -1
        }
        return 0
      })

      rows.forEach((row) => tbody.appendChild(row))

      // Refrescar paginación tras ordenar
      refreshTempPagination();
    })
  })

  // --- Inicializar paginación al cargar ---
  if (temporaryUsersTable && tempPaginationContainer) {
    refreshTempPagination();
  }

  // --- Funcionalidad para los modales ---
  if (deleteModal) {
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
          const userId = currentRow.dataset.id
          
          try {
            const response = await fetch(`/eliminarUsuarioTemporal/${userId}`, {
              method: 'DELETE',
              headers: {
                'Content-Type': 'application/json',
              }
            })

            const data = await response.json()

            if (data.success) {
              currentRow.style.backgroundColor = "#ffebee"
              setTimeout(() => {
                currentRow.remove()
              }, 300)
              showNotification("Usuario eliminado exitosamente", "success")
            } else {
              showNotification(data.message || "Error al eliminar usuario", "error")
            }
          } catch (error) {
            console.error('Error:', error)
            showNotification("Error de conexión al eliminar usuario", "error")
          }
        }
        deleteModal.style.display = "none"
      })
    }
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

  function attachTableActionListeners(row) {
    const deleteBtn = row.querySelector(".btn-action.delete")
    const confirmBtn = row.querySelector(".btn-action.confirm")

    if (deleteBtn) {
      deleteBtn.addEventListener("click", function () {
        currentRow = this.closest("tr")
        deleteModal.style.display = "flex"
      })
    }
    
    if (confirmBtn) {
      confirmBtn.addEventListener("click", async function () {
        currentRow = this.closest("tr")
        nfcConfirmModal.style.display = "flex"
      })
    }
  }

  // --- NFC Confirmation Modal Logic MEJORADO ---
  if (nfcConfirmModal) {
    // Cerrar modal con el botón X
    if (closeNfcConfirmModal) {
      closeNfcConfirmModal.addEventListener("click", () => {
        nfcConfirmModal.style.display = "none"
      })
    }

    // Botón "Sí" - MEJORADO
    if (nfcConfirmYes) {
      nfcConfirmYes.addEventListener("click", async () => {
        nfcConfirmModal.style.display = "none"

        if (currentRow) {
          // Obtener datos del usuario de la fila
          const userData = {
            name: currentRow.cells[0].textContent.trim(),
            surname: currentRow.cells[1].textContent.trim(),
            dni: currentRow.cells[2].textContent.trim(),
            id: currentRow.dataset.id
          }
          
          console.log("Datos del usuario para NFC:", userData)
          
          // Guardar en localStorage para que la página de grabación pueda acceder
          localStorage.setItem("nfcUserData", JSON.stringify(userData))
          
          showNotification("Redirigiendo al sistema de grabación NFC...", "info")
          
          // Redirigir a la página de grabación NFC
          setTimeout(() => {
            window.location.href = `${window.APP_CONFIG.grabarNfcUrl}?id_useratributes=${userData.id}`
          }, 1000)
        }
      })
    }

    // Botón "No"
    if (nfcConfirmNo) {
      nfcConfirmNo.addEventListener("click", () => {
        nfcConfirmModal.style.display = "none"
        showNotification("Operación cancelada", "info")
      })
    }

    // Cerrar modal al hacer clic fuera
    window.addEventListener("click", (event) => {
      if (event.target === nfcConfirmModal) {
        nfcConfirmModal.style.display = "none"
      }
    })
  }

  // --- Adjuntar listeners a todos los botones de acción existentes al cargar la página ---
  document.querySelectorAll("#temporaryUsersTable tbody tr").forEach((row) => {
    attachTableActionListeners(row)
  })
  
  // --- Función para actualizar el estado de una fila después de grabación NFC exitosa ---
  window.actualizarFilaUsuario = function(userId) {
    const row = document.querySelector(`tr[data-id="${userId}"]`)
    if (row) {
      const statusCell = row.cells[3]
      if (statusCell) {
        const badge = statusCell.querySelector('.badge')
        if (badge) {
          badge.textContent = 'Confirmado'
          badge.className = 'badge confirmed'
        }
      }
      
      // Opcionalmente, deshabilitar el botón de confirmar
      const confirmBtn = row.querySelector('.btn-action.confirm')
      if (confirmBtn) {
        confirmBtn.disabled = true
        confirmBtn.style.opacity = '0.5'
        confirmBtn.style.cursor = 'not-allowed'
      }
    }
  }
  
  // Verificar si venimos de una grabación exitosa
  const urlParams = new URLSearchParams(window.location.search)
  const nfcSuccess = urlParams.get('nfc_success')
  const userId = urlParams.get('user_id')
  
  if (nfcSuccess === 'true' && userId) {
    showNotification("Tarjeta NFC grabada exitosamente", "success")
    actualizarFilaUsuario(userId)
    
    // Limpiar los parámetros de la URL
    const newUrl = window.location.pathname
    window.history.replaceState({}, document.title, newUrl)
  }
})