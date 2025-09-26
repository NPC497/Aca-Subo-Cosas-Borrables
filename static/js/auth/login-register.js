document.addEventListener("DOMContentLoaded", () => {
  const themeToggle = document.getElementById("theme-toggle");
  
  // Only initialize theme functionality if the toggle exists
  if (themeToggle) {
    const themeIcon = themeToggle.querySelector("i");
    const themeImage = document.getElementById("theme-image");

    // Only proceed if required elements exist
    if (themeIcon && themeImage) {
      // Rutas de las imágenes para cada tema
      const defaultImage = "img/LOGOSINFONDO.png";
      const hoverImage = "img/LOGOCOMIENDOPACMAN.png";

      // Verificar si hay un tema guardado en localStorage
      const savedTheme = localStorage.getItem("theme");

      // Función para configurar los event listeners de hover para la imagen
      function setupHoverEffects() {
        // Añadir efectos de hover para ambos temas
        themeImage.addEventListener("mouseenter", () => {
          themeImage.src = hoverImage;
        });

        themeImage.addEventListener("mouseleave", () => {
          themeImage.src = defaultImage;
        });
      }

      // Aplicar el tema guardado o el tema por defecto (claro)
      if (savedTheme === "dark") {
        document.body.setAttribute("data-theme", "dark");
        themeIcon.classList.remove("fa-moon");
        themeIcon.classList.add("fa-sun");
      } else {
        document.body.removeAttribute("data-theme");
        themeIcon.classList.remove("fa-sun");
        themeIcon.classList.add("fa-moon");
      }

      // Establecer la imagen inicial
      themeImage.src = defaultImage;

      // Configurar los efectos hover
      setupHoverEffects();

      // Función para cambiar el tema
      function toggleTheme() {
        // Añadir clase para la animación de transición
        themeImage.classList.add("image-transition");

        if (document.body.getAttribute("data-theme") === "dark") {
          // Cambiar a tema claro
          document.body.removeAttribute("data-theme");
          localStorage.setItem("theme", "light");
          themeIcon.classList.remove("fa-sun");
          themeIcon.classList.add("fa-moon");
        } else {
          // Cambiar a tema oscuro
          document.body.setAttribute("data-theme", "dark");
          localStorage.setItem("theme", "dark");
          themeIcon.classList.remove("fa-moon");
          themeIcon.classList.add("fa-sun");
        }

        // Eliminar la clase de transición después de la animación
        setTimeout(() => {
          themeImage.classList.remove("image-transition");
        }, 300);
      }

      // Agregar evento de clic al botón de cambio de tema
      themeToggle.addEventListener("click", toggleTheme);
    }
  }
});