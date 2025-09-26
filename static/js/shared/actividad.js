document.addEventListener("DOMContentLoaded", () => {
  console.log("Página de actividad inicializada")

  // Elementos del DOM
  const mobileMenuToggle = document.getElementById("mobileMenuToggle");
  const mainNav = document.getElementById("mainNav");
  const logoutButton = document.getElementById("logoutButton");
  const logoutModal = document.getElementById("logoutModal");
  const modalOverlay = document.getElementById("modalOverlay");
  const modalClose = document.getElementById("modalClose");
  const cancelLogout = document.getElementById("cancelLogout");
  const confirmLogout = document.getElementById("confirmLogout");
  const dateFilter = document.getElementById("dateFilter");
  const typeFilter = document.getElementById("typeFilter");
  const refreshButton = document.getElementById("refreshButton");
  const timelineContainer = document.getElementById("timelineContainer");
  const loadMoreButton = document.getElementById("loadMoreButton");
  const loadingSpinner = document.getElementById("loadingSpinner");
  const activityCount = document.getElementById("activityCount");
  const loginCountElement = document.getElementById("loginCount");
  const doorAccessCountElement = document.getElementById("doorAccessCount");
  const lastAccessElement = document.getElementById("lastAccess");

  // Variables de estado
  let currentPage = 1;
  let isLoading = false;
  let hasMoreData = true;
  const activitiesPerPage = 10;
  let allActivities = [];
  let filteredActivities = [];

  // Funciones auxiliares
  const showLogoutModal = () => {
    if (logoutModal) logoutModal.classList.add("active");
    if (modalOverlay) modalOverlay.classList.add("active");
    document.body.style.overflow = "hidden";
  };

  const closeLogoutModal = () => {
    if (logoutModal) logoutModal.classList.remove("active");
    if (modalOverlay) modalOverlay.classList.remove("active");
    document.body.style.overflow = "";
  };

  const showNotification = (message, type = "success") => {
    // Implementar notificación si es necesario
    console.log(`${type}: ${message}`);
  };

  const showLoading = () => {
    if (loadingSpinner) loadingSpinner.style.display = "flex";
    isLoading = true;
  };

  const hideLoading = () => {
    if (loadingSpinner) loadingSpinner.style.display = "none";
    isLoading = false;
  };

  const updateLoadMoreButton = () => {
    if (loadMoreButton) {
      loadMoreButton.style.display = hasMoreData ? "flex" : "none";
    }
  };

  const updateActivityCount = (count) => {
    if (activityCount) {
      activityCount.textContent = `Mostrando ${count} acciones`;
    }
  };

  // Cargar actividades desde la API
  const loadActivities = async (reset = false) => {
    if (isLoading) return;
    
    showLoading();
    
    if (reset) {
      currentPage = 1;
      allActivities = [];
      timelineContainer.innerHTML = '';
      hasMoreData = true;
    }

    try {
      const tipo = typeFilter ? typeFilter.value !== 'all' ? typeFilter.value : null : null;
      const response = await fetch(`/api/actividades?limit=${activitiesPerPage * currentPage}${tipo ? `&tipo=${tipo}` : ''}`);
      
      if (!response.ok) {
        throw new Error('Error al cargar actividades');
      }
      
      const data = await response.json();
      
      if (data.success && data.data) {
        allActivities = data.data;
        filteredActivities = [...allActivities];
        
        // Actualizar la interfaz
        renderActivities();
        updateActivityCount(filteredActivities.length);
        
        // Verificar si hay más datos
        hasMoreData = data.data.length >= activitiesPerPage * currentPage;
        updateLoadMoreButton();
      }
    } catch (error) {
      console.error('Error al cargar actividades:', error);
      showNotification('Error al cargar las actividades', 'error');
    } finally {
      hideLoading();
    }
  };

  // Cargar estadísticas
  const loadStatistics = async () => {
    try {
      const response = await fetch('/api/actividades/estadisticas');
      
      if (!response.ok) {
        throw new Error('Error al cargar estadísticas');
      }
      
      const data = await response.json();
      
      if (data.success && data.data) {
        const stats = data.data;
        
        // Actualizar estadísticas en la interfaz
        if (loginCountElement) {
          loginCountElement.textContent = stats.logins_este_mes || '0';
        }
        
        if (doorAccessCountElement) {
          doorAccessCountElement.textContent = stats.accesos_puertas_este_mes || '0';
        }
        
        if (lastAccessElement) {
          if (stats.ultimo_acceso) {
            lastAccessElement.textContent = stats.ultimo_acceso.puerta || '-';
            // Actualizar también el span de la hora si existe
            const lastAccessTimeElement = document.getElementById('lastAccessTime');
            if (lastAccessTimeElement) {
              lastAccessTimeElement.textContent = stats.ultimo_acceso.hora || '';
            }
          } else {
            lastAccessElement.textContent = '-';
            const lastAccessTimeElement = document.getElementById('lastAccessTime');
            if (lastAccessTimeElement) {
              lastAccessTimeElement.textContent = '';
            }
          }
        }
      }
    } catch (error) {
      console.error('Error al cargar estadísticas:', error);
    }
  };

  // Renderizar actividades en la línea de tiempo
  const renderActivities = () => {
    if (!timelineContainer) return;
    
    // Limpiar solo si es una recarga completa
    if (currentPage === 1) {
      timelineContainer.innerHTML = '';
    }
    
    // Obtener actividades para la página actual
    const startIndex = (currentPage - 1) * activitiesPerPage;
    const endIndex = startIndex + activitiesPerPage;
    const activitiesToShow = filteredActivities.slice(0, endIndex);
    
    // Generar HTML para cada actividad
    activitiesToShow.forEach(activity => {
      const activityElement = createActivityElement(activity);
      timelineContainer.appendChild(activityElement);
    });
    
    // Actualizar contador
    updateActivityCount(activitiesToShow.length);
  };
  
  // Crear elemento HTML para una actividad
  const createActivityElement = (activity) => {
    const activityElement = document.createElement('div');
    activityElement.className = `activity-entry ${activity.status || 'success'}`;
    
    // Determinar el ícono según el tipo de actividad
    let iconClass = 'fa-info-circle';
    if (activity.tipo_actividad === 'door') iconClass = 'fa-door-open';
    else if (activity.tipo_actividad === 'login') iconClass = 'fa-sign-in-alt';
    else if (activity.tipo_actividad === 'profile') iconClass = 'fa-user-edit';
    
    // Determinar la clase de estado
    const statusClass = activity.status === 'error' ? 'error' : 'success';
    
    // Formatear la fecha
    const fechaFormateada = formatTime(activity.fecha_hora);
    
    // Obtener título y descripción basados en el tipo de actividad
    let title = activity.detalles || 'Actividad';
    let description = '';
    
    // Si es un acceso a puerta, extraer la descripción
    if (activity.tipo_actividad === 'door' && activity.detalles) {
      const match = activity.detalles.match(/Acceso (exitoso|denegado) a (.*)/i);
      if (match) {
        title = `Acceso ${match[1] === 'exitoso' ? 'Autorizado' : 'Denegado'}`;
        description = `Puerta: ${activity.puerta || 'Desconocida'}`;
      }
    } else if (activity.tipo_actividad === 'login' && activity.detalles) {
      // Para inicios de sesión
      title = 'Inicio de sesión';
      description = activity.detalles;
    } else if (activity.tipo_actividad === 'profile' && activity.detalles) {
      // Para actualizaciones de perfil
      title = 'Actualización de perfil';
      description = activity.detalles;
    }
    
    activityElement.innerHTML = `
      <div class="activity-icon-timeline ${activity.tipo_actividad || 'default'}">
        <i class="fas ${iconClass}"></i>
      </div>
      <div class="activity-content">
        <div class="activity-title">${title}</div>
        ${description ? `<div class="activity-description">${description}</div>` : ''}
        <div class="activity-meta">
          <div class="activity-time">
            <i class="fas fa-clock"></i>
            ${fechaFormateada}
          </div>
          ${activity.puerta ? `
          <div class="activity-location">
            <i class="fas fa-map-marker-alt"></i>
            ${activity.puerta}
          </div>
          ` : ''}
          <div class="activity-status ${statusClass}">
            ${statusClass === 'success' ? 'Completado' : 'Error'}
          </div>
        </div>
      </div>
    `;
    
    return activityElement;
  };
  
  // Función para formatear la fecha en formato relativo
  const formatTime = (timeString) => {
    const date = new Date(timeString);
    const now = new Date();
    const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);
    
    if (diffInSeconds < 60) {
      return "Hace unos segundos";
    } else if (diffInSeconds < 3600) {
      const minutes = Math.floor(diffInSeconds / 60);
      return `Hace ${minutes} minuto${minutes > 1 ? 's' : ''}`;
    } else if (diffInSeconds < 86400) {
      const hours = Math.floor(diffInSeconds / 3600);
      return `Hace ${hours} hora${hours > 1 ? 's' : ''}`;
    } else if (diffInSeconds < 604800) {
      const days = Math.floor(diffInSeconds / 86400);
      return `Hace ${days} día${days > 1 ? 's' : ''}`;
    } else {
      return date.toLocaleDateString('es-ES', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    }
  };

  // Manejar cambios en los filtros
  const handleFilterChange = () => {
    loadActivities(true);
  };

  // Cargar más actividades
  const loadMoreActivities = () => {
    if (!hasMoreData || isLoading) return;
    
    currentPage++;
    loadActivities(false);
  };

  // Inicializar la página
  const initializeActivity = () => {
    loadActivities(true);
    loadStatistics();
  };

  // Configurar event listeners
  const setupEventListeners = () => {
    // Filtros
    if (dateFilter) {
      dateFilter.addEventListener('change', handleFilterChange);
    }
    
    if (typeFilter) {
      typeFilter.addEventListener('change', handleFilterChange);
    }
    
    // Botón de actualizar
    if (refreshButton) {
      refreshButton.addEventListener('click', () => {
        loadActivities(true);
        loadStatistics();
      });
    }
    
    // Botón de cargar más
    if (loadMoreButton) {
      loadMoreButton.addEventListener('click', loadMoreActivities);
    }
    
    // Cerrar sesión
    if (logoutButton) {
      logoutButton.addEventListener('click', showLogoutModal);
    }
    
    if (modalClose) {
      modalClose.addEventListener('click', closeLogoutModal);
    }
    
    if (cancelLogout) {
      cancelLogout.addEventListener('click', closeLogoutModal);
    }
    
    if (confirmLogout) {
      confirmLogout.addEventListener('click', () => {
        window.location.href = '/logout';
      });
    }
    
    if (modalOverlay) {
      modalOverlay.addEventListener('click', closeLogoutModal);
    }
    
    // Menú móvil
    if (mobileMenuToggle && mainNav) {
      mobileMenuToggle.addEventListener('click', () => {
        mainNav.classList.toggle('active');
      });
    }
  };

  // Inicializar
  initializeActivity();
  setupEventListeners();
});
