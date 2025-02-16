// ========== Global DOM Elements ==========
const patientSearch = document.getElementById('patientSearch');
const patientList = document.getElementById('patientList');
const patientOverview = document.getElementById('patientOverview');
const conditionTables = document.getElementById('conditionTables');

// The three tables
const diabetesTableBody = document.querySelector('#diabetesTable tbody');
const cardioTableBody = document.querySelector('#cardioTable tbody');
const hyperTableBody = document.querySelector('#hyperTable tbody');

// Right sidebar
const doctorSummaryContainer = document.getElementById('doctorSummaryContainer');
const patientSummaryContainer = document.getElementById('patientSummaryContainer');
const aiSources = document.getElementById('aiSources');

// ========== bulletify ==========
// Removes leading dash & asterisks, shows lines as bullet points
function bulletify(text) {
  if (!text) return "<p>No summary available.</p>";
  let lines = text.split('\n').map(l => l.trim()).filter(l => l.length > 0);
  const items = lines.map(line => {
    line = line.replace(/^-\s*/, '').replace(/\*/g, '');
    return `<li>${line}</li>`;
  }).join('');
  return `<ul class="list-disc list-inside">${items}</ul>`;
}

// ========== Searching Patients ==========
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
}

// ========== Auto-Select Patient 0 on Load ==========
document.addEventListener("DOMContentLoaded", () => {
  const patient0Item = document.querySelector('#patientList li[data-patient*="patient_0"]');
  if (patient0Item) {
    patient0Item.click();
  }
});

// ========== Handle Patient Selection ==========
const patientItems = document.querySelectorAll('#patientList li');
patientItems.forEach(item => {
  item.addEventListener('click', async () => {
    const patient = JSON.parse(item.getAttribute('data-patient'));
    console.log("User selected:", patient);

    // Update center panel
    patientOverview.innerHTML = `
      <h2 class="text-2xl font-bold mb-4">${patient.name} - Age: ${patient.age}</h2>
      <p>Loading AI analysis for ${patient.name}...</p>
    `;
    conditionTables.hidden = false;
    resetTables();

    // Right sidebar placeholders
    doctorSummaryContainer.innerHTML = `<p>Loading doctor summary...</p>`;
    patientSummaryContainer.innerHTML = `<p>Loading patient summary...</p>`;
    aiSources.innerHTML = `<p>Loading AI sources...</p>`;

    // We'll do a GET to /analysis/patient_0, etc.
    try {
      const url = `http://127.0.0.1:8000/analysis/${patient.id}`;
      console.log("Fetching:", url);
      const response = await fetch(url);
      console.log("Response status:", response.status);

      if (!response.ok) {
        // If it's 404, we interpret it as "still processing"
        if (response.status === 404) {
          throw new Error("Analysis is still processing. Please try again later.");
        } else {
          throw new Error(`Server returned status ${response.status}`);
        }
      }
      const aiResult = await response.json();
      console.log("AI result for", patient.id, aiResult);
      displayAiAnalysis(aiResult);
    } catch (error) {
      console.error("Error fetching analysis:", error);
      // If it's "still processing," show a special message
      patientOverview.innerHTML += `<p class="text-red-600 mt-2">${error.message}</p>`;
      conditionTables.hidden = true;
    }
  });
});

// ========== Display AI Analysis ==========
function displayAiAnalysis(aiResult) {
  resetTables();
  const { initial_response, doctor_summary, patient_summary } = aiResult;
  if (!initial_response) {
    patientOverview.innerHTML += `<p class="text-red-600">No initial_response in AI result</p>`;
    return;
  }
  const { risks, sources } = initial_response;

  // Fill the Diabetes table
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

  // Summaries
  doctorSummaryContainer.innerHTML = bulletify(doctor_summary);
  patientSummaryContainer.innerHTML = bulletify(patient_summary);

  // AI Sources
  let sourcesHTML = (sources || []).map(src => `<li class="text-sm text-blue-600 hover:underline"><a href="#">${src}</a></li>`).join("");
  if (!sourcesHTML) sourcesHTML = "<li>No sources found</li>";
  aiSources.innerHTML = `<ul class="list-disc list-inside">${sourcesHTML}</ul>`;
}
