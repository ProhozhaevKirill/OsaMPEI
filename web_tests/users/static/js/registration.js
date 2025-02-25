document.addEventListener("DOMContentLoaded", function () {
    const signupBtn = document.getElementById("signup-btn");
    const signinBtn = document.getElementById("signin-btn");
    const signupForm = document.getElementById("signup-form");
    const signinForm = document.getElementById("signin-form");

    signupBtn.addEventListener("click", () => {
        signupForm.style.display = "block";
        signinForm.style.display = "none";
        signupBtn.classList.add("active");
        signinBtn.classList.remove("active");
    });

    signinBtn.addEventListener("click", () => {
        signupForm.style.display = "none";
        signinForm.style.display = "block";
        signupBtn.classList.remove("active");
        signinBtn.classList.add("active");
    });
});
