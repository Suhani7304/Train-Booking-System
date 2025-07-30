
// Called on seat type dropdown change
function updatePrice(seatType) {
    const select = document.querySelector('select[name="seat_type"]');
    const selected = select.options[select.selectedIndex];
    const price = selected.getAttribute('data-price');
    document.getElementById("final_price").value = price;
}

// Optional: validate date is not in the past
function validateDate() {
    const dateInput = document.querySelector('input[name="date"]');
    const selectedDate = new Date(dateInput.value);
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    if (selectedDate < today) {
        alert("Please select a valid date (today or future).");
        dateInput.value = "";
        return false;
    }
    return true;
}

// Add event listener for date validation if present
document.addEventListener("DOMContentLoaded", function () {
    const dateInput = document.querySelector('input[name="date"]');
    if (dateInput) {
        dateInput.addEventListener("change", validateDate);
    }
});

function cancelBooking(bookingId, rowId) {
  if (confirm('Are you sure you want to cancel this booking?')) {
    fetch(`/cancel_booking/${bookingId}`, { method: 'POST' })
      .then(response => response.json())
      .then(data => {
        if (data.status === 'success') {
          alert('Cancelled Successfully');
          const row = document.getElementById(rowId);
          if (row) {
            // Update Status cell text to 'Cancelled'
            const statusCell = row.querySelector('.status-cell');
            if (statusCell) statusCell.textContent = 'Cancelled';

            // Hide Cancel button
            const cancelBtn = row.querySelector('.cancel-booking-btn');
            if (cancelBtn) cancelBtn.style.display = 'none';
          }
        } else {
          alert('Error cancelling booking');
        }
      })
      .catch(() => alert('Network error while cancelling booking'));
  }
}

document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('.view-details-btn').forEach(button => {
    button.addEventListener('click', () => {
      viewDetails(button.dataset.train, button.dataset.date, button.dataset.source, button.dataset.dest);
    });
  });

  document.querySelectorAll('.cancel-booking-btn').forEach(button => {
    button.addEventListener('click', () => {
      cancelBooking(button.dataset.bookingId, button.dataset.rowId);
    });
  });
});
