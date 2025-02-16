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
  
  // Determine if the API returned a nested structure (old) or a flat structure (new)
  let riskData, doctorSummaryText, patientSummaryText, sources;
  
  if (aiResult.initial_response && aiResult.initial_response.risks) {
    // Old (nested) structure
    riskData = aiResult.initial_response.risks;
    doctorSummaryText = aiResult.doctor_summary;
    patientSummaryText = aiResult.patient_summary;
    sources = aiResult.initial_response.sources;
  } else {
    // Flat structure: create an array with one element using the flat keys
    riskData = [{
      risk: aiResult.risk,
      severity_level: aiResult.severity_level,
      observations: aiResult.observations,
      therapeutic_goal: aiResult.therapeutic_goal
    }];
    doctorSummaryText = aiResult.doctor_advise;
    patientSummaryText = aiResult.patient_advise;
    sources = aiResult.sources || [];
  }
  
  // Fill the Diabetes table with a single row (4 columns):
  // Risk, Severity, Observations, and Therapeutic Goal.
  if (riskData && riskData.length > 0) {
    riskData.forEach(riskItem => {
      const rowHTML = `
        <tr>
          <td class="border px-4 py-2">${riskItem.risk || "No data"}</td>
          <td class="border px-4 py-2">${riskItem.severity_level || "--"}</td>
          <td class="border px-4 py-2">${riskItem.observations || "--"}</td>
          <td class="border px-4 py-2">${riskItem.therapeutic_goal || "--"}</td>
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
        <td class="border px-4 py-2">--</td>
      </tr>
    `;
  }
  
  // Update the right sidebar summaries
  doctorSummaryContainer.innerHTML = bulletify(doctorSummaryText);
  patientSummaryContainer.innerHTML = bulletify(patientSummaryText);
  
  // Update AI sources if available
  let sourcesHTML = (sources || [])
    .map(src => `<li class="text-sm text-blue-600 hover:underline"><a href="#">${src}</a></li>`)
    .join("");
  if (!sourcesHTML) sourcesHTML = "<li>No sources found</li>";
  aiSources.innerHTML = `<ul class="list-disc list-inside">${sourcesHTML}</ul>`;
}

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