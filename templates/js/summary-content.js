function populateSummary() {
    // Assuming you have an element with ID 'summary-content' inside your '.summary-container'
    const summaryContentElement = document.getElementById('summary-content');
    summaryContentElement.innerHTML = ''; // Clear out existing content

    // Create the Patient Overview section
    const patientOverviewTitle = document.createElement('h3');
    patientOverviewTitle.textContent = 'Patient Overview';
    summaryContentElement.appendChild(patientOverviewTitle);

    const patientOverviewElement = document.createElement('p');
    patientOverviewElement.textContent = patientData.overview;
    summaryContentElement.appendChild(patientOverviewElement);

    // Create the Problems section
    const problemsTitle = document.createElement('h3');
    problemsTitle.textContent = 'Problems';
    summaryContentElement.appendChild(problemsTitle);

    const problemsContainer = document.createElement('div');
    patientData.problems.forEach(problem => {
        const problemButton = document.createElement('button');
        problemButton.textContent = `${problem.name}: ${problem.status}`;
        problemButton.className = 'summary-button'; // Apply CSS class for styling
        problemButton.addEventListener('click', () => {
            document.querySelector('.tabs button:nth-child(2)').click(); // This assumes 'Problems' is the second button
            document.querySelector(`.condition-tab[data-condition-id="${problem.name.toLowerCase().replace(/\s/g, '-')}"`).click(); // Convert problem name to id
        });
        problemsContainer.appendChild(problemButton);
    });
    summaryContentElement.appendChild(problemsContainer);

    // Create the Medications section
    const medicationsTitle = document.createElement('h3');
    medicationsTitle.textContent = 'Medications';
    summaryContentElement.appendChild(medicationsTitle);

    const medicationsContainer = document.createElement('div');
    patientData.medications.forEach(medication => {
        const medicationButton = document.createElement('button');
        medicationButton.textContent = `${medication.name} ${medication.dose} (${medication.status})`;
        medicationButton.className = 'summary-button'; // Apply CSS class for styling
        medicationsContainer.appendChild(medicationButton);
    });
    summaryContentElement.appendChild(medicationsContainer);

    // Add any additional elements you need for the summary content here...
}