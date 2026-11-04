/**
 * Black Eagles Zipline - Real-Time Slot Booking Engine
 * Developed for PL SOFT TECH SOLUTIONS
 */

document.addEventListener('DOMContentLoaded', function () {
  const dateInput = document.getElementById('id_booking_date');
  const slotContainer = document.getElementById('slotsContainer');
  const slotLoading = document.getElementById('slotLoading');
  const slotError = document.getElementById('slotErrorMessage');
  const hiddenSlotInput = document.getElementById('id_slot_id');
  const membersInput = document.getElementById('id_number_of_members');
  const btnDecrement = document.getElementById('btnDecrementMembers');
  const btnIncrement = document.getElementById('btnIncrementMembers');
  const bookingSubmitBtn = document.getElementById('btnSubmitBooking');
  const bookingForm = document.getElementById('customerBookingForm');

  // Summary Elements
  const summaryDate = document.getElementById('summaryDate');
  const summarySlot = document.getElementById('summarySlot');
  const summaryMembers = document.getElementById('summaryMembers');

  let currentSelectedSlot = null;

  // Initialize
  if (dateInput && slotContainer) {
    // Fetch availability on load
    fetchSlotsForDate(dateInput.value);

    // Fetch availability on date change
    dateInput.addEventListener('change', function () {
      fetchSlotsForDate(this.value);
    });
  }

  function fetchSlotsForDate(dateStr) {
    if (!dateStr) return;

    // Reset selection
    currentSelectedSlot = null;
    if (hiddenSlotInput) hiddenSlotInput.value = '';
    updateSummary();

    // Check Wednesday on client side for instant feedback (noon anchor avoids timezone boundary shifts)
    const [year, month, day] = dateStr.split('-').map(Number);
    const chosenDate = new Date(year, month - 1, day, 12, 0, 0);
    if (chosenDate.getDay() === 3) { // Wednesday is day 3 in JS getDay() (Sunday=0, Wed=3)
      showError("Sorry! Bookings are not available on this date.");
      slotContainer.innerHTML = '';
      return;
    }

    // Show loading
    if (slotLoading) slotLoading.classList.remove('d-none');
    if (slotError) slotError.classList.add('d-none');
    slotContainer.innerHTML = '';

    fetch(`/book/availability/?date=${encodeURIComponent(dateStr)}`)
      .then(response => response.json())
      .then(data => {
        if (slotLoading) slotLoading.classList.add('d-none');

        if (!data.success) {
          showError(data.message || "Sorry! Bookings are not available on this date.");
          return;
        }

        if (!data.slots || data.slots.length === 0) {
          showError("All slots are fully booked for this date. Please select another date.");
          return;
        }

        renderSlots(data.slots);
      })
      .catch(err => {
        if (slotLoading) slotLoading.classList.add('d-none');
        showError("Failed to fetch slot availability. Please try again or select another date.");
        console.error("Slot fetch error:", err);
      });
  }

  function showError(msg) {
    if (slotError) {
      slotError.textContent = msg;
      slotError.classList.remove('d-none');
    }
    if (slotContainer) {
      slotContainer.innerHTML = `
        <div class="col-12">
          <div class="alert alert-dark border border-warning text-warning d-flex align-items-center gap-2" role="alert">
            <i class="bi bi-exclamation-triangle-fill fs-5"></i>
            <div>${msg}</div>
          </div>
        </div>
      `;
    }
  }

  function renderSlots(slots) {
    slotContainer.innerHTML = '';
    slots.forEach(slot => {
      const col = document.createElement('div');
      col.className = 'col-md-6 mb-3';

      const seatBadgeClass = slot.available_seats <= 2 ? 'seat-badge limited' : 'seat-badge available';

      col.innerHTML = `
        <div class="slot-card" data-slot-id="${slot.id}" data-slot-name="${slot.name}" data-slot-time="${slot.formatted_time}" data-available="${slot.available_seats}">
          <div class="d-flex justify-content-between align-items-start mb-2">
            <h6 class="mb-0 text-white fw-bold">${slot.name}</h6>
            <span class="${seatBadgeClass}">
              ${slot.available_seats} seat${slot.available_seats > 1 ? 's' : ''} left
            </span>
          </div>
          <div class="d-flex align-items-center gap-2 text-warning fs-6">
            <i class="bi bi-clock-fill"></i>
            <span>${slot.formatted_time}</span>
          </div>
        </div>
      `;

      col.querySelector('.slot-card').addEventListener('click', function () {
        document.querySelectorAll('.slot-card').forEach(c => c.classList.remove('selected'));
        this.classList.add('selected');

        currentSelectedSlot = {
          id: slot.id,
          name: slot.name,
          time: slot.formatted_time,
          available: slot.available_seats
        };

        if (hiddenSlotInput) {
          hiddenSlotInput.value = slot.id;
        }

        // Adjust member count if current selection exceeds slot capacity
        const currentMembers = parseInt(membersInput.value, 10) || 1;
        if (currentMembers > slot.available_seats) {
          membersInput.value = slot.available_seats;
        }

        updateSummary();
      });

      slotContainer.appendChild(col);
    });

    // Auto-select first slot
    const firstSlot = slotContainer.querySelector('.slot-card');
    if (firstSlot) {
      firstSlot.click();
    }
  }

  // Stepper handlers
  if (btnDecrement && membersInput) {
    btnDecrement.addEventListener('click', function () {
      let val = parseInt(membersInput.value, 10) || 1;
      if (val > 1) {
        membersInput.value = val - 1;
        updateSummary();
      }
    });
  }

  if (btnIncrement && membersInput) {
    btnIncrement.addEventListener('click', function () {
      let val = parseInt(membersInput.value, 10) || 1;
      const maxAllowed = currentSelectedSlot ? Math.min(6, currentSelectedSlot.available) : 6;
      if (val < maxAllowed) {
        membersInput.value = val + 1;
        updateSummary();
      } else if (currentSelectedSlot && val >= currentSelectedSlot.available) {
        alert(`This slot only has ${currentSelectedSlot.available} seat(s) remaining.`);
      }
    });
  }

  function updateSummary() {
    if (dateInput && summaryDate) {
      const val = dateInput.value;
      if (val) {
        const parts = val.split('-');
        const d = new Date(parts[0], parts[1] - 1, parts[2]);
        summaryDate.textContent = d.toLocaleDateString('en-GB', {
          weekday: 'short',
          day: 'numeric',
          month: 'short',
          year: 'numeric'
        });
      } else {
        summaryDate.textContent = 'None selected';
      }
    }

    if (summarySlot) {
      if (currentSelectedSlot) {
        summarySlot.textContent = `${currentSelectedSlot.name} (${currentSelectedSlot.time})`;
      } else {
        summarySlot.textContent = 'Select a slot below';
      }
    }

    if (summaryMembers && membersInput) {
      const count = membersInput.value || 1;
      summaryMembers.textContent = `${count} Passenger${count > 1 ? 's' : ''}`;
    }
  }

  // Prevent multiple submits
  if (bookingForm && bookingSubmitBtn) {
    bookingForm.addEventListener('submit', function (e) {
      if (!hiddenSlotInput || !hiddenSlotInput.value) {
        e.preventDefault();
        alert('Please select an available time slot before submitting.');
        return;
      }
      bookingSubmitBtn.disabled = true;
      bookingSubmitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span> Reserving Slots...';
    });
  }
});

