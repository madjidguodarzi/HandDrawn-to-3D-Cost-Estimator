// static/plan/plan.js

// --- Initialization & Helpers ---
function getPathParam(param) {
    const pathSegments = window.location.pathname.split('/');
    if (pathSegments[1] === 'project' && pathSegments[2]) return pathSegments[2];
    return null;
}

const projectId = new URLSearchParams(window.location.search).get('id') || getPathParam('id') || 'demo_project';
const API_BASE = ''; 

// State Variables
let originalImage = null;
let detectedLines = []; 
let detectedRooms = []; 
let highlightedLineIndex = -1;
let highlightedRoomIndex = -1; 
let roomColors = [];

// Cost Data Structures
let wallsCosts = []; 
let roomsCosts = []; 

// Drawing State
let currentTool = 'select';
let isDrawing = false;
let startPoint = null;
let currentMousePos = null;
const SNAP_DISTANCE = 15;

const canvas = document.getElementById('previewCanvas');
const ctx = canvas.getContext('2d');

// --- UI Tools ---
document.querySelectorAll('.tool-btn[data-tool]').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.tool-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentTool = btn.getAttribute('data-tool');
        isDrawing = false;
        startPoint = null;
        updatePreview();
    });
});

// --- Image Handling ---
document.getElementById('mapFile').addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (evt) => {
        originalImage = new Image();
        originalImage.onload = () => { resetState(); updatePreview(); };
        originalImage.src = evt.target.result;
    };
    reader.readAsDataURL(file);

    if (!projectId) return;
    setStatus("Uploading...", "loading");
    try {
        const formData = new FormData();
        formData.append("file", file);
        await fetch(`${API_BASE}/api/project/${projectId}/plan`, { method: "POST", body: formData });
        setStatus("✅ Image uploaded.", "success");
    } catch (err) { setStatus("❌ Upload failed.", "error"); }
});

async function loadMapFromServer() {
    setStatus("Fetching map from server...", "loading");
    try {
        const response = await fetch(`${API_BASE}/api/project/${projectId}/plan`, { headers: { 'accept': 'application/json' } });
        if (!response.ok) throw new Error("Image not found");
        const data = await response.json();
        if (data && data.map_image_base64) {
            let src = data.map_image_base64.startsWith('data:') ? data.map_image_base64 : `data:image/png;base64,${data.map_image_base64}`;
            originalImage = new Image();
            originalImage.onload = () => { resetState(); updatePreview(); setStatus("✅ Map loaded.", "success"); };
            originalImage.src = src;
        }
    } catch (err) { setStatus("❌ Failed to load image.", "error"); }
}

function resetState() {
    detectedLines = []; detectedRooms = []; wallsCosts = []; roomsCosts = [];
    roomColors = []; highlightedLineIndex = -1; highlightedRoomIndex = -1;
    renderDebugList();
}

// --- Rendering Logic ---
function getHatchPattern() {
    const pCanvas = document.createElement('canvas');
    pCanvas.width = 10; pCanvas.height = 10;
    const pCtx = pCanvas.getContext('2d');
    pCtx.strokeStyle = '#eab308'; pCtx.lineWidth = 1;
    pCtx.beginPath(); pCtx.moveTo(0, 10); pCtx.lineTo(10, 0); pCtx.stroke();
    return ctx.createPattern(pCanvas, 'repeat');
}

function updatePreview() {
    if (!originalImage) return;
    
    const b = document.getElementById('brightness').value / 100;
    const c = document.getElementById('contrast').value / 100;
    document.getElementById('brightnessVal').textContent = Math.round(b * 100) + '%';
    document.getElementById('contrastVal').textContent = Math.round(c * 100) + '%';

    if (canvas.width !== originalImage.width || canvas.height !== originalImage.height) {
        canvas.width = originalImage.width; canvas.height = originalImage.height;
    }
    
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.filter = `brightness(${b}) contrast(${c})`;
    ctx.drawImage(originalImage, 0, 0);
    ctx.filter = 'none';

    // Draw Rooms
    detectedRooms.forEach((room, i) => {
        if (room.length < 3) return;
        ctx.beginPath();
        ctx.moveTo(room[0][0], room[0][1]);
        for (let j = 1; j < room.length; j++) ctx.lineTo(room[j][0], room[j][1]);
        ctx.closePath();

        if (i === highlightedRoomIndex) {
            ctx.fillStyle = getHatchPattern();
            ctx.fill();
            ctx.strokeStyle = '#fff'; ctx.lineWidth = 3; ctx.stroke();
        } else {
            ctx.fillStyle = roomColors[i] || 'rgba(59, 130, 246, 0.3)';
            ctx.fill();
            ctx.strokeStyle = darkenColor(roomColors[i] || 'rgba(59, 130, 246, 0.3)', 0.4);
            ctx.lineWidth = 1; ctx.stroke();
        }
    });

    // Draw Walls
    detectedLines.forEach((l, i) => {
        const [x1, y1, x2, y2] = l;
        ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2);
        if (i === highlightedLineIndex) { ctx.strokeStyle = '#ffd700'; ctx.lineWidth = 5; } 
        else { ctx.strokeStyle = '#ff0000'; ctx.lineWidth = 2; }
        ctx.lineCap = 'round'; ctx.stroke();
        ctx.fillStyle = '#000'; 
        ctx.beginPath(); ctx.arc(x1, y1, 4, 0, Math.PI*2); ctx.fill();
        ctx.beginPath(); ctx.arc(x2, y2, 4, 0, Math.PI*2); ctx.fill();
    });

    // Drawing Preview
    if (isDrawing && startPoint && currentMousePos) {
        ctx.beginPath(); ctx.lineWidth = 3; ctx.strokeStyle = '#3b82f6'; ctx.setLineDash([6, 4]);
        if (currentTool === 'line') { ctx.moveTo(startPoint.x, startPoint.y); ctx.lineTo(currentMousePos.x, currentMousePos.y); }
        ctx.stroke(); ctx.setLineDash([]);
    }

    // Snap Indicator
    if (currentTool !== 'select' && currentMousePos && currentMousePos.isSnapped) {
        ctx.beginPath(); ctx.arc(currentMousePos.x, currentMousePos.y, 6, 0, Math.PI * 2);
        ctx.fillStyle = '#ef4444'; ctx.fill(); ctx.lineWidth = 2; ctx.strokeStyle = '#fff'; ctx.stroke();
    }
}

// --- Interaction Logic ---
function getSnappedPoint(pos) {
    let snapX = pos.x, snapY = pos.y, minDist = SNAP_DISTANCE, isSnapped = false;
    detectedLines.forEach(l => {
        [{x: l[0], y: l[1]}, {x: l[2], y: l[3]}].forEach(p => {
            let dist = Math.hypot(p.x - pos.x, p.y - pos.y);
            if (dist < minDist) { minDist = dist; snapX = p.x; snapY = p.y; isSnapped = true; }
        });
    });
    return { x: snapX, y: snapY, isSnapped };
}

canvas.addEventListener('click', (e) => {
    if (!originalImage) return;
    const rect = canvas.getBoundingClientRect();
    let pos = { x: e.clientX - rect.left, y: e.clientY - rect.top };
    let snapResult = getSnappedPoint(pos);
    let clickedPos = { x: snapResult.x, y: snapResult.y };

    if (currentTool === 'line') {
        if (!isDrawing) { isDrawing = true; startPoint = clickedPos; } 
        else {
            isDrawing = false;
            detectedLines.push([startPoint.x, startPoint.y, clickedPos.x, clickedPos.y]);
            wallsCosts.push({ left: [], right: [], dbId: null });
            startPoint = null;
            updatePreview(); renderDebugList();
        }
    } else if (currentTool === 'select') {
        let clickedIdx = -1, minDist = 10;
        detectedLines.forEach((l, idx) => {
            if (distToSegment(clickedPos, {x:l[0], y:l[1]}, {x:l[2], y:l[3]}) < minDist) clickedIdx = idx;
        });
        highlightedLineIndex = clickedIdx; highlightedRoomIndex = -1;
        updatePreview(); renderDebugList();
    }
});

canvas.addEventListener('mousemove', (e) => {
    if (!originalImage) return;
    const rect = canvas.getBoundingClientRect();
    currentMousePos = getSnappedPoint({ x: e.clientX - rect.left, y: e.clientY - rect.top });
    if (isDrawing || currentTool !== 'select') updatePreview();
});

window.addEventListener('keydown', (e) => {
    if ((e.key === 'Delete' || e.key === 'Backspace') && highlightedLineIndex !== -1) deleteWall(highlightedLineIndex);
    if ((e.key === 'Delete' || e.key === 'Backspace') && highlightedRoomIndex !== -1) deleteRoom(highlightedRoomIndex);
});

// --- API Functions ---
async function detectWalls() {
    const fileInput = document.getElementById('mapFile');
    if (!fileInput.files.length && !originalImage) return alert("Please select an image first.");
    setStatus("Processing walls...", "loading");
    const formData = new FormData();
    if (fileInput.files.length > 0) formData.append('file', fileInput.files[0]);
    else { await new Promise(resolve => canvas.toBlob(b => { formData.append('file', b, 'map.jpg'); resolve(); }, 'image/jpeg')); }
    formData.append('brightness', document.getElementById('brightness').value / 100);
    formData.append('contrast', document.getElementById('contrast').value / 100);

    try {
        const res = await fetch(`${API_BASE}/api/maps/process/walls`, { method: 'POST', body: formData });
        if (!res.ok) throw new Error("Failed to detect walls");
        const walls = await res.json();
        
        // ✅ تغییر: ذخیره کامل آبجکت دیوار برای استفاده در مراحل بعد
        detectedLines = walls.map(w => [w.x1, w.y1, w.x2, w.y2]);
        
        // ذخیره اطلاعات تکمیلی دیوارها (طول، ارتفاع، مساحت و ...)
        wallsCosts = walls.map((w, i) => ({ 
            left: [], 
            right: [], 
            dbId: null,
            length_m: w.length_m,
            height_m: w.height_m,
            area_m2: w.area_m2,
            notes: w.notes,
            index: w.index
        }));
        
        updatePreview(); renderDebugList();
        setStatus(`✅ Detected ${detectedLines.length} walls.`, "success");
    } catch (e) { setStatus(`❌ ${e.message}`, "error"); }
}

async function saveWalls() {
    if (!projectId || detectedLines.length === 0) return;
    setStatus("Saving walls...", "loading");
    try {
        // ✅ تغییر: ساخت payload دقیق مطابق با Body Request API
        const payload = detectedLines.map((l, i) => {
            const wc = wallsCosts[i] || {};
            return {
                x1: l[0],
                y1: l[1],
                x2: l[2],
                y2: l[3],
                length_m: wc.length_m || 0,
                height_m: wc.height_m || 2.7,
                area_m2: wc.area_m2 || 0,
                notes: wc.notes || "",
                project_id: parseInt(projectId),
                index: i
            };
        });

        const res = await fetch(`${API_BASE}/api/project/${projectId}/walls`, {
            method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload)
        });
        if (!res.ok) throw new Error("Save failed");
        const saved = await res.json();
        
        // ✅ تغییر: به‌روزرسانی wallsCosts با داده‌های برگشتی از سرور (شامل ID جدید)
        wallsCosts = saved.map((w, i) => ({ 
            ...(wallsCosts[i] || {}), 
            dbId: w.id,
            id: w.id,
            project_id: w.project_id,
            created_at: w.created_at
        }));
        
        renderDebugList(); setStatus("✅ Walls saved.", "success");
    } catch (e) { setStatus(`❌ ${e.message}`, "error"); }
}

async function detectRooms() {
    if (detectedLines.length === 0) return alert("No walls.");
    // بررسی اینکه آیا دیوارها دارای ID هستند یا خیر (اختیاری ولی توصیه می‌شود)
    if (wallsCosts.some(w => !w?.dbId)) return setStatus("⚠ Save walls first.", "error");
    
    setStatus("Detecting rooms...", "loading");
    try {
        // ✅ تغییر: ساخت payload دقیق شامل تمام فیلدهای دیوار
        const payload = detectedLines.map((l, i) => {
            const wc = wallsCosts[i] || {};
            return {
                x1: l[0],
                y1: l[1],
                x2: l[2],
                y2: l[3],
                length_m: wc.length_m || 0,
                height_m: wc.height_m || 2.7,
                area_m2: wc.area_m2 || 0,
                notes: wc.notes || "",
                id: wc.dbId,
                project_id: parseInt(projectId),
                index: i
            };
        });

        const res = await fetch(`${API_BASE}/api/maps/process/rooms`, {
            method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)
        });
        if (!res.ok) throw new Error("Detection failed");
        const rooms = await res.json();
        
        // ✅ تغییر: ذخیره مختصات و اطلاعات تکمیلی اتاق
        detectedRooms = rooms.map(r => r.coordinates ? r.coordinates.map(c => [c.x, c.y]) : []);
        roomColors = rooms.map(() => getRandomPastelColor());
        
        roomsCosts = rooms.map((r, i) => ({ 
            costs: [], 
            dbId: null, 
            wall_ids: r.related_objects || [], // فرض بر این است که related_objects حاوی ID دیوارهاست یا باید از منطق بک‌اند استخراج شود
            name: r.name,
            floor_area_m2: r.floor_area_m2,
            wall_area_m2: r.wall_area_m2,
            perimeter_m: r.perimeter_m,
            notes: r.notes,
            index: r.index
        }));
        
        updatePreview(); renderDebugList();
        setStatus(`✅ ${rooms.length} rooms found.`, "success");
    } catch (e) { setStatus(`❌ ${e.message}`, "error"); }
}

async function saveRooms() {
    if (!projectId || detectedRooms.length === 0) return;
    setStatus("Saving rooms...", "loading");
    try {
        // ✅ تغییر: ساخت payload دقیق مطابق با Body Request API برای Rooms
        const payload = detectedRooms.map((r, i) => {
            const rc = roomsCosts[i] || {};
            return {
                name: rc.name || "Room",
                floor_area_m2: rc.floor_area_m2 || 0,
                wall_area_m2: rc.wall_area_m2 || 0,
                perimeter_m: rc.perimeter_m || 0,
                notes: rc.notes || "",
                project_id: parseInt(projectId),
                index: i,
                coordinates: r.map(pt => ({ x: pt[0], y: pt[1] })),
                related_objects: rc.wall_ids || []
            };
        });

        const res = await fetch(`${API_BASE}/api/project/${projectId}/rooms`, {
            method: "POST", 
            headers: { "Content-Type": "application/json" }, 
            body: JSON.stringify(payload)
        });

        if (!res.ok) throw new Error("Save failed");
        
        const saved = await res.json();
        
        // ✅ بروزرسانی dbIdها و اطلاعات پس از ذخیره موفق
        roomsCosts = saved.map((r, i) => ({ 
            ...(roomsCosts[i] || {}), 
            dbId: r.id,
            id: r.id,
            project_id: r.project_id,
            created_at: r.created_at
        }));

        renderDebugList(); 
        setStatus("✅ Rooms saved.", "success");
    } catch (e) { 
        setStatus(`❌ ${e.message}`, "error"); 
    }
}

// --- Debug List & Selection ---
function renderDebugList() {
    const wList = document.getElementById('wallsList');
    const rList = document.getElementById('roomsList');

    if (wList) {
        wList.innerHTML = 
        // `<div style="padding:8px; border-bottom:1px solid #333; display:flex; justify-content:space-between;">
        //     <span style="color:#4ec9b0">Walls</span>
        //     <button onclick="saveWalls()" style="color:#28a745; background:none; border:1px solid #28a745; border-radius:4px; cursor:pointer;">Save</button>
        // </div>` + 
        detectedLines.map((l, i) => `
            <div class="item-row ${i===highlightedLineIndex?'active':''}" onclick="highlightWall(${i})" style="padding:5px; display:flex; justify-content:space-between; cursor:pointer;">
                <span>${wallsCosts[i]?.dbId?'✅':'⭕'} Wall #${i+1}</span>
                <button onclick="event.stopPropagation(); deleteWall(${i})" style="background:none; border:none; color:red;">✕</button>
            </div>
        `).join('');
    }

    if (rList) {
        rList.innerHTML = 
        // `<div style="padding:8px; border-bottom:1px solid #333; display:flex; justify-content:space-between; margin-top:10px;">
        //     <span style="color:#4ec9b0">Rooms</span>
        //     <button onclick="saveRooms()" style="color:#28a745; background:none; border:1px solid #28a745; border-radius:4px; cursor:pointer;">Save</button>
        // </div>` + 
        detectedRooms.map((r, i) => `
            <div class="item-row ${i===highlightedRoomIndex?'active':''}" onclick="highlightRoom(${i})" style="padding:5px; display:flex; justify-content:space-between; align-items:center; cursor:pointer;">
                <div style="display:flex; align-items:center; gap:5px;">
                    <span style="width:10px; height:10px; background:${roomColors[i]}; border-radius:50%;"></span>
                    <span>${roomsCosts[i]?.dbId?'✅':'⭕'} Room #${i+1}</span>
                </div>
                <div>
                    <button onclick="event.stopPropagation(); showRoomInfo(${i})" style="background:none; border:none; color:#60a5fa; cursor:pointer; margin-right:5px;"><i class="fa-solid fa-gear"></i></button>
                    <button onclick="event.stopPropagation(); deleteRoom(${i})" style="background:none; border:none; color:red;">✕</button>
                </div>
            </div>
        `).join('');
    }
}

function highlightWall(i) { highlightedLineIndex = i; highlightedRoomIndex = -1; updatePreview(); renderDebugList(); }
function highlightRoom(i) { highlightedRoomIndex = i; highlightedLineIndex = -1; updatePreview(); renderDebugList(); }
function deleteWall(i) { detectedLines.splice(i,1); wallsCosts.splice(i,1); detectedRooms=[]; roomsCosts=[]; highlightedLineIndex=-1; updatePreview(); renderDebugList(); }
function deleteRoom(i) { detectedRooms.splice(i,1); roomsCosts.splice(i,1); highlightedRoomIndex=-1; updatePreview(); renderDebugList(); }

// --- Room Info Modal (Updated for New Design) ---
async function showRoomInfo(roomIndex) {
    highlightedRoomIndex = roomIndex;
    updatePreview();
    
    const roomData = roomsCosts[roomIndex];
    if (!roomData?.dbId) return setStatus("⚠ Save room first.", "error");

    const modal = document.getElementById('roomModal');
    modal.style.display = 'flex'; // Use flex for centering
    
    // Set initial values in inputs
    const typeSelect = document.getElementById('modalRoomType');
    const areaInput = document.getElementById('modalRoomArea');
    const perimInput = document.getElementById('modalRoomPerimeter');
    
    // Calculate area/perim locally for immediate display
    const coords = detectedRooms[roomIndex];
    const area = calculatePolygonArea(coords) / 10000; // Assuming pixels to m2 conversion needed or just raw
    // Note: Real area comes from backend, but we can show placeholder
    
    areaInput.value = area;
    perimInput.value = "Loading...";
    
    await refreshRoomPopup(roomIndex);
}

async function refreshRoomPopup(roomIndex) {
    const roomData = roomsCosts[roomIndex];
    if (!roomData?.dbId) return;
    
    try {
        const res = await fetch(`${API_BASE}/api/project/${projectId}/rooms/${roomData.dbId}`);
        if (!res.ok) throw new Error("Load failed");
        const room = await res.json();

        // Update Inputs
        const typeSelect = document.getElementById('modalRoomType');
        if (typeSelect) typeSelect.value = room.name || "Other";
        
        document.getElementById('modalRoomArea').value = room.floor_area_m2 ? room.floor_area_m2.toFixed(2) + ' m²' : '—';
        document.getElementById('modalRoomPerimeter').value = room.perimeter_m ? room.perimeter_m.toFixed(2) + ' m' : '—';

        // Update Related Objects List
        const container = document.getElementById('modalRelatedObjects');
        const related = room.related_objects || [];
        
        if (related.length === 0) {
            container.innerHTML = `<div style="color:#64748b; text-align:center; padding:10px;">No objects yet</div>`;
        } else {
            container.innerHTML = related.map(obj => `
                <div onclick="window.open('/project/${projectId}/objects/${obj.relation_id}/cost', '_blank')" 
                     style="display:flex; justify-content:space-between; align-items:center; padding:8px; background:#1e293b; margin-bottom:4px; border-radius:4px; cursor:pointer; border:1px solid #334155;">
                    <span style="color:#e2e8f0; font-size:0.9rem;"><i class="fa-solid fa-box" style="margin-right:6px; color:#3b82f6;"></i> ${obj.object_type}</span>
                    <span style="font-size:0.75rem; color:#38bdf8;">View Cost <i class="fa-solid fa-arrow-up-right-from-square"></i></span>
                </div>
            `).join('');
        }
    } catch (e) { console.error(e); }
}

async function updateRoomTypeOnServer() {
    const modal = document.getElementById('roomModal');
    const roomIndex = highlightedRoomIndex;
    if (roomIndex === -1) return;
    
    const roomData = roomsCosts[roomIndex];
    if (!roomData?.dbId) return;

    const typeSelect = document.getElementById('modalRoomType');
    const typeName = typeSelect.value;

    setStatus(`Updating costs for ${typeName}...`, "loading");
    try {
        const res = await fetch(`${API_BASE}/api/project/${projectId}/rooms/${roomData.dbId}/suggest-costs`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ room_type: typeName })
        });
        if (!res.ok) throw new Error("Update failed");
        setStatus("✅ Costs updated.", "success");
        await refreshRoomPopup(roomIndex);
    } catch (e) { setStatus(`❌ ${e.message}`, "error"); }
}

function closeRoomModal() { 
    document.getElementById('roomModal').style.display = 'none'; 
    highlightedRoomIndex = -1;
    updatePreview();
}

function saveRoomProperties() {
    updateRoomTypeOnServer();
    closeRoomModal();
}

// --- Export & Utilities ---
async function exportSh3d(e) {
    e.preventDefault();
    if (detectedLines.length === 0) return alert("No walls to export");
    
    setStatus("Generating .sh3d...", "loading");
    try {
        // ✅ Construct full WallRead objects from local state
        const wallsPayload = detectedLines.map((l, i) => {
            const wc = wallsCosts[i] || {};
            return {
                x1: l[0],
                y1: l[1],
                x2: l[2],
                y2: l[3],
                length_m: wc.length_m || 0,
                height_m: wc.height_m || 2.7,
                area_m2: wc.area_m2 || 0,
                notes: wc.notes || "",
                id: wc.dbId || null, // Include ID if saved
                project_id: parseInt(projectId),
                index: i
            };
        });

        // ✅ Construct full RoomRead objects from local state
        const roomsPayload = detectedRooms.map((r, i) => {
            const rc = roomsCosts[i] || {};
            return {
                id: rc.dbId || null,
                project_id: parseInt(projectId),
                index: i,
                name: rc.name || "Room",
                floor_area_m2: rc.floor_area_m2 || 0,
                wall_area_m2: rc.wall_area_m2 || 0,
                perimeter_m: rc.perimeter_m || 0,
                coordinates: r.map(pt => ({ x: pt[0], y: pt[1] })),
                related_objects: rc.wall_ids || [] 
            };
        });

        const res = await fetch(`${API_BASE}/api/maps/export/sh3d`, {
            method: 'POST', 
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ 
                walls: wallsPayload, 
                rooms: roomsPayload 
            })
        });

        if (!res.ok) throw new Error("Export failed");
        
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a'); 
        a.href = url; 
        a.download = `project_${projectId}.sh3d`;
        document.body.appendChild(a); 
        a.click(); 
        window.URL.revokeObjectURL(url);
        
        setStatus("✅ Download started.", "success");
    } catch (e) { 
        console.error(e);
        setStatus("❌ Export failed.", "error"); 
    }
}

function setStatus(msg, type) {
    const el = document.getElementById('status');
    if(el) { el.textContent = msg; el.style.color = type === 'error' ? '#ef4444' : (type === 'success' ? '#10b981' : '#3b82f6'); }
}
function getRandomPastelColor() { return `hsla(${Math.floor(Math.random() * 360)}, 70%, 70%, 0.3)`; }
function darkenColor(hslaStr, amount) { return hslaStr.replace('0.3', '1').replace('70%', '40%'); }
function distToSegment(p, p1, p2) {
    let l2 = (p2.x - p1.x)**2 + (p2.y - p1.y)**2;
    if (l2 === 0) return Math.hypot(p.x - p1.x, p.y - p1.y);
    let t = ((p.x - p1.x)*(p2.x - p1.x) + (p.y - p1.y)*(p2.y - p1.y)) / l2;
    t = Math.max(0, Math.min(1, t));
    return Math.hypot(p.x - (p1.x + t*(p2.x - p1.x)), p.y - (p1.y + t*(p2.y - p1.y)));
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

// --- Load on Start ---
document.addEventListener('DOMContentLoaded', loadProjectData);
async function loadProjectData() {
    if (!projectId) return;
    try {
        const [pRes, wRes, rRes] = await Promise.all([
            fetch(`${API_BASE}/api/project/${projectId}/plan`),
            fetch(`${API_BASE}/api/project/${projectId}/walls`),
            fetch(`${API_BASE}/api/project/${projectId}/rooms`)
        ]);
        
        if (pRes.ok) {
            const d = await pRes.json();
            if (d.map_image_base64) {
                originalImage = new Image();
                let src = d.map_image_base64.startsWith('data:') ? d.map_image_base64 : `data:image/png;base64,${d.map_image_base64}`;
                originalImage.src = src;
                originalImage.onload = () => updatePreview();
            }
        }
        if (wRes.ok) {
            const w = await wRes.json();
            detectedLines = w.map(x => [x.x1, x.y1, x.x2, x.y2]);
            wallsCosts = w.map(x => ({ left:[], right:[], dbId: x.id }));
        }
        if (rRes.ok) {
            const r = await rRes.json();
            detectedRooms = r.map(x => x.coordinates.map(c => [c.x, c.y]));
            roomColors = r.map(() => getRandomPastelColor());
            roomsCosts = r.map(x => ({ costs:[], dbId: x.id, wall_ids: x.wall_ids||[] }));
        }
        renderDebugList();
    } catch(e) { console.error(e); }
}