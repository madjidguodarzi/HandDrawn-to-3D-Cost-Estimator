const API_BASE = "/api";
const chatMessages = document.getElementById('chatMessages');
const userInput = document.getElementById('userInput');
const typingIndicator = document.getElementById('typingIndicator');
const sendBtn = document.getElementById('sendBtn');
const samplesContainer = document.getElementById('samplesContainer');

// --- Mock Data Storage ---
let mockDatabase = {};

// --- Quick Samples Configuration ---
const quickSamples = [
    { icon: "fa-database", text: "Export DB" },
    { icon: "fa-calculator", text: "Total cost of Living Room" },
    { icon: "fa-paint-roller", text: "Painting costs for all rooms" },
    { icon: "fa-layer-group", text: "List all floor tiles and prices" },
    { icon: "fa-ruler-combined", text: "Show walls larger than 5 (m2)" },
    { icon: "fa-money-bill-wave", text: "Most expensive item in Kitchen" }
];

// Initialize Page
document.addEventListener('DOMContentLoaded', async () => {
    initSamples();
    await loadMockData();
});

/**
 * 1. Load Mock Data from JSON file on startup
 */
async function loadMockData() {
    try {
        const response = await fetch('/static/report/mock_data.json');
        if (response.ok) {
            mockDatabase = await response.json();
            console.log("✅ Mock data loaded:", Object.keys(mockDatabase).length, "entries");
        } else {
            console.warn("⚠️ mock_data.json not found.");
        }
    } catch (e) {
        console.warn("⚠️ Could not load mock data.", e);
    }
}

function initSamples() {
    samplesContainer.innerHTML = quickSamples.map(sample => `
        <div class="sample-chip" onclick="handleSampleClick('${sample.text}')">
            <i class="fa-solid ${sample.icon}"></i>
            ${sample.text}
        </div>
    `).join('');
}

/**
 * 2. Dedicated Handler for Sample Chips (Reads directly from JSON)
 * This function NEVER calls the LLM or API.
 */
window.handleSampleClick = function(question) {
    const mockResult = mockDatabase[question];
    question = mockDatabase[question].question;

    // Fill input for visual feedback
    userInput.value = question;

    // Add User Message to Chat
    addMessage(question, 'user');
    
    // Simulate thinking time for better UX
    showLoading(true);
    
    setTimeout(() => {
        showLoading(false);
        
        if (mockResult) {
            renderAIResponse(mockResult);
        } else {
            addMessage(`⚠️ No mock data found for "${question}". Please type your request to use the live AI.`, 'ai');
        }
        
        userInput.value = ''; // Clear input after sample click
    }, 400); // Small delay for realism
}

/**
 * 3. Main Send Function (ALWAYS calls LLM/API)
 */
async function sendMessage() {
    const question = userInput.value.trim();
    if (!question) return;

    const projectId = getProjectIdFromPath();
    
    // Add User Message
    addMessage(question, 'user');
    userInput.value = '';
    
    // Show Loading
    showLoading(true);
    sendBtn.disabled = true;

    try {
        if (!projectId) {
            throw new Error("Could not find Project ID in URL.");
        }
        
        // Call Real API
        const response = await fetch(`${API_BASE}/project/report`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                question: question,
                project_id: parseInt(projectId)
            })
        });

        if (!response.ok) throw new Error('Network response was not ok');
        const data = await response.json();
        
        renderAIResponse(data);

    } catch (error) {
        console.error(error);
        addMessage(`❌ Error: ${error.message}`, 'ai');
    } finally {
        showLoading(false);
        sendBtn.disabled = false;
        userInput.focus();
    }
}

/**
 * Helper to render any response (Mock or Live) consistently
 */
function renderAIResponse(data) {
    let aiResponseHtml = "";
    
    if (data.message && data.message.includes("❌")) {
        aiResponseHtml = `<strong>Error:</strong> ${data.message}`;
    } else if (data.data && data.data.length > 0) {
        aiResponseHtml = `Here are the results:<br>`;
        aiResponseHtml += generateTable(data.data);
        
        if (data.generated_sql) {
            aiResponseHtml += `<details style="margin-top:10px; cursor:pointer;">
                <summary style="font-size:0.8rem; color:#666;">View Generated SQL</summary>
                <div class="sql-preview">${escapeHtml(data.generated_sql)}</div>
            </details>`;
        }
    } else {
        aiResponseHtml = "I couldn't find any data matching that request.";
    }

    addMessage(aiResponseHtml, 'ai', true);
}

// --- Utility Functions ---

function getProjectIdFromPath() {
    const pathParts = window.location.pathname.split('/');
    const projectIndex = pathParts.indexOf('project');
    if (projectIndex !== -1 && pathParts[projectIndex + 1]) {
        return pathParts[projectIndex + 1];
    }
    return null;
}

function addMessage(content, sender, isHtml = false) {
    const div = document.createElement('div');
    div.className = `message ${sender}`;
    if (isHtml) {
        div.innerHTML = content;
    } else {
        div.textContent = content;
    }
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function showLoading(show) {
    typingIndicator.style.display = show ? 'block' : 'none';
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function generateTable(data) {
    if (!data || data.length === 0) return '';
    const headers = Object.keys(data[0]);
    let html = '<div class="result-table-wrapper"><table><thead><tr>';
    headers.forEach(h => {
        const formattedHeader = h.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
        html += `<th>${formattedHeader}</th>`;
    });
    html += '</tr></thead><tbody>';
    data.forEach(row => {
        html += '<tr>';
        headers.forEach(h => {
            let val = row[h];
            if (typeof val === 'number' && !Number.isInteger(val)) val = val.toFixed(2);
            html += `<td>${val !== null ? val : '-'}</td>`;
        });
        html += '</tr>';
    });
    html += '</tbody></table></div>';
    return html;
}

function escapeHtml(text) {
    if (!text) return text;
    return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}

// Allow Enter key to send
userInput.addEventListener('keypress', function (e) {
    if (e.key === 'Enter') sendMessage();
});