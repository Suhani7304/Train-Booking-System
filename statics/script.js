
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
