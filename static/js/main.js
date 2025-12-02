// Filtros del catálogo
document.addEventListener('DOMContentLoaded', function() {
    const filterType = document.getElementById('filter-type');
    const filterSize = document.getElementById('filter-size');
    const petCards = document.querySelectorAll('.pet-card');
    
    function filterPets() {
        const selectedType = filterType ? filterType.value : 'all';
        const selectedSize = filterSize ? filterSize.value : 'all';
        
        petCards.forEach(card => {
            const petType = card.dataset.type;
            const petSize = card.dataset.size;
            
            const typeMatch = selectedType === 'all' || petType === selectedType;
            const sizeMatch = selectedSize === 'all' || petSize === selectedSize;
            
            if (typeMatch && sizeMatch) {
                card.style.display = 'block';
            } else {
                card.style.display = 'none';
            }
        });
    }
    
    if (filterType && filterSize) {
        filterType.addEventListener('change', filterPets);
        filterSize.addEventListener('change', filterPets);
    }
    
    const messages = document.querySelectorAll('.message');
    messages.forEach(message => {
        setTimeout(() => {
            message.style.opacity = '0';
            setTimeout(() => {
                message.remove();
            }, 300);
        }, 5000);
    });
    
    // Funciones para reportes
    window.generatePDFReport = function() {
        alert('Generando reporte PDF...');
    };
    
    window.generateCSVReport = function() {
        alert('Generando reporte CSV...');
    };
});