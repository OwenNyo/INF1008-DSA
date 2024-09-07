document.addEventListener("DOMContentLoaded", function() {
  const operatorBtn = document.querySelector("label.operator");
  const guestsBtn = document.querySelector("label.guests");
  const sliderTab = document.querySelector(".slider-tab");
  const formInner = document.querySelector(".form-inner");
  const title = document.querySelector(".title");

  operatorBtn.addEventListener("click", () => {
    sliderTab.style.left = "0";
    formInner.style.transform = "translateX(0)";
    title.textContent = "Operator Login";
  });

  guestsBtn.addEventListener("click", () => {
    sliderTab.style.left = "50%";
    formInner.style.transform = "translateX(-50%)";
    title.textContent = "Guests Login";
  });
});
