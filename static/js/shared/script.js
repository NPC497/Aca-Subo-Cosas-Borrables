document.addEventListener('DOMContentLoaded', function() {
    const squares = document.querySelectorAll('.square');
    const animationDuration = 3000; // 3 segundos por animación
    const totalDistance = 340; // Distancia total que recorren los cuadrados (px)
    
    // Calculamos el espacio entre cuadrados para que estén equidistantes
    const spaceBetweenSquares = totalDistance / squares.length;
    
    function startAnimation() {
        squares.forEach((square, index) => {
            // Configurar la animación con retraso progresivo
            square.style.animation = `moveLeft ${animationDuration}ms linear infinite`;
            
            // Calculamos el retraso para que los cuadrados mantengan su distancia
            // y creen un efecto de "tren" continuo
            const delay = (animationDuration / totalDistance) * spaceBetweenSquares * index;
            square.style.animationDelay = `${delay}ms`;
        });
    }
    
    startAnimation();
});

const images = document.querySelectorAll('.image-container img');
let currentIndex = 0;
const changeInterval = 180; // 3 segundos
function changeImage() {
  images[currentIndex].classList.remove('active');
  currentIndex = (currentIndex + 1) % images.length;
  images[currentIndex].classList.add('active');
}
setInterval(changeImage, changeInterval);