// JavaScript for Blockchain Hotel Booking System

document.addEventListener('DOMContentLoaded', function () {
    // 1. Live Price Calculation on Booking Page
    const checkinInput = document.getElementById('checkin');
    const checkoutInput = document.getElementById('checkout');
    const roomTypeSelect = document.getElementById('room_type');
    const basePriceText = document.getElementById('base_price_display');
    const totalAmountText = document.getElementById('total_amount_display');
    const totalNightsText = document.getElementById('total_nights_display');
    const totalAmountInput = document.getElementById('total_amount_input');

    // Room multiplier configuration
    const roomMultipliers = {
        'Standard Room': 1.0,
        'Deluxe Room': 1.5,
        'Luxury Room': 2.2,
        'Suite': 3.5
    };

    function calculateBookingPrice() {
        if (!checkinInput || !checkoutInput || !roomTypeSelect || !totalAmountText) return;

        const checkinDateVal = checkinInput.value;
        const checkoutDateVal = checkoutInput.value;
        const roomType = roomTypeSelect.value;
        const basePrice = parseInt(basePriceText.dataset.price || 0, 10);

        if (!checkinDateVal || !checkoutDateVal) {
            totalAmountText.innerText = "₹" + basePrice.toLocaleString('en-IN');
            totalNightsText.innerText = "0";
            return;
        }

        const checkin = new Date(checkinDateVal);
        const checkout = new Date(checkoutDateVal);

        // Time difference in milliseconds
        const timeDiff = checkout.getTime() - checkin.getTime();
        
        if (timeDiff <= 0) {
            totalAmountText.innerText = "Invalid Dates";
            totalNightsText.innerText = "0";
            if (totalAmountInput) totalAmountInput.value = 0;
            return;
        }

        // Calculate nights
        const nights = Math.ceil(timeDiff / (1000 * 3600 * 24));
        const multiplier = roomMultipliers[roomType] || 1.0;
        const pricePerNight = basePrice * multiplier;
        const totalAmount = Math.round(pricePerNight * nights);

        // Update displays
        totalNightsText.innerText = nights;
        totalAmountText.innerText = "₹" + totalAmount.toLocaleString('en-IN');
        if (totalAmountInput) totalAmountInput.value = totalAmount;
    }

    // Set event listeners for calculation
    if (checkinInput && checkoutInput && roomTypeSelect) {
        checkinInput.addEventListener('change', calculateBookingPrice);
        checkoutInput.addEventListener('change', calculateBookingPrice);
        roomTypeSelect.addEventListener('change', calculateBookingPrice);
        
        // Prevent selecting past checkin date
        const today = new Date().toISOString().split('T')[0];
        checkinInput.setAttribute('min', today);
        
        // Prevent selecting checkout date before checkin date
        checkinInput.addEventListener('change', function() {
            checkoutInput.setAttribute('min', checkinInput.value);
            if (checkoutInput.value && checkoutInput.value <= checkinInput.value) {
                checkoutInput.value = '';
            }
            calculateBookingPrice();
        });

        // Trigger on load
        calculateBookingPrice();
    }

    // 2. Form submission protection & animations
    const bookingForm = document.getElementById('booking-form');
    if (bookingForm) {
        bookingForm.addEventListener('submit', function (e) {
            const checkinVal = checkinInput.value;
            const checkoutVal = checkoutInput.value;
            if (new Date(checkoutVal) <= new Date(checkinVal)) {
                e.preventDefault();
                alert("Check-out date must be later than check-in date.");
            }
        });
    }

    // 3. Delete Confirmation Dialogs
    const deleteButtons = document.querySelectorAll('.confirm-delete');
    deleteButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            const message = this.dataset.message || "Are you sure you want to delete this item?";
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });
});

// 4. Download PDF Receipt (using client-side html2pdf.js)
function downloadPDFReceipt(elementId, filename) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    // Add temporary styling for PDF optimization
    element.style.padding = "20px";
    
    const opt = {
        margin:       0.3,
        filename:     filename,
        image:        { type: 'jpeg', quality: 0.98 },
        html2canvas:  { scale: 2, useCORS: true },
        jsPDF:        { unit: 'in', format: 'letter', orientation: 'portrait' }
    };
    
    // Check if html2pdf is loaded from CDN
    if (typeof html2pdf !== 'undefined') {
        html2pdf().set(opt).from(element).save().then(() => {
            // Restore styling
            element.style.padding = "";
        });
    } else {
        // Fallback: Trigger browser printing
        window.print();
    }
}

// 5. Generate QR Code
function showQRCode(text, modalId, title) {
    const qrContainer = document.getElementById('qrcode-container');
    const qrTitle = document.getElementById('qr-modal-title');
    if (!qrContainer) return;
    
    qrContainer.innerHTML = ''; // clear previous
    if (qrTitle) qrTitle.innerText = title || "Booking Details";
    
    // Check if QRCode is loaded from CDN
    if (typeof QRCode !== 'undefined') {
        new QRCode(qrContainer, {
            text: text,
            width: 160,
            height: 160,
            colorDark: "#0a192f",
            colorLight: "#ffffff",
            correctLevel: QRCode.CorrectLevel.H
        });
    } else {
        // Fallback to Google Charts API if offline
        const img = document.createElement('img');
        img.src = `https://chart.googleapis.com/chart?chs=160x160&cht=qr&chl=${encodeURIComponent(text)}&choe=UTF-8`;
        img.alt = "Booking QR Code";
        img.style.border = "1px solid #ddd";
        qrContainer.appendChild(img);
    }
}
