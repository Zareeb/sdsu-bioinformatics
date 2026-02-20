document.addEventListener("DOMContentLoaded", function () {
  const toggle = document.getElementById("menu-toggle");
  const nav = document.getElementById("nav-links");

  if (toggle) {
    toggle.addEventListener("click", function () {
      nav.classList.toggle("active");
    });
  }
});