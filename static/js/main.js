// Main JavaScript file for MAGIK TIKET

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM fully loaded - initializing scripts');
    
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Add favorite button functionality with AJAX
    const favoriteButtons = document.querySelectorAll('.favorite-btn');
    console.log('Found favorite buttons:', favoriteButtons.length);
    
    favoriteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('Favorite button clicked');
            
            const eventId = this.getAttribute('data-event-id');
            const isFavorite = this.classList.contains('active');
            const action = isFavorite ? 'remove' : 'add';
            
            console.log(`Processing ${action} favorite for event ${eventId}`);
            
            // Send AJAX request
            fetch(`/favorites/${action}/${eventId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin'
            })
            .then(response => {
                console.log('Response status:', response.status);
                return response.json();
            })
            .then(data => {
                console.log('Response data:', data);
                if (data.success) {
                    // Toggle active class
                    this.classList.toggle('active');
                    
                    // Update icon color
                    const icon = this.querySelector('i');
                    if (icon) {
                        icon.classList.toggle('text-white');
                        icon.classList.toggle('text-warning');
                    }
                    
                    // Update text
                    const textSpan = this.querySelector('.favorite-text');
                    if (textSpan) {
                        textSpan.textContent = action === 'add' ? 'Удалить из избранного' : 'Добавить в избранное';
                    }
                    
                    // Show toast notification
                    const toastContainer = document.getElementById('toast-container');
                    console.log('Toast container:', toastContainer);
                    
                    const toastId = `toast-${Date.now()}`;
                    const toastHtml = `
                        <div id="${toastId}" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
                            <div class="toast-header bg-${action === 'add' ? 'success' : 'warning'}">
                                <i class="fas fa-${action === 'add' ? 'heart' : 'times'} me-2" style="color: white;"></i>
                                <strong class="me-auto" style="color: white;">Избранное</strong>
                                <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
                            </div>
                            <div class="toast-body">
                                Мероприятие ${action === 'add' ? 'добавлено в' : 'удалено из'} избранное
                            </div>
                        </div>
                    `;
                    
                    toastContainer.innerHTML += toastHtml;
                    const toast = new bootstrap.Toast(document.getElementById(toastId));
                    toast.show();
                }
            })
            .catch(error => console.error('Error:', error));
        });
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
