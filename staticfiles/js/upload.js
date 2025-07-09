// Disable upload button function
function updateUploadButtonState() {
    const mainFileError = document.getElementById('formFileError').textContent.trim();
    const secondaryFileError = document.getElementById('formFileSearchError').textContent.trim();
    const uploadButton = document.getElementById('uploadButton');
    const mainFile = document.getElementById('formFile').files.length > 0;
    const secondaryFile = document.getElementById('formFileSearch').files.length > 0;

    // Disable the upload button if:
    // 1. Any error exists in either file.
    // 2. Either file is not uploaded.
    if (mainFileError || secondaryFileError || !mainFile || !secondaryFile) {
        uploadButton.classList.add('hidden');
        uploadButton.disabled = true;
    } else {
        uploadButton.classList.remove('hidden');
        uploadButton.disabled = false;
    }
}

// Function to handle dropdown selection and visibility of file upload section
function handleSelectionChange() {
    const dropdown = document.getElementById('searchOption');
    const fileUploadSection = document.getElementById('fileUploadSection');
    const fileLabel = document.getElementById('fileLabel');
    const uploadButton = document.getElementById('uploadButton');
    const selectedOption = dropdown.options[dropdown.selectedIndex].text;

    // Update the file label text
    fileLabel.textContent = `Upload File for ${selectedOption}`;

    // Show the file upload section and upload button
    if (dropdown.value) {
        fileUploadSection.classList.remove('hidden');
        uploadButton.classList.remove('hidden');
    }
    updateUploadButtonState(); // Ensure the button state is updated
}

// Function to validate the main file
const mainFileInput = document.getElementById('formFile');
const mainFileError = document.getElementById('formFileError');

mainFileInput.addEventListener('change', () => {
    const file = mainFileInput.files[0];
    mainFileError.textContent = '';

    if (file) {
        if (file.type !== 'application/vnd.ms-excel' && file.type !== 'text/csv') {
            mainFileError.textContent = 'Please upload a valid CSV file.';
            mainFileInput.value = '';
        } else if (file.size === 0) {
            mainFileError.textContent = 'The file is empty. Please upload a non-empty CSV file.';
            mainFileInput.value = '';
        }

        // Store the file name in localStorage
        if (file && !mainFileError.textContent) {
            localStorage.setItem('csvFileName', file.name);
        }
    }
    updateUploadButtonState(); // Update button state after file validation
});

// Function to validate the secondary file
const secondaryFileInput = document.getElementById('formFileSearch');
const secondaryFileError = document.getElementById('formFileSearchError');

secondaryFileInput.addEventListener('change', () => {
    const file = secondaryFileInput.files[0];
    secondaryFileError.textContent = '';

    if (file) {
        if (file.type !== 'application/vnd.ms-excel' && file.type !== 'text/csv') {
            secondaryFileError.textContent = 'Please upload a valid CSV file.';
            secondaryFileInput.value = '';
        } else if (file.size === 0) {
            secondaryFileError.textContent = 'The file is empty. Please upload a non-empty CSV file.';
            secondaryFileInput.value = '';
        }

        // Store the secondary file name in localStorage
        if (file && !secondaryFileError.textContent) {
            localStorage.setItem('secondaryCsvFileName', file.name);
        }
    }
    updateUploadButtonState(); // Update button state after file validation
});

// Code to check the CSV files columns to ensure correct files get uploaded
function validateCSV(file, requiredColumns, errorElement) {
    const reader = new FileReader();
    reader.onload = function (event) {
        const csvData = event.target.result.split("\n");
        const headers = csvData[0].split(",").map(header => header.trim());

        // Check if all required columns are present
        const missingColumns = requiredColumns.filter(col => !headers.includes(col));
        if (missingColumns.length > 0) {
            errorElement.textContent = `Missing columns: ${missingColumns.join(", ")}`;
        } else {
            errorElement.textContent = ''; // Clear error if validation passes
        }
        updateUploadButtonState(); // Update button state after validation
    };

    reader.onerror = function () {
        errorElement.textContent = 'Error reading the file. Please try again.';
        updateUploadButtonState(); // Update button state in case of error
    };

    reader.readAsText(file);
}

// Remember the uploaded file names on page load
window.onload = function() {
    const storedMainFileName = localStorage.getItem('csvFileName');
    const storedSecondaryFileName = localStorage.getItem('secondaryCsvFileName');

    if (storedMainFileName) {
        document.getElementById('formFile').nextElementSibling.innerText = storedMainFileName;
    }

    if (storedSecondaryFileName) {
        document.getElementById('formFileSearch').nextElementSibling.innerText = storedSecondaryFileName;
    }

    updateUploadButtonState(); // Check if button should be enabled or disabled
};
