const navToggle = document.querySelector("[data-nav-toggle]");
const siteNav = document.querySelector("[data-site-nav]");
const toast = document.querySelector("[data-toast]");

const runButton = document.querySelector("[data-run-agents]");
const statusFill = document.querySelector("[data-status-fill]");
const statusText = document.querySelector("[data-status-text]");
const statusSteps = Array.from(document.querySelectorAll("[data-step]"));
const metricsBlock = document.querySelector("[data-result-metrics]");
const grantsBlock = document.querySelector("[data-grants]");

function showToast(message = "Backend hook pending. UI placeholder only.") {
    if (!toast) return;
    toast.textContent = message;
    toast.classList.add("is-visible");
    window.clearTimeout(showToast.timer);
    showToast.timer = window.setTimeout(() => {
        toast.classList.remove("is-visible");
    }, 2200);
}

if (navToggle && siteNav) {
    navToggle.addEventListener("click", () => {
        siteNav.classList.toggle("is-open");
    });
}

document.querySelectorAll("[data-placeholder]").forEach((element) => {
    element.addEventListener("click", () => {
        showToast();
    });
});

function updateProgress(stepIndex) {
    const totalSteps = statusSteps.length;
    const percent = Math.round(((stepIndex + 1) / totalSteps) * 100);
    statusFill.style.width = `${percent}%`;
    statusText.textContent = statusSteps[stepIndex].textContent;

    statusSteps.forEach((step, index) => {
        step.classList.remove("is-active", "is-done");
        if (index < stepIndex) step.classList.add("is-done");
        if (index === stepIndex) step.classList.add("is-active");
    });
}

if (runButton && statusFill && statusText && statusSteps.length) {
    let running = false;
    runButton.addEventListener("click", () => {
        if (running) return;
        running = true;
        runButton.disabled = true;
        runButton.textContent = "Running...";

        let currentStep = -1;
        const timer = window.setInterval(() => {
            currentStep += 1;
            if (currentStep < statusSteps.length) {
                updateProgress(currentStep);
                return;
            }

            window.clearInterval(timer);
            statusText.textContent = "Done. Ranked grants and draft actions are ready.";
            statusSteps.forEach((step) => {
                step.classList.remove("is-active");
                step.classList.add("is-done");
            });
            runButton.textContent = "Run again";
            runButton.disabled = false;
            running = false;

            if (metricsBlock) {
                metricsBlock.hidden = false;
                metricsBlock.classList.add("is-revealed");
            }
            if (grantsBlock) {
                grantsBlock.hidden = false;
                grantsBlock.classList.add("is-revealed");
            }
        }, 700);
    });
}
