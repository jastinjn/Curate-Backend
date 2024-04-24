function showConditionContent(conditionId) {
    // Hide all condition sections
    const conditionContents = document.querySelectorAll('.condition-details .problem-section');
    conditionContents.forEach(section => {
        section.style.display = 'none'; // Initially hide all condition content
    });

    // Show the content for the clicked condition
    const conditionContent = document.getElementById(conditionId);
    if (conditionContent) {
        conditionContent.style.display = 'block'; // Display the content for the active condition
    }
}

function setupConditionTabs() {
    const conditionTabs = document.querySelectorAll('.condition-tab');
    conditionTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            conditionTabs.forEach(ct => ct.classList.remove('active'));
            tab.classList.add('active');
            showConditionContent(tab.dataset.conditionId);
        });
    });

    // Trigger click on the first condition tab to set it as active by default
    if (conditionTabs.length > 0) {
        conditionTabs[0].click();
    }
    setupEventTabs();
}

function setupEventTabs() {
    const eventTabs = document.querySelectorAll('.event-tab');

    eventTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            eventTabs.forEach(et => et.classList.remove('active'));
            // Hide all event content sections for the currently active condition
            const activeConditionId = document.querySelector('.condition-tab.active').dataset.conditionId;
            document.querySelectorAll(`#${activeConditionId}-results-content .event-content`).forEach(ec => ec.style.display = 'none');

            tab.classList.add('active');
            const eventType = tab.dataset.eventTab; // "results", "notes", "treatments"
            
            // Correctly reference the container for the event types
            const eventContentId = `${activeConditionId}-${eventType}`;
            const eventContent = document.getElementById(eventContentId);
            if (eventContent) {
                eventContent.style.display = 'block'; // Show the correct event content
            } else {
                // If not, log an error
                console.error(`Content for ${eventContentId} not found`);
            }

            // If the Results tab was clicked, generate buttons specifically for that condition
            if (eventType === 'results') {
                generateResultsButtons(activeConditionId);
            }
            if (eventType === 'treatments') {
                generateTreatmentsButtons(activeConditionId);
            }
            if (eventType === 'notes') {
                generateNotesButtons(activeConditionId);
            }
        });
    });

    // Click the first event tab to show its content by default if it exists
    if (eventTabs.length > 0) {
        eventTabs[0].click();
    }
}

function generateResultsButtons(conditionId) {
    console.log('Generating results buttons for condition:', conditionId);
    const resultsData = {
        'breast-cancer': [
            {
                title: 'Mammography',
                description: 'Revealed a suspicious mass in the right breast, BI-RADS category 4.',
                date: '2/16/2022',
                documentLink: 'mammography-document.html'
            },
            {
                title: 'Core Needle Biopsy',
                description: 'Histopathological examination confirmed invasive ductal carcinoma, estrogen receptor-positive, HER2-negative',
                date: '2/18/2022',
                documentLink: 'biopsy-document.html'
            }
            // ... add more results data as needed
        ],
        'hypertension': [
            {
                title: 'Mammography',
                description: 'Revealed a suspicious mass in the right breast, BI-RADS category 4.',
                date: '2/16/2022',
                documentLink: 'mammography-document.html'
            },
            {
                title: 'Core Needle Biopsy',
                description: 'Histopathological examination confirmed invasive ductal carcinoma, estrogen receptor-positive, HER2-negative',
                date: '2/18/2022',
                documentLink: 'biopsy-document.html'
            }
            // ... add more results data as needed
        ],

        // ... add results data for other conditions if needed
    };

    // Get the container for the results content
    const resultsContentContainer = document.getElementById(`${conditionId}-results`);

    if (!resultsContentContainer) {
        console.error(`No results content container found for condition: ${conditionId}`);
        return; // Exit the function if the container isn't found
    }

    resultsContentContainer.innerHTML = ''; // Clear existing content

    const resultsForCondition = resultsData[conditionId];
    if (resultsForCondition) {
        resultsForCondition.forEach(result => {
            const resultButton = document.createElement('button');
            resultButton.classList.add('result-button');
            resultButton.innerHTML = `
                <div class="result-title">${result.title}:</div>
                <div class="result-description">${result.description}</div>
                <div class="result-date">${result.date}</div>
            `; // Add inner HTML structure as needed
            resultButton.addEventListener('click', () => {
                window.location.href = result.documentLink; // Navigate to the document page
            });
            resultsContentContainer.appendChild(resultButton);
            
        });
    }
}

function generateTreatmentsButtons(conditionId) {
    console.log('Generating treatments buttons for condition:', conditionId);
    const treatmentsData = {
        'breast-cancer': [
            {
                title: 'Chemotherapy Treatment Medical Report',
                date: '10/1/2022',
                documentLink: 'mammography-document.html'
            },
            {
                title: 'Core Needle Biopsy',
                date: '3/27/2022',
                documentLink: 'biopsy-document.html'
            }
            // ... add more results data as needed
        ],
        'hypertension': [
            {
                title: 'Chemotherapy Treatment Medical Report',
                date: '10/1/2022',
                documentLink: 'mammography-document.html'
            },
            {
                title: 'Core Needle Biopsy',
                date: '3/27/2022',
                documentLink: 'biopsy-document.html'
            }
            // ... add more results data as needed
        ]
        // ... add results data for other conditions if needed
    };

    // Get the container for the results content
    const treatmentsContentContainer = document.getElementById(`${conditionId}-treatments`);

    if (!treatmentsContentContainer) {
        console.error(`No results content container found for condition: ${conditionId}`);
        return; // Exit the function if the container isn't found
    }

    treatmentsContentContainer.innerHTML = ''; // Clear existing content

    const treatmentsForCondition = treatmentsData[conditionId];
    if (treatmentsForCondition) {
        treatmentsForCondition.forEach(treatment => {
            const treatmentsButton = document.createElement('button');
            treatmentsButton.classList.add('treatment-button');
            treatmentsButton.innerHTML = `
                <div class="treatment-title">${treatment.title}</div>
                <div class="treatment-date">${treatment.date}</div>
            `; // Add inner HTML structure as needed
            treatmentsButton.addEventListener('click', () => {
                window.location.href = treatment.documentLink; // Navigate to the document page
            });
            treatmentsContentContainer.appendChild(treatmentsButton);
            
        });
    }
}

function generateNotesButtons(conditionId) {
    console.log('Generating notes buttons for condition:', conditionId);
    const notesData = {
        'breast-cancer': [
            {
                title: 'Follow-up Consultation Note',
                date: '10/1/2022',
                documentLink: 'mammography-document.html'
            }
            // ... add more results data as needed
        ], 
        'hypertension': [
            {
                title: 'Follow-up Consultation Note',
                date: '10/1/2022',
                documentLink: 'mammography-document.html'
            }
            // ... add more results data as needed
        ]
        // ... add results data for other conditions if needed
    };

    // Get the container for the results content
    const notesContentContainer = document.getElementById(`${conditionId}-notes`);
    console.log(notesContentContainer)

    if (!notesContentContainer) {
        console.error(`No results content container found for condition: ${conditionId}`);
        return; // Exit the function if the container isn't found
    }

    notesContentContainer.innerHTML = ''; // Clear existing content

    const notesForCondition = notesData[conditionId];
    console.log(notesForCondition)
    if (notesForCondition) {
        notesForCondition.forEach(note => {
            const notesButton = document.createElement('button');
            notesButton.classList.add('note-button');
            notesButton.innerHTML = `
                <div class="note-title">${note.title}</div>
                <div class="note-date">${note.date}</div>
            `; // Add inner HTML structure as needed
            notesButton.addEventListener('click', () => {
                window.location.href = note.documentLink; // Navigate to the document page
            });
            console.log(notesButton)
            notesContentContainer.appendChild(notesButton);
            
        });
    }
}

// Assuming this script is included after main.js and executes after main.js has set up the tabs
setupConditionTabs();
setupEventTabs();