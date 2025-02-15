// ========== Global DOM Elements ==========
const patientSearch = document.getElementById('patientSearch');
const patientList = document.getElementById('patientList');
const patientOverview = document.getElementById('patientOverview');
const analysisResult = document.getElementById('analysisResult');
const conditionTables = document.getElementById('conditionTables');

// The 3 tables
const diabetesTableBody = document.querySelector('#diabetesTable tbody');
const cardioTableBody = document.querySelector('#cardioTable tbody');
const hyperTableBody = document.querySelector('#hyperTable tbody');

// Right sidebar sections
const testProps = document.getElementById('testProps');
const lifestyleRecs = document.getElementById('lifestyleRecs');
const aiSources = document.getElementById('aiSources');

let selectedPatient = null;

// ========== Patient Search ==========
patientSearch.addEventListener('input', function() {
  const filter = this.value.toLowerCase();
  const items = patientList.getElementsByTagName('li');
  Array.from(items).forEach(item => {
    const name = item.textContent.toLowerCase();
    item.style.display = name.includes(filter) ? '' : 'none';
  });
});

// ========== Reset the 3 tables ==========
function resetTables() {
  diabetesTableBody.innerHTML = '';
  cardioTableBody.innerHTML = '';
  hyperTableBody.innerHTML = '';
}

// ========== Display an error message in the center panel ==========
function displayError(errorMsg, patientName) {
  conditionTables.hidden = true;
  analysisResult.classList.remove('hidden');
  analysisResult.innerHTML = `
    <h2 class="text-xl font-bold mb-2 text-[#05066D]">Analysis Error</h2>
    <p class="text-red-600">Error analyzing ${patientName}: ${errorMsg}</p>
  `;
}

// ========== Display AI Analysis ==========
function displayAiAnalysis(aiResult) {
  // Clear old table data
  resetTables();

  // Show analysis container
  analysisResult.classList.remove('hidden');
  analysisResult.innerHTML = '';

  // Extract data
  const { initial_response, doctor_summary, patient_summary } = aiResult;
  if (!initial_response) {
    analysisResult.innerHTML = '<p class="text-red-600">No initial_response in AI result</p>';
    return;
  }
  const { risks, sources } = initial_response;

  // Fill the 3 tables from "risks"
  (risks || []).forEach(riskItem => {
    const rowHTML = `
      <tr>
        <td class="border px-4 py-2">${riskItem.risk}</td>
        <td class="border px-4 py-2">${riskItem.observations}</td>
        <td class="border px-4 py-2">${riskItem.severity_level}</td>
      </tr>
    `;
    const riskLower = (riskItem.risk || "").toLowerCase();
    if (riskLower.includes('bmi') || riskLower.includes('hba1c') || riskLower.includes('diabetes')) {
      diabetesTableBody.innerHTML += rowHTML;
    } else if (riskLower.includes('cholesterol') || riskLower.includes('cardio')) {
      cardioTableBody.innerHTML += rowHTML;
    } else if (riskLower.includes('hypertension') || riskLower.includes('blood pressure') || riskLower.includes('bp')) {
      hyperTableBody.innerHTML += rowHTML;
    } else {
      // If no match, put in Diabetes by default
      diabetesTableBody.innerHTML += rowHTML;
    }
  });

  // If any table is empty, show "No data"
  if (!diabetesTableBody.innerHTML) {
    diabetesTableBody.innerHTML = `
      <tr>
        <td class="border px-4 py-2">No data</td>
        <td class="border px-4 py-2">--</td>
        <td class="border px-4 py-2">--</td>
      </tr>
    `;
  }
  if (!cardioTableBody.innerHTML) {
    cardioTableBody.innerHTML = `
      <tr>
        <td class="border px-4 py-2">No data</td>
        <td class="border px-4 py-2">--</td>
        <td class="border px-4 py-2">--</td>
      </tr>
    `;
  }
  if (!hyperTableBody.innerHTML) {
    hyperTableBody.innerHTML = `
      <tr>
        <td class="border px-4 py-2">No data</td>
        <td class="border px-4 py-2">--</td>
        <td class="border px-4 py-2">--</td>
      </tr>
    `;
  }

  // Fill the center analysis result
  analysisResult.innerHTML = `
    <h2 class="text-xl font-bold mb-2 text-[#05066D]">AI Analysis Result</h2>
    <div class="mb-4">
      <h3 class="font-semibold text-[#05066D]">Doctor Summary:</h3>
      <p class="text-sm text-gray-800 whitespace-pre-line">${doctor_summary || "No summary."}</p>
    </div>
    <div class="mb-4">
      <h3 class="font-semibold text-[#05066D]">Patient Summary:</h3>
      <p class="text-sm text-gray-800 whitespace-pre-line">${patient_summary || "No summary."}</p>
    </div>
  `;

  // Right sidebar
  let testPropositionsHTML = '';
  let lifestyleHTML = '';
  (risks || []).forEach(r => {
    testPropositionsHTML += `<li>- ${r.doctor_advise}</li>`;
    lifestyleHTML += `<li>- ${r.patient_advise}</li>`;
  });
  testProps.innerHTML = `<ul class="list-disc list-inside">${testPropositionsHTML || "<li>No test propositions</li>"}</ul>`;
  lifestyleRecs.innerHTML = `<ul class="list-disc list-inside">${lifestyleHTML || "<li>No lifestyle recs</li>"}</ul>`;

  let sourcesHTML = (sources || []).map(s => `<li class="text-sm text-blue-600 hover:underline"><a href="#">${s}</a></li>`).join("");
  if (!sourcesHTML) sourcesHTML = "<li>No sources found</li>";
  aiSources.innerHTML = `<ul class="list-disc list-inside">${sourcesHTML}</ul>`;
}

// ========== Automatic AI Analysis on Patient Click ==========
const items = document.querySelectorAll('#patientList li');
items.forEach(li => {
  li.addEventListener('click', async () => {
    // Parse patient
    const patient = JSON.parse(li.getAttribute('data-patient'));
    // Update the overview with basic info
    patientOverview.innerHTML = `
      <h2 class="text-2xl font-bold mb-4">${patient.name} - Age: ${patient.age}</h2>
      <p>Loading AI analysis...</p>
    `;
    // Show the tables area, reset them
    conditionTables.hidden = false;
    resetTables();
    // Hide old analysis
    analysisResult.classList.add('hidden');
    analysisResult.innerHTML = '';
    // Right sidebar placeholders
    testProps.innerHTML = '<p>Loading test propositions...</p>';
    lifestyleRecs.innerHTML = '<p>Loading lifestyle recommendations...</p>';
    aiSources.innerHTML = '<p>Loading AI sources...</p>';

    // Now call the AI backend
    try {
      const response = await fetch("http://127.0.0.1:8000/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ directory: patient.directory })
      });
      if (!response.ok) {
        throw new Error(`Error analyzing: ${response.statusText}`);
      }
      const aiResult = await response.json();
      displayAiAnalysis(aiResult);
    } catch (error) {
      console.error("Error analyzing patient:", error);
      displayError(error.message, patient.name);
    }
  });
});

// Original patient handling code unchanged
    // Patient Search Functionality
    const searchInput = document.getElementById('patientSearch');
    
    searchInput.addEventListener('input', function() {
      const filter = this.value.toLowerCase();
      const items = patientList.getElementsByTagName('li');
      Array.from(items).forEach(item => {
        const name = item.textContent.toLowerCase();
        item.style.display = name.includes(filter) ? '' : 'none';
      });
    });

class FileUploader {
  constructor() {
    this.fileMap = new Map();
    this.uploadContainer = document.getElementById('uploadContainer');
    this.fileInput = document.getElementById('fileInput');
    this.fileList = document.getElementById('fileList');
    this.initEventHandlers();
  }

  initEventHandlers() {
    this.uploadContainer.addEventListener('click', () => this.fileInput.click());
    
    this.fileInput.addEventListener('change', (e) => {
      this.handleFiles(e.target.files);
    });

    // Drag-and-drop handlers
    ['dragenter', 'dragover'].forEach(event => {
      this.uploadContainer.addEventListener(event, this.highlightDropzone.bind(this));
    });
    
    ['dragleave', 'drop'].forEach(event => {
      this.uploadContainer.addEventListener(event, this.unhighlightDropzone.bind(this));
    });

    this.uploadContainer.addEventListener('drop', (e) => {
      e.preventDefault();
      this.handleFiles(e.dataTransfer.files);
    });
  }

  handleFiles(files) {
    Array.from(files).forEach(file => {
      if(this.validateFile(file)) {
        this.fileMap.set(file.name, file);
      }
    });
    this.renderFileList();
  }

  validateFile(file) {
    const MAX_SIZE = 25 * 1024 * 1024; // 25MB
    const validTypes = ['image/png', 'application/pdf'];
    
    if(!validTypes.includes(file.type)) {
      alert('Invalid file type');
      return false;
    }
    
    if(file.size > MAX_SIZE) {
      alert('File size exceeds 25MB limit');
      return false;
    }
    
    return true;
  }

  renderFileList() {
    this.fileList.innerHTML = '';
    
    this.fileMap.forEach((file, name) => {
      const fileEl = document.createElement('div');
      fileEl.className = 'flex items-center justify-between p-3 bg-white rounded-lg border border-[#E1EAFE]';
      
      fileEl.innerHTML = `
        <div class="flex-1 truncate">
          <span class="font-medium text-[#05066D]">${name}</span>
          <span class="text-sm text-[#05066D]/80 ml-2">${this.formatFileSize(file.size)}</span>
        </div>
        <button class="text-red-500 hover:text-red-700 transition-colors" aria-label="Remove file">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/>
          </svg>
        </button>
      `;
      
      fileEl.querySelector('button').addEventListener('click', () => {
        this.fileMap.delete(name);
        this.renderFileList();
      });
      
      this.fileList.appendChild(fileEl);
    });
  }

  formatFileSize(bytes) {
    const units = ['B', 'KB', 'MB', 'GB'];
    let size = bytes;
    let unitIndex = 0;
    
    while(size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }
    
    return `${size.toFixed(1)}${units[unitIndex]}`;
  }

  highlightDropzone(e) {
    e.preventDefault();
    this.uploadContainer.classList.add('dragover');
  }

  unhighlightDropzone(e) {
    e.preventDefault();
    this.uploadContainer.classList.remove('dragover');
  }
}

// Initialize uploader
new FileUploader();

