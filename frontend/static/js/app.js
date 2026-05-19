const navToggle = document.querySelector("[data-nav-toggle]");
const siteNav = document.querySelector("[data-site-nav]");

if (navToggle && siteNav) {
    navToggle.addEventListener("click", () => {
        siteNav.classList.toggle("is-open");
    });
}

const pipelineForm = document.querySelector("[data-pipeline-form]");
const pipelineOverlay = document.getElementById("pipeline-overlay");
const pipelineProgress = document.getElementById("pipeline-progress");
const pipelineStatus = document.getElementById("pipeline-status");

const PIPELINE_STAGES = [
    { progress: 20, message: "Searching for grant opportunities…" },
    { progress: 50, message: "Ranking fit to your project…" },
    { progress: 80, message: "Writing concept note (300–400 words)…" },
    { progress: 95, message: "Almost done…" },
];

function startPipelineOverlay() {
    if (!pipelineOverlay || !pipelineProgress) return;
    pipelineOverlay.hidden = false;
    document.body.style.overflow = "hidden";
    let index = 0;
    if (pipelineStatus) pipelineStatus.textContent = PIPELINE_STAGES[0].message;
    pipelineProgress.style.width = "8%";
    window.setInterval(() => {
        if (index >= PIPELINE_STAGES.length) return;
        const stage = PIPELINE_STAGES[index++];
        pipelineProgress.style.width = `${stage.progress}%`;
        if (pipelineStatus) pipelineStatus.textContent = stage.message;
    }, 4500);
}

if (pipelineForm) {
    pipelineForm.addEventListener("submit", () => {
        const submitBtn = pipelineForm.querySelector("[data-submit-btn]");
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.textContent = "Running pipeline…";
        }
        startPipelineOverlay();
    });
}
