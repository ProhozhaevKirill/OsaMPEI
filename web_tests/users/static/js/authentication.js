$(document).ready(function () {
    $(".tab-btn").click(function () {
        const target = $(this).attr("id") === "login-tab" ? "#login-form" : "#register-form";

        $(".tab-btn").removeClass("active");
        $(this).addClass("active");

        $(".form").removeClass("active");
        $(target).addClass("active");
    });
});
