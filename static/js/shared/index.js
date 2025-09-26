document.addEventListener("DOMContentLoaded", () => {
  // Seleccionar todos los contenedores
  const containers = document.querySelectorAll(".container");

  // Asegurar que todos los contenedores tengan la misma altura
  function equalizeContainerHeights() {
    // Resetear alturas para recalcular
    containers.forEach((container) => {
      container.style.height = "auto";
    });

    // Encontrar la altura máxima
    let maxHeight = 0;
    containers.forEach((container) => {
      const height = container.offsetHeight;
      maxHeight = Math.max(maxHeight, height);
    });

    // Aplicar la altura máxima a todos los contenedores
    containers.forEach((container) => {
      container.style.height = `${maxHeight}px`;
    });
  }

  // Ejecutar al cargar y al cambiar el tamaño de la ventana
  equalizeContainerHeights();
  window.addEventListener("resize", equalizeContainerHeights);

  // Añadir efectos al pasar el mouse
  containers.forEach((container) => {
    // Efecto de entrada suave al cargar la página
    container.style.opacity = "1";

    container.addEventListener("mouseenter", function () {
      // Transición suave para el hover
      const icon = this.querySelector("i");

      // Añadir clase para animación controlada
      if (icon) {
        // Eliminar cualquier animación previa
        icon.style.animation = "none";

        // Forzar un reflow para reiniciar la animación
        void icon.offsetWidth;

        // Aplicar la animación de forma suave
        icon.style.animation = "iconPulse 1s cubic-bezier(0.34, 1.56, 0.64, 1) forwards";
      }
    });

    // Restaurar transición normal al salir
    container.addEventListener("mouseleave", function () {
      const icon = this.querySelector("i");
      if (icon) {
        icon.style.animation = "";
      }
    });

    // Añadir efecto de clic
    container.addEventListener("mousedown", function () {
      // Efecto sutil de presión
      this.style.transform = "translateY(-5px) scale(0.98)";
    });

    container.addEventListener("mouseup", function () {
      // Restaurar estado
      this.style.transform = "translateY(-10px)";
    });

    // Asegurar que el efecto se restaure si el mouse sale durante el clic
    container.addEventListener("mouseleave", function () {
      this.style.transform = "";
    });
  });

  // Añadir estilos dinámicos para animaciones
  const style = document.createElement("style");
  style.innerHTML = `
    @keyframes iconPulse {
      0% { transform: scale(1); }
      50% { transform: scale(1.15); }
      100% { transform: scale(1.15); }
    }
    
    .container {
      transition: transform 0.4s cubic-bezier(0.22, 1, 0.36, 1), 
                  box-shadow 0.4s cubic-bezier(0.22, 1, 0.36, 1),
                  background 0.4s ease;
    }
    
    .container:active {
      transition: transform 0.2s cubic-bezier(0.22, 1, 0.36, 1);
    }
  `;
  document.head.appendChild(style);

  // Animación al hacer scroll
  const cards = document.querySelectorAll('.card');
  
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('animate-box');
        observer.unobserve(entry.target);
      }
    });
  }, {
    threshold: 0.1
  });
  
  cards.forEach(card => {
    card.classList.remove('animate-box');
    observer.observe(card);
  });

  // Simulación de notificaciones
  const notificationCount = 3;
  const notificationLinks = document.querySelectorAll('a[href="#"][title="Notificaciones"]');

  notificationLinks.forEach(link => {
    const badge = document.createElement('span');
    badge.classList.add('notification-badge');
    badge.textContent = notificationCount;
    link.appendChild(badge);
  });

  const grid = document.querySelector('.cards-grid');
  if (grid && grid.children.length === 2) {
    grid.classList.add('two-items');
  }

  // NUEVA FUNCIONALIDAD - Menú móvil responsive
  const mobileMenuToggle = document.getElementById('mobileMenuToggle');
  const mainNav = document.getElementById('mainNav');
  
  if (mobileMenuToggle && mainNav) {
    mobileMenuToggle.addEventListener('click', function() {
      this.classList.toggle('active');
      mainNav.classList.toggle('show');
    });
    
    // Cerrar menú al hacer clic en un enlace
    const navLinks = mainNav.querySelectorAll('a');
    navLinks.forEach(link => {
      link.addEventListener('click', () => {
        mobileMenuToggle.classList.remove('active');
        mainNav.classList.remove('show');
      });
    });
    
    // Cerrar menú al hacer clic fuera
    document.addEventListener('click', function(e) {
      if (!mobileMenuToggle.contains(e.target) && !mainNav.contains(e.target)) {
        mobileMenuToggle.classList.remove('active');
        mainNav.classList.remove('show');
      }
    });
  }

  // NUEVA FUNCIONALIDAD - Modal de confirmación para cerrar sesión
  const logoutButton = document.getElementById('logoutButton');
  const logoutModal = document.getElementById('logoutModal');
  const modalOverlay = document.getElementById('modalOverlay');
  const modalClose = document.getElementById('modalClose');
  const cancelLogout = document.getElementById('cancelLogout');
  const confirmLogout = document.getElementById('confirmLogout');
  
  // Mostrar modal de confirmación
  if (logoutButton) {
    logoutButton.addEventListener('click', function(e) {
      e.preventDefault();
      showLogoutModal();
    });
  }
  
  // Cerrar modal
  function closeLogoutModal() {
    if (logoutModal) logoutModal.classList.remove('show');
    if (modalOverlay) modalOverlay.classList.remove('show');
  }
  
  // Mostrar modal
  function showLogoutModal() {
    if (logoutModal) logoutModal.classList.add('show');
    if (modalOverlay) modalOverlay.classList.add('show');
  }
  
  // Event listeners para cerrar modal
  if (modalClose) {
    modalClose.addEventListener('click', closeLogoutModal);
  }
  
  if (cancelLogout) {
    cancelLogout.addEventListener('click', closeLogoutModal);
  }
  
  if (modalOverlay) {
    modalOverlay.addEventListener('click', closeLogoutModal);
  }
  
  // Confirmar cierre de sesión
  if (confirmLogout) {
    confirmLogout.addEventListener('click', function() {
      // Mostrar mensaje de carga
      this.textContent = 'Cerrando...';
      this.disabled = true;
      
      // Realizar petición al servidor para cerrar sesión
      fetch('/auth/logout', {
        method: 'GET',
        credentials: 'same-origin'
      })
      .then(response => {
        if (response.ok) {
          // Limpiar localStorage si es necesario
          localStorage.clear();
          
          // Redirigir directamente a login
          window.location.href = '/login';
        } else {
          console.error('Error al cerrar sesión');
          window.location.href = '/login';
        }
      })
      .catch(error => {
        console.error('Error:', error);
        window.location.href = '/login';
      });
    });
  }
  
  // Cerrar modal con tecla Escape
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
      closeLogoutModal();
    }
  });
  
  // Función para mostrar notificaciones temporales
  function showNotification(message, type = 'info') {
    // Crear elemento de notificación temporal
    const notification = document.createElement('div');
    notification.className = `temp-notification ${type}`;
    notification.textContent = message;
    
    // Estilos para la notificación temporal
    notification.style.cssText = `
      position: fixed;
      top: 90px;
      right: 20px;
      background: ${type === 'success' ? '#10B981' : type === 'error' ? '#EF4444' : '#3B82F6'};
      color: white;
      padding: 12px 20px;
      border-radius: 8px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
      z-index: 10000;
      font-weight: 500;
      transform: translateX(100%);
      transition: transform 0.3s ease;
      max-width: 300px;
      word-wrap: break-word;
    `;
    
    document.body.appendChild(notification);
    
    // Animar entrada
    setTimeout(() => {
      notification.style.transform = 'translateX(0)';
    }, 100);
    
    // Remover después de 3 segundos
    setTimeout(() => {
      notification.style.transform = 'translateX(100%)';
      setTimeout(() => {
        if (notification.parentNode) {
          notification.parentNode.removeChild(notification);
        }
      }, 300);
    }, 3000);
  }
  
  // Ajustar layout en cambio de tamaño de ventana
  window.addEventListener('resize', function() {
    // Cerrar menú móvil si se cambia a desktop
    if (window.innerWidth > 768) {
      if (mobileMenuToggle) mobileMenuToggle.classList.remove('active');
      if (mainNav) mainNav.classList.remove('show');
    }
    
    // Cerrar modal en pantallas muy pequeñas si causa problemas
    if (window.innerWidth < 400) {
      closeLogoutModal();
    }
  });
  
  console.log("Dashboard inicializado correctamente");
});

// Funciones adicionales para mejorar la experiencia
window.addEventListener('resize', function() {
  // Cerrar elementos que puedan causar problemas en resize
  const mainNav = document.getElementById('mainNav');
  const mobileMenuToggle = document.getElementById('mobileMenuToggle');
  
  if (window.innerWidth > 768) {
    if (mainNav) mainNav.classList.remove('show');
    if (mobileMenuToggle) mobileMenuToggle.classList.remove('active');
  }
});

// Mejorar accesibilidad con navegación por teclado
document.addEventListener('keydown', function(e) {
  // Navegación con Tab más fluida
  if (e.key === 'Tab') {
    document.body.classList.add('keyboard-navigation');
  }
});

document.addEventListener('mousedown', function() {
  document.body.classList.remove('keyboard-navigation');
});

// Agregar estilos para navegación por teclado
const keyboardStyle = document.createElement('style');
keyboardStyle.innerHTML = `
  .keyboard-navigation *:focus {
    outline: 2px solid var(--color2) !important;
    outline-offset: 2px;
  }
`;
document.head.appendChild(keyboardStyle);