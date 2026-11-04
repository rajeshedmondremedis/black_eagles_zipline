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

  // Summary Card Elements
  const summaryDate = document.getElementById('summaryDate');
  const summarySlot = document.getElementById('summarySlot');
  const summaryMembers = document.getElementById('summaryMembers');

  let currentSelectedSlot = null;

  // Initialize
  if (dateInput && slotContainer) {
    // Initial fetch on page load
    fetchSlotsForDate(dateInput.value);

    // Fetch on date change
    dateInput.addEventListener('change', function () {
      fetchSlotsForDate(this.value);
    });
  }

  function fetchSlotsForDate(dateStr) {
    if (!dateStr) return;

    // Reset current selection
    currentSelectedSlot = null;
    if (hiddenSlotInput) hiddenSlotInput.value = '';
    updateSummary();

    // Check Wednesday on client side for instant feedback (noon anchor prevents timezone edge issues)
    const [year, month, day] = dateStr.split('-').map(Number);
    const chosenDate = new Date(year, month - 1, day, 12, 0, 0);
    if (chosenDate.getDay() === 3) { // 3 = Wednesday
      showError("Sorry! Bookings are not available on this date. Wednesdays are reserved for routine line testing & maintenance.");
      if (slotContainer) slotContainer.innerHTML = '';
      return;
    }

    // Show loading state
    if (slotLoading) slotLoading.classList.remove('d-none');
    if (slotError) slotError.classList.add('d-none');
    if (slotContainer) slotContainer.innerHTML = '';

    fetch(`/book/availability/?date=${encodeURIComponent(dateStr)}`)
      .then(response => response.json())
      .then(data => {
        if (slotLoading) slotLoading.classList.add('d-none');

        if (!data.success) {
          showError(data.message || "Sorry! Bookings are not available on this date.");
          return;
        }

        if (!data.slots || data.slots.length === 0) {
          showError("All operating slots are fully booked for this date. Please select another flight date.");
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
          <div class="p-3 rounded-3 bg-dark border border-warning border-opacity-50 text-warning d-flex align-items-center gap-3">
            <i class="bi bi-shield-exclamation fs-3"></i>
            <div>
              <strong class="d-block text-white">Date Unavailable</strong>
              <span class="small">${msg}</span>
            </div>
          </div>
        </div>
      `;
    }
  }

  function renderSlots(slots) {
    slotContainer.innerHTML = '';

    slots.forEach((slot, index) => {
      const col = document.createElement('div');
      col.className = 'col-sm-6 mb-3';

      const isLimited = slot.available_seats <= 2;
      const seatBadgeClass = isLimited ? 'seat-badge limited' : 'seat-badge available';
      const badgeIcon = isLimited ? 'bi-exclamation-circle' : 'bi-check-circle-fill';

      // Pick contextual icon based on order / slot name
      let slotIcon = 'bi-clock-fill';
      const lower = (slot.name || '').toLowerCase();
      if (lower.includes('morning') || lower.includes('early')) slotIcon = 'bi-sunrise-fill';
      else if (lower.includes('noon') || lower.includes('mid')) slotIcon = 'bi-sun-fill';
      else if (lower.includes('sunset') || lower.includes('evening')) slotIcon = 'bi-sunset-fill';

      col.innerHTML = `
        <div class="slot-card" data-slot-id="${slot.id}" data-slot-name="${slot.name}" data-slot-time="${slot.formatted_time}" data-available="${slot.available_seats}">
          <div class="d-flex justify-content-between align-items-start mb-2">
            <div class="d-flex align-items-center gap-2">
              <i class="bi ${slotIcon} text-warning fs-5"></i>
              <h6 class="mb-0 text-white fw-bold">${slot.name}</h6>
            </div>
            <span class="${seatBadgeClass}">
              <i class="bi ${badgeIcon}"></i> ${slot.available_seats} seat${slot.available_seats > 1 ? 's' : ''} left
            </span>
          </div>
          <div class="d-flex align-items-center gap-2 text-warning fs-6 fw-bold mt-2">
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

        // Adjust member count if current members exceeds available seats in this slot
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
        alert(`This flight slot only has ${currentSelectedSlot.available} seat(s) remaining.`);
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
        summarySlot.textContent = 'Select an operating slot';
      }
    }

    if (summaryMembers && membersInput) {
      const count = membersInput.value || 1;
      summaryMembers.textContent = `${count} Passenger${count > 1 ? 's' : ''}`;
    }
  }

  // Prevent multiple submits & show loading indicator
  if (bookingForm && bookingSubmitBtn) {
    bookingForm.addEventListener('submit', function (e) {
      if (!hiddenSlotInput || !hiddenSlotInput.value) {
        e.preventDefault();
        alert('Please select an operating time slot before proceeding.');
        return;
      }
      bookingSubmitBtn.disabled = true;
      bookingSubmitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status"></span> Reserving Your Flight...';
    });
  }
});
