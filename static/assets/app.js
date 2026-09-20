// static/assets/app.js
const API_BASE = "/api";

async function apiRequest(url, method = 'GET', body = null) {
    const options = {
        method,
        headers: { 'Content-Type': 'application/json' }
    };
    if (body) options.body = JSON.stringify(body);
    
    try {
        const response = await fetch(`${API_BASE}${url}`, options);
        if (!response.ok) throw new Error(`API Error: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error(error);
        alert("خطا در ارتباط با سرور");
        return null;
    }
}

function getQueryParam(param) {
    return new URLSearchParams(window.location.search).get(param);
}
