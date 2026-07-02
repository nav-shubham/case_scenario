/* ==========================================================================
   CA Case Scenario Solver - Dashboard Page Logic
   ========================================================================== */

let currentLevel = null;        // 'Final' or 'Intermediate'
let userProfile = null;         // Candidate profile: { name, regNo }
let progress = {};              // Schema: { "Subject Name": { case_no: { status, score, total } } }
let questionDifficulties = {};  // Schema: { "Subject Name": { case_no: { q_no: 'easy'|'medium'|'hard' } } }

// Initialize Page
function init() {
    console.log("[+] Initializing Dashboard...");

    // Check login state
    try {
        const storedProfile = localStorage.getItem("ca_user_profile");
        if (!storedProfile) {
            window.location.href = "login.html";
            return;
        }
        userProfile = JSON.parse(storedProfile);
        if (!userProfile || !userProfile.name || !userProfile.regNo) {
            window.location.href = "login.html";
            return;
        }
    } catch (e) {
        console.error("[-] Error reading profile from localStorage:", e);
        window.location.href = "login.html";
        return;
    }

    // Load progress and difficulties from localStorage
    try {
        const storedProgress = localStorage.getItem("ca_user_progress");
        if (storedProgress) progress = JSON.parse(storedProgress) || {};

        const storedDiffs = localStorage.getItem("ca_question_difficulties");
        if (storedDiffs) questionDifficulties = JSON.parse(storedDiffs) || {};
    } catch (e) {
        console.error("[-] Error loading data from localStorage:", e);
    }

    if (!progress || typeof progress !== 'object') progress = {};
    if (!questionDifficulties || typeof questionDifficulties !== 'object') questionDifficulties = {};

    // Update Header Profile UI
    updateProfileUI();

    // Set up Event Listeners
    setupEventListeners();

    // Route based on URL query parameter `level`
    handleParamsRouting();
}

function setupEventListeners() {
    // Header Logo Click
    document.getElementById("header-logo").addEventListener("click", () => {
        window.location.href = "dashboard.html";
    });

    // Level selector cards
    const levelCards = document.querySelectorAll(".level-card");
    levelCards.forEach(card => {
        card.addEventListener("click", () => {
            const level = card.getAttribute("data-level");
            selectLevel(level);
        });
    });

    // Back to Levels button
    document.getElementById("btn-back-to-levels").addEventListener("click", () => {
        // Remove level param and refresh view
        const url = new URL(window.location);
        url.searchParams.delete('level');
        window.history.pushState({}, '', url);
        handleParamsRouting();
    });

    // Logout
    document.getElementById("btn-logout").addEventListener("click", handleLogout);

    // Reset All Data
    document.getElementById("btn-reset-all").addEventListener("click", resetAllData);
}

function handleParamsRouting() {
    const urlParams = new URLSearchParams(window.location.search);
    const levelParam = urlParams.get('level');

    if (levelParam && (levelParam.toLowerCase() === 'final' || levelParam.toLowerCase() === 'intermediate')) {
        currentLevel = levelParam.toLowerCase() === 'final' ? 'Final' : 'Intermediate';
        showSubjectSelectorScreen();
    } else {
        currentLevel = null;
        showLevelSelectorScreen();
    }

    updateDashboardStats();
}

function showLevelSelectorScreen() {
    document.getElementById("subject-selector-screen").style.display = "none";
    document.getElementById("level-selector-screen").style.display = "block";
}

function showSubjectSelectorScreen() {
    document.getElementById("level-selector-screen").style.display = "none";
    document.getElementById("subject-selector-screen").style.display = "block";
    document.getElementById("level-heading").innerText = `CA ${currentLevel} - Subjects`;
    buildSubjectList();
}

function selectLevel(level) {
    const url = new URL(window.location);
    url.searchParams.set('level', level.toLowerCase());
    window.history.pushState({}, '', url);
    handleParamsRouting();
}

function selectSubject(subjectName) {
    if (!currentLevel) return;
    window.location.href = `workspace.html?level=${currentLevel.toLowerCase()}&subject=${encodeURIComponent(subjectName)}`;
}

function buildSubjectList() {
    const container = document.getElementById("subject-list-container");
    container.innerHTML = "";
    
    if (!window.EXAM_DATABASE || !window.EXAM_DATABASE[currentLevel]) return;
    
    const subjects = window.EXAM_DATABASE[currentLevel];
    subjects.forEach(sub => {
        const card = document.createElement("div");
        card.className = "subject-card";
        
        // Progress calculation
        const totalCases = sub.cases ? sub.cases.length : 0;
        let completedCases = 0;
        if (progress[sub.subject]) {
            completedCases = Object.values(progress[sub.subject]).filter(c => c.status === 'completed').length;
        }
        const percent = totalCases > 0 ? Math.round((completedCases / totalCases) * 100) : 0;
        
        card.innerHTML = `
            <div>
                <h3 class="subject-name">${sub.subject}</h3>
            </div>
            <div>
                <div class="subject-stats">
                    <span>${totalCases} Case Scenarios</span>
                    <span>${percent}% Done</span>
                </div>
                <div class="progress-bar-container">
                    <div class="progress-bar" style="width: ${percent}%;"></div>
                </div>
            </div>
        `;
        
        card.addEventListener("click", () => selectSubject(sub.subject));
        container.appendChild(card);
    });
}

function updateDashboardStats() {
    const statsPanel = document.getElementById("dashboard-stats-panel");
    if (!statsPanel) return;
    
    let totalCases = 0;
    let completedCasesCount = 0;
    let totalScore = 0;
    let totalScoreQuestions = 0;
    
    if (window.EXAM_DATABASE) {
        Object.keys(window.EXAM_DATABASE).forEach(lvl => {
            window.EXAM_DATABASE[lvl].forEach(sub => {
                if (sub.cases) {
                    totalCases += sub.cases.length;
                }
            });
        });
    }
    
    Object.keys(progress).forEach(subName => {
        if (progress[subName]) {
            Object.keys(progress[subName]).forEach(caseNo => {
                const cProg = progress[subName][caseNo];
                if (cProg && cProg.status === 'completed') {
                    completedCasesCount++;
                    if (typeof cProg.score === 'number') {
                        totalScore += cProg.score;
                        totalScoreQuestions += cProg.total || 0;
                    }
                }
            });
        }
    });
    
    const accuracy = totalScoreQuestions > 0 ? Math.round((totalScore / totalScoreQuestions) * 100) : 0;
    
    let easyCount = 0;
    let mediumCount = 0;
    let hardCount = 0;
    
    Object.keys(questionDifficulties).forEach(subName => {
        if (questionDifficulties[subName]) {
            Object.keys(questionDifficulties[subName]).forEach(caseNo => {
                Object.keys(questionDifficulties[subName][caseNo]).forEach(qNo => {
                    const diff = questionDifficulties[subName][caseNo][qNo];
                    if (diff === 'easy') easyCount++;
                    else if (diff === 'medium') mediumCount++;
                    else if (diff === 'hard') hardCount++;
                });
            });
        }
    });
    
    if (completedCasesCount > 0 || easyCount > 0 || mediumCount > 0 || hardCount > 0) {
        statsPanel.style.display = "grid";
        document.getElementById("stat-completed").innerText = `${completedCasesCount}/${totalCases}`;
        document.getElementById("stat-accuracy").innerText = `${accuracy}%`;
        document.getElementById("stat-easy-count").innerText = `Easy: ${easyCount}`;
        document.getElementById("stat-medium-count").innerText = `Medium: ${mediumCount}`;
        document.getElementById("stat-hard-count").innerText = `Hard: ${hardCount}`;
    } else {
        statsPanel.style.display = "none";
    }
}

function handleLogout() {
    const confirmLogout = confirm("Are you sure you want to log out of the Candidate Portal?");
    if (!confirmLogout) return;
    
    try {
        localStorage.removeItem("ca_user_profile");
    } catch (e) {
        console.warn("[-] Failed to remove user profile from localStorage:", e);
    }
    userProfile = null;
    window.location.href = "login.html";
}

function resetAllData() {
    const confirmReset = confirm("⚠️ WARNING: This will permanently reset all your answers, case progress, highlights, and custom tags. Are you sure?");
    if (!confirmReset) return;
    
    try {
        localStorage.clear();
        console.log("[+] LocalStorage cleared successfully!");
        window.location.href = "login.html";
    } catch (e) {
        console.error("[-] Failed to clear localStorage:", e);
        alert("Failed to reset database. Make sure local storage is enabled.");
    }
}

function updateProfileUI() {
    if (userProfile) {
        document.getElementById("header-candidate-name").innerText = userProfile.name;
        document.getElementById("header-candidate-reg").innerText = `(${userProfile.regNo})`;
        document.getElementById("candidate-info-header").style.display = "flex";
    }
}

// Initial Routing / Load
document.addEventListener("DOMContentLoaded", init);
window.addEventListener("popstate", handleParamsRouting);
