const tabMap = {
    'Summary': '.summary-container',
    'Problems': '.problem-container',
    'Medicine': '.medicine-container',
    'Surgeries': '.surgeries-container',
    'Tests': '.tests-container'
};

const patientData = {
    overview: "Emily Johnson, 52, with a history of hypertension, diagnosed with estrogen receptor-positive, HER2-negative invasive ductal carcinoma, underwent lumpectomy, adjuvant therapy (TAC chemotherapy, radiation, tamoxifen), and showed no recurrence during post-treatment follow-up.",
    problems: [
        { name: 'Breast Cancer: Invasive Ductal Carcinoma, Stage IIO', status: 'Active' },
        { name: 'Hypertension', status: 'Active' }
    ],
    medications: [
        { name: 'Acetaminophen', dose: '500 mg', status: 'Active' },
        { name: 'Ondansetron', dose: '4 mg', status: 'Active' },
        { name: 'Amlodipine', dose: '5 mg', status: '2006-2019' }
    ]
};

function loadFile() {
    var fileInput = document.getElementById('file-input');
    var filePath = fileInput.value;
    
    // Check if any file is selected or not
    if (fileInput.files.length > 0) {
        var allowedExtensions = /(\.pdf)$/i;
        
        if (!allowedExtensions.exec(filePath)) {
            alert('Please upload file having extensions .pdf only.');
            fileInput.value = ''; // Clear the input
            return false;
        } else {
            // Image preview
            document.getElementById('loading').style.display = 'block';
            setTimeout(() => {
                window.location.href = 'dashboard.html';
            }, 3000); // simulate loading time
        }
    } else {
        alert('Please select a file.');
    }
}

function generateTimeline() {
    const timelineData = [
        { type: 'Diagnosis', date: 'Feb 2022', color: 'navy' },
        { type: 'Surgery', date: 'Mar 2022', color: 'red' },
        // Add more timeline events as needed
    ];

    const timelineElement = document.querySelector('.timeline');
    timelineData.forEach(event => {
        const barElement = document.createElement('div');
        barElement.style.backgroundColor = event.color;
        barElement.title = `${event.type} - ${event.date}`;
        timelineElement.appendChild(barElement);
    });
}

function showTabContent(tabName) {
    const selector = tabMap[tabName];
    if (selector) {
        const content = document.querySelector(selector);
        content.style.display = 'flex';

        // Hide other tab contents
        Object.values(tabMap).forEach(tabSelector => {
            if (tabSelector !== selector) {
                document.querySelector(tabSelector).style.display = 'none';
            }
        });

        if (tabName === 'Problems') {
            generateTimeline();
            setupConditionTabs();
        } else if (tabName === 'Summary') {
            // Call populateSummary from summary-content.js
            populateSummary();
        }
    }
}

function resetTabs(allTabContents, tabs) {
    allTabContents.forEach(content => content.style.display = 'none');
    tabs.forEach(tab => tab.classList.remove('active'));
}



document.addEventListener('DOMContentLoaded', () => {
    const tabs = document.querySelectorAll('.tabs button');
    const allTabContents = document.querySelectorAll('.tab-content > div');

    tabs.forEach(tab => {
        tab.addEventListener('click', (e) => {
            resetTabs(allTabContents, tabs); // Hide all content and remove 'active' class
            e.target.classList.add('active'); // Add 'active' class to the clicked tab
            showTabContent(e.target.textContent.trim()); // Show content for the clicked tab
        });
    });

    // Set the default tab as active and show its content
    const defaultTab = document.querySelector('.tabs button:nth-child(2)'); // Assuming 'Problems' is the second tab
    if (defaultTab) {
        defaultTab.classList.add('active');
        showTabContent(defaultTab.textContent.trim());
        setupConditionTabs(); // Set up the condition tabs

        // After setting up the condition tabs, find the default condition tab that is active
        const activeConditionTab = document.querySelector('.condition-tab.active');
        if (activeConditionTab) {
            const activeConditionId = activeConditionTab.dataset.conditionId;
            setupEventTabs(); // Set up the event tabs

            // Find the default event tab within the active condition and click it
            const defaultEventTab = document.querySelector(`#${activeConditionId} .event-tab[data-event-tab="results"]`);
            if (defaultEventTab) {
                defaultEventTab.click(); // This will also call generateResultsButtons for the active condition
            }
        }
    }

    const summaryTabIsActive = document.querySelector('.tabs button.active').textContent.trim() === 'Summary';
    if (summaryTabIsActive) {
        populateSummary();
    }
});