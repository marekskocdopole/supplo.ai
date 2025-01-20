// Globální proměnné
let selectedFarmId = null;
let products = [];
let socket = null;

// Inicializace při načtení stránky
document.addEventListener('DOMContentLoaded', () => {
    try {
        initializeSocket();
    } catch (error) {
        console.warn('Socket.IO není k dispozici:', error);
    }
    initializeFarmSelector();
});

// Inicializace Socket.IO
function initializeSocket() {
    if (typeof io === 'undefined') {
        console.warn('Socket.IO není načteno');
        return;
    }
    
    try {
        socket = io();
        
        socket.on('progress_update', (data) => {
            const { product_index, type, progress, status } = data;
            updateProgressBar(product_index, type, progress, status);
        });
        
        socket.on('content_update', (data) => {
            const { product_index, type, content } = data;
            updateContent(product_index, type, content);
        });
        
        socket.on('error', (data) => {
            const { product_index, type, message } = data;
            handleError(product_index, type, message);
        });
        
        console.log('Socket.IO úspěšně inicializováno');
    } catch (error) {
        console.error('Chyba při inicializaci Socket.IO:', error);
    }
}

// Inicializace výběru farmy
function initializeFarmSelector() {
    console.log('Inicializace výběru farmy');
    const farmSelect = document.getElementById('farm-select');
    
    if (!farmSelect) {
        console.error('Element farm-select nebyl nalezen!');
        return;
    }
    
    console.log('Přidávám event listener pro změnu farmy');
    farmSelect.addEventListener('change', async (e) => {
        console.log('Změna vybrané farmy');
        selectedFarmId = e.target.value;
        console.log('Nově vybraná farma:', selectedFarmId);
        
        if (selectedFarmId) {
            console.log('Začínám načítat produkty pro nově vybranou farmu');
            await loadProducts(selectedFarmId);
        } else {
            console.log('Žádná farma není vybrána, mažu produkty');
            clearProducts();
        }
    });
    
    // Pokud je farma předvybraná v URL, načteme ji
    const urlParams = new URLSearchParams(window.location.search);
    const farmId = urlParams.get('farm_id');
    if (farmId) {
        console.log('Farma je předvybraná v URL:', farmId);
        farmSelect.value = farmId;
        if (farmId) {
            loadProducts(farmId);
        }
    }
}

// Načtení produktů
async function loadProducts(farmId) {
    console.log('Začínám načítat produkty pro farmu:', farmId);
    try {
        const apiUrl = `/products/api/farms/${farmId}/products`;
        console.log('Volám API endpoint:', apiUrl);
        
        const response = await fetch(apiUrl);
        console.log('Odpověď od serveru:', {
            status: response.status,
            statusText: response.statusText,
            headers: Object.fromEntries(response.headers.entries())
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => null);
            console.error('Server vrátil chybu:', errorData || response.statusText);
            throw new Error(errorData?.error || 'Načtení produktů selhalo');
        }
        
        const data = await response.json();
        console.log('Načtená data:', data);
        
        products = data;
        console.log('Načteno produktů:', products.length);
        
        renderProducts();
        updateOverallProgress();
        
    } catch (error) {
        console.error('Chyba při načítání produktů:', error);
        showError('Chyba při načítání produktů: ' + error.message);
    }
}

// Vykreslení produktů
function renderProducts() {
    console.log('Začínám vykreslovat produkty');
    const container = document.getElementById('products-container');
    if (!container) {
        console.error('Container pro produkty nebyl nalezen!');
        return;
    }
    container.innerHTML = '';
    
    const template = document.getElementById('product-template');
    if (!template) {
        console.error('Šablona produktu nebyla nalezena!');
        return;
    }
    
    products.forEach((product, index) => {
        console.log(`Vykreslování produktu ${index}:`, product);
        let html = template.innerHTML
            .replace(/\${index}/g, index)
            .replace(/\${product\.name}/g, product.name);
            
        const div = document.createElement('div');
        div.innerHTML = html;
        const productElement = div.firstElementChild;
        
        // Nastavení stavu
        if (product.is_confirmed) {
            productElement.dataset.confirmed = 'true';
            productElement.classList.add('confirmed');
        }
        
        // Nastavení existujícího obsahu
        if (product.short_description) {
            const shortDesc = productElement.querySelector(`#short-description-${index}`);
            if (shortDesc) {
                shortDesc.innerHTML = product.short_description;
                // Nastavení progress baru na completed
                const shortProgressBar = productElement.querySelector(`.progress-bar[data-type="short"][data-index="${index}"]`);
                if (shortProgressBar) {
                    shortProgressBar.style.width = '100%';
                    shortProgressBar.classList.remove('generating', 'error');
                    shortProgressBar.classList.add('completed');
                    shortProgressBar.querySelector('.progress-text').textContent = 'Hotovo';
                }
                // Aktivace tlačítka pro regeneraci krátkého popisu
                const shortRegenerateBtn = productElement.querySelector(`.regenerate-btn[data-type="short"]`);
                if (shortRegenerateBtn) shortRegenerateBtn.disabled = false;
            }
        }
        if (product.long_description) {
            const longDesc = productElement.querySelector(`#long-description-${index}`);
            if (longDesc) {
                longDesc.innerHTML = product.long_description;
                // Nastavení progress baru na completed
                const longProgressBar = productElement.querySelector(`.progress-bar[data-type="long"][data-index="${index}"]`);
                if (longProgressBar) {
                    longProgressBar.style.width = '100%';
                    longProgressBar.classList.remove('generating', 'error');
                    longProgressBar.classList.add('completed');
                    longProgressBar.querySelector('.progress-text').textContent = 'Hotovo';
                }
                // Aktivace tlačítka pro regeneraci dlouhého popisu
                const longRegenerateBtn = productElement.querySelector(`.regenerate-btn[data-type="long"]`);
                if (longRegenerateBtn) longRegenerateBtn.disabled = false;
            }
        }
        if (product.image_path) {
            const preview = productElement.querySelector(`#image-preview-${index}`);
            if (preview) {
                preview.innerHTML = `<img src="${product.image_path}" alt="${product.name}">`;
                // Nastavení progress baru na completed
                const imageProgressBar = productElement.querySelector(`.progress-bar[data-type="images"][data-index="${index}"]`);
                if (imageProgressBar) {
                    imageProgressBar.style.width = '100%';
                    imageProgressBar.classList.remove('generating', 'error');
                    imageProgressBar.classList.add('completed');
                    imageProgressBar.querySelector('.progress-text').textContent = 'Hotovo';
                }
            }
        }
        
        container.appendChild(productElement);
    });
    
    console.log('Vykreslování produktů dokončeno');
}

// Generování obsahu
async function startGeneration(index) {
    if (!validateBeforeGeneration(index)) return;
    
    const product = products[index];
    const productRow = document.getElementById(`product-row-${index}`);
    
    // Deaktivace tlačítka potvrdit během generování
    const confirmButton = document.getElementById(`confirmButton_${index}`);
    if (confirmButton) {
        confirmButton.disabled = true;
    }
    
    // Nastavení stavu generování
    productRow.querySelector('.generate-icon').classList.add('generating');
    setProgressBarsGenerating(index);
    
    try {
        // Generování popisků
        const descResult = await generateDescriptions(product.sku);
        updateContent(index, 'short', descResult.short_description);
        updateContent(index, 'long', descResult.long_description);
        
        // Aktivace regeneračních tlačítek
        enableRegenerationButtons(index);
        
    } catch (error) {
        handleError(index, 'all', error.message);
    } finally {
        productRow.querySelector('.generate-icon').classList.remove('generating');
        // Aktivace tlačítka potvrdit po dokončení
        if (confirmButton) {
            confirmButton.disabled = false;
        }
    }
}

// Validace před generováním
function validateBeforeGeneration(index) {
    if (!selectedFarmId) {
        showError('Nejprve vyberte farmu');
        return false;
    }
    
    const productRow = document.getElementById(`product-row-${index}`);
    if (productRow.dataset.confirmed === 'true') {
        showError('Produkt je již potvrzen');
        return false;
    }
    
    return true;
}

// Aktualizace progress baru
function updateProgressBar(index, type, progress, status) {
    const progressBar = document.querySelector(`.progress-bar[data-type="${type}"][data-index="${index}"]`);
    if (!progressBar) return;
    
    progressBar.style.width = `${progress}%`;
    progressBar.querySelector('.progress-text').textContent = `${progress}%`;
    
    if (status) {
        progressBar.classList.remove('generating', 'completed', 'error');
        progressBar.classList.add(status);
    }
}

// Aktualizace obsahu
function updateContent(index, type, content) {
    const container = document.getElementById(`${type}-description-${index}`);
    if (!container) return;
    
    container.innerHTML = content;
    updateProgressBar(index, type, 100, 'completed');
}

// Potvrzení produktu
function confirmProduct(index) {
    // Kontrola indexu
    if (index < 0 || index >= products.length) {
        console.error('Neplatný index produktu:', index);
        return;
    }

    // Získání aktuálního obsahu popisků
    const shortDesc = document.getElementById(`short-description-${index}`).innerHTML;
    const longDesc = document.getElementById(`long-description-${index}`).innerHTML;
    const imagePath = products[index].image_path;

    // Nastavení progress baru
    const progressBar = document.querySelector(`.progress-bar[data-type="confirm"][data-index="${index}"]`);
    if (progressBar) {
        progressBar.style.width = '0%';
        progressBar.classList.remove('completed', 'error');
        progressBar.classList.add('generating');
        progressBar.querySelector('.progress-text').textContent = 'Potvrzování...';
    }

    // Odeslání požadavku
    fetch('/products/api/products/confirm', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            farm_id: selectedFarmId,
            sku: products[index].sku,
            short_description: shortDesc,
            long_description: longDesc,
            image_path: imagePath
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Aktualizace stavu produktu
        products[index].is_confirmed = true;
        
        // Deaktivace tlačítek
        const productRow = document.getElementById(`product-row-${index}`);
        if (productRow) {
            // Deaktivace tlačítka pro generování
            const generateIcon = productRow.querySelector('.generate-icon');
            if (generateIcon) generateIcon.style.display = 'none';
            
            // Deaktivace tlačítek pro regeneraci
            const regenerateButtons = productRow.querySelectorAll('.regenerate-btn');
            regenerateButtons.forEach(btn => btn.style.display = 'none');
            
            // Deaktivace tlačítka pro nahrání obrázku
            const uploadButton = productRow.querySelector('.upload-image-btn');
            if (uploadButton) uploadButton.style.display = 'none';
        }
        
        // Aktualizace tlačítka potvrzení
        const confirmButton = document.getElementById(`confirmButton_${index}`);
        if (confirmButton) {
            confirmButton.disabled = true;
            confirmButton.textContent = 'Potvrzeno';
        }
        
        // Aktualizace progress baru
        if (progressBar) {
            progressBar.style.width = '100%';
            progressBar.classList.remove('generating');
            progressBar.classList.add('completed');
            progressBar.querySelector('.progress-text').textContent = '100%';
        }

        // Aktualizace celkového progress baru
        updateOverallProgress();
    })
    .catch(error => {
        console.error('Chyba při potvrzování:', error);
        showError(error.message || 'Chyba při potvrzování produktu');
        
        // Aktualizace progress baru
        if (progressBar) {
            progressBar.style.width = '100%';
            progressBar.classList.remove('generating');
            progressBar.classList.add('error');
            progressBar.querySelector('.progress-text').textContent = 'Chyba';
        }
    });
}

// Upload obrázku
function triggerImageUpload(index) {
    document.getElementById(`image-upload-${index}`).click();
}

function handleImageUpload(index) {
    const fileInput = document.getElementById(`image-upload-${index}`);
    const file = fileInput.files[0];
    if (!file) {
        showError('Vyberte prosím obrázek');
        return;
    }

    // Kontrola typu souboru
    if (!file.type.match('image.*')) {
        showError('Vyberte prosím obrázek ve formátu JPG, PNG nebo GIF');
        return;
    }

    // Kontrola farm_id
    if (!selectedFarmId) {
        showError('Není vybrána farma');
        return;
    }

    // Deaktivace tlačítka potvrdit během nahrávání
    const confirmButton = document.getElementById(`confirmButton_${index}`);
    if (confirmButton) {
        confirmButton.disabled = true;
        confirmButton.textContent = 'Nahrávám...';
    }

    // Vytvoření FormData
    const formData = new FormData();
    formData.append('image', file);
    formData.append('farm_id', selectedFarmId);
    formData.append('sku', products[index].sku);

    console.log('DEBUG: Odesílám data:', {
        farm_id: selectedFarmId,
        sku: products[index].sku,
        file_name: file.name,
        file_type: file.type
    });

    // Nastavení progress baru
    const progressBar = document.querySelector(`.progress-bar[data-type="images"][data-index="${index}"]`);
    if (!progressBar) {
        console.error('Progress bar nebyl nalezen');
        return;
    }
    
    progressBar.style.width = '0%';
    progressBar.classList.remove('completed', 'error');
    progressBar.classList.add('generating');
    progressBar.querySelector('.progress-text').textContent = 'Nahrávání...';

    // Odeslání požadavku
    fetch('/products/api/upload_image', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        console.log('DEBUG: Server response:', response.status, response.statusText);
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.error || 'Chyba při nahrávání obrázku');
            });
        }
        return response.json();
    })
    .then(data => {
        console.log('DEBUG: Server data:', data);
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Aktualizace obrázku v products array
        products[index].image_path = data.image_path;
        
        // Aktualizace náhledu
        const preview = document.getElementById(`image-preview-${index}`);
        if (preview) {
            // Přidání timestamp pro vynucení obnovení cache
            const timestamp = new Date().getTime();
            preview.innerHTML = `<img src="${data.image_path}?t=${timestamp}" alt="Náhled produktu">`;
        }
        
        // Aktualizace progress baru
        progressBar.style.width = '100%';
        progressBar.classList.remove('generating');
        progressBar.classList.add('completed');
        progressBar.querySelector('.progress-text').textContent = '100%';

        // Aktivace tlačítka potvrdit po úspěšném nahrání
        if (confirmButton) {
            confirmButton.disabled = false;
            confirmButton.textContent = 'Potvrdit';
        }
    })
    .catch(error => {
        console.error('DEBUG: Chyba při nahrávání:', error);
        showError(error.message || 'Chyba při nahrávání obrázku');
        
        // Aktualizace progress baru
        progressBar.style.width = '100%';
        progressBar.classList.remove('generating');
        progressBar.classList.add('error');
        progressBar.querySelector('.progress-text').textContent = 'Chyba';

        // Aktivace tlačítka potvrdit i v případě chyby
        if (confirmButton) {
            confirmButton.disabled = false;
            confirmButton.textContent = 'Potvrdit';
        }
    });
}

// Regenerace obsahu
async function regenerateDescriptionShort(index) {
    await regenerateContent(index, 'short');
}

async function regenerateDescriptionLong(index) {
    await regenerateContent(index, 'long');
}

async function regenerateContent(index, type) {
    if (!validateBeforeGeneration(index)) return;
    
    const product = products[index];
    const productRow = document.getElementById(`product-row-${index}`);
    
    // Nastavení stavu generování pro tlačítko regenerace
    const regenerateButton = productRow.querySelector(`.regenerate-btn[data-type="${type}"]`);
    if (regenerateButton) {
        regenerateButton.classList.add('generating');
    }
    
    // Nastavení stavu generování
    setProgressBarGenerating(index, type);
    
    try {
        const response = await fetch(`/products/api/products/${product.sku}/regenerate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                farm_id: selectedFarmId,
                type: type
            })
        });
        
        if (!response.ok) throw new Error('Regenerace selhala');
        
        const data = await response.json();
        updateContent(index, type, data[`${type}_description`]);
        
    } catch (error) {
        handleError(index, type, error.message);
    } finally {
        // Odstranění třídy generating po dokončení
        if (regenerateButton) {
            regenerateButton.classList.remove('generating');
        }
    }
}

function setProgressBarGenerating(index, type) {
    const progressBar = document.querySelector(`.progress-bar[data-type="${type}"][data-index="${index}"]`);
    if (progressBar) {
        progressBar.classList.remove('completed', 'error');
        progressBar.classList.add('generating');
        progressBar.style.width = '0%';
        progressBar.querySelector('.progress-text').textContent = 'Generování...';
    }
}

// Pomocné funkce
function showError(message) {
    const alert = document.createElement('div');
    alert.className = 'alert alert-danger alert-dismissible fade show';
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('.container');
    if (container) {
        container.insertAdjacentElement('afterbegin', alert);
    } else {
        document.body.insertAdjacentElement('afterbegin', alert);
    }
}

function handleError(index, type, message) {
    showError(message);
    if (type === 'all') {
        updateProgressBar(index, 'short', 100, 'error');
        updateProgressBar(index, 'long', 100, 'error');
    } else {
        updateProgressBar(index, type, 100, 'error');
    }
}

function setProgressBarsGenerating(index) {
    ['short', 'long'].forEach(type => {
        const progressBar = document.querySelector(`.progress-bar[data-type="${type}"][data-index="${index}"]`);
        if (progressBar) {
            progressBar.classList.remove('completed', 'error');
            progressBar.classList.add('generating');
            progressBar.style.width = '0%';
            progressBar.querySelector('.progress-text').textContent = 'Generování...';
        }
    });
}

function enableRegenerationButtons(index) {
    const buttons = document.querySelectorAll(`#product-row-${index} .regenerate-btn`);
    buttons.forEach(button => button.disabled = false);
}

function updateOverallProgress() {
    const total = products.length;
    const confirmed = products.filter(p => p.is_confirmed).length;
    
    document.getElementById('progress-counter').textContent = `${confirmed}/${total} produktů potvrzeno`;
    document.getElementById('main-progress-bar').style.width = `${(confirmed / total) * 100}%`;
    
    const exportSection = document.getElementById('export-section');
    exportSection.style.display = confirmed > 0 ? 'block' : 'none';
}

// Export do CSV
async function exportToCSV() {
    try {
        const format = document.getElementById('export-format').value || 'csv';
        const response = await fetch(`/products/api/farms/${selectedFarmId}/export?format=${format}`);
        if (!response.ok) throw new Error('Export selhal');
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `farm_${selectedFarmId}_export.${format === 'excel' ? 'xlsx' : format}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();
        
    } catch (error) {
        showError('Chyba při exportu: ' + error.message);
    }
}

// Generování popisů
async function generateDescriptions(sku) {
    console.log('Začínám generovat popisky pro SKU:', sku);
    console.log('Data pro odeslání:', { farm_id: selectedFarmId, sku: sku });
    
    try {
        const response = await fetch('/products/generate_product_content', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                farm_id: selectedFarmId,
                sku: sku
            })
        });
        
        console.log('Odpověď od serveru:', {
            status: response.status,
            statusText: response.statusText
        });
        
        const data = await response.json();
        console.log('Přijatá data:', data);
        
        if (!response.ok) {
            throw new Error(data.error || 'Generování selhalo');
        }
        
        return data;
    } catch (error) {
        console.error('Chyba při generování:', error);
        throw error;
    }
}

// Vymazání produktů
function clearProducts() {
    console.log('Mažu seznam produktů');
    products = [];
    const container = document.getElementById('products-container');
    if (container) {
        container.innerHTML = '';
    }
    updateOverallProgress();
}

function enableEdit(index) {
    const productRow = document.getElementById(`product-row-${index}`);
    if (productRow) {
        // Aktivace tlačítka pro generování
        const generateIcon = productRow.querySelector('.generate-icon');
        if (generateIcon) generateIcon.style.display = '';
        
        // Aktivace tlačítek pro regeneraci
        const regenerateButtons = productRow.querySelectorAll('.regenerate-btn');
        regenerateButtons.forEach(btn => {
            btn.style.display = '';
            btn.disabled = false;  // Okamžitě aktivujeme tlačítka
        });
        
        // Aktivace tlačítka pro nahrání obrázku
        const uploadButton = productRow.querySelector('.upload-image-btn');
        if (uploadButton) uploadButton.style.display = '';
        
        // Aktivace tlačítka pro potvrzení
        const confirmButton = document.getElementById(`confirmButton_${index}`);
        if (confirmButton) {
            confirmButton.disabled = false;
            confirmButton.textContent = 'Potvrdit';
        }

        // Nastavení produktu jako nepotvrzený
        products[index].is_confirmed = false;
        
        // Aktualizace celkového progress baru
        updateOverallProgress();
    }
} 