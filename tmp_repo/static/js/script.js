// BiletService main JavaScript file

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Handle favorite button clicks
    setupFavoriteButtons();
    
    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    const popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl, {
            html: true
        });
    });
    
    // Handle quantity inputs
    setupQuantityInputs();
    
    // Initialize date picker elements if available
    setupDatePickers();
    
    // Setup search form
    setupSearchForm();
    
    // Setup filter toggle
    setupFilterToggle();
});

// Setup favorite buttons with AJAX functionality
function setupFavoriteButtons() {
    const favoriteButtons = document.querySelectorAll('.favorite-btn');
    
    favoriteButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Check if user is logged in
            if (this.dataset.requireLogin === 'true') {
                window.location.href = '/login';
                return;
            }
            
            const eventId = this.dataset.eventId;
            const icon = this.querySelector('i');
            
            // Send AJAX request
            fetch(`/favorites/add/${eventId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'added') {
                    this.classList.add('active');
                    icon.classList.remove('far');
                    icon.classList.add('fas');
                    showToast('Мероприятие добавлено в избранное', 'success');
                } else {
                    this.classList.remove('active');
                    icon.classList.remove('fas');
                    icon.classList.add('far');
                    showToast('Мероприятие удалено из избранного', 'info');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showToast('Произошла ошибка. Пожалуйста, попробуйте еще раз.', 'danger');
            });
        });
    });
}

// Setup quantity input controls
function setupQuantityInputs() {
    const quantityControls = document.querySelectorAll('.quantity-control');
    
    quantityControls.forEach(control => {
        const decreaseBtn = control.querySelector('.quantity-decrease');
        const increaseBtn = control.querySelector('.quantity-increase');
        const input = control.querySelector('input');
        
        if (decreaseBtn && increaseBtn && input) {
            decreaseBtn.addEventListener('click', function() {
                let value = parseInt(input.value);
                if (value > 1) {
                    input.value = value - 1;
                    
                    // If in cart, submit the form
                    const updateForm = this.closest('form');
                    if (updateForm && updateForm.classList.contains('update-cart-form')) {
                        updateForm.submit();
                    }
                }
            });
            
            increaseBtn.addEventListener('click', function() {
                let value = parseInt(input.value);
                input.value = value + 1;
                
                // If in cart, submit the form
                const updateForm = this.closest('form');
                if (updateForm && updateForm.classList.contains('update-cart-form')) {
                    updateForm.submit();
                }
            });
            
            input.addEventListener('change', function() {
                let value = parseInt(this.value);
                if (isNaN(value) || value < 1) {
                    this.value = 1;
                }
            });
        }
    });
}

// Setup datepicker if flatpickr is available
function setupDatePickers() {
    if (typeof flatpickr !== 'undefined') {
        flatpickr(".datepicker", {
            dateFormat: "Y-m-d",
            locale: "ru"
        });
        
        flatpickr(".datetimepicker", {
            dateFormat: "Y-m-d H:i",
            enableTime: true,
            time_24hr: true,
            locale: "ru"
        });
    }
}

// Show toast notifications
function showToast(message, type = 'info') {
    // Create toast container if not exist
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(container);
    }
    
    const toastId = `toast-${Date.now()}`;
    const html = `
        <div id="${toastId}" class="toast align-items-center text-white bg-${type} border-0" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;
    
    container.insertAdjacentHTML('beforeend', html);
    
    const toastEl = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastEl, {
        autohide: true,
        delay: 3000
    });
    
    toast.show();
    
    // Remove toast from DOM after it's hidden
    toastEl.addEventListener('hidden.bs.toast', function() {
        this.remove();
    });
}

// Setup search form
function setupSearchForm() {
    const searchForm = document.getElementById('search-form');
    const filterToggle = document.getElementById('filter-toggle');
    
    if (searchForm && filterToggle) {
        searchForm.addEventListener('submit', function(e) {
            // Remove empty inputs to keep URL clean
            const inputs = this.querySelectorAll('input, select');
            inputs.forEach(input => {
                if (input.value === '' || input.value === '0') {
                    input.disabled = true;
                }
            });
        });
    }
}

// Setup filter toggle
function setupFilterToggle() {
    const filterToggle = document.getElementById('filter-toggle');
    const filterContainer = document.getElementById('filter-container');
    
    if (filterToggle && filterContainer) {
        filterToggle.addEventListener('click', function(e) {
            e.preventDefault();
            filterContainer.classList.toggle('d-none');
        });
    }
}
