// static/plan/plan.js

// در ابتدای plan.js
function getPathParam(param) {
    const pathSegments = window.location.pathname.split('/');
    // فرض بر ساختار /project/{id}
    if (pathSegments[1] === 'project' && pathSegments[2]) {
        return pathSegments[2];
    }
    return null;
}

// جایگزینی یا ترکیب با getQueryParam
const projectId = getQueryParam('id') || getPathParam('id');

if (!projectId) window.location.href = '/static/index.html';

// State Variables
let originalImage = null;
let detectedLines = []; // Walls: [[x1,y1,x2,y2], ...]
let detectedRooms = []; // Rooms: [[[x,y],...], ...]
let highlightedLineIndex = -1;
let highlightedRoomIndex = -1;
let roomColors = [];

// Cost Data Structures
// wallsCosts[i] = { left: [...items], right: [...items] }
let wallsCosts = []; 
let roomsCosts = []; // roomsCosts[i] = [...items]

const canvas = document.getElementById('previewCanvas');
const ctx = canvas.getContext('2d');

// --- Image Handling ---
// --- Image Handling ---
document.getElementById('mapFile').addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // ۱. نمایش فوری تصویر در کانواس (بدون معطلی برای آپلود)
    const reader = new FileReader();
    reader.onload = (evt) => {
        originalImage = new Image();
        originalImage.onload = () => {
            resetState();
            updatePreview();
        };
        originalImage.src = evt.target.result;
    };
    reader.readAsDataURL(file);

    // ۲. آپلود همزمان به سرور
    if (!projectId) {
        console.warn("No projectId found. Cannot upload plan.");
        return;
    }

    setStatus("Uploading plan image...", "loading");
    try {
        const formData = new FormData();
        formData.append("file", file);

        const res = await fetch(`${API_BASE}/project/${projectId}/plan`, {
            method: "POST",
            body: formData,
            // ❌ Content-Type را ست نکنید! 
            // مرورگر خودش boundary صحیح multipart/form-data را اضافه می‌کند
        });

        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || `Upload failed (${res.status})`);
        }

        const data = await res.json();
        console.log("✅ Plan uploaded:", data.map_image_base64?.substring(0, 30) + "...");
        setStatus("✅ Plan image saved.", "success");
    } catch (error) {
        console.error("Plan upload error:", error);
        setStatus(`❌ Upload failed: ${error.message}`, "error");
    }
});

function resetState() {
    detectedLines = [];
    detectedRooms = [];
    wallsCosts = [];
    roomsCosts = [];
    roomColors = [];
    highlightedLineIndex = -1;
    highlightedRoomIndex = -1;
    // document.getElementById('detectRoomBtn').disabled = true;
    document.getElementById('downloadLink').style.display = 'none';
    renderDebugList();
}

function updatePreview() {
    if (!originalImage) return;
    
    const b = document.getElementById('brightness').value / 100;
    const c = document.getElementById('contrast').value / 100;
    
    document.getElementById('brightnessVal').textContent = Math.round(b * 100) + '%';
    document.getElementById('contrastVal').textContent = Math.round(c * 100) + '%';

    if (canvas.width !== originalImage.width || canvas.height !== originalImage.height) {
        canvas.width = originalImage.width;
        canvas.height = originalImage.height;
    }
    
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.filter = `brightness(${b}) contrast(${c})`;
    ctx.drawImage(originalImage, 0, 0);
    ctx.filter = 'none';
    
    drawOverlays();
}

function drawOverlays() {
    // 1. پاک کردن کامل کانواس و رسم مجدد تصویر پایه (حذف اثرات انتخاب قبلی)
    if (!originalImage) return;
    
    const b = document.getElementById('brightness').value / 100;
    const c = document.getElementById('contrast').value / 100;
    
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.filter = `brightness(${b}) contrast(${c})`;
    ctx.drawImage(originalImage, 0, 0);
    ctx.filter = 'none';

    // 2. رسم اتاق‌ها (لایه زیرین)
    if (detectedRooms.length > 0) {
        for (let i = 0; i < detectedRooms.length; i++) {
            const room = detectedRooms[i];
            if (room.length < 3) continue;
            
            ctx.beginPath();
            ctx.moveTo(room[0][0], room[0][1]);
            for (let j = 1; j < room.length; j++) ctx.lineTo(room[j][0], room[j][1]);
            ctx.closePath();

            if (i === highlightedRoomIndex) {
                // حالت انتخاب شده: رنگ پررنگ‌تر + هاشور سفید
                ctx.fillStyle = roomColors[i].replace('0.3', '0.6');
                ctx.fill();
                
                ctx.save();
                ctx.clip();
                ctx.strokeStyle = 'rgba(255,255,255,0.6)';
                ctx.lineWidth = 2;
                // رسم هاشور مورب
                for(let k=-canvas.width; k<canvas.width*2; k+=20) {
                    ctx.beginPath(); 
                    ctx.moveTo(k, 0); 
                    ctx.lineTo(k - canvas.height, canvas.height); 
                    ctx.stroke();
                }
                ctx.restore();
                
                // حاشیه سفید ضخیم برای اتاق انتخاب شده
                ctx.strokeStyle = '#fff';
                ctx.lineWidth = 3;
                ctx.stroke();
            } else {
                // حالت عادی
                ctx.fillStyle = roomColors[i];
                ctx.fill();
                ctx.strokeStyle = darkenColor(roomColors[i], 0.4);
                ctx.lineWidth = 1;
                ctx.stroke();
            }
        }
    }

    // 3. رسم دیوارها (لایه رویی)
    for (let i = 0; i < detectedLines.length; i++) {
        const [x1, y1, x2, y2] = detectedLines[i];
        
        // رسم خط دیوار
        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
        
        if (i === highlightedLineIndex) {
            ctx.strokeStyle = '#ffd700'; // طلایی برای دیوار انتخاب شده
            ctx.lineWidth = 5;
        } else {
            ctx.strokeStyle = '#ff0000'; // قرمز برای دیوارهای عادی
            ctx.lineWidth = 2;
        }
        ctx.lineCap = 'round';
        ctx.stroke();

        // 4. رسم نقاط ابتدا و انتها (همیشه مشکی)
        // نکته مهم: این بخش خارج از شرط if (i === highlightedLineIndex) قرار دارد
        // تا رنگ نقاط همیشه مشکی باقی بماند و زرد نشود.
        ctx.fillStyle = '#000000'; 
        ctx.beginPath(); ctx.arc(x1, y1, 4, 0, Math.PI*2); ctx.fill();
        ctx.beginPath(); ctx.arc(x2, y2, 4, 0, Math.PI*2); ctx.fill();
    }
}

// --- API Calls ---
async function detectWalls() {
    const fileInput = document.getElementById('mapFile');
    if (!fileInput.files.length) return alert("Please select an image first.");

    setStatus("Processing walls...", "loading");
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('brightness', document.getElementById('brightness').value / 100);
    formData.append('contrast', document.getElementById('contrast').value / 100);

    try {
        const res = await fetch(`${API_BASE}/maps/process/walls`, { method: 'POST', body: formData });
        if (!res.ok) throw new Error("Failed to detect walls");
        
        // ✅ خروجی اکنون مستقیماً List[WallRead] است (نه {lines: [...]})
        const walls = await res.json();
        
        // تبدیل WallRead به فرمت داخلی کانواس [x1, y1, x2, y2]
        detectedLines = walls.map(w => [w.x1, w.y1, w.x2, w.y2]);
        
        // Initialize costs for each wall with left/right sides
        wallsCosts = walls.map(() => ({ left: [], right: [] }));
        
        updatePreview();
        renderDebugList();
        
        if (detectedLines.length > 0) {
            setStatus(`✅ Detected ${detectedLines.length} walls.`, "success");
            // document.getElementById('detectRoomBtn').disabled = false;
        } else {
            setStatus("⚠ No walls detected.", "error");
        }
    } catch (e) {
        console.error(e);
        setStatus("❌ Error detecting walls.", "error");
    }
}

async function detectRooms() {
    if (detectedLines.length === 0) return;
    
    // ✅ قبل از ارسال، دیوارها باید ذخیره شده باشند (دارای dbId)
    const unsavedWalls = wallsCosts.filter(w => !w?.dbId);
    if (unsavedWalls.length > 0) {
        setStatus("⚠ Please save walls first before detecting rooms.", "error");
        return;
    }
    
    setStatus("Calculating rooms...", "loading");
    
    try {
        // ✅ ورودی اکنون List[WallRead] است — باید دیوارهای ذخیره‌شده را بفرستیم
        const wallsForDetection = wallsCosts.map((wc, i) => {
            const line = detectedLines[i];
            return {
                id: wc.dbId,
                x1: line[0], y1: line[1],
                x2: line[2], y2: line[3],
            };
        });

        const res = await fetch(`${API_BASE}/maps/process/rooms`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(wallsForDetection),
        });
        if (!res.ok) throw new Error("Failed to detect rooms");
        
        // ✅ خروجی اکنون مستقیماً List[RoomRead] است (نه {rooms: [...]})
        const rooms = await res.json();
        detectedRooms = rooms;
        // detectedRooms = rooms.map(r => r.coordinates.map(c => [c.x, c.y]));
        roomColors = rooms.map(() => getRandomPastelColor());

        // ✅ ذخیره wall_ids همراه با هر اتاق
        roomsCosts = rooms.map(r => ({
            costs: [],
            dbId: null,          // هنوز ذخیره نشده
            wall_ids: r.wall_ids || [],  // ✅ نگهداری wall_ids
        }));
        
        updatePreview();
        renderDebugList();
        setStatus(`✅ Found ${rooms.length} rooms.`, "success");
        
        if (rooms.length > 0) {
            document.getElementById('downloadLink').style.display = 'inline-block';
        }
    } catch (e) {
        console.error(e);
        setStatus("❌ Error detecting rooms.", "error");
    }
}

// --- Interaction & Debug List ---
function renderDebugList() {
    document.getElementById('wallCountBadge').textContent = `${detectedLines.length} walls`;
    
    // --- Walls List ---
    const wList = document.getElementById('wallsList');
    wList.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:center; padding:8px; border-bottom:1px solid #333;">
            <span style="color:#4ec9b0; text-transform:uppercase; font-size:0.8rem;">Walls</span>
            <button class="cost-btn" onclick="saveWalls()" 
                    style="border-color:#28a745; color:#28a745; font-size:0.75rem;"
                    title="Save all walls to DB">
                <i class="fa-solid fa-save"></i> Save
            </button>
        </div>
    ` + (detectedLines.map((l, i) => {
        const activeClass = (i === highlightedLineIndex) ? 'active' : '';
        const wallDbId = wallsCosts[i]?.dbId || 'new'; 
        
        return `
            <div class="item-row ${activeClass}" onclick="highlightWall(${i})">
                <div>Wall #${i+1}</div>
                <div>
                    <a href="/project/${projectId}/walls/${wallDbId}/cost?side=left" 
                       class="cost-btn" title="Left Side Cost" target="_blank">
                       <i class="fa-solid fa-arrow-left"></i>
                    </a>
                    <a href="/project/${projectId}/walls/${wallDbId}/cost?side=right" 
                       class="cost-btn" title="Right Side Cost" target="_blank">
                       <i class="fa-solid fa-arrow-right"></i>
                    </a>
                    <button class="delete-btn" onclick="event.stopPropagation(); deleteWall(${i})">✕</button>
                </div>
            </div>`;
    }).join('') || '<div style="color:#666; padding:10px;">No walls detected</div>');

    // --- Rooms List ---
    const rList = document.getElementById('roomsList');
    rList.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:center; padding:8px; border-bottom:1px solid #333;">
            <span style="color:#4ec9b0; text-transform:uppercase; font-size:0.8rem;">Rooms</span>
            <button class="cost-btn" onclick="saveRooms()" 
                    style="border-color:#28a745; color:#28a745; font-size:0.75rem;"
                    title="Save all rooms to DB">
                <i class="fa-solid fa-save"></i> Save
            </button>
        </div>
    ` + (detectedRooms.map((r, i) => {
        const activeClass = (i === highlightedRoomIndex) ? 'active' : '';
        const roomDbId = roomsCosts[i]?.dbId || 'new';
        
        return `
            <div class="item-row ${activeClass}" onclick="highlightRoom(${i})">
                <div style="display:flex; align-items:center;">
                    <span style="width:10px; height:10px; background:${roomColors[i]}; display:inline-block; margin-right:5px; border-radius:50%;"></span>
                    Room #${i+1}
                </div>
                <div>
                    <button class="cost-btn" 
                            onclick="event.stopPropagation(); showRoomInfo(${i})" 
                            title="Room Details">
                        <i class="fa-solid fa-info-circle"></i>
                    </button>
                    <button class="delete-btn" onclick="event.stopPropagation(); deleteRoom(${i})">✕</button>
                </div>
            </div>`;
    }).join('') || '<div style="color:#666; padding:10px;">No rooms detected</div>');
}

// --- Save Walls Independently ---
async function saveWalls() {
    if (!projectId) return alert("No project ID found.");
    
    // ✅ خواندن مستقیم از state جاری (منعکس‌کننده Human Check)
    const currentWalls = detectedLines;
    
    if (currentWalls.length === 0) {
        return setStatus("⚠ No walls to save.", "error");
    }

    setStatus("Saving walls...", "loading");
    try {
        // ✅ بازسازی index بر اساس ترتیب فعلی لیست قابل مشاهده
        const wallsPayload = currentWalls.map((l, i) => ({
            x1: l[0], y1: l[1], x2: l[2], y2: l[3],
            index: i,  // ترتیب فعلی در UI
        }));

        const res = await fetch(`${API_BASE}/project/${projectId}/walls`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(wallsPayload),
        });

        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || `Save failed (${res.status})`);
        }

        const savedWalls = await res.json();

        // ✅ بروزرسانی dbId متناسب با ترتیب فعلی
        // پس از save، wallsCosts باید دقیقاً هم‌طول detectedLines باشد
        wallsCosts = savedWalls.map((w, i) => {
            // حفظ هزینه‌های موجود اگر index قبلی مطابقت دارد
            const existing = wallsCosts[i] || { left: [], right: [] };
            return {
                left: existing.left || [],
                right: existing.right || [],
                dbId: w.id,
            };
        });

        renderDebugList();
        setStatus(`✅ ${savedWalls.length} walls saved.`, "success");
    } catch (error) {
        console.error("Save walls error:", error);
        setStatus(`❌ Save walls failed: ${error.message}`, "error");
    }
}

// --- Save Rooms Independently ---
async function saveRooms() {
    // ✅ محافظت در برابر undefined/null
    if (!Array.isArray(detectedRooms)) {
        console.error('saveRooms: detectedRooms is not an array', detectedRooms);
        return [];
    }

    roomsPayload = detectedRooms;
    // const roomsPayload = detectedRooms.map(room => ({
    //     coordinates: room.coordinates || [],
    //     floor_area_m2: room.floor_area_m2 ?? null,
    //     name: room.name || null,
    //     notes: room.notes || null,
    //     wall_ids: (room.related_objects || [])
    //         .filter(obj => obj.object_type === 'wall' && obj.wall_id != null)
    //         .map(obj => obj.wall_id)
    // }));

    const response = await fetch(`/api/project/${projectId}/rooms`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(roomsPayload)
    });

    if (!response.ok) throw new Error(`Failed to save rooms: ${response.status}`);
    return await response.json();
}

function highlightWall(i) {
    highlightedLineIndex = i;
    highlightedRoomIndex = -1;
    drawOverlays();
    renderDebugList();
}

function highlightRoom(i) {
    highlightedRoomIndex = i;
    highlightedLineIndex = -1;
    drawOverlays();
    renderDebugList();
}

function deleteWall(i) {
    // 1. حذف دیوار از آرایه اصلی
    detectedLines.splice(i, 1);
    
    // 2. حذف داده‌های هزینه مربوط به آن دیوار
    wallsCosts.splice(i, 1);
    
    // 3. ریست کردن انتخاب‌ها
    highlightedLineIndex = -1;
    highlightedRoomIndex = -1;
    
    // 4. حذف اتاق‌ها چون ساختار دیوارها تغییر کرده و اتاق‌های قبلی نامعتبر هستند
    detectedRooms = []; 
    roomsCosts = [];
    roomColors = [];
    
    // 5. نکته کلیدی: فعال کردن مجدد دکمه تشخیص اتاق
    // document.getElementById('detectRoomBtn').disabled = false;
    
    // 6. مخفی کردن دکمه اکسپورت تا زمانی که اتاق‌های جدید ساخته شوند
    document.getElementById('downloadLink').style.display = 'none';
    
    // 7. بروزرسانی تصویر و لیست
    updatePreview();
    renderDebugList();
}


function deleteRoom(i) {
    detectedRooms.splice(i, 1);
    roomsCosts.splice(i, 1);
    roomColors.splice(i, 1);
    highlightedRoomIndex = -1;
    drawOverlays();
    renderDebugList();
}

function clearAll() {
    resetState();
    if (originalImage) updatePreview();
}

// --- Cost Management ---
async function openCost(type, index, side = null) {
    setStatus("Checking database sync...", "loading");
    try {
        let targetId = null;
        let costUrl = ""; // متغیر برای ذخیره آدرس نهایی

        if (type === 'wall') {
            // بررسی وجود ID قبلی یا ایجاد جدید
            if (wallsCosts[index] && wallsCosts[index].dbId) {
                targetId = wallsCosts[index].dbId;
            } else {
                const wallData = detectedLines[index];
                const res = await apiRequest(`/project/${projectId}/walls`, 'POST', {
                    project_id: projectId,
                    index: index,
                    x1: wallData[0], y1: wallData[1],
                    x2: wallData[2], y2: wallData[3]
                });
                if (res && res.id) {
                    targetId = res.id;
                    if (!wallsCosts[index]) wallsCosts[index] = {};
                    wallsCosts[index].dbId = targetId;
                } else {
                    throw new Error("Failed to get wall ID");
                }
            }
            // ✅ استفاده از روت جدید بک‌اند
            costUrl = `/project/${projectId}/walls/${targetId}/cost`;
            
        } else if (type === 'room') {
            if (roomsCosts[index] && roomsCosts[index].dbId) {
                targetId = roomsCosts[index].dbId;
            } else {
                const roomData = detectedRooms[index];
                const res = await apiRequest(`/project/${projectId}/rooms`, 'POST', {
                    project_id: projectId,
                    index: index,
                    floor_area_m2: calculatePolygonArea(roomData) / 10000
                });
                if (res && res.id) {
                    targetId = res.id;
                    if (!roomsCosts[index]) roomsCosts[index] = {};
                    roomsCosts[index].dbId = targetId;
                } else {
                    throw new Error("Failed to get room ID");
                }
            }
            // ✅ استفاده از روت جدید بک‌اند برای اتاق
            costUrl = `/project/${projectId}/rooms/${targetId}/cost`;
        }

        // باز کردن صفحه Cost با آدرس جدید
        // نکته: دیگر نیازی به localStorage نیست چون پارامترها در URL هستند
        window.open(costUrl, '_blank');
        
        setStatus("✅ Ready.", "success");
    } catch (e) {
        console.error(e);
        setStatus(`❌ Error: ${e.message}`, "error");
    }
}

async function loadProjectData() {
    if (!projectId) return;
    
    setStatus("Loading project data...", "loading");
    
    try {
        // ✅ فراخوانی موازی سه اندپوینت مستقل
        const [planRes, wallsRes, roomsRes] = await Promise.all([
            fetch(`${API_BASE}/project/${projectId}/plan`),
            fetch(`${API_BASE}/project/${projectId}/walls`),
            fetch(`${API_BASE}/project/${projectId}/rooms`),
        ]);

        // --- 1. لود تصویر نقشه ---
        let imageLoaded = false;
        if (planRes.ok) {
            const planData = await planRes.json();
            if (planData.map_image_base64) {
                originalImage = new Image();
                
                // ✅ Promise برای اطمینان از لود کامل تصویر قبل از رسم
                await new Promise((resolve, reject) => {
                    originalImage.onload = resolve;
                    originalImage.onerror = reject;
                    
                    let src = planData.map_image_base64;
                    if (!src.startsWith('data:image')) {
                        src = `data:image/png;base64,${src}`;
                    }
                    originalImage.src = src;
                });

                canvas.width = originalImage.width;
                canvas.height = originalImage.height;
                imageLoaded = true;

                // ✅ رفع مشکل "Please select an image first"
                // تبدیل base64 به File و قرار دادن در fileInput
                try {
                    const byteString = atob(planData.map_image_base64.split(',')[1]);
                    const mimeMatch = planData.map_image_base64.match(/data:(image\/\w+);/);
                    const mimeType = mimeMatch ? mimeMatch[1] : 'image/png';
                    const ab = new ArrayBuffer(byteString.length);
                    const ia = new Uint8Array(ab);
                    for (let i = 0; i < byteString.length; i++) ia[i] = byteString.charCodeAt(i);
                    
                    const blob = new Blob([ab], { type: mimeType });
                    const file = new File([blob], 'plan.png', { type: mimeType });
                    
                    const dt = new DataTransfer();
                    dt.items.add(file);
                    document.getElementById('mapFile').files = dt.files;
                } catch (e) {
                    console.warn("Could not restore file input:", e);
                }
            }
        }

        // --- 2. لود دیوارها ---
        if (wallsRes.ok) {
            const walls = await wallsRes.json();
            
            detectedLines = walls.map(w => [w.x1, w.y1, w.x2, w.y2]);
            wallsCosts = walls.map(w => ({
                left: [],   // هزینه‌ها جداگانه لود می‌شوند
                right: [],
                dbId: w.id,
            }));
        }

        // --- 3. لود اتاق‌ها ---
        if (roomsRes.ok) {
            const rooms = await roomsRes.json();
            
            detectedRooms = rooms.map(r => 
                r.coordinates.map(c => [c.x, c.y])
            );
            roomColors = rooms.map(() => getRandomPastelColor());
            roomsCosts = rooms.map(r => ({
                costs: [],
                dbId: r.id,
            }));
            
            if (rooms.length > 0) {
                // document.getElementById('detectRoomBtn').disabled = false;
                document.getElementById('downloadLink').style.display = 'inline-block';
            }
        }

        // --- 4. رسم نهایی ---
        if (imageLoaded) {
            updatePreview();
        }
        renderDebugList();
        
        const wallCount = detectedLines.length;
        const roomCount = detectedRooms.length;
        setStatus(
            `✅ Loaded: ${wallCount} walls, ${roomCount} rooms.${imageLoaded ? '' : ' ⚠ No map image.'}`,
            imageLoaded ? "success" : "error"
        );
        
    } catch (e) {
        console.error(e);
        setStatus("❌ Failed to load project data.", "error");
    }
}

// --- Save & Export ---
async function saveProjectData() {
    if (!projectId) return;
    
    // ✅ اضافه کردن تصویر به payload
    const mapImageBase64 = originalImage ? originalImage.src : null;
    
    const payload = {
        project: {
            map_image_base64: mapImageBase64
        },
        walls: detectedLines.map((l, i) => ({
            index: i,
            x1: l[0], y1: l[1], x2: l[2], y2: l[3],
            costs: [
                ...wallsCosts[i].left.map(c => ({...c, side: 'left'})), 
                ...wallsCosts[i].right.map(c => ({...c, side: 'right'}))
            ]
        })),
        rooms: detectedRooms.map((r, i) => ({
            index: i,
            floor_area_m2: calculatePolygonArea(r) / 10000, 
            costs: roomsCosts[i]
        }))
    };

    setStatus("Saving to database...", "loading");
    try {
        const res = await apiRequest(`/project/${projectId}/data`, 'PUT', payload);
        if (res) setStatus("✅ Project saved successfully!", "success");
    } catch (e) {
        console.error(e);
        setStatus("❌ Save failed.", "error");
    }
}

async function exportSh3d(e) {
    e.preventDefault();
    if (detectedLines.length === 0) return alert("No walls to export");
    
    setStatus("Generating .sh3d...", "loading");
    try {
        const res = await fetch(`${API_BASE}/maps/export/sh3d/`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ walls: detectedLines, rooms: detectedRooms })
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

// --- Helpers ---
function setStatus(msg, type) {
    const el = document.getElementById('status');
    el.textContent = msg;
    el.style.color = type === 'error' ? '#dc3545' : (type === 'success' ? '#28a745' : '#007bff');
}

function getRandomPastelColor() {
    const hue = Math.floor(Math.random() * 360);
    return `hsla(${hue}, 70%, 70%, 0.3)`;
}

function darkenColor(hslaStr, amount) {
    return hslaStr.replace('0.3', '1').replace('70%', '40%');
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

// --- Room Info Popup ---
async function showRoomInfo(roomIndex) {
    const roomData = roomsCosts[roomIndex];
    if (!roomData?.dbId) {
        return setStatus("⚠ Please save rooms first to view details.", "error");
    }

    const modal = document.getElementById('roomInfoModal');
    const title = document.getElementById('roomInfoTitle');
    const content = document.getElementById('roomInfoContent');

    modal.dataset.roomIndex = roomIndex;
    modal.dataset.roomId = roomData.dbId;

    title.innerHTML = `<i class="fa-solid fa-door-open"></i> Room #${roomIndex + 1}`;
    content.innerHTML = '<div style="text-align:center; padding:2rem; color:#666;"><i class="fa-solid fa-spinner fa-spin"></i> Loading...</div>';
    modal.style.display = 'flex';

    await refreshRoomPopup(roomIndex);
}

// ✅ تابع جداگانه برای رفرش محتوای popup (بدون بستن)
// ✅ تابع اصلاح شده برای تم روشن و مدرن
async function refreshRoomPopup(roomIndex) {
    const roomData = roomsCosts[roomIndex];
    if (!roomData?.dbId) return;

    const content = document.getElementById('roomInfoContent');
    const title = document.getElementById('roomInfoTitle');

    try {
        const res = await fetch(`${API_BASE}/project/${projectId}/rooms/${roomData.dbId}`);
        if (!res.ok) throw new Error(`Failed to load room (${res.status})`);

        const room = await res.json();

        // ذخیره اطلاعات در مودال
        const modal = document.getElementById('roomInfoModal');
        modal.dataset.roomId = room.id;
        modal.dataset.roomIndex = roomIndex;

        // --- هدر: نام + نوع اتاق + دکمه رفرش ---
        let html = `
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1.5rem; padding-bottom:1rem; border-bottom:1px solid var(--border);">
                <div style="display:flex; align-items:center; gap:12px;">
                    <select id="roomTypeSelect" data-room-id="${room.id}"
                            onchange="updateRoomName(${room.id}, this.value)"
                            style="padding:8px 12px; border-radius:8px; border:1px solid var(--border); background:#fff; color:var(--text-main); font-size:0.9rem; min-width:160px; box-shadow:var(--shadow-sm); cursor:pointer;">
                        <option value="">— Select Type —</option>
                        <option value="Bedroom" ${room.name === 'Bedroom' ? 'selected' : ''}>🛏️ Bedroom</option>
                        <option value="Bathroom" ${room.name === 'Bathroom' ? 'selected' : ''}> Bathroom</option>
                        <option value="Kitchen" ${room.name === 'Kitchen' ? 'selected' : ''}>🍳 Kitchen</option>
                        <option value="Living Room" ${room.name === 'Living Room' ? 'selected' : ''}>️ Living Room</option>
                        <option value="Dining Room" ${room.name === 'Dining Room' ? 'selected' : ''}>️ Dining Room</option>
                        <option value="Hallway" ${room.name === 'Hallway' ? 'selected' : ''}>🚪 Hallway</option>
                        <option value="Balcony" ${room.name === 'Balcony' ? 'selected' : ''}>🌿 Balcony</option>
                        <option value="Storage" ${room.name === 'Storage' ? 'selected' : ''}>📦 Storage</option>
                        <option value="Office" ${room.name === 'Office' ? 'selected' : ''}>💼 Office</option>
                        <option value="Garage" ${room.name === 'Garage' ? 'selected' : ''}>🚗 Garage</option>
                    </select>
                    <span style="color:var(--text-muted); font-size:0.8rem; background:#f1f5f9; padding:4px 8px; border-radius:6px; border:1px solid var(--border);">ID: ${room.id}</span>
                </div>
                <button onclick="refreshRoomPopup(${roomIndex})" 
                        class="btn btn-secondary" 
                        style="padding:8px 14px; font-size:0.85rem;"
                        title="Refresh data from server">
                    <i class="fa-solid fa-rotate-right"></i> Refresh
                </button>
            </div>
        `;

        // --- اطلاعات پایه اتاق ---
        html += `
            <div style="background:#f8fafc; border-radius:8px; padding:1rem; margin-bottom:1.5rem; border:1px solid var(--border);">
                <table style="width:100%; border-collapse:collapse; font-size:0.9rem;">
                    <tr>
                        <td style="padding:8px 0; color:var(--text-muted); width:120px; font-weight:500;">Floor Area</td>
                        <td style="padding:8px 0; color:var(--text-main); font-weight:600;">${room.floor_area_m2 ? room.floor_area_m2.toFixed(2) + ' m²' : '—'}</td>
                    </tr>
                    <tr>
                        <td style="padding:8px 0; color:var(--text-muted); font-weight:500;">Wall Area</td>
                        <td style="padding:8px 0; color:var(--text-main); font-weight:600;">${room.wall_area_m2 ? room.wall_area_m2.toFixed(2) + ' m²' : '—'}</td>
                    </tr>
                    <tr>
                        <td style="padding:8px 0; color:var(--text-muted); font-weight:500;">Perimeter</td>
                        <td style="padding:8px 0; color:var(--text-main); font-weight:600;">${room.perimeter_m ? room.perimeter_m.toFixed(2) + ' m' : '—'}</td>
                    </tr>
                </table>
            </div>
        `;

        // --- Related Objects ---
        const related = room.related_objects || [];

        if (related.length === 0) {
            html += `<div style="color:var(--text-muted); padding:2rem; text-align:center; border:1px dashed var(--border); border-radius:8px;">No related objects found.</div>`;
        } else {
            const walls = related.filter(r => r.object_type === 'wall');
            const floors = related.filter(r => r.object_type === 'floor');
            const ceilings = related.filter(r => r.object_type === 'ceiling');

            html += `<div style="margin-top:1rem;">`;
            html += `<div style="color:var(--primary); text-transform:uppercase; font-size:0.75rem; font-weight:700; margin-bottom:1rem; letter-spacing:0.5px;">Related Objects (${related.length})</div>`;

            // ✅ تابع داخلی برای رندر گروه‌ها با تم روشن
            const renderGroup = (items, label, icon, colorHex) => {
                if (items.length === 0) return '';
                let g = `<div style="margin-bottom:1.5rem;">
                    <div style="display:flex; align-items:center; gap:6px; margin-bottom:0.75rem; color:var(--text-main); font-weight:600; font-size:0.9rem;">
                        <span>${icon}</span> ${label} <span style="color:var(--text-muted); font-weight:400; font-size:0.8rem;">(${items.length})</span>
                    </div>`;

                items.forEach(item => {
                    const coordLabel = (item.wall_x1 !== null)
                        ? `<span style="color:var(--text-muted); font-size:0.75rem; margin-left:5px;">(${item.wall_x1},${item.wall_y1})→(${item.wall_x2},${item.wall_y2})</span>`
                        : '';
                    const sideLabel = item.side_type ? `<span style="background:#e0f2fe; color:#0369a1; padding:2px 6px; border-radius:4px; font-size:0.7rem; margin-left:5px; font-weight:600;">${item.side_type.toUpperCase()}</span>` : '';

                    // استفاده از تم روشن برای کارت‌ها
                    g += `<div style="padding:12px 15px; margin-bottom:8px; background:#ffffff; border-radius:8px; border:1px solid var(--border); border-left:4px solid ${colorHex}; display:flex; justify-content:space-between; align-items:center; box-shadow:var(--shadow-sm); transition:transform 0.2s;">`;

                    // اطلاعات Object
                    g += `<div style="font-size:0.85rem; color:var(--text-main); line-height:1.5;">
                        <span style="font-weight:600;">${item.object_type === 'wall' ? 'Wall #' + item.wall_id : item.object_type.charAt(0).toUpperCase() + item.object_type.slice(1)}</span>
                        ${sideLabel}${coordLabel}
                        <div style="font-size:0.75rem; color:var(--text-muted); margin-top:2px;">Rel ID: ${item.relation_id}</div>
                    </div>`;

                    // ✅ لینک مستقیم به صفحه Cost این Object
                    g += `<a href="/project/${projectId}/objects/${item.relation_id}/cost" 
                              target="_blank"
                              class="btn btn-primary"
                              style="padding:6px 12px; font-size:0.75rem; height:auto;"
                              title="Manage costs for this object">
                            <i class="fa-solid fa-coins"></i> Manage Costs
                         </a>`;

                    g += `</div>`;
                });

                g += `</div>`;
                return g;
            };

            // رنگ‌های ملایم و مدرن برای دسته‌بندی‌ها
            html += renderGroup(walls, 'Walls', '🧱', '#ef4444');      // قرمز ملایم
            html += renderGroup(floors, 'Floor', '⬜', '#10b981');     // سبز زمردی
            html += renderGroup(ceilings, 'Ceiling', '⬛', '#3b82f6'); // آبی

            html += `</div>`;
        }

        content.innerHTML = html;
        title.innerHTML = `<i class="fa-solid fa-door-open" style="color:var(--primary);"></i> Room #${roomIndex + 1} ${room.name ? '— ' + room.name : ''}`;

    } catch (error) {
        content.innerHTML = `<div style="color:var(--danger); padding:2rem; text-align:center; background:#fef2f2; border-radius:8px; border:1px solid #fecaca;">❌ ${error.message}</div>`;
    }
}

// ✅ updateRoomName — بدون بستن popup، فقط رفرش محتوا
async function updateRoomName(roomId, typeName) {
    if (!typeName) return;

    const modal = document.getElementById('roomInfoModal');
    const roomIndex = parseInt(modal.dataset.roomIndex);
    const content = document.getElementById('roomInfoContent');

    // جلوگیری از کلیک‌های تکراری
    if (content.style.pointerEvents === 'none') return;

    // نمایش حالت لودینگ
    content.style.opacity = '0.5';
    content.style.pointerEvents = 'none';
    setStatus(`🤖 Generating costs for "${typeName}"...`, "loading");

    try {
        const res = await fetch(`${API_BASE}/project/${projectId}/rooms/${roomId}/suggest-costs`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ room_type: typeName }),
        });

        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || `Server error (${res.status})`);
        }

        const data = await res.json();
        console.log("Suggest costs response:", data);

        setStatus(`✅ Costs updated for ${typeName}`, "success");

        // ✅ رفرش محتوای popup بدون بستن
        // مهم: ابتدا opacity را برمی‌گردانیم تا کاربر حس نکند صفحه فریز شده
        content.style.opacity = '1';
        content.style.pointerEvents = 'auto';
        
        await refreshRoomPopup(roomIndex);

    } catch (e) {
        console.error("suggest-costs error:", e);
        setStatus(`❌ Failed: ${e.message}`, "error");
        
        // بازگرداندن قابلیت کلیک در صورت خطا
        content.style.opacity = '1';
        content.style.pointerEvents = 'auto';
        
        // نمایش پیام خطا داخل خود پاپ‌آپ برای آگاهی کاربر
        alert(`Error updating room: ${e.message}`);
    }
}

// ✅ addCostToRelation — اضافه کردن cost و رفرش popup
async function addCostToRelation(relationId, roomIndex) {
    const itemName = prompt("Item name:", "New Item");
    if (!itemName) return;

    const qty = parseFloat(prompt("Quantity:", "1")) || 1;
    const unit = prompt("Unit (m2, m, piece, liter, kg, hour):", "m2") || "m2";
    const price = parseFloat(prompt("Unit price ($):", "0")) || 0;

    try {
        const res = await fetch(`${API_BASE}/project/${projectId}/objects/${relationId}/cost`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                relation_id: relationId,
                item_name: itemName,
                quantity: qty,
                unit: unit,
                unit_price: price,
                duration_days: 1,
            }),
        });

        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || 'Failed');
        }

        setStatus("✅ Cost item added.", "success");

        // ✅ رفرش popup بدون بستن
        await refreshRoomPopup(roomIndex);

    } catch (e) {
        alert("Failed to add cost: " + e.message);
    }
}

function closeRoomInfo() {
    document.getElementById('roomInfoModal').style.display = 'none';
}

// بستن با کلیک روی overlay
document.getElementById('roomInfoModal')?.addEventListener('click', function(e) {
    if (e.target === this) closeRoomInfo();
});

// اجرای خودکار هنگام لود صفحه
document.addEventListener('DOMContentLoaded', () => {
    // اگر تصویر اصلی قبلاً لود نشده باشد، ابتدا باید منتظر آن بمانیم
    // اما چون تصویر از دیتابیس نمی‌آید (یا باید جداگانه لود شود)، 
    // فعلا فقط داده‌های هندسی را لود می‌کنیم.
    // اگر map_image_base64 دارید، باید اینجا decode و لود شود.
    loadProjectData();
});

