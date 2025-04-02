// Main JavaScript file for MAGIK TIKET

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Add favorite button functionality
    const favoriteButtons = document.querySelectorAll('.favorite-btn');
    
    favoriteButtons.forEach(button => {
        // We don't need to attach click handler anymore since buttons now directly submit the form
        // The type="submit" attribute on the button will take care of form submission
    });

    // Delivery method toggle in checkout form
    const deliveryMethodRadios = document.querySelectorAll('input[name="delivery_method"]');
    const addressField = document.getElementById('address-field');
    
    if (deliveryMethodRadios.length > 0 && addressField) {
        deliveryMethodRadios.forEach(radio => {
            radio.addEventListener('change', function() {
                if (this.value === 'courier') {
                    addressField.classList.remove('d-none');
                } else {
                    addressField.classList.add('d-none');
                }
            });
        });
        
        // Initial state
        const checkedMethod = document.querySelector('input[name="delivery_method"]:checked');
        if (checkedMethod && checkedMethod.value === 'courier') {
            addressField.classList.remove('d-none');
        } else {
            addressField.classList.add('d-none');
        }
    }

    // Ticket type toggle in sell ticket form
    const ticketTypeRadios = document.querySelectorAll('input[name="ticket_type"]');
    const sectionRowSeatFields = document.getElementById('section-row-seat-fields');
    
    if (ticketTypeRadios.length > 0 && sectionRowSeatFields) {
        ticketTypeRadios.forEach(radio => {
            radio.addEventListener('change', function() {
                if (this.value === 'physical') {
                    sectionRowSeatFields.classList.remove('d-none');
                } else {
                    sectionRowSeatFields.classList.add('d-none');
                }
            });
        });
        
        // Initial state
        const checkedType = document.querySelector('input[name="ticket_type"]:checked');
        if (checkedType && checkedType.value === 'physical') {
            sectionRowSeatFields.classList.remove('d-none');
        } else {
            sectionRowSeatFields.classList.add('d-none');
        }
    }

    // Search form validation
    const searchForm = document.querySelector('.search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            const queryInput = this.querySelector('input[name="query"]');
            if (queryInput && queryInput.value.trim() === '') {
                e.preventDefault();
                
                // Add focus to search input
                queryInput.focus();
                
                // Add error class
                queryInput.classList.add('is-invalid');
                
                // Add error message
                let errorMessage = document.createElement('div');
                errorMessage.className = 'invalid-feedback';
                errorMessage.textContent = 'Введите поисковый запрос';
                
                // Remove any existing error message first
                const existingError = queryInput.nextElementSibling;
                if (existingError && existingError.className === 'invalid-feedback') {
                    existingError.remove();
                }
                
                queryInput.parentNode.appendChild(errorMessage);
            }
        });
    }

    // Venue map modal
    const venueMapBtn = document.getElementById('venue-map-btn');
    const venueMap = document.getElementById('venue-map');
    
    if (venueMapBtn && venueMap) {
        venueMapBtn.addEventListener('click', function() {
            const mapModal = new bootstrap.Modal(document.getElementById('venue-map-modal'));
            mapModal.show();
        });
    }

    // Admin dashboard charts (if Chart.js is included)
    if (typeof Chart !== 'undefined' && document.getElementById('sales-chart')) {
        const salesCtx = document.getElementById('sales-chart').getContext('2d');
        
        const salesChart = new Chart(salesCtx, {
            type: 'line',
            data: {
                labels: ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь'],
                datasets: [{
                    label: 'Продажи',
                    data: [12, 19, 3, 5, 2, 3],
                    backgroundColor: 'rgba(255, 52, 52, 0.2)',
                    borderColor: '#FF3434',
                    borderWidth: 2,
                    tension: 0.4
                }]
            },
            options: {
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
    
    if (typeof Chart !== 'undefined' && document.getElementById('events-chart')) {
        const eventsCtx = document.getElementById('events-chart').getContext('2d');
        
        const eventsChart = new Chart(eventsCtx, {
            type: 'doughnut',
            data: {
                labels: ['Концерты', 'Театр', 'Спорт', 'Выставки', 'Детям', 'Кино'],
                datasets: [{
                    label: 'Мероприятия',
                    data: [12, 19, 3, 5, 2, 3],
                    backgroundColor: [
                        '#FF3434',
                        '#FFCC33',
                        '#151443',
                        '#36A2EB',
                        '#4BC0C0',
                        '#9966FF'
                    ],
                    borderWidth: 1
                }]
            }
        });
    }
});
