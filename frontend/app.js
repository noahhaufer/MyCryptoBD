// Telegram Web App API
const tg = window.Telegram.WebApp;

// API Configuration
const API_URL = 'http://localhost:8000';  // Change this to your backend URL

// State
let accessToken = null;
let currentUser = null;
let contacts = [];
let selectedContact = null;

// Initialize the app
async function init() {
    // Check if opened in Telegram
    if (!window.Telegram || !window.Telegram.WebApp || !tg.initData) {
        document.getElementById('loading').innerHTML = `
            <div style="text-align: center; padding: 40px 20px;">
                <h2 style="font-size: 24px; margin-bottom: 16px;">⚠️ Open in Telegram</h2>
                <p style="color: #666; line-height: 1.6;">
                    This app only works when opened through your Telegram bot.
                    <br><br>
                    <strong>How to open:</strong><br>
                    1. Find your bot on Telegram<br>
                    2. Send /start<br>
                    3. Click "Open Contacts Tracker"
                </p>
            </div>
        `;
        return;
    }

    // Expand Telegram Web App
    tg.expand();

    // Apply Telegram theme
    document.body.style.backgroundColor = tg.themeParams.bg_color || '#ffffff';

    try {
        // Authenticate with backend
        await authenticate();

        // Load contacts
        await loadContacts();

        // Show main app
        document.getElementById('loading').classList.add('hidden');
        document.getElementById('main-app').classList.remove('hidden');

        // Setup event listeners
        setupEventListeners();

        // Update stats
        updateStats();

    } catch (error) {
        console.error('Initialization error:', error);
        document.getElementById('loading').innerHTML = `
            <div style="text-align: center; padding: 40px 20px;">
                <h2 style="font-size: 24px; margin-bottom: 16px; color: #e53e3e;">❌ Error</h2>
                <p style="color: #666;">
                    ${error.message}
                    <br><br>
                    Please try again or contact support.
                </p>
            </div>
        `;
    }
}

// Authenticate with backend using Telegram init data
async function authenticate() {
    const initData = tg.initData;

    const response = await fetch(`${API_URL}/auth/telegram`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            init_data: initData
        })
    });

    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Authentication failed: ${errorText}`);
    }

    const data = await response.json();
    accessToken = data.access_token;
    currentUser = data.user;

    console.log('Authenticated successfully');
}

// Load contacts from backend
async function loadContacts() {
    try {
        const response = await fetch(`${API_URL}/contacts`, {
            headers: {
                'Authorization': `Bearer ${accessToken}`
            }
        });

        if (!response.ok) {
            throw new Error('Failed to load contacts');
        }

        contacts = await response.json();
        renderContacts(contacts);

    } catch (error) {
        console.error('Error loading contacts:', error);
        tg.showAlert('Failed to load contacts');
    }
}

// Render contacts list
function renderContacts(contactsToRender) {
    const contactsList = document.getElementById('contacts-list');
    const emptyState = document.getElementById('empty-state');

    if (contactsToRender.length === 0) {
        contactsList.innerHTML = '';
        emptyState.classList.remove('hidden');
        return;
    }

    emptyState.classList.add('hidden');

    contactsList.innerHTML = contactsToRender.map(contact => {
        const fullName = [contact.first_name, contact.last_name]
            .filter(Boolean)
            .join(' ') || 'Unknown';

        const addedDate = new Date(contact.added_date).toLocaleDateString();

        return `
            <div class="contact-card" data-id="${contact.id}">
                <div class="contact-header">
                    <div class="contact-name">${fullName}</div>
                    <div class="contact-badge ${contact.is_exported ? 'badge-exported' : 'badge-new'}">
                        ${contact.is_exported ? 'Exported' : 'New'}
                    </div>
                </div>
                <div class="contact-info">
                    ${contact.company ? `<div class="contact-company">${contact.company}</div>` : ''}
                    ${contact.username ? `<div class="contact-username">@${contact.username}</div>` : ''}
                    ${contact.phone_number ? `<div class="contact-phone">${contact.phone_number}</div>` : ''}
                    <div class="contact-date">Added: ${addedDate}</div>
                </div>
            </div>
        `;
    }).join('');

    // Add click listeners to contact cards
    document.querySelectorAll('.contact-card').forEach(card => {
        card.addEventListener('click', () => {
            const contactId = parseInt(card.dataset.id);
            openContactModal(contactId);
        });
    });
}

// Update statistics
function updateStats() {
    const total = contacts.length;
    const exported = contacts.filter(c => c.is_exported).length;
    const newContacts = total - exported;

    document.getElementById('total-contacts').textContent = total;
    document.getElementById('exported-contacts').textContent = exported;
    document.getElementById('new-contacts').textContent = newContacts;
}

// Open contact detail modal
function openContactModal(contactId) {
    selectedContact = contacts.find(c => c.id === contactId);

    if (!selectedContact) return;

    const fullName = [selectedContact.first_name, selectedContact.last_name]
        .filter(Boolean)
        .join(' ') || 'Unknown';

    document.getElementById('modal-name').textContent = fullName;
    document.getElementById('modal-username').textContent = selectedContact.username
        ? `@${selectedContact.username}`
        : '-';
    document.getElementById('modal-phone').textContent = selectedContact.phone_number || '-';
    document.getElementById('modal-company').value = selectedContact.company || '';
    document.getElementById('modal-notes').value = selectedContact.notes || '';
    document.getElementById('modal-date').textContent = new Date(selectedContact.added_date).toLocaleString();

    document.getElementById('contact-modal').classList.remove('hidden');
}

// Close contact modal
function closeContactModal() {
    document.getElementById('contact-modal').classList.add('hidden');
    selectedContact = null;
}

// Save contact changes
async function saveContact() {
    if (!selectedContact) return;

    const company = document.getElementById('modal-company').value;
    const notes = document.getElementById('modal-notes').value;

    try {
        const response = await fetch(`${API_URL}/contacts/${selectedContact.id}`, {
            method: 'PATCH',
            headers: {
                'Authorization': `Bearer ${accessToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ company, notes })
        });

        if (!response.ok) {
            throw new Error('Failed to save contact');
        }

        const updatedContact = await response.json();

        // Update local state
        const index = contacts.findIndex(c => c.id === selectedContact.id);
        if (index !== -1) {
            contacts[index] = updatedContact;
        }

        renderContacts(contacts);
        closeContactModal();

        tg.showAlert('Contact saved successfully!');

    } catch (error) {
        console.error('Error saving contact:', error);
        tg.showAlert('Failed to save contact');
    }
}

// Delete contact
async function deleteContact() {
    if (!selectedContact) return;

    const confirmed = confirm('Are you sure you want to delete this contact?');
    if (!confirmed) return;

    try {
        const response = await fetch(`${API_URL}/contacts/${selectedContact.id}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${accessToken}`
            }
        });

        if (!response.ok) {
            throw new Error('Failed to delete contact');
        }

        // Remove from local state
        contacts = contacts.filter(c => c.id !== selectedContact.id);

        renderContacts(contacts);
        updateStats();
        closeContactModal();

        tg.showAlert('Contact deleted successfully!');

    } catch (error) {
        console.error('Error deleting contact:', error);
        tg.showAlert('Failed to delete contact');
    }
}

// Export contacts to Google Sheets
async function exportContacts() {
    try {
        tg.showAlert('Exporting contacts to Google Sheets...');

        const response = await fetch(`${API_URL}/export`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${accessToken}`
            }
        });

        if (!response.ok) {
            throw new Error('Export failed');
        }

        const result = await response.json();

        tg.showAlert(result.message);

        // Reload contacts to update exported status
        await loadContacts();
        updateStats();

    } catch (error) {
        console.error('Error exporting contacts:', error);
        tg.showAlert('Failed to export contacts');
    }
}

// Search contacts
function searchContacts(query) {
    const lowercaseQuery = query.toLowerCase();

    const filtered = contacts.filter(contact => {
        const fullName = [contact.first_name, contact.last_name]
            .filter(Boolean)
            .join(' ')
            .toLowerCase();

        const username = (contact.username || '').toLowerCase();
        const company = (contact.company || '').toLowerCase();

        return fullName.includes(lowercaseQuery) ||
               username.includes(lowercaseQuery) ||
               company.includes(lowercaseQuery);
    });

    renderContacts(filtered);
}

// Setup event listeners
function setupEventListeners() {
    // Export button
    document.getElementById('export-btn').addEventListener('click', exportContacts);

    // Search input
    document.getElementById('search-input').addEventListener('input', (e) => {
        searchContacts(e.target.value);
    });

    // Modal close button
    document.getElementById('close-modal').addEventListener('click', closeContactModal);

    // Save contact button
    document.getElementById('save-contact').addEventListener('click', saveContact);

    // Delete contact button
    document.getElementById('delete-contact').addEventListener('click', deleteContact);

    // Close modal when clicking outside
    document.getElementById('contact-modal').addEventListener('click', (e) => {
        if (e.target.id === 'contact-modal') {
            closeContactModal();
        }
    });

    // Telegram back button
    tg.BackButton.onClick(closeContactModal);
}

// Start the app when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
