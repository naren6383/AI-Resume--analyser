document.addEventListener('DOMContentLoaded', function() {
    
    // -------------------------------------------------------------
    // 1. Dark/Light Theme Handler
    // -------------------------------------------------------------
    const htmlEl = document.documentElement;
    const themeToggleBtn = document.getElementById('themeToggleBtn');
    const themeToggleIcon = document.getElementById('themeToggleIcon');
    
    // Check saved theme or system preferences
    const savedTheme = localStorage.getItem('theme');
    const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    let activeTheme = 'light';
    if (savedTheme === 'dark' || (!savedTheme && systemPrefersDark)) {
        activeTheme = 'dark';
    }
    
    // Apply initial theme
    applyTheme(activeTheme);
    
    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', function() {
            const currentTheme = htmlEl.getAttribute('data-bs-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            applyTheme(newTheme);
        });
    }
    
    function applyTheme(theme) {
        htmlEl.setAttribute('data-bs-theme', theme);
        localStorage.setItem('theme', theme);
        
        if (themeToggleIcon) {
            if (theme == 'dark') {
                themeToggleIcon.className = 'fa-solid fa-sun text-warning';
            } else {
                themeToggleIcon.className = 'fa-solid fa-moon text-dark';
            }
        }
    }

    // -------------------------------------------------------------
    // 2. Drag & Drop File Upload Interactions
    // -------------------------------------------------------------
    const dropZone = document.getElementById('uploadDropZone');
    const fileInput = document.getElementById('resumeInput');
    const fileSelectBtn = document.getElementById('fileSelectBtn');
    const fileInfoDiv = document.getElementById('fileInfo');
    const selectedFileName = document.getElementById('selectedFileName');
    const uploadForm = document.getElementById('uploadForm');
    const loadingOverlay = document.getElementById('loadingOverlay');
    const processingStep = document.getElementById('processingStep');

    if (dropZone && fileInput) {
        
        // Clicks on drop zone trigger input click
        dropZone.addEventListener('click', () => fileInput.click());
        
        if (fileSelectBtn) {
            fileSelectBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                fileInput.click();
            });
        }
        
        // Handle file input changes
        fileInput.addEventListener('change', handleFileSelection);
        
        // Drag events
        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropZone.classList.add('dragover');
            }, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropZone.classList.remove('dragover');
            }, false);
        });
        
        // Drop handler
        dropZone.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;
            if (files.length) {
                fileInput.files = files;
                handleFileSelection();
            }
        });
    }

    function handleFileSelection() {
        if (fileInput.files.length) {
            const file = fileInput.files[0];
            const extension = file.name.split('.').pop().toLowerCase();
            const allowed = ['pdf', 'docx'];
            const maxSize = 5 * 1024 * 1024; // 5MB
            
            if (!allowed.includes(extension)) {
                alert('Invalid file format. Please upload a PDF or DOCX file.');
                fileInput.value = '';
                if (fileInfoDiv) fileInfoDiv.classList.add('d-none');
                return;
            }
            
            if (file.size > maxSize) {
                alert('File size exceeds the 5MB limit. Please upload a smaller resume.');
                fileInput.value = '';
                if (fileInfoDiv) fileInfoDiv.classList.add('d-none');
                return;
            }
            
            // Update UI
            if (selectedFileName) {
                selectedFileName.textContent = `${file.name} (${(file.size / (1024 * 1024)).toFixed(2)} MB)`;
            }
            if (fileInfoDiv) {
                fileInfoDiv.classList.remove('d-none');
            }
        }
    }

    // -------------------------------------------------------------
    // 3. Show Spinner on Upload Form Submit
    // -------------------------------------------------------------
    if (uploadForm && loadingOverlay) {
        uploadForm.addEventListener('submit', function(e) {
            if (!fileInput.files.length) {
                e.preventDefault();
                alert('Please upload a resume file before analyzing.');
                return;
            }
            
            // Display loading overlay
            loadingOverlay.style.display = 'flex';
            
            // Cycle visual steps for a high-end feel
            const steps = [
                "Uploading resume document...",
                "Extracting resume structures & text...",
                "Running heuristic parser and ATS rules...",
                "Calling AI provider for deep content review...",
                "Compiling job matches & recommendations..."
            ];
            
            let currentStep = 0;
            if (processingStep) {
                processingStep.textContent = steps[currentStep];
                setInterval(() => {
                    if (currentStep < steps.length - 1) {
                        currentStep++;
                        processingStep.textContent = steps[currentStep];
                    }
                }, 4000);
            }
        });
    }

    // -------------------------------------------------------------
    // 4. Copy Analysis Button Dashboard
    // -------------------------------------------------------------
    const copyAnalysisBtn = document.getElementById('copyAnalysisBtn');
    if (copyAnalysisBtn) {
        copyAnalysisBtn.addEventListener('click', function() {
            const summaryText = document.getElementById('resumeSummaryContent')?.innerText || "";
            const suggestionsText = document.getElementById('resumeSuggestionsContent')?.innerText || "";
            
            if (!summaryText) {
                alert("Nothing to copy.");
                return;
            }
            
            const fullReportText = `RESUME ANALYSIS REPORT\n\nEXECUTIVE SUMMARY:\n${summaryText}\n\nRECOMMENDATIONS & SUGGESTIONS:\n${suggestionsText}`;
            
            navigator.clipboard.writeText(fullReportText).then(function() {
                // Temporary success tooltip/text change
                const originalHTML = copyAnalysisBtn.innerHTML;
                copyAnalysisBtn.innerHTML = '<i class="fa-solid fa-check me-2"></i>Copied!';
                copyAnalysisBtn.classList.remove('btn-outline-primary');
                copyAnalysisBtn.classList.add('btn-success');
                
                setTimeout(() => {
                    copyAnalysisBtn.innerHTML = originalHTML;
                    copyAnalysisBtn.classList.remove('btn-success');
                    copyAnalysisBtn.classList.add('btn-outline-primary');
                }, 2500);
            }).catch(function(err) {
                console.error('Could not copy text: ', err);
            });
        });
    }

    // -------------------------------------------------------------
    // 5. Dynamic API/Model Form Selection Toggle in Settings
    // -------------------------------------------------------------
    const activeProviderSelect = document.getElementById('activeAiProvider');
    if (activeProviderSelect) {
        const sections = {
            'gemini': document.getElementById('geminiSettingsSection'),
            'openrouter': document.getElementById('openrouterSettingsSection'),
            'groq': document.getElementById('groqSettingsSection')
        };
        
        function toggleSections() {
            const selected = activeProviderSelect.value;
            Object.keys(sections).forEach(key => {
                if (sections[key]) {
                    if (key === selected) {
                        sections[key].classList.remove('d-none');
                    } else {
                        sections[key].classList.add('d-none');
                    }
                }
            });
        }
        
        activeProviderSelect.addEventListener('change', toggleSections);
        toggleSections(); // Execute once on load
    }

    // -------------------------------------------------------------
    // 6. Test Key Connection Handler
    // -------------------------------------------------------------
    const testButtons = document.querySelectorAll('.test-connection-btn');
    testButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const provider = btn.getAttribute('data-provider');
            let apiKey = '';
            let model = '';
            
            if (provider === 'gemini') {
                apiKey = document.getElementById('gemini_api_key')?.value;
                model = document.getElementById('gemini_model')?.value;
            } else if (provider === 'openrouter') {
                apiKey = document.getElementById('openrouter_api_key')?.value;
                model = document.getElementById('openrouter_model')?.value;
            } else if (provider === 'groq') {
                apiKey = document.getElementById('groq_api_key')?.value;
                model = document.getElementById('groq_model')?.value;
            }
            
            if (!apiKey) {
                alert('Please enter an API Key first before testing connection.');
                return;
            }
            
            // Update button visual state
            const originalText = btn.innerHTML;
            btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Testing...';
            btn.disabled = true;
            
            // Post test connection endpoint
            fetch('/api/test-connection', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    provider: provider,
                    api_key: apiKey,
                    model: model
                })
            })
            .then(res => res.json())
            .then(data => {
                btn.innerHTML = originalText;
                btn.disabled = false;
                
                if (data.success) {
                    alert('SUCCESS: ' + data.message);
                } else {
                    alert('ERROR: ' + data.message);
                }
            })
            .catch(err => {
                btn.innerHTML = originalText;
                btn.disabled = false;
                alert('Connection failure contacting local server: ' + err.message);
            });
        });
    });
});
