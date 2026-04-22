async function loadLeads() {
    const res = await fetch("/api/leads");
    const data = await res.json();

    const grid = document.getElementById("grid");
    grid.innerHTML = "";

    data.forEach(lead => {
        const card = document.createElement("div");

        card.className = "bg-white p-4 rounded-2xl shadow";

        card.innerHTML = `
            <h2 class="text-lg font-bold">${lead.name}</h2>
            <p class="text-sm text-gray-600">${lead.industry}</p>

            <div class="mt-2">
                <span class="text-green-600 font-bold">
                    Score: ${lead.score}
                </span>
            </div>

            <p class="text-sm mt-2">
                ${lead.reason}
            </p>
        `;

        grid.appendChild(card);
    });
}