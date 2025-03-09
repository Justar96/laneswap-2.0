// Internationalization support
const translations = {
    en: {
        title: "LaneSwap Monitor",
        nav: {
            title: "LaneSwap Monitor",
            dashboard: "Dashboard",
            settings: "Settings",
            help: "Help"
        },
        api: {
            url: "API URL",
            connect: "Connect"
        },
        refresh: {
            interval: "Refresh",
            manual: "Manual",
            "5sec": "5 seconds",
            "10sec": "10 seconds",
            "30sec": "30 seconds",
            "60sec": "60 seconds",
            button: "Refresh"
        },
        search: {
            label: "Search"
        },
        summary: {
            healthy: "Healthy",
            warning: "Warning",
            error: "Error",
            stale: "Stale",
            total: "Total"
        },
        status: {
            healthy: "Healthy",
            warning: "Warning",
            error: "Error",
            stale: "Stale",
            unknown: "Unknown"
        },
        service: {
            id: "Service ID",
            name: "Name",
            status: "Status",
            lastHeartbeat: "Last Heartbeat",
            message: "Message",
            metadata: "Metadata",
            noMessage: "No message",
            noMetadata: "No metadata"
        },
        modal: {
            serviceDetails: "Service Details",
            close: "Close",
            cancel: "Cancel",
            save: "Save",
            ok: "OK"
        },
        settings: {
            title: "Settings",
            theme: "Theme",
            light: "Light",
            dark: "Dark",
            system: "System",
            language: "Language",
            english: "English",
            thai: "Thai",
            dateFormat: "Date Format",
            relative: "Relative (5 minutes ago)",
            absolute: "Absolute (YYYY-MM-DD HH:MM:SS)"
        },
        help: {
            title: "Help",
            about: "About LaneSwap Monitor",
            description: "LaneSwap Monitor is a real-time dashboard for monitoring service health in distributed systems.",
            usage: "Usage",
            step1: "Enter the API URL (e.g., http://localhost:8000)",
            step2: "Click \"Connect\" to fetch services",
            step3: "Set the refresh interval or manually refresh",
            step4: "Click on a service card to view details",
            statusCodes: "Status Codes",
            healthy: "Service is operating normally",
            warning: "Service has non-critical issues",
            error: "Service has critical issues",
            stale: "Service hasn't sent a heartbeat recently"
        },
        time: {
            now: "just now",
            seconds: "seconds ago",
            minute: "minute ago",
            minutes: "minutes ago",
            hour: "hour ago",
            hours: "hours ago",
            day: "day ago",
            days: "days ago"
        },
        loading: "Loading services...",
        error: "Error loading services",
        noServices: "No services found",
        lastUpdated: "Last updated: Never",
        poweredBy: "Powered by"
    },
    th: {
        title: "ระบบติดตาม LaneSwap",
        nav: {
            title: "ระบบติดตาม LaneSwap",
            dashboard: "แดชบอร์ด",
            settings: "ตั้งค่า",
            help: "ช่วยเหลือ"
        },
        api: {
            url: "URL ของ API",
            connect: "เชื่อมต่อ"
        },
        refresh: {
            interval: "รีเฟรช",
            manual: "ด้วยตนเอง",
            "5sec": "5 วินาที",
            "10sec": "10 วินาที",
            "30sec": "30 วินาที",
            "60sec": "60 วินาที",
            button: "รีเฟรช"
        },
        search: {
            label: "ค้นหา"
        },
        summary: {
            healthy: "ปกติ",
            warning: "เตือน",
            error: "ผิดพลาด",
            stale: "ไม่ตอบสนอง",
            total: "ทั้งหมด"
        },
        status: {
            healthy: "ปกติ",
            warning: "เตือน",
            error: "ผิดพลาด",
            stale: "ไม่ตอบสนอง",
            unknown: "ไม่ทราบ"
        },
        service: {
            id: "รหัสบริการ",
            name: "ชื่อ",
            status: "สถานะ",
            lastHeartbeat: "สัญญาณล่าสุด",
            message: "ข้อความ",
            metadata: "ข้อมูลเพิ่มเติม",
            noMessage: "ไม่มีข้อความ",
            noMetadata: "ไม่มีข้อมูลเพิ่มเติม"
        },
        modal: {
            serviceDetails: "รายละเอียดบริการ",
            close: "ปิด",
            cancel: "ยกเลิก",
            save: "บันทึก",
            ok: "ตกลง"
        },
        settings: {
            title: "ตั้งค่า",
            theme: "ธีม",
            light: "สว่าง",
            dark: "มืด",
            system: "ระบบ",
            language: "ภาษา",
            english: "อังกฤษ",
            thai: "ไทย",
            dateFormat: "รูปแบบวันที่",
            relative: "สัมพัทธ์ (5 นาทีที่แล้ว)",
            absolute: "สัมบูรณ์ (YYYY-MM-DD HH:MM:SS)"
        },
        help: {
            title: "ช่วยเหลือ",
            about: "เกี่ยวกับระบบติดตาม LaneSwap",
            description: "ระบบติดตาม LaneSwap เป็นแดชบอร์ดแบบเรียลไทม์สำหรับติดตามสถานะบริการในระบบกระจาย",
            usage: "วิธีใช้งาน",
            step1: "ป้อน URL ของ API (เช่น http://localhost:8000)",
            step2: "คลิก \"เชื่อมต่อ\" เพื่อดึงข้อมูลบริการ",
            step3: "ตั้งค่าช่วงเวลารีเฟรชหรือรีเฟรชด้วยตนเอง",
            step4: "คลิกที่การ์ดบริการเพื่อดูรายละเอียด",
            statusCodes: "รหัสสถานะ",
            healthy: "บริการทำงานปกติ",
            warning: "บริการมีปัญหาที่ไม่วิกฤต",
            error: "บริการมีปัญหาวิกฤต",
            stale: "บริการไม่ได้ส่งสัญญาณเป็นเวลานาน"
        },
        time: {
            now: "เมื่อสักครู่",
            seconds: "วินาทีที่แล้ว",
            minute: "นาทีที่แล้ว",
            minutes: "นาทีที่แล้ว",
            hour: "ชั่วโมงที่แล้ว",
            hours: "ชั่วโมงที่แล้ว",
            day: "วันที่แล้ว",
            days: "วันที่แล้ว"
        },
        loading: "กำลังโหลดบริการ...",
        error: "เกิดข้อผิดพลาดในการโหลดบริการ",
        noServices: "ไม่พบบริการ",
        lastUpdated: "อัปเดตล่าสุด: ไม่เคย",
        poweredBy: "ขับเคลื่อนโดย"
    }
};

// Default language
let currentLanguage = localStorage.getItem('laneswap-language') || 'en';

// Function to change language
function changeLanguage(lang) {
    currentLanguage = lang;
    localStorage.setItem('laneswap-language', lang);
    updateLanguage();
}

// Function to update all text elements with translations
function updateLanguage() {
    const elements = document.querySelectorAll('[data-i18n]');
    elements.forEach(element => {
        const key = element.getAttribute('data-i18n');
        const keys = key.split('.');
        let translation = translations[currentLanguage];
        
        // Navigate through nested keys
        for (const k of keys) {
            if (translation && translation[k]) {
                translation = translation[k];
            } else {
                translation = key;
                break;
            }
        }
        
        if (typeof translation === 'string') {
            element.textContent = translation;
        }
    });
    
    // Update document title
    document.title = translations[currentLanguage].title;
    
    // Update language selector in settings
    const languageSelect = document.getElementById('languageSelect');
    if (languageSelect) {
        languageSelect.value = currentLanguage;
    }
}

// Function to get a translation by key
function getTranslation(key) {
    const keys = key.split('.');
    let translation = translations[currentLanguage];
    
    // Navigate through nested keys
    for (const k of keys) {
        if (translation && translation[k]) {
            translation = translation[k];
        } else {
            return key;
        }
    }
    
    return translation;
}

// Initialize language on page load
document.addEventListener('DOMContentLoaded', () => {
    updateLanguage();
    
    // Set up language selector in settings
    const languageSelect = document.getElementById('languageSelect');
    if (languageSelect) {
        languageSelect.value = currentLanguage;
        languageSelect.addEventListener('change', (e) => {
            changeLanguage(e.target.value);
        });
    }
}); 