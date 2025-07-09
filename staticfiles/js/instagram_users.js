function filterRows() {
    const filterValue = document.getElementById("filter").value.toLowerCase();
    const allRows = document.querySelectorAll("#all-users-table tbody tr"); // Hidden table rows
    const visibleTable = document.querySelector("#users-table tbody");
    visibleTable.innerHTML = ""; // Clear the visible table rows

    allRows.forEach(row => {
        const profileViewedCell = row.querySelector("td:nth-child(4)"); // "Profile Viewed" column
        const profileViewedValue = profileViewedCell ? profileViewedCell.textContent.trim().toLowerCase() : "";

        // Check the filter condition
        if (
            filterValue === "all" ||
            (filterValue === "yes" && profileViewedValue === "yes") ||
            (filterValue === "no" && profileViewedValue === "no")
        ) {
            visibleTable.appendChild(row.cloneNode(true)); // Add filtered row to the visible table
        }
    });

    // If no rows match, display a message
    if (visibleTable.innerHTML.trim() === "") {
        visibleTable.innerHTML = `<tr><td colspan="4">No users found.</td></tr>`;
    }
}
