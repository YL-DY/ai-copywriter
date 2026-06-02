document.addEventListener("DOMContentLoaded", function () {
    var btn = document.querySelector(".nav-generate-btn");
    if (btn) {
        btn.addEventListener("click", function () {
            if (typeof setPageView === "function") {
                setPageView("generate");
            } else {
                window.location.href = "/generate";
            }
        });
    }
});
