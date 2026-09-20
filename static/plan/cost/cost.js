// static/plan/cost/cost.js

let context = { projectId: null, relationId: null };
let costItems = [];

document.addEventListener('DOMContentLoaded', async () => {
    // استخراج پارامترها از URL Path یا Query String
    const pathSegments = window.location.pathname.split('/');
    // فرض بر ساختار /project/{id}/objects/{id}/cost
    if (pathSegments[1] === 'project' && pathSegments[2] && pathSegments[3] === 'objects') {
        context.projectId = pathSegments[2];
        context.relationId = pathSegments[4];
    } 
    
    // Fallback برای query string (اگر نیاز بود)
    if (!context.projectId || !context.relationId) {
        const params = new URLSearchParams(window.location.search);
        context.projectId = params.get('project_id');
        context.relationId = params.get('relation_id');
    }

    if (!context.projectId || !context.relationId) {
        document.body.innerHTML = `<div style="padding:2rem; text-align:center; color:#dc3545;">
            <h3>Error: Missing Project or Object ID</h3>
            <p>Please access this page via the Room Objects panel.</p>
        </div>`;
        return;
    }

    updatePageTitle();
    await loadCostsFromDB();
});

function updatePageTitle() {
    document.title = `Object #${context.relationId} - Cost Sheet`;
    const h2 = document.getElementById('pageTitle');
    if (h2) h2.innerHTML = `<i class="fa-solid fa-coins"></i> Object #${context.relationId} Costs`;
}

async function loadCostsFromDB() {
    try {
        const data = await apiRequest(`/project/${context.projectId}/objects/${context.relationId}/cost`, 'GET');
        costItems = data || [];
        renderTable();
    } catch (e) {
        console.error(e);
        alert("Failed to load costs: " + e.message);
    }
}

function renderTable() {
    const tbody = document.getElementById('tableBody');
    if (!tbody) return;
    
    if (costItems.length === 0) {
        tbody.innerHTML = `<tr><td colspan="10" style="text-align:center; padding:2rem; color:#666;">No cost items yet. Click "Add Item" to start.</td></tr>`;
        return;
    }

    tbody.innerHTML = costItems.map((item, i) => {
        const total = ((parseFloat(item.quantity) || 0) * (parseFloat(item.unit_price) || 0)).toFixed(2);
        return `
        <tr data-id="${item.id}">
            <td contenteditable="true" onblur="updateItem(${i}, 'item_name', this.innerText)">${item.item_name || ''}</td>
            <td contenteditable="true" onblur="updateItem(${i}, 'quantity', this.innerText)">${item.quantity || 0}</td>
            <td>
                <select onchange="updateItem(${i}, 'unit', this.value)">
                    ${['m2','m','piece','liter','kg','hour'].map(u => 
                        `<option value="${u}" ${item.unit === u ? 'selected' : ''}>${u}</option>`
                    ).join('')}
                </select>
            </td>
            <td contenteditable="true" onblur="updateItem(${i}, 'unit_price', this.innerText)">${item.unit_price || 0}</td>
            <td class="total-col">$${total}</td>
            <td contenteditable="true" onblur="updateItem(${i}, 'duration_days', this.innerText)">${item.duration_days || 1}</td>
            <td><input type="date" value="${item.start_date || ''}" onchange="updateItem(${i}, 'start_date', this.value)" style="border:none; background:transparent; color:inherit; width:auto;"></td>
            <td contenteditable="true" onblur="updateItem(${i}, 'predecessor_id', this.innerText)">${item.predecessor_id || '-'}</td>
            <td contenteditable="true" onblur="updateItem(${i}, 'material_quality', this.innerText)">${item.material_quality || '-'}</td>
            <td style="text-align:center;">
                <button class="btn btn-sm btn-warning" onclick="openEditModal(${i})" title="Edit Details"><i class="fa-solid fa-pen"></i></button>
                <button class="btn btn-sm btn-danger" onclick="deleteRow(${i}, ${item.id})" title="Delete"><i class="fa-solid fa-trash"></i></button>
            </td>
        </tr>`;
    }).join('');
}

// --- CRUD Operations ---

async function addRow() {
    const newItem = {
        relation_id: parseInt(context.relationId),
        item_name: "New Item",
        quantity: 1,
        unit: "m2",
        unit_price: 0,
        duration_days: 1,
        source: "manual"
    };

    try {
        const created = await apiRequest(
            `/project/${context.projectId}/objects/${context.relationId}/cost`,
            'POST', newItem
        );
        if (created) await loadCostsFromDB();
    } catch (e) {
        alert("Failed to add item: " + e.message);
    }
}

async function updateItem(index, field, value) {
    const item = costItems[index];
    if (!item || !item.id) return;
    
    // تبدیل نوع داده بر اساس فیلد
    let parsedValue = value;
    if (['quantity', 'unit_price'].includes(field)) parsedValue = parseFloat(value) || 0;
    if (['duration_days', 'predecessor_id'].includes(field)) parsedValue = parseInt(value) || null;
    
    const updateData = { [field]: parsedValue };
    
    try {
        await apiRequest(
            `/project/${context.projectId}/objects/${context.relationId}/cost/${item.id}`,
            'PUT', updateData
        );
        // رفرش جزئی برای آپدیت Total بدون لود مجدد کل دیتا
        item[field] = parsedValue;
        renderTable(); 
    } catch (e) {
        alert("Update failed: " + e.message);
    }
}

async function deleteRow(index, itemId) {
    if (!confirm("Are you sure you want to delete this cost item?")) return;
    try {
        await apiRequest(
            `/project/${context.projectId}/objects/${context.relationId}/cost/${itemId}`,
            'DELETE'
        );
        await loadCostsFromDB();
    } catch (e) {
        alert("Delete failed: " + e.message);
    }
}

// --- Modal Functions ---

function openEditModal(index) {
    const item = costItems[index];
    if (!item) return;

    document.getElementById('editIndex').value = index;
    document.getElementById('editItemName').value = item.item_name || '';
    document.getElementById('editCategory').value = item.category || '';
    document.getElementById('editQty').value = item.quantity || 0;
    document.getElementById('editUnit').value = item.unit || 'm2';
    document.getElementById('editPrice').value = item.unit_price || 0;
    document.getElementById('editDuration').value = item.duration_days || 1;
    document.getElementById('editStartDate').value = item.start_date || '';
    document.getElementById('editPredecessor').value = item.predecessor_id || '';
    document.getElementById('editQuality').value = item.material_quality || '';
    document.getElementById('editNotes').value = item.notes || '';
    
    document.getElementById('editModal').style.display = 'flex';
}

function closeEditModal() {
    document.getElementById('editModal').style.display = 'none';
}

async function saveEditModal() {
    const index = parseInt(document.getElementById('editIndex').value);
    const item = costItems[index];
    if (!item || !item.id) return;

    const updateData = {
        item_name: document.getElementById('editItemName').value,
        category: document.getElementById('editCategory').value || null,
        quantity: parseFloat(document.getElementById('editQty').value) || 0,
        unit: document.getElementById('editUnit').value,
        unit_price: parseFloat(document.getElementById('editPrice').value) || 0,
        duration_days: parseInt(document.getElementById('editDuration').value) || 1,
        start_date: document.getElementById('editStartDate').value || null,
        predecessor_id: document.getElementById('editPredecessor').value ? parseInt(document.getElementById('editPredecessor').value) : null,
        material_quality: document.getElementById('editQuality').value || null,
        notes: document.getElementById('editNotes').value || null,
    };

    try {
        await apiRequest(
            `/project/${context.projectId}/objects/${context.relationId}/cost/${item.id}`,
            'PUT', updateData
        );
        closeEditModal();
        await loadCostsFromDB();
    } catch (e) {
        alert("Update failed: " + e.message);
    }
}

// دکمه Save All (اختیاری - اگر بخواهید همه تغییرات را یکجا بفرستید)
async function saveAllCosts() {
    setStatus("Saving all changes...", "loading");
    // در حال حاضر چون هر تغییر بلافاصله ذخیره می‌شود، این دکمه فقط برای اطمینان کاربر است
    await loadCostsFromDB();
    setStatus("All costs are up to date.", "success");
}

function setStatus(msg, type) {
    // اگر تابع setStatus در app.js وجود ندارد، اینجا تعریف کنید
    console.log(`[${type.toUpperCase()}] ${msg}`);
}