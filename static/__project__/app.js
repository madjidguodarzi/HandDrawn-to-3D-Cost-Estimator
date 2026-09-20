const urlParams = new URLSearchParams(window.location.search);
const currentProjectId = urlParams.get('project_id');

// اگر ID پروژه وجود نداشت، کاربر را به صفحه اصلی برمی‌گردانیم
if (!currentProjectId) {
    alert("No project selected! Redirecting to project manager.");
    // window.location.href = "/"; 
}

const canvas = document.getElementById('previewCanvas');
const ctx = canvas.getContext('2d');
const wrapper = document.getElementById('canvasWrapper');
const placeholder = document.getElementById('placeholder');
const statusDiv = document.getElementById('status');
const debugContent = document.getElementById('debugContent');
const wallCountBadge = document.getElementById('wallCountBadge');
const downloadLink = document.getElementById('download-link');
const detectWallBtn = document.getElementById('detectWallBtn');
const detectRoomBtn = document.getElementById('detectRoomBtn');
const fileInput = document.getElementById('mapFile');

const brightnessSlider = document.getElementById('brightness');
const contrastSlider = document.getElementById('contrast');
const brightnessVal = document.getElementById('brightnessVal');
const contrastVal = document.getElementById('contrastVal');

let originalImage = null;
let detectedLines = []; // Walls: [[x1,y1,x2,y2], ...]
let detectedRooms = []; // Rooms: [[[x,y], [x,y]...], ...]
let highlightedLineIndex = -1;
let highlightedRoomIndex = -1;
let roomColors = []; 

// --- COST DATA MANAGEMENT ---
// نگهداری هزینه‌ها به صورت جداگانه برای هر دیوار و اتاق
// ساختار: wallsCosts[i] = آرایه‌ای از آیتم‌های هزینه
let wallsCosts = []; 
let roomsCosts = [];

// Load Image Preview
fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
        originalImage = new Image();
        originalImage.onload = () => {
            resetState();
            updatePreview();
        };
        originalImage.src = event.target.result;
    };
    reader.readAsDataURL(file);
});

function resetState() {
    detectedLines = [];
    detectedRooms = [];
    wallsCosts = [];
    roomsCosts = [];
    roomColors = [];
    highlightedLineIndex = -1;
    highlightedRoomIndex = -1;
    statusDiv.textContent = '';
    statusDiv.className = '';
    downloadLink.style.display = 'none';
    detectRoomBtn.disabled = true;
    clearDebug();
}

function updatePreview() {
    if (!originalImage) return;
    
    brightnessVal.textContent = brightnessSlider.value + '%';
    contrastVal.textContent = contrastSlider.value + '%';

    canvas.width = originalImage.width;
    canvas.height = originalImage.height;
    
    const b = brightnessSlider.value / 100;
    const c = contrastSlider.value / 100;
    ctx.filter = `brightness(${b}) contrast(${c})`;
    ctx.drawImage(originalImage, 0, 0);
    ctx.filter = 'none';
    
    wrapper.classList.add('has-image');
    placeholder.style.display = 'none';

    drawAll();
}

function drawAll() {
    // Redraw base image
    const b = brightnessSlider.value / 100;
    const c = contrastSlider.value / 100;
    ctx.filter = `brightness(${b}) contrast(${c})`;
    ctx.drawImage(originalImage, 0, 0);
    ctx.filter = 'none';

    // 1. Draw Rooms
    if (detectedRooms.length > 0) {
        for (let i = 0; i < detectedRooms.length; i++) {
            const room = detectedRooms[i];
            if (room.length < 3) continue;
            const isActive = (i === highlightedRoomIndex);
            
            ctx.beginPath();
            ctx.moveTo(room[0][0], room[0][1]);
            for (let j = 1; j < room.length; j++) ctx.lineTo(room[j][0], room[j][1]);
            ctx.closePath();

            if (isActive) {
                ctx.fillStyle = roomColors[i].replace('0.3', '0.5');
                ctx.fill();
                ctx.save();
                ctx.clip();
                ctx.fillStyle = createHatchPattern('#ffffff', 1.5, 8);
                ctx.fill();
                ctx.restore();
                ctx.strokeStyle = '#ffffff';
                ctx.lineWidth = 3;
                ctx.stroke();
            } else {
                ctx.fillStyle = roomColors[i];
                ctx.fill();
                ctx.strokeStyle = darkenColor(roomColors[i], 0.4);
                ctx.lineWidth = 1;
                ctx.stroke();
            }
        }
    }

    // 2. Draw Walls
    for (let i = 0; i < detectedLines.length; i++) {
        const [x1, y1, x2, y2] = detectedLines[i];
        if (i === highlightedLineIndex) {
            ctx.strokeStyle = '#ffd700';
            ctx.lineWidth = 4;
        } else {
            ctx.strokeStyle = '#ff0000';
            ctx.lineWidth = 2;
        }
        ctx.lineCap = 'round';
        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
        ctx.stroke();
    }
}

async function detectWalls() {
    if (!fileInput.files.length) { alert("Please select an image first."); return; }

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('brightness', brightnessSlider.value / 100);
    formData.append('contrast', contrastSlider.value / 100);

    setStatus("Processing... Detecting walls...", "loading");
    detectWallBtn.disabled = true;
    detectedRooms = []; 
    roomColors = [];
    wallsCosts = []; // Reset costs when structure changes

    try {
        // استفاده از اندپوینت جدید پردازش نقشه
        const response = await fetch(`http://127.0.0.1:8000/api/projects/${currentProjectId}/map/process`, { 
            method: 'POST', 
            body: formData 
        });
        
        if (!response.ok) throw new Error("Failed to detect walls");
        const data = await response.json();
        
        // در این نسخه، بک‌اند دیوارها را در دیتابیس ذخیره می‌کند اما ما برای نمایش نیاز به مختصات داریم
        // فرض می‌کنیم بک‌اند لیست خطوط را برنمی‌گرداند مگر اینکه در سرویس تغییر دهیم.
        // برای سادگی، فعلاً از همان لاجیک قبلی برای نمایش استفاده می‌کنیم اما در Save نهایی به بک‌اند می‌فرستیم.
        // نکته: در کد پایتون جدید، process_map فقط پیام موفقیت برمی‌گرداند.
        // برای نمایش زنده، بهتر است از endpoint قدیمی detect-walls استفاده کنیم یا خروجی را اصلاح کنیم.
        // اینجا فرض می‌کنیم شما می‌خواهید فقط نمایش دهید و در نهایت Save کنید.
        
        // *راه حل موقت برای نمایش:* از اندپوینت عمومی detect-walls استفاده می‌کنیم تا مختصات بگیریم
        const detectResp = await fetch('http://127.0.0.1:8000/detect-walls', {
             method: 'POST', body: formData
        });
        const detectData = await detectResp.json();
        detectedLines = detectData.lines || [];
        
        // Initialize empty cost arrays for each wall
        wallsCosts = new Array(detectedLines.length).fill([]).map(() => []);

        updatePreview();
        renderDebugList();
        
        if (detectedLines.length > 0) {
            setStatus(`✅ Detected ${detectedLines.length} walls.`, "success");
            detectRoomBtn.disabled = false;
        } else {
            setStatus("⚠ No walls detected.", "error");
        }

    } catch (error) {
        setStatus("❌ Error: " + error.message, "error");
    } finally {
        detectWallBtn.disabled = false;
    }
}

async function detectRooms() {
    if (detectedLines.length === 0) return;
    setStatus("Calculating rooms...", "loading");
    
    try {
        const response = await fetch('http://127.0.0.1:8000/detect-rooms', { 
            method: 'POST', 
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(detectedLines) 
        });
        
        if (!response.ok) throw new Error("Failed to detect rooms");
        const data = await response.json();
        detectedRooms = data.rooms || [];
        roomColors = detectedRooms.map(() => getRandomPastelColor());
        roomsCosts = new Array(detectedRooms.length).fill([]).map(() => []);
        
        updatePreview(); 
        renderDebugList(); 
        setStatus(`✅ Found ${detectedRooms.length} rooms.`, "success");
        if (detectedRooms.length > 0) downloadLink.style.display = 'inline-block';

    } catch (error) {
        setStatus("❌ Error: " + error.message, "error");
    }
}

// --- NEW SAVE LOGIC ---
async function saveProjectToDB() {
    if (!currentProjectId) return;

    // ساختار داده مطابق با Schema بک‌اند جدید
    const payload = {
        walls: detectedLines.map((line, index) => ({
            index: index,
            x1: line[0], y1: line[1], x2: line[2], y2: line[3],
            costs: wallsCosts[index] || [] // ارسال هزینه‌های متصل به این دیوار
        })),
        rooms: detectedRooms.map((room, index) => ({
            index: index,
            floor_area_m2: calculatePolygonArea(room) / 10000,
            costs: roomsCosts[index] || [] // ارسال هزینه‌های متصل به این اتاق
        }))
    };

    try {
        setStatus("Saving all data to database...", "loading");
        // استفاده از اندپوینت جدید PUT /projects/{id}/data
        const response = await fetch(`http://127.0.0.1:8000/api/projects/${currentProjectId}/data`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (response.ok) {
            setStatus("✅ Project saved successfully!", "success");
        } else {
            const err = await response.json();
            setStatus("❌ Failed: " + err.detail, "error");
        }
    } catch (error) {
        console.error(error);
        setStatus("❌ Network error.", "error");
    }
}

function deleteWall(index) {
    detectedLines.splice(index, 1);
    wallsCosts.splice(index, 1); // حذف هزینه‌های مربوطه
    highlightedLineIndex = -1;
    detectedRooms = []; 
    roomsCosts = [];
    roomColors = [];
    updatePreview();
    renderDebugList();
    setStatus("Wall deleted. Please detect rooms again.", "loading");
    detectRoomBtn.disabled = false;
    downloadLink.style.display = 'none';
}

function deleteRoom(index) {
    detectedRooms.splice(index, 1);
    roomsCosts.splice(index, 1);
    roomColors.splice(index, 1);
    highlightedRoomIndex = -1;
    updatePreview();
    renderDebugList();
}

function openWallCostPage(wallIndex) {
    // باز کردن مودال یا صفحه جدید برای ویرایش هزینه‌ها
    // برای سادگی، اینجا فقط یک آرایه نمونه اضافه می‌کنیم تا تست شود
    // در نسخه واقعی باید یک مودال باز شود
    const defaultCost = {
        item_name: "New Wall Item",
        quantity: 10,
        unit: "m2",
        unit_price: 50,
        duration_days: 1,
        start_date: "",
        predecessor_id: null
    };
    
    if (!wallsCosts[wallIndex]) wallsCosts[wallIndex] = [];
    wallsCosts[wallIndex].push(defaultCost);
    
    alert(`Added a sample cost item to Wall #${wallIndex + 1}. Click Save Project to store it.`);
    renderDebugList(); // برای نمایش تعداد هزینه‌ها
}

function openRoomCostPage(roomIndex) {
    const defaultCost = {
        item_name: "New Room Item",
        quantity: 5,
        unit: "piece",
        unit_price: 100,
        duration_days: 2,
        start_date: "",
        predecessor_id: null
    };

    if (!roomsCosts[roomIndex]) roomsCosts[roomIndex] = [];
    roomsCosts[roomIndex].push(defaultCost);
    
    alert(`Added a sample cost item to Room #${roomIndex + 1}. Click Save Project to store it.`);
    renderDebugList();
}

function renderDebugList() {
    wallCountBadge.textContent = `${detectedLines.length} walls`;
    let html = '';

    // WALLS
    html += `<div class="debug-section-title">WALLS (${detectedLines.length})</div>`;
    if (detectedLines.length === 0) {
        html += '<div class="debug-empty">No walls.</div>';
    } else {
        detectedLines.forEach((l, i) => {
            const activeClass = (i === highlightedLineIndex) ? 'active' : '';
            const costCount = (wallsCosts[i] || []).length;
            html += `<div class="debug-line-item ${activeClass}" onclick="highlightWall(${i})">
                <div>#${i+1} <span style="font-size:0.7em; color:#888">($${costCount} items)</span></div>
                <div style="display:flex; gap:3px;">
                    <button class="wall-cost-btn" onclick="event.stopPropagation(); openWallCostPage(${i})" title="Add Cost">
                        <i class="fa-solid fa-coins"></i>
                    </button>
                    <button class="delete-btn" onclick="event.stopPropagation(); deleteWall(${i})">✕</button>
                </div>
            </div>`;
        });
    }

    // ROOMS
    html += `<div class="debug-section-title">ROOMS (${detectedRooms.length})</div>`;
    if (detectedRooms.length === 0) {
        html += '<div class="debug-empty">No rooms.</div>';
    } else {
        detectedRooms.forEach((r, i) => {
            const activeClass = (i === highlightedRoomIndex) ? 'active' : '';
            const costCount = (roomsCosts[i] || []).length;
            html += `<div class="debug-room-item ${activeClass}" onclick="highlightRoom(${i})">
                <div style="display:flex; align-items:center; flex-grow:1;">
                    <span class="color-indicator" style="background-color: ${roomColors[i]}"></span>
                    Room #${i+1} <span style="font-size:0.7em; color:#888">($${costCount} items)</span>
                </div>
                <div style="display:flex; gap:5px;">
                    <button class="cost-btn" onclick="event.stopPropagation(); openRoomCostPage(${i})" title="Add Cost">
                        <i class="fa-solid fa-coins"></i>
                    </button>
                    <button class="delete-btn" onclick="event.stopPropagation(); deleteRoom(${i})">✕</button>
                </div>
            </div>`;
        });
    }
    debugContent.innerHTML = html;
}

function highlightWall(index) {
    highlightedLineIndex = index;
    highlightedRoomIndex = -1;
    drawAll();
    renderDebugList();
}

function highlightRoom(index) {
    highlightedRoomIndex = index;
    highlightedLineIndex = -1;
    drawAll();
    renderDebugList();
}

function clearDrawingsOnly() {
    resetState();
    if (originalImage) updatePreview();
}

function setStatus(msg, type) {
    statusDiv.textContent = msg;
    statusDiv.className = type;
}

function calculatePolygonArea(points) {
    let area = 0;
    for (let i = 0; i < points.length; i++) {
        let j = (i + 1) % points.length;
        area += points[i][0] * points[j][1];
        area -= points[j][0] * points[i][1];
    }
    return Math.abs(area / 2);
}

function getRandomPastelColor() {
    const hue = Math.floor(Math.random() * 360);
    return `hsla(${hue}, 70%, 70%, 0.3)`;
}

function darkenColor(hslaStr, amount) {
    const match = hslaStr.match(/hsla\((\d+),\s*(\d+)%,\s*(\d+)%,\s*([\d.]+)\)/);
    if (match) {
        let l = Math.max(0, parseInt(match[3]) - 30);
        return `hsla(${match[1]}, ${match[2]}%, ${l}%, 1)`;
    }
    return '#333';
}

function createHatchPattern(color, lineWidth, spacing) {
    const pCanvas = document.createElement('canvas');
    const pCtx = pCanvas.getContext('2d');
    pCanvas.width = spacing;
    pCanvas.height = spacing;
    pCtx.beginPath();
    pCtx.moveTo(0, spacing);
    pCtx.lineTo(spacing, 0);
    pCtx.strokeStyle = color;
    pCtx.lineWidth = lineWidth;
    pCtx.stroke();
    return ctx.createPattern(pCanvas, 'repeat');
}

async function downloadSh3d(event) {
    event.preventDefault();
    if (detectedLines.length === 0 || detectedRooms.length === 0) {
        setStatus("⚠ Please detect walls and rooms first.", "error");
        return;
    }
    setStatus("Converting...", "loading");
    try {
        const response = await fetch('http://127.0.0.1:8000/convert-to-sh3d', { 
            method: 'POST', 
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ walls: detectedLines, rooms: detectedRooms }) 
        });
        if (!response.ok) throw new Error("Conversion failed");
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'floor_plan.sh3d';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        setStatus("✅ Downloaded!", "success");
    } catch (error) {
        setStatus("❌ Error: " + error.message, "error");
    }
}