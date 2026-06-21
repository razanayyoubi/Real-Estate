/* -------------------------------------------------------------
   LEBESTATES CONSULTATIONS MANAGEMENT CLIENT CONTROLLER
   ------------------------------------------------------------- */

document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const searchInput = document.getElementById('search-consultations');
    const filterStatus = document.getElementById('filter-status');
    const filterConsultant = document.getElementById('filter-consultant');
    const filterMethod = document.getElementById('filter-method');
    const tableBody = document.getElementById('consultations-tbody');
    const tableRows = tableBody ? tableBody.querySelectorAll('tr[id^="consultation-row-"]') : [];

    // Modals
    const scheduleModal = document.getElementById('modal-schedule');
    const notesModal = document.getElementById('modal-notes');

    // 1. FILTER FUNCTIONALITY
    function applyFilters() {
        const query = searchInput.value.toLowerCase().trim();
        const status = filterStatus.value;
        const consultant = filterConsultant.value;
        const method = filterMethod.value;

        let visibleCount = 0;

        tableRows.forEach(row => {
            const rowSearch = row.getAttribute('data-search') || '';
            const rowStatus = row.getAttribute('data-status') || '';
            const rowConsultant = row.getAttribute('data-consultant') || '';
            const rowMethod = row.getAttribute('data-method') || '';

            const matchesSearch = !query || rowSearch.includes(query);
            const matchesStatus = status === 'All' || rowStatus === status;
            const matchesConsultant = consultant === 'All' || rowConsultant === consultant;
            const matchesMethod = method === 'All' || rowMethod === method;

            if (matchesSearch && matchesStatus && matchesConsultant && matchesMethod) {
                row.style.display = '';
                visibleCount++;
            } else {
                row.style.display = 'none';
            }
        });

        // Toggle Empty State Row
        const emptyRow = document.getElementById('empty-row');
        if (emptyRow) {
            if (visibleCount === 0) {
                emptyRow.style.display = '';
            } else {
                emptyRow.style.display = 'none';
            }
        }
    }

    if (searchInput) searchInput.addEventListener('input', applyFilters);
    if (filterStatus) filterStatus.addEventListener('change', applyFilters);
    if (filterConsultant) filterConsultant.addEventListener('change', applyFilters);
    if (filterMethod) filterMethod.addEventListener('change', applyFilters);

    // 2. ASSIGN CONSULTANT (AJAX)
    const consultantDropdowns = document.querySelectorAll('.consultant-dropdown');
    consultantDropdowns.forEach(dropdown => {
        dropdown.addEventListener('change', async (e) => {
            const id = dropdown.getAttribute('data-id');
            const employeeId = dropdown.value;
            const selectedOption = dropdown.options[dropdown.selectedIndex];
            const name = selectedOption ? selectedOption.getAttribute('data-name') : '';

            // Update row attributes for consultant filtering
            const row = document.getElementById(`consultation-row-${id}`);
            if (row) {
                row.setAttribute('data-consultant', employeeId || 'Unassigned');
            }

            // Update Avatar Initials
            const avatar = document.getElementById(`avatar-${id}`);
            if (avatar) {
                if (employeeId && name) {
                    const parts = name.split(' ');
                    avatar.textContent = parts.length > 1 ? (parts[0][0] + parts[1][0]).toUpperCase() : parts[0][0].toUpperCase();
                } else {
                    avatar.textContent = '--';
                }
            }

            try {
                const response = await fetch(`/control-panel/consultations/${id}/update_consultant`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ employee_id: employeeId ? parseInt(employeeId) : null })
                });
                const res = await response.json();
                if (!response.ok) {
                    alert(res.error || 'Failed to update consultant');
                }
            } catch (err) {
                console.error(err);
                alert('Network error. Failed to assign consultant.');
            }
        });
    });

    // 3. UPDATE STATUS (AJAX)
    const statusDropdowns = document.querySelectorAll('.status-badge');
    statusDropdowns.forEach(dropdown => {
        dropdown.addEventListener('change', async (e) => {
            const id = dropdown.getAttribute('data-id');
            const status = dropdown.value;

            // Update row attribute for status filtering
            const row = document.getElementById(`consultation-row-${id}`);
            if (row) {
                row.setAttribute('data-status', status);
            }

            // Update class lists for style colors
            dropdown.className = `status-badge status-${status.toLowerCase()}`;

            try {
                const response = await fetch(`/control-panel/consultations/${id}/update_status`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ status })
                });
                const res = await response.json();
                if (!response.ok) {
                    alert(res.error || 'Failed to update status');
                } else {
                    // Quick reload to refresh dashboard completion statistics cards
                    setTimeout(() => window.location.reload(), 300);
                }
            } catch (err) {
                console.error(err);
                alert('Network error. Failed to update status.');
            }
        });
    });

    // 4. MODAL CONTROLS: SCHEDULE
    const scheduleButtons = document.querySelectorAll('.btn-schedule');
    scheduleButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const id = btn.getAttribute('data-id');
            const date = btn.getAttribute('data-date');
            const time = btn.getAttribute('data-time');

            document.getElementById('schedule-consultation-id').value = id;
            document.getElementById('scheduled-date-input').value = date || '';
            document.getElementById('scheduled-time-input').value = time ? time.substring(0, 5) : '';

            if (scheduleModal) scheduleModal.classList.add('active');
        });
    });

    function closeScheduleModal() {
        if (scheduleModal) scheduleModal.classList.remove('active');
    }

    const closeScheduleBtn = document.getElementById('close-schedule-modal');
    const cancelScheduleBtn = document.getElementById('cancel-schedule-modal');
    if (closeScheduleBtn) closeScheduleBtn.addEventListener('click', closeScheduleModal);
    if (cancelScheduleBtn) cancelScheduleBtn.addEventListener('click', closeScheduleModal);

    const formSchedule = document.getElementById('form-schedule');
    if (formSchedule) {
        formSchedule.addEventListener('submit', async (e) => {
            e.preventDefault();
            const id = document.getElementById('schedule-consultation-id').value;
            const date = document.getElementById('scheduled-date-input').value;
            const time = document.getElementById('scheduled-time-input').value;

            try {
                const response = await fetch(`/control-panel/consultations/${id}/update_schedule`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ scheduled_date: date, scheduled_time: time })
                });
                const res = await response.json();
                if (response.ok) {
                    window.location.reload();
                } else {
                    alert(res.error || 'Failed to schedule');
                }
            } catch (err) {
                console.error(err);
                alert('Network error. Failed to schedule appointment.');
            }
        });
    }

    // 5. MODAL CONTROLS: NOTES
    const notesButtons = document.querySelectorAll('.btn-notes');
    notesButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const id = btn.getAttribute('data-id');
            const message = btn.getAttribute('data-message');
            const notes = btn.getAttribute('data-notes');

            document.getElementById('notes-consultation-id').value = id;
            document.getElementById('notes-customer-msg').textContent = message || '(No initial message sent)';
            document.getElementById('notes-textarea').value = notes || '';

            if (notesModal) notesModal.classList.add('active');
        });
    });

    function closeNotesModal() {
        if (notesModal) notesModal.classList.remove('active');
    }

    const closeNotesBtn = document.getElementById('close-notes-modal');
    const cancelNotesBtn = document.getElementById('cancel-notes-modal');
    if (closeNotesBtn) closeNotesBtn.addEventListener('click', closeNotesModal);
    if (cancelNotesBtn) cancelNotesBtn.addEventListener('click', closeNotesModal);

    const formNotes = document.getElementById('form-notes');
    if (formNotes) {
        formNotes.addEventListener('submit', async (e) => {
            e.preventDefault();
            const id = document.getElementById('notes-consultation-id').value;
            const notesText = document.getElementById('notes-textarea').value;

            try {
                const response = await fetch(`/control-panel/consultations/${id}/update_notes`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ notes: notesText })
                });
                const res = await response.json();
                if (response.ok) {
                    window.location.reload();
                } else {
                    alert(res.error || 'Failed to save notes');
                }
            } catch (err) {
                console.error(err);
                alert('Network error. Failed to update notes.');
            }
        });
    }

    // 6. PDF REPORT PRINTING
    const btnExport = document.getElementById('btn-export-pdf');
    if (btnExport) {
        btnExport.addEventListener('click', () => {
            window.print();
        });
    }
});
