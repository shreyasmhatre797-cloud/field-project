function toggleMenu() {
    document.querySelector(".nav-links").classList.toggle("active");
}


function joinPlan(plan) {
    window.location.href = "/register?plan=" + encodeURIComponent(plan);
}


function submitForm(event) {

    event.preventDefault();

    let name = document.getElementById("name").value;

    alert(
        "Thank you " +
        name +
        "! Your message has been submitted."
    );

    document.querySelector("form").reset();
}

window.addEventListener("DOMContentLoaded", function () {
    const params = new URLSearchParams(window.location.search);
    const plan = params.get("plan");
    const membership = document.getElementById("membership");

    if (plan && membership) {
        membership.value = plan;
    }
});