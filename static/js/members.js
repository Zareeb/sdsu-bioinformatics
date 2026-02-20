document.addEventListener("DOMContentLoaded", function () {
  // Future you (or someone else):
  // Make sure execBoard name matches names in the csv (or whatever database it will be on in the future)
  const execBoard = [
    "Natalia Contreras",
    "Kayla Poirier",
    "Melissa Samperio",
    "Mrunal Natu",
    "Zareeb Lorenzana"
  ];

  // Retrieve members list from json file. Location could change in the future
  fetch("/members.json")
    .then(response => response.json())
    .then(data => {

      // elementId needs to match div id in members html file
      const container = document.getElementById("member-list");

      // Sort alphabetically by last name, then first name
      data.sort((a, b) => {
        if (a.last_name === b.last_name) {
          return a.first_name.localeCompare(b.first_name);
        }
        return a.last_name.localeCompare(b.last_name);
      });

      data.forEach(member => {

        const fullName = `${member.first_name} ${member.last_name}`;

        // Skip executive board
        if (execBoard.includes(fullName)) return;

        const memberDiv = document.createElement("div");
        memberDiv.classList.add("board-member");

        const showGraduate =
          member.status &&
          member.status.toLowerCase().includes("graduate");

        memberDiv.innerHTML = `
          <div class="board-name">${fullName}</div>
          <div class="board-meta">${member.major || ""}</div>
          ${showGraduate ? `<div class="board-meta">${member.status}</div>` : ""}
        `;

        container.appendChild(memberDiv);
      });
    })
    .catch(error => {
      console.error("Error loading members:", error);
    });
});
