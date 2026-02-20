document.addEventListener("DOMContentLoaded", function () {

  // Executive board names (must match CSV values, check members.csv)
  // Ideally this would be done via SQL?
  const execBoard = [
    "Natalia Contreras",
    "Kayla Poirier",
    "Melissa Samperio",
    "Mrunal Natu",
    "Zareeb Lorenzana"
  ];

  fetch("/members.csv")
    .then(response => response.text())
    .then(csv => {
      const rows = csv.trim().split("\n").slice(1); // skip header
      const container = document.getElementById("member-list");

      rows.forEach(row => {
        const cols = row.split(",");

        const firstName = cols[0].trim();
        const lastName = cols[1].trim();
        const major = cols[2].trim();
        const status = cols[3] ? cols[3].trim() : "";

        const fullName = `${firstName} ${lastName}`;

        // Exclude executive board
        if (execBoard.includes(fullName)) return;

        const memberDiv = document.createElement("div");
        memberDiv.classList.add("board-member");

        memberDiv.innerHTML = `
          <div class="board-name">${fullName}</div>
          <div class="board-meta">${major}</div>
          ${status.toLowerCase().includes("graduate") 
            ? `<div class="board-meta">${status}</div>` 
            : ""}
        `;

        container.appendChild(memberDiv);
      });
    });
});
