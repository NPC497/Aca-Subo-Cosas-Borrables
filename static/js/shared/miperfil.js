// Variables globales
let originalFormData = {}
const DEFAULT_PHOTO_URL = "/static/img/shared/default.jpeg" // URL de la imagen predeterminada
let selectedPhotoFile = null // archivo seleccionado para subir
let photoRemoved = false // si el usuario marcó eliminar foto

// Inicialización cuando se carga la página
document.addEventListener("DOMContentLoaded", () => {
  initializePage()
})

// Función de inicialización
function initializePage() {
  // Guardar datos originales del formulario
  saveOriginalFormData()

  // Configurar event listeners
  setupEventListeners()

  // No sobrescribir la imagen inicial proveniente del servidor
  updatePhotoButtonsState()
  selectedPhotoFile = null
  photoRemoved = false

  // Mostrar mensaje de bienvenida
  setTimeout(() => {
    showToast("Bienvenido a tu perfil", "success")
  }, 500)
}

// Guardar datos originales del formulario
function saveOriginalFormData() {
  const personalForm = document.getElementById("personalForm")
  const formData = new FormData(personalForm)

  originalFormData = {}
  for (const [key, value] of formData.entries()) {
    originalFormData[key] = value
  }
}

// Configurar event listeners
function setupEventListeners() {
  // Validación en tiempo real para contraseñas
  const confirmPassword = document.getElementById("confirmPassword")
  const newPassword = document.getElementById("newPassword")

  confirmPassword.addEventListener("input", validatePasswordMatch)
  newPassword.addEventListener("input", validatePasswordStrength)

  // Prevenir envío de formularios
  document.getElementById("personalForm").addEventListener("submit", (e) => {
    e.preventDefault()
    saveChanges()
  })

  document.getElementById("passwordForm").addEventListener("submit", (e) => {
    e.preventDefault()
    saveChanges()
  })

  // Cerrar modal al hacer clic fuera
  document.getElementById("deleteModal").addEventListener("click", function (e) {
    if (e.target === this) {
      hideDeleteModal()
    }
  })

  // Detectar cambios en el formulario
  const inputs = document.querySelectorAll("input, select, textarea")
  inputs.forEach((input) => {
    input.addEventListener("change", markFormAsChanged)
  })
}

// Marcar formulario como modificado
function markFormAsChanged() {
  const saveBtn = document.querySelector(".btn-primary")
  if (saveBtn && !saveBtn.classList.contains("changed")) {
    saveBtn.classList.add("changed")
    saveBtn.innerHTML = '<i class="fas fa-save"></i> Guardar Cambios *'
  }
}

// Funciones para manejo de contraseñas
function togglePassword(fieldId) {
  const field = document.getElementById(fieldId)
  const button = field.nextElementSibling
  const icon = button.querySelector("i")

  if (field.type === "password") {
    field.type = "text"
    icon.classList.remove("fa-eye")
    icon.classList.add("fa-eye-slash")
  } else {
    field.type = "password"
    icon.classList.remove("fa-eye-slash")
    icon.classList.add("fa-eye")
  }
}

// Validar coincidencia de contraseñas
function validatePasswordMatch() {
  const newPassword = document.getElementById("newPassword").value
  const confirmPassword = document.getElementById("confirmPassword").value
  const confirmField = document.getElementById("confirmPassword")

  if (confirmPassword && newPassword !== confirmPassword) {
    confirmField.classList.add("input-error")
    confirmField.classList.remove("input-success")
    return false
  } else if (confirmPassword) {
    confirmField.classList.remove("input-error")
    confirmField.classList.add("input-success")
    return true
  }

  confirmField.classList.remove("input-error", "input-success")
  return true
}

// Validar fortaleza de contraseña
function validatePasswordStrength() {
  const password = document.getElementById("newPassword").value
  const field = document.getElementById("newPassword")

  if (!password) {
    field.classList.remove("input-error", "input-success")
    return
  }

  const hasMinLength = password.length >= 8
  const hasUpperCase = /[A-Z]/.test(password)
  const hasLowerCase = /[a-z]/.test(password)
  const hasNumbers = /\d/.test(password)
  const hasSpecialChar = /[!@#$%^&*(),.?":{}|<>]/.test(password)

  const strength = [hasMinLength, hasUpperCase, hasLowerCase, hasNumbers, hasSpecialChar].filter(Boolean).length

  if (strength < 3) {
    field.classList.add("input-error")
    field.classList.remove("input-success")
  } else {
    field.classList.remove("input-error")
    field.classList.add("input-success")
  }
}

// Funciones para manejo de foto de perfil
function handlePhotoUpload(event) {
  const file = event.target.files[0]
  if (!file) return

  // Validar tipo de archivo
  if (!file.type.startsWith("image/")) {
    showToast("Por favor selecciona un archivo de imagen válido.", "error")
    return
  }

  // Validar tamaño (5MB máximo)
  if (file.size > 5 * 1024 * 1024) {
    showToast("El archivo es demasiado grande. Máximo 5MB.", "error")
    return
  }

  // Mostrar loading visual
  const photoContainer = document.querySelector(".profile-photo-container")
  photoContainer.style.opacity = "0.6"

  const reader = new FileReader()
  reader.onload = (e) => {
    const img = document.getElementById("profilePhoto")
    img.src = e.target.result
    photoContainer.style.opacity = "1"
    img.style.transform = "scale(1.1)"
    setTimeout(() => { img.style.transform = "scale(1)" }, 300)

    selectedPhotoFile = file
    photoRemoved = false
    showToast("Foto seleccionada. Recuerda guardar cambios.", "success")
    markFormAsChanged()
    updatePhotoButtonsState()
  }
  reader.onerror = () => {
    photoContainer.style.opacity = "1"
    showToast("Error al cargar la imagen. Inténtalo de nuevo.", "error")
  }
  reader.readAsDataURL(file)
}

// Función para actualizar el estado de los botones
function updatePhotoButtonsState() {
  const removeBtn = document.getElementById("removePhotoBtn")
  const changeBtn = document.getElementById("changePhotoBtn")
  const isDefault = isDefaultPhoto()

  if (isDefault) {
    // Cuando es foto por defecto
    removeBtn.style.display = "none"
    changeBtn.innerHTML = '<i class="fas fa-plus"></i> Añadir Foto'
    changeBtn.title = "Añadir foto de perfil"
  } else {
    // Cuando no es foto por defecto
    removeBtn.style.display = "inline-block"
    removeBtn.disabled = false
    removeBtn.title = "Eliminar foto de perfil"
    changeBtn.innerHTML = '<i class="fas fa-upload"></i> Cambiar Foto'
    changeBtn.title = "Cambiar foto de perfil"
  }
}

function removePhoto() {
  if (isDefaultPhoto()) {
    showToast("No se puede eliminar la foto predeterminada.", "error")
    return
  }

  if (confirm("¿Estás seguro de que deseas eliminar tu foto de perfil?")) {
    const img = document.getElementById("profilePhoto")

    // Animar la eliminación
    img.style.transform = "scale(0)"
    setTimeout(() => {
      img.src = DEFAULT_PHOTO_URL // Vuelve a la imagen predeterminada
      img.style.transform = "scale(1)"
      updatePhotoButtonsState() // Actualizar el estado de los botones
    }, 300)

    document.getElementById("photoInput").value = "" // Limpiar el input de archivo
    selectedPhotoFile = null
    photoRemoved = true
    showToast("La foto se eliminará al guardar.", "success")
    markFormAsChanged()
  }
}

// (Eliminada función duplicada handlePhotoUpload)

// Función para verificar si es la foto por defecto
function isDefaultPhoto() {
  const img = document.getElementById("profilePhoto")
  // Verificar si la imagen actual es la por defecto
  return img.src.includes("default.jpeg") || img.src.includes("default.jpg")
}

// Llamar a la función al cargar la página para establecer el estado inicial
document.addEventListener('DOMContentLoaded', function() {
  updatePhotoButtonsState()
  // Limpiar posibles valores autofill de contraseñas
  const pwdIds = ["currentPassword", "newPassword", "confirmPassword"]
  pwdIds.forEach(id => {
    const el = document.getElementById(id)
    if (el) {
      el.value = ""
      el.setAttribute("value", "")
      setTimeout(() => {
        el.value = ""
        el.setAttribute("value", "")
      }, 0)
    }
  })
})

// Funciones para guardar cambios
async function saveChanges() {
  // Mostrar loading
  const saveBtn = document.querySelector(".btn-primary")
  const originalText = saveBtn.innerHTML
  saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Guardando...'
  saveBtn.disabled = true

  try {
    // Validar formulario personal
    const personalForm = document.getElementById("personalForm")
    if (!personalForm.checkValidity()) {
      personalForm.reportValidity()
      return
    }

    // Datos personales
    const nombre = document.getElementById("nombre").value.trim()
    const apellido = document.getElementById("apellido").value.trim()
    const email = document.getElementById("email").value.trim()

    // Validar contraseñas si se están cambiando
    const newPassword = document.getElementById("newPassword").value
    const confirmPassword = document.getElementById("confirmPassword").value
    const currentPassword = document.getElementById("currentPassword").value

    if (newPassword || confirmPassword) {
      if (!currentPassword) {
        showToast("Debes ingresar tu contraseña actual para cambiarla.", "error")
        return
      }
      if (newPassword !== confirmPassword) {
        showToast("Las contraseñas nuevas no coinciden.", "error")
        return
      }
      // Reglas: mínimo 8, una mayúscula, una minúscula, un número y un caracter especial
      const hasMinLength = newPassword.length >= 8
      const hasUpperCase = /[A-Z]/.test(newPassword)
      const hasLowerCase = /[a-z]/.test(newPassword)
      const hasNumbers = /\d/.test(newPassword)
      const hasSpecialChar = /[!@#$%^&*(),.?":{}|<>]/.test(newPassword)
      if (!(hasMinLength && hasUpperCase && hasLowerCase && hasNumbers && hasSpecialChar)) {
        showToast("La nueva contraseña debe tener mínimo 8 caracteres, una mayúscula, una minúscula, un número y un caracter especial.", "error")
        return
      }
    }

    // 1) Guardar información personal
    const respInfo = await fetch('/api/miPerfil/actualizar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ nombre, apellido, email })
    })
    const dataInfo = await respInfo.json()
    if (!respInfo.ok || !dataInfo.success) {
      throw new Error(dataInfo.message || 'Error al actualizar la información')
    }

    // 2) Cambiar contraseña si corresponde
    if (newPassword) {
      const respPwd = await fetch('/api/miPerfil/cambiar-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ currentPassword, newPassword })
      })
      const dataPwd = await respPwd.json()
      if (!respPwd.ok || !dataPwd.success) {
        throw new Error(dataPwd.message || 'Error al cambiar la contraseña')
      }
    }

    // 3) Subir/eliminar foto si corresponde
    if (selectedPhotoFile || photoRemoved) {
      const formData = new FormData()
      if (photoRemoved) {
        formData.append('remove', '1')
      } else if (selectedPhotoFile) {
        formData.append('foto', selectedPhotoFile)
      }
      const respPhoto = await fetch('/api/miPerfil/foto', {
        method: 'POST',
        body: formData
      })
      const dataPhoto = await respPhoto.json()
      if (!respPhoto.ok || !dataPhoto.success) {
        throw new Error(dataPhoto.message || 'Error al actualizar la foto de perfil')
      }
      // Actualizar src con la URL devuelta o default si fue eliminada
      const img = document.getElementById('profilePhoto')
      img.src = dataPhoto.photo_url || DEFAULT_PHOTO_URL
      updatePhotoButtonsState()
      // Resetear flags
      selectedPhotoFile = null
      photoRemoved = false
    }

    // Éxito
    showToast("Cambios guardados correctamente.", "success")

    // Animar las secciones actualizadas
    const sections = document.querySelectorAll(".form-section")
    sections.forEach((section) => {
      section.classList.add("updated")
      setTimeout(() => {
        section.classList.remove("updated")
      }, 500)
    })

    // Actualizar datos originales
    saveOriginalFormData()

    // Limpiar campos de contraseña
    document.getElementById("currentPassword").value = ""
    document.getElementById("newPassword").value = ""
    document.getElementById("confirmPassword").value = ""

    // Remover clases de validación
    document.querySelectorAll(".input-error, .input-success").forEach((input) => {
      input.classList.remove("input-error", "input-success")
    })
  } catch (e) {
    console.error(e)
    showToast(e.message || "Error al guardar cambios.", "error")
  } finally {
    restoreSaveButton(saveBtn, originalText)
  }
}

function restoreSaveButton(button, originalText) {
  button.innerHTML = originalText
  button.disabled = false
  button.classList.remove("changed")
}

function resetForms() {
  if (confirm("¿Estás seguro de que deseas cancelar los cambios?")) {
    // Restaurar formulario personal
    const personalForm = document.getElementById("personalForm")
    Object.keys(originalFormData).forEach((key) => {
      const field = personalForm.querySelector(`[name="${key}"]`)
      if (field) {
        field.value = originalFormData[key]
      }
    })

    // Limpiar formulario de contraseña
    document.getElementById("passwordForm").reset()

    // Remover clases de validación
    document.querySelectorAll(".input-error, .input-success").forEach((input) => {
      input.classList.remove("input-error", "input-success")
    })

    // Restaurar botón de guardar
    const saveBtn = document.querySelector(".btn-primary")
    saveBtn.classList.remove("changed")
    saveBtn.innerHTML = '<i class="fas fa-save"></i> Guardar Cambios'

    showToast("Formularios restablecidos.", "success")
  }
}

// Funciones para acciones de cuenta
function logout() {
  if (confirm("¿Estás seguro de que deseas cerrar sesión?")) {
    showToast("Cerrando sesión...", "success")

    // Animar salida
    const container = document.querySelector(".main-container")
    container.style.transform = "scale(0.9)"
    container.style.opacity = "0.5"

    setTimeout(() => {
      // Redirección real al logout del backend
      window.location.href = '/auth/logout'
    }, 1500)
  }
}

function showDeleteModal() {
  const modal = document.getElementById("deleteModal")
  modal.classList.add("show")

  // Enfocar en el primer botón
  setTimeout(() => {
    modal.querySelector(".btn-secondary").focus()
  }, 100)
}

function hideDeleteModal() {
  const modal = document.getElementById("deleteModal")
  modal.classList.remove("show")

  // Limpiar el select
  document.getElementById("deleteReason").value = ""
}

async function deleteAccount() {
  const reason = document.getElementById("deleteReason").value

  // Mostrar confirmación final
  const confirmText = 'Para confirmar la eliminación, escribe "ELIMINAR" en mayúsculas:'
  const userConfirmation = prompt(confirmText)

  if (userConfirmation !== "ELIMINAR") {
    showToast("Eliminación cancelada.", "error")
    return
  }

  showToast("Procesando baja de cuenta...", "error")

  const container = document.querySelector(".main-container")
  container.style.transform = "scale(0.8)"
  container.style.opacity = "0.3"

  try {
    const resp = await fetch('/api/miPerfil/baja', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reason })
    })
    const data = await resp.json().catch(() => ({ success: false }))
    if (!resp.ok || !data.success) {
      throw new Error(data.message || 'No se pudo desactivar la cuenta')
    }

    hideDeleteModal()
    showToast("Cuenta desactivada. Cerrando sesión...", "success")
    setTimeout(() => {
      window.location.href = '/auth/logout'
    }, 1200)
  } catch (e) {
    console.error(e)
    showToast(e.message || 'Error al procesar la baja de cuenta', 'error')
    // Revertir animación si falla
    container.style.transform = "scale(1)"
    container.style.opacity = "1"
  }
}

// Funciones para mostrar toast
function showToast(message, type = "success") {
  const toast = document.getElementById("toast")
  const toastMessage = document.getElementById("toastMessage")

  toastMessage.textContent = message
  toast.className = `toast ${type} show`

  // Auto-hide después de 4 segundos
  setTimeout(() => {
    hideToast()
  }, 4000)
}

function hideToast() {
  const toast = document.getElementById("toast")
  toast.classList.remove("show")
}

// Determinar si el formulario tiene cambios reales
function isFormDirty() {
  // Comparar datos personales
  const personalForm = document.getElementById('personalForm')
  const current = new FormData(personalForm)
  for (const [key, value] of current.entries()) {
    if ((originalFormData[key] || '') !== (value || '')) {
      return true
    }
  }
  // Revisar campos que no están en personalForm (contraseñas)
  const currentPassword = document.getElementById('currentPassword')?.value || ''
  const newPassword = document.getElementById('newPassword')?.value || ''
  const confirmPassword = document.getElementById('confirmPassword')?.value || ''
  if (currentPassword || newPassword || confirmPassword) return true

  // Revisar cambios de foto pendientes
  if (selectedPhotoFile || photoRemoved) return true

  return false
}

// Función para volver atrás
function goBack() {
  const hasChanges = isFormDirty()

  const navigate = () => {
    const fallback = '/'
    const ref = document.referrer && document.referrer !== location.href ? document.referrer : fallback
    const url = new URL(ref, window.location.origin)
    url.searchParams.set('_ts', Date.now().toString()) // cache-busting para forzar recarga
    window.location.replace(url.toString())
  }

  if (hasChanges) {
    if (confirm("¿Estás seguro de que deseas salir? Los cambios no guardados se perderán.")) {
      navigate()
    }
  } else {
    navigate()
  }
}

// Funciones de utilidad
function validateEmail(email) {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return re.test(email)
}

function validatePhone(phone) {
  const re = /^[+]?[1-9][\d]{0,15}$/
  return re.test(phone.replace(/\s/g, ""))
}

// Manejo de errores globales
window.addEventListener("error", (e) => {
  console.error("Error:", e.error)
  showToast("Ha ocurrido un error inesperado. Por favor, recarga la página.", "error")
})

// Prevenir pérdida de datos al cerrar la página
window.addEventListener("beforeunload", (e) => {
  const hasChanges = typeof isFormDirty === 'function' ? isFormDirty() : !!document.querySelector('.btn-primary.changed')

  if (hasChanges) {
    e.preventDefault()
    e.returnValue = "¿Estás seguro de que deseas salir? Los cambios no guardados se perderán."
    return e.returnValue
  }
})
