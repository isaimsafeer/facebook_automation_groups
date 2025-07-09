// Function to filter the table rows based on the selected filter
function filterRows() {
    const filterValue = document.getElementById("filter").value.toLowerCase();
    const allRows = document.querySelectorAll("#messages-table tbody tr"); // Use the table that is shown to the user
    const visibleTable = document.querySelector("#messages-table tbody");

    // Clear the visible table rows before applying the filter
    visibleTable.innerHTML = "";

    allRows.forEach(row => {
        const deliveredCell = row.querySelector("td:nth-child(3)");
        const deliveredValue = deliveredCell ? deliveredCell.textContent.trim().toLowerCase() : "";

        // Apply the filter logic to decide whether to show the row
        if (filterValue === "all" ||
            (filterValue === "delivered" && deliveredValue === "delivered") ||
            (filterValue === "not-delivered" && deliveredValue !== "delivered")) {
            visibleTable.appendChild(row.cloneNode(true)); // Add matching rows to visible table
        }
    });

   
}

// Function to download the filtered table content as a CSV file
function downloadCSV() {
    const visibleRows = document.querySelectorAll("#messages-table tbody tr");
    const csv = [];

    // Iterate through each visible row and get the cell data
    visibleRows.forEach(row => {
        const cells = row.querySelectorAll('th, td');
        const rowData = Array.from(cells).map(cell => cell.textContent.trim());
        csv.push(rowData.join(',')); // Add each row to the CSV array
    });

    // Convert array to CSV format
    const csvContent = csv.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);

    // Create a temporary link and trigger the download
    const link = document.createElement('a');
    link.href = url;
    link.download = 'filtered_messages.csv';
    link.click();

    // Cleanup
    URL.revokeObjectURL(url);
}

// Ensure filter is applied on page load (if needed)
document.addEventListener("DOMContentLoaded", function() {
    filterRows(); // Apply filter immediately when the page loads
});
