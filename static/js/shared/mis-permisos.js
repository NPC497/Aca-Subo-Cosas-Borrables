document.addEventListener("DOMContentLoaded", () => {
  const permissionsDisplay = document.getElementById("permissions-display");

  let currentPage = 1;
  const itemsPerPage = 10;
  let allPermissions = [];

  // Función para cargar permisos desde el servidor
  async function cargarPermisos() {
    try {
      permissionsDisplay.innerHTML = `
        <div class="loading-container">
          <div class="loading-spinner"></div>
          <p>Cargando permisos...</p>
        </div>
      `;

      const response = await fetch('/api/mis-permisos');
      const data = await response.json();
      
      if (data.success) {
        allPermissions = data.data || [];
        renderPermissions(allPermissions);
      } else {
        throw new Error(data.message || 'Error al cargar permisos');
      }
    } catch (error) {
      console.error('Error:', error);
      permissionsDisplay.innerHTML = `
        <div class="message-box error">
          <i class="fas fa-exclamation-triangle"></i>
          Error al cargar permisos: ${error.message}
        </div>
      `;
    }
  }

  // Función para renderizar permisos
  function renderPermissions(permissions) {
    if (!permissions || permissions.length === 0) {
      permissionsDisplay.innerHTML = `
        <div class="message-box">
          <i class="fas fa-info-circle"></i>
          No tienes acceso a ninguna puerta.
        </div>
      `;
      return;
    }

    let permissionsHtml = '<ul class="permissions-list">';
    
    permissions.forEach((permission) => {
      let accessDetails = "";
      
      if (permission.accessType === "permanent") {
        accessDetails = '<span class="access-type permanent">Acceso Permanente</span>';
      } else if (permission.accessType === "temporary" && permission.expirationDate) {
        const expiration = new Date(permission.expirationDate);
        const now = new Date();
        
        if (expiration > now) {
          const timeLeft = expiration.getTime() - now.getTime();
          const days = Math.floor(timeLeft / (1000 * 60 * 60 * 24));
          const hours = Math.floor((timeLeft % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
          accessDetails = `<span class="access-type temporary">Acceso Temporal:</span> Vence en ${days}d ${hours}h`;
        } else {
          accessDetails = `<span class="access-type expired">Acceso Temporal:</span> Vencido`;
        }
      }

      let grantedBy = "";
      if (permission.grantedBy && permission.grantedBy !== 'Direct') {
        grantedBy = `<p class="granted-by">Otorgado por: ${permission.grantedBy}</p>`;
      }

      permissionsHtml += `
        <li class="permission-item">
          <div class="permission-header">
            <strong>${permission.doorName}</strong>
          </div>
          <div class="permission-details">
            <p>${accessDetails}</p>
            ${grantedBy}
          </div>
        </li>
      `;
    });
    
    permissionsHtml += "</ul>";
    permissionsDisplay.innerHTML = permissionsHtml;
  }

  // Cargar permisos al iniciar
  cargarPermisos();
});
