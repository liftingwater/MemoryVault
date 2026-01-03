// DOM Elements
const frontTypeRadios = document.querySelectorAll('input[name="front-type"]');
const backTypeRadios = document.querySelectorAll('input[name="back-type"]');
const frontTextInput = document.getElementById('front-text');
const frontImageInput = document.getElementById('front-image');
const frontAltInput = document.getElementById('front-alt');
const backTextInput = document.getElementById('back-text');
const backImageInput = document.getElementById('back-image');
const backAltInput = document.getElementById('back-alt');
const previewCard = document.getElementById('preview-card');
const previewFrontContent = document.getElementById('preview-front-content');
const previewBackContent = document.getElementById('preview-back-content');
const createBtn = document.getElementById('create-btn');
const clearBtn = document.getElementById('clear-btn');
const flipBtn = document.getElementById('flip-btn');
const successMessage = document.getElementById('success-message');

// State
let currentFrontType = 'text';
let currentBackType = 'text';

// Event Listeners - Content Type Selection
frontTypeRadios.forEach(radio => {
    radio.addEventListener('change', (e) => {
        currentFrontType = e.target.value;
        toggleInputs('front', currentFrontType);
        updatePreview();
    });
});

backTypeRadios.forEach(radio => {
    radio.addEventListener('change', (e) => {
        currentBackType = e.target.value;
        toggleInputs('back', currentBackType);
        updatePreview();
    });
});

// Event Listeners - Input Changes
frontTextInput.addEventListener('input', updatePreview);
frontImageInput.addEventListener('input', updatePreview);
frontAltInput.addEventListener('input', updatePreview);
backTextInput.addEventListener('input', updatePreview);
backImageInput.addEventListener('input', updatePreview);
backAltInput.addEventListener('input', updatePreview);

// Event Listeners - Buttons
createBtn.addEventListener('click', createCard);
clearBtn.addEventListener('click', clearForm);
flipBtn.addEventListener('click', flipCard);

// Toggle input fields based on content type
function toggleInputs(side, type) {
    const textInput = side === 'front' ? frontTextInput : backTextInput;
    const imageInput = side === 'front' ? frontImageInput : backImageInput;
    const altInput = side === 'front' ? frontAltInput : backAltInput;
    
    if (type === 'text') {
        textInput.classList.add('active');
        imageInput.classList.remove('active');
        altInput.classList.remove('active');
    } else {
        textInput.classList.remove('active');
        imageInput.classList.add('active');
        altInput.classList.add('active');
    }
}

// Update preview
function updatePreview() {
    updateSidePreview('front', currentFrontType, previewFrontContent);
    updateSidePreview('back', currentBackType, previewBackContent);
}

function updateSidePreview(side, type, contentElement) {
    const textInput = side === 'front' ? frontTextInput : backTextInput;
    const imageInput = side === 'front' ? frontImageInput : backImageInput;
    const altInput = side === 'front' ? frontAltInput : backAltInput;
    
    if (type === 'text') {
        const text = textInput.value.trim();
        if (text) {
            contentElement.innerHTML = `<p>${escapeHtml(text)}</p>`;
        } else {
            contentElement.innerHTML = `<p class="placeholder">Your ${side} content will appear here...</p>`;
        }
    } else {
        const imageUrl = imageInput.value.trim();
        const altText = altInput.value.trim();
        if (imageUrl) {
            contentElement.innerHTML = `<img src="${escapeHtml(imageUrl)}" alt="${escapeHtml(altText || 'Card image')}" onerror="this.src='data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' width=\'200\' height=\'200\'%3E%3Crect fill=\'%23ddd\' width=\'200\' height=\'200\'/%3E%3Ctext fill=\'%23999\' x=\'50%25\' y=\'50%25\' text-anchor=\'middle\' dy=\'.3em\'%3EImage not found%3C/text%3E%3C/svg%3E'">`;
        } else {
            contentElement.innerHTML = `<p class="placeholder">Your ${side} image will appear here...</p>`;
        }
    }
}

// Flip card
function flipCard() {
    previewCard.classList.toggle('flipped');
}

// Create card
function createCard() {
    const cardData = getCardData();
    
    if (!cardData) {
        alert('Please fill in both front and back content!');
        return;
    }
    
    console.log('Card created:', cardData);
    
    // Show success message
    showSuccessMessage();
    
    // Clear form after creation
    setTimeout(() => {
        clearForm();
    }, 1000);
}

// Get card data
function getCardData() {
    const front = currentFrontType === 'text' 
        ? frontTextInput.value.trim()
        : frontImageInput.value.trim();
    
    const back = currentBackType === 'text'
        ? backTextInput.value.trim()
        : backImageInput.value.trim();
    
    if (!front || !back) {
        return null;
    }
    
    return {
        front: currentFrontType === 'text'
            ? front
            : {
                type: 'image',
                value: front,
                alt_text: frontAltInput.value.trim() || undefined
            },
        back: currentBackType === 'text'
            ? back
            : {
                type: 'image',
                value: back,
                alt_text: backAltInput.value.trim() || undefined
            }
    };
}

// Clear form
function clearForm() {
    frontTextInput.value = '';
    frontImageInput.value = '';
    frontAltInput.value = '';
    backTextInput.value = '';
    backImageInput.value = '';
    backAltInput.value = '';

    // Reset to text type
    document.querySelector('input[name="front-type"][value="text"]').checked = true;
    document.querySelector('input[name="back-type"][value="text"]').checked = true;
    currentFrontType = 'text';
    currentBackType = 'text';

    toggleInputs('front', 'text');
    toggleInputs('back', 'text');

    // Reset card flip
    previewCard.classList.remove('flipped');

    updatePreview();
}

// Show success message
function showSuccessMessage() {
    successMessage.classList.remove('hidden');
    setTimeout(() => {
        successMessage.classList.add('hidden');
    }, 3000);
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Initialize
updatePreview();

