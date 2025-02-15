// ========== Global DOM Elements ==========
const patientSearch = document.getElementById('patientSearch');
const patientList = document.getElementById('patientList');
const patientOverview = document.getElementById('patientOverview');
const conditionTables = document.getElementById('conditionTables');

// The three tables (only Diabetes is used; the others show "No data")
const diabetesTableBody = document.querySelector('#diabetesTable tbody');
const cardioTableBody = document.querySelector('#cardioTable tbody');
const hyperTableBody = document.querySelector('#hyperTable tbody');

// Right sidebar
const testProps = document.getElementById('testProps');
const doctorSummaryContainer = document.getElementById('doctorSummaryContainer');
const patientSummaryContainer = document.getElementById('patientSummaryContainer');
const aiSources = document.getElementById('aiSources');

let selectedPatient = null;

// ========== Bulletify Function ==========
// Converts lines that start with '-' into bullet points, removing the dash from the text.
function bulletify(text) {
  if (!text) return "<p>No summary available.</p>";

  // Split the text by newlines
  let lines = text.split('\n').map(line => line.trim()).filter(l => l.length > 0);

  // Convert each line into a <li>, removing a leading dash if present
  const items = lines.map(line => {
    // Remove a leading dash and any whitespace
    line = line.replace(/^-\s*/, '');
    return `<li>${line}</li>`;
  }).join('');

  return `<ul class="list-disc">${items}</ul>`;
}

// ========== Filter Patient List ==========
patientSearch.addEventListener('input', function() {
  const filter = this.value.toLowerCase();
  const items = patientList.getElementsByTagName('li');
  Array.from(items).forEach(item => {
    const name = item.textContent.toLowerCase();
    item.style.display = name.includes(filter) ? '' : 'none';
  });
});

// ========== Reset the Diabetes Table ==========
function resetTables() {
  diabetesTableBody.innerHTML = '';
  // Cardiovascular & Hypertension remain "No data" by default
}

// ========== Patient Selection & Analysis ==========
const patientItems = document.querySelectorAll('#patientList li');
patientItems.forEach(item => {
  item.addEventListener('click', async () => {
    // Parse the selected patient
    selectedPatient = JSON.parse(item.getAttribute('data-patient'));

    // Update the center panel with basic info
    patientOverview.innerHTML = `
      <h2 class="text-2xl font-bold mb-4">${selectedPatient.name} - Age: ${selectedPatient.age}</h2>
      <p>Loading AI analysis for ${selectedPatient.name}...</p>
    `;
    
    // Show & reset the condition tables
    conditionTables.hidden = false;
    resetTables();

    // Reset the right sidebar
    testProps.innerHTML = `<p>Loading test propositions...</p>`;
    doctorSummaryContainer.innerHTML = `<p>Loading doctor summary...</p>`;
    patientSummaryContainer.innerHTML = `<p>Loading patient summary...</p>`;
    aiSources.innerHTML = `<p>Loading AI sources...</p>`;

    // Make the POST request to your backend /analyze endpoint
    try {
      const response = await fetch("http://127.0.0.1:8000/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ directory: selectedPatient.directory })
      });
      if (!response.ok) {
        throw new Error(`Error analyzing: ${response.statusText}`);
      }
      const aiResult = await response.json();
      displayAiAnalysis(aiResult);
    } catch (error) {
      console.error("Error analyzing patient:", error);
      patientOverview.innerHTML += `<p class="text-red-600 mt-2">Analysis Error: ${error.message}</p>`;
      conditionTables.hidden = true;
    }
  });
});

// ========== Display AI Analysis ==========
function displayAiAnalysis(aiResult) {
  // We only care about the Diabetes table
  resetTables();

  const { initial_response, doctor_summary, patient_summary } = aiResult;
  if (!initial_response) {
    patientOverview.innerHTML += `<p class="text-red-600">No initial_response in AI result</p>`;
    return;
  }
  const { risks, sources } = initial_response;

  // Fill Diabetes table
  if (risks && risks.length > 0) {
    risks.forEach(riskItem => {
      const rowHTML = `
        <tr>
          <td class="border px-4 py-2">${riskItem.risk}</td>
          <td class="border px-4 py-2">${riskItem.observations}</td>
          <td class="border px-4 py-2">${riskItem.severity_level}</td>
        </tr>
      `;
      diabetesTableBody.innerHTML += rowHTML;
    });
  }
  if (!diabetesTableBody.innerHTML) {
    diabetesTableBody.innerHTML = `
      <tr>
        <td class="border px-4 py-2">No data</td>
        <td class="border px-4 py-2">--</td>
        <td class="border px-4 py-2">--</td>
      </tr>
    `;
  }

  // Test Propositions: remove dash from text
  let testPropositionsHTML = '';
  (risks || []).forEach(r => {
    // remove leading dash from doctor advise
    const adviseClean = r.doctor_advise.replace(/^-\s*/, '');
    testPropositionsHTML += `<li>${adviseClean}</li>`;
  });
  if (!testPropositionsHTML) {
    testPropositionsHTML = "<li>No test propositions</li>";
  }
  testProps.innerHTML = `<ul class="list-disc list-inside">${testPropositionsHTML}</ul>`;

  // Doctor & Patient Summaries: bulletify lines that start with dash
  doctorSummaryContainer.innerHTML = bulletify(doctor_summary);
  patientSummaryContainer.innerHTML = bulletify(patient_summary);

  // AI Sources
  let sourcesHTML = (sources || []).map(s => `<li class="text-sm text-blue-600 hover:underline"><a href="#">${s}</a></li>`).join("");
  if (!sourcesHTML) sourcesHTML = "<li>No sources found</li>";
  aiSources.innerHTML = `<ul class="list-disc list-inside">${sourcesHTML}</ul>`;
}
