const apiBase = "http://localhost:8080/v2";
let modelMap = {};
const submittedJobIds = [];

window.addEventListener("DOMContentLoaded", async () => {
  const loggedIn = await initAuth();
  updateUI(loggedIn);
  if (loggedIn) loadModels();

  document.getElementById("login").onclick = async () => {
    await login();
    updateUI(true);
    loadModels();
  };

  document.getElementById("logout").onclick = logout;

  document.getElementById("predict-form").onsubmit = submitPrediction;
  document.getElementById("job-form").onsubmit = checkJob;
  document.getElementById("fetch-models").onclick = fetchAllModels;
  document.getElementById("model-info").onclick = fetchModelMetadata;
});

function updateUI(authenticated) {
  document.getElementById("login").style.display = authenticated ? "none" : "inline";
  document.getElementById("logout").style.display = authenticated ? "inline" : "none";
  document.getElementById("auth-status").textContent = authenticated ? "✅ Authenticated" : "🔓 Not Logged In";
  document.getElementById("predict-form").style.display = authenticated ? "block" : "none";
  document.getElementById("job-form").style.display = authenticated ? "block" : "none";
  document.getElementById("fetch-models").style.display = authenticated ? "inline" : "none";
}

async function loadModels() {
  try {
    const res = await fetch(`${apiBase}/models`, {
      headers: { Authorization: `Bearer ${getToken()}` }
    });
    const models = await res.json();

    if (!Array.isArray(models)) throw new Error("Expected models to be an array");

    const dropdown = document.getElementById("model-id");
    dropdown.innerHTML = "";
    modelMap = {};

    models.forEach(m => {
      const opt = document.createElement("option");
      opt.value = m.model_id;
      opt.textContent = m.name;
      dropdown.appendChild(opt);
      modelMap[m.model_id] = m;
    });
  } catch (e) {
    console.error("Failed to load models", e);
  }
}

async function fetchModelMetadata() {
  const modelId = document.getElementById("model-id").value;
  try {
    const res = await fetch(`${apiBase}/models/${modelId}`, {
      headers: { Authorization: `Bearer ${getToken()}` }
    });
    const data = await res.json();
    document.getElementById("model-metadata").textContent = JSON.stringify(data, null, 2);
  } catch (err) {
    document.getElementById("model-metadata").textContent = "❌ Error loading metadata";
  }
}

async function submitPrediction(e) {
  e.preventDefault();
  const modelId = document.getElementById("model-id").value;
  const model = modelMap[modelId];
  const isAsync = model?.type === "async";
  const endpoint = isAsync ? "/jobs" : "/predict";
  const inputs = JSON.parse(document.getElementById("inputs").value);

  document.getElementById("response").textContent = "⏳ Sending...";

  try {
    const res = await fetch(`${apiBase}${endpoint}`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${getToken()}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ model_id: modelId, inputs })
    });
    const data = await res.json();
    document.getElementById("response").textContent = JSON.stringify(data, null, 2);

    // Track job ID if async
    if (isAsync && data.job_id) {
      submittedJobIds.push(data.job_id);
      const jobDropdown = document.getElementById("job-id-dropdown");
      const opt = document.createElement("option");
      opt.value = data.job_id;
      opt.textContent = data.job_id;
      jobDropdown.appendChild(opt);
    }

  } catch (err) {
    document.getElementById("response").textContent = "❌ " + err.message;
  }
}

async function checkJob(e) {
  e.preventDefault();
  const jobId = document.getElementById("job-id-dropdown").value;
  document.getElementById("job-response").textContent = "🔄 Fetching job...";
  try {
    const res = await fetch(`${apiBase}/jobs/${jobId}`, {
      headers: { Authorization: `Bearer ${getToken()}` }
    });
    const data = await res.json();
    document.getElementById("job-response").textContent = JSON.stringify(data, null, 2);
  } catch (err) {
    document.getElementById("job-response").textContent = "❌ " + err.message;
  }
}

async function fetchAllModels() {
  document.getElementById("model-list").textContent = "Loading...";
  try {
    const res = await fetch(`${apiBase}/models`, {
      headers: { Authorization: `Bearer ${getToken()}` }
    });
    const data = await res.json();
    document.getElementById("model-list").textContent = JSON.stringify(data, null, 2);
  } catch (err) {
    document.getElementById("model-list").textContent = "❌ " + err.message;
  }
}
