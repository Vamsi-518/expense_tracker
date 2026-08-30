

const searchInput = document.getElementById("searchInput");

if (searchInput) {

    searchInput.addEventListener("keyup", function () {

        const searchValue = this.value.toLowerCase();

        const rows = document.querySelectorAll(
            "#transactionTable tbody tr"
        );

        rows.forEach(function (row) {

            const text = row.textContent.toLowerCase();

            if (text.includes(searchValue)) {
                row.style.display = "";
            } else {
                row.style.display = "none";
            }

        });

    });

}


function confirmDelete() {

    return confirm(
        "Are you sure you want to delete this transaction?"
    );

}



const dateInput = document.getElementById("transaction_date");

if (dateInput) {

    const today = new Date();

    const year = today.getFullYear();

    const month = String(
        today.getMonth() + 1
    ).padStart(2, "0");

    const day = String(
        today.getDate()
    ).padStart(2, "0");

    dateInput.value = `${year}-${month}-${day}`;
}