let contadorReenvio = 60;
let intervaloCuentaRegresiva;
let currentEmail = ""; // To store the email entered in step 1

// Helper function to show a step and hide others
function showStep(stepId) {
  document.querySelectorAll(".form-step").forEach((step) => {
    step.classList.add("hidden");
  });
  document.getElementById(stepId).classList.remove("hidden");
}

// Validation functions
function validateEmail(email) {
  const patronEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return patronEmail.test(email);
}

function validateCode(code) {
  const codigo = code.replace(/\D/g, ""); // Only numbers
  return codigo.length === 6;
}

function validatePassword(password) {
  // At least 6 characters (matching server-side validation)
  return password.length >= 6;
}

// Formatear entrada del código (only numbers)
document.getElementById("campoCodigo")?.addEventListener("input", function (e) {
  this.value = this.value.replace(/\D/g, "");
  // Optional: add real-time validation feedback here if desired
});

// Step 1: Handle Email Submission
document.getElementById("formularioEmail")?.addEventListener("submit", function (evento) {
  evento.preventDefault();

  const campoEmail = document.getElementById("campoEmail");
  const emailValue = campoEmail.value.trim();
  const invalidFeedback = campoEmail.nextElementSibling;
  const submitButton = this.querySelector("button[type='submit']");
  const buttonText = this.querySelector(".button-text-code");
  const loadingIndicator = this.querySelector(".loading-indicator-code");

  if (!validateEmail(emailValue)) {
    campoEmail.classList.add("is-invalid");
    if (invalidFeedback) invalidFeedback.style.display = "block";
    return;
  } else {
    campoEmail.classList.remove("is-invalid");
    if (invalidFeedback) invalidFeedback.style.display = "none";
  }

  // Show loading state
  if (loadingIndicator && buttonText && submitButton) {
    buttonText.classList.add("d-none");
    loadingIndicator.classList.remove("d-none");
    submitButton.disabled = true;
  }

  // Send request to server
  fetch("/auth/solicitar-codigo", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ email: emailValue }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        currentEmail = emailValue;
        showStep("paso2");
        iniciarCuentaRegresiva();
      } else {
        alert(data.message || "Error al enviar el código de verificación");
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      alert("Ocurrió un error al procesar la solicitud.");
    })
    .finally(() => {
      // Reset button state
      if (loadingIndicator && buttonText && submitButton) {
        buttonText.classList.remove("d-none");
        loadingIndicator.classList.add("d-none");
        submitButton.disabled = false;
      }
    });
});

// Step 2: Handle Code Verification
document.getElementById("formularioCodigo")?.addEventListener("submit", function (evento) {
  evento.preventDefault();

  const campoCodigo = document.getElementById("campoCodigo");
  const codigo = campoCodigo.value.trim();
  const submitButton = this.querySelector("button[type='submit']");
  const buttonText = this.querySelector(".button-text-code");
  const loadingIndicator = this.querySelector(".loading-indicator-code");

  if (!validateCode(codigo)) {
    alert("Por favor ingrese un código de 6 dígitos");
    return;
  }

  // Show loading state
  if (loadingIndicator && buttonText && submitButton) {
    buttonText.classList.add("d-none");
    loadingIndicator.classList.remove("d-none");
    submitButton.disabled = true;
  }

  // Send request to server
  fetch("/auth/verificar-codigo", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ 
      email: currentEmail,
      codigo: codigo
    }),
    credentials: 'same-origin'  // Important for session cookies
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        showStep("paso3");
      } else {
        alert(data.message || "Código inválido o expirado");
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      alert("Ocurrió un error al verificar el código.");
    })
    .finally(() => {
      // Reset button state
      if (loadingIndicator && buttonText && submitButton) {
        buttonText.classList.remove("d-none");
        loadingIndicator.classList.add("d-none");
        submitButton.disabled = false;
      }
    });
});

// Step 3: Handle Password Change
document.getElementById("formularioNuevaContrasena")?.addEventListener("submit", function (evento) {
  evento.preventDefault();

  const nuevaContrasena = document.getElementById("campoContrasena").value;
  const confirmarContrasena = document.getElementById("campoConfirmarContrasena").value;
  const submitButton = this.querySelector("button[type='submit']");
  const buttonText = submitButton.querySelector(".button-text");
  const loadingIndicator = submitButton.querySelector(".loading-indicator");

  if (nuevaContrasena.length < 8) {
    alert("La contraseña debe tener al menos 8 caracteres");
    return;
  }

  if (nuevaContrasena !== confirmarContrasena) {
    alert("Las contraseñas no coinciden");
    return;
  }

  // Show loading state
  if (loadingIndicator && buttonText) {
    buttonText.classList.add("d-none");
    loadingIndicator.classList.remove("d-none");
    submitButton.disabled = true;
  }

  // Send request to server
  fetch("/auth/cambiar-contrasena", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ 
      nueva_contrasena: nuevaContrasena 
    }),
    credentials: 'same-origin' // Important for sessions to work
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        // Show success message and redirect to login after 2 seconds
        alert("¡Contraseña actualizada exitosamente!");
        window.location.href = "/auth/login";
      } else {
        alert(data.message || "Error al actualizar la contraseña");
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      alert("Ocurrió un error al actualizar la contraseña.");
    })
    .finally(() => {
      // Reset button state
      if (loadingIndicator && buttonText) {
        buttonText.classList.remove("d-none");
        loadingIndicator.classList.add("d-none");
        submitButton.disabled = false;
      }
    });
});

// Timer for resend code button
function iniciarCuentaRegresiva() {
  const botonReenviar = document.getElementById("botonReenviar");
  const contadorElemento = document.getElementById("contadorReenvio");
  
  if (!botonReenviar) return;
  
  botonReenviar.disabled = true;
  contadorReenvio = 60;
  
  if (contadorElemento) {
    contadorElemento.textContent = contadorReenvio;
    contadorElemento.style.display = "inline";
  }
  
  intervaloCuentaRegresiva = setInterval(() => {
    contadorReenvio--;
    
    if (contadorElemento) {
      contadorElemento.textContent = contadorReenvio;
    }
    
    if (contadorReenvio <= 0) {
      clearInterval(intervaloCuentaRegresiva);
      botonReenviar.disabled = false;
      if (contadorElemento) {
        contadorElemento.style.display = "none";
      }
    }
  }, 1000);
}

// Resend code button click handler
document.getElementById("botonReenviar")?.addEventListener("click", function () {
  if (this.disabled) return;
  
  // Reuse the email submission logic
  const submitEvent = new Event("submit");
  document.getElementById("formularioEmail").dispatchEvent(submitEvent);
});

// Navigation functions
function volverPaso1() {
  showStep("paso1");
}

function redirigirNuevaContrasena() {
  showStep("paso4");
}

function volverPaso2() {
  showStep("paso2");
}

// Toggle password visibility
function togglePasswordVisibility(inputId) {
  const input = document.getElementById(inputId);
  const icon = document.querySelector(`[onclick="togglePasswordVisibility('${inputId}')"] i`);
  
  if (input.type === "password") {
    input.type = "text";
    icon.classList.remove("fa-eye");
    icon.classList.add("fa-eye-slash");
  } else {
    input.type = "password";
    icon.classList.remove("fa-eye-slash");
    icon.classList.add("fa-eye");
  }
}

// Initial setup: show step 1
document.addEventListener("DOMContentLoaded", () => {
  showStep("paso1");
});
