/* ==========================================================================
   CA Case Scenario Solver - Main Application Logic
   ========================================================================== */

// Global State Variables
let currentLevel = null;        // 'Final' or 'Intermediate'
let currentSubject = null;      // Subject object from EXAM_DATABASE
let currentCase = null;         // Case scenario object
let currentMode = 'practice';    // 'practice' or 'exam'
let fontSize = 17;              // Base font size in px
let highlighterActive = false;  // Highlighter state

let userAnswers = {};           // Schema: { "Subject Name": { case_no: { q_no: "selected_opt" } } }
let progress = {};              // Schema: { "Subject Name": { case_no: { status: 'completed'|'in-progress', score: X, total: Y } } }
let questionDifficulties = {};  // Schema: { "Subject Name": { case_no: { q_no: 'easy'|'medium'|'hard' } } }

let layoutMode = 'single';      // 'single' or 'all'
let currentQuestionIndex = 0;   // 0-indexed question tracker for 'single' layout mode
let currentSidebarTab = 'cases'; // 'cases' or 'tags'
let currentTagFilter = 'all';    // 'all', 'easy', 'medium', 'hard'
let userProfile = null;         // Candidate profile: { name, regNo }

let examTimerInterval = null;
let examTimerSeconds = 0;
let isExamSubmitted = false;
let isPracticeSubmitted = false;

// Initialize Application
function init() {
    console.log("[+] Initializing CA MCQ Application...");
    
    // Load data from localStorage
    try {
        const storedAnswers = localStorage.getItem("ca_user_answers");
        if (storedAnswers) userAnswers = JSON.parse(storedAnswers);
        
        const storedProgress = localStorage.getItem("ca_user_progress");
        if (storedProgress) progress = JSON.parse(storedProgress);

        const storedDiffs = localStorage.getItem("ca_question_difficulties");
        if (storedDiffs) questionDifficulties = JSON.parse(storedDiffs);

        const storedProfile = localStorage.getItem("ca_user_profile");
        if (storedProfile) userProfile = JSON.parse(storedProfile);
    } catch (e) {
        console.error("[-] Error loading progress from localStorage:", e);
    }

    // Set up Event Listeners
    setupEventListeners();
    
    // Check if user is logged in
    if (userProfile) {
        updateProfileUI();
        showDashboard();
    } else {
        showLoginScreen();
    }
}

function setupEventListeners() {
    // Header controls
    document.getElementById("header-logo").addEventListener("click", goHome);
    document.getElementById("btn-dashboard").addEventListener("click", showDashboard);
    document.getElementById("btn-reset-all").addEventListener("click", resetAllData);
    
    // Login form submission
    document.getElementById("login-form").addEventListener("submit", (e) => {
        e.preventDefault();
        handleLogin();
    });
    
    // Logout button click
    document.getElementById("btn-logout").addEventListener("click", handleLogout);
    
    // Welcome / Level Cards
    const levelCards = document.querySelectorAll(".level-card");
    levelCards.forEach(card => {
        card.addEventListener("click", () => {
            const level = card.getAttribute("data-level");
            selectLevel(level);
        });
    });
    
    // Back to Levels button
    document.getElementById("btn-back-to-levels").addEventListener("click", () => {
        document.getElementById("subject-selector-screen").style.display = "none";
        document.getElementById("level-selector-screen").style.display = "block";
        currentLevel = null;
        updateBreadcrumbs();
    });

    // Font Controls
    document.getElementById("btn-font-inc").addEventListener("click", () => changeFontSize(1));
    document.getElementById("btn-font-dec").addEventListener("click", () => changeFontSize(-1));
    
    // Highlighter tool
    const highlighterBtn = document.getElementById("btn-toggle-highlighter");
    highlighterBtn.addEventListener("click", () => {
        highlighterActive = !highlighterActive;
        highlighterBtn.style.background = highlighterActive ? "var(--accent)" : "rgba(255, 235, 59, 0.2)";
        highlighterBtn.style.borderColor = highlighterActive ? "var(--accent)" : "rgb(255, 235, 59)";
        if (highlighterActive) {
            console.log("[+] Text Highlighter Activated");
        }
    });

    // Text highlighting mouseup trigger
    document.getElementById("case-text").addEventListener("mouseup", handleTextHighlight);

    // Search bar for case scenarios
    document.getElementById("search-cases").addEventListener("input", (e) => {
        renderSidebarList(e.target.value);
    });

    // Mode toggles
    document.getElementById("btn-mode-practice").addEventListener("click", () => setMode('practice'));
    document.getElementById("btn-mode-exam").addEventListener("click", () => setMode('exam'));

    // Layout toggles
    document.getElementById("btn-layout-single").addEventListener("click", () => setLayoutMode('single'));
    document.getElementById("btn-layout-all").addEventListener("click", () => setLayoutMode('all'));

    // Navigation buttons
    document.getElementById("btn-prev-q").addEventListener("click", () => navigateQuestion(-1));
    document.getElementById("btn-next-q").addEventListener("click", () => navigateQuestion(1));

    // Export Action Menu Dropdown Toggle
    const exportBtn = document.getElementById("btn-export-menu");
    const exportMenu = document.getElementById("export-menu");
    exportBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        exportMenu.classList.toggle("show");
    });
    
    // Close dropdown when clicking outside
    document.addEventListener("click", () => {
        exportMenu.classList.remove("show");
    });

    // Export actions trigger
    document.getElementById("export-case-csv").addEventListener("click", (e) => { e.preventDefault(); exportCaseToCSV(); });
    document.getElementById("export-case-pdf").addEventListener("click", (e) => { e.preventDefault(); window.print(); });
    document.getElementById("export-progress-csv").addEventListener("click", (e) => { e.preventDefault(); exportProgressReport(); });
    document.getElementById("export-backup-json").addEventListener("click", (e) => { e.preventDefault(); exportBackupJSON(); });
    
    // Backup Import triggers
    const fileInput = document.getElementById("import-backup-file");
    document.getElementById("import-backup-trigger").addEventListener("click", (e) => {
        e.preventDefault();
        fileInput.click();
    });
    fileInput.addEventListener("change", handleBackupImport);

    // Exam submit button
    document.getElementById("btn-submit-exam").addEventListener("click", submitExam);

    // Practice submit button
    document.getElementById("btn-submit-practice").addEventListener("click", submitPractice);

    // PDF button
    const btnOpenPdf = document.getElementById("btn-open-pdf");
    if (btnOpenPdf) {
        btnOpenPdf.addEventListener("click", () => {
            if (currentSubject && currentSubject.pdf_file) {
                const pdfUrl = getPureQuestionBankUrl(currentLevel, currentSubject.pdf_file);
                window.open(pdfUrl, '_blank');
            }
        });
    }

    // Sidebar Tabs Switcher
    document.getElementById("btn-sidebar-tab-cases").addEventListener("click", () => setSidebarTab('cases'));
    document.getElementById("btn-sidebar-tab-tags").addEventListener("click", () => setSidebarTab('tags'));

    // Tag Filters click handler
    const tagFilterBtns = document.querySelectorAll("#tag-filter-container .layout-toggle-btn");
    tagFilterBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            const filterVal = btn.getAttribute("data-filter");
            setTagFilter(filterVal);
        });
    });

    // Modal buttons
    document.getElementById("btn-modal-close").addEventListener("click", closeModal);
    document.getElementById("btn-modal-review").addEventListener("click", () => {
        closeModal();
        // Re-render questions in review state
        renderQuestions();
    });
}

// Navigation helpers
function goHome() {
    if (!userProfile) return;
    currentLevel = null;
    currentSubject = null;
    currentCase = null;
    document.getElementById("view-workspace").style.display = "none";
    document.getElementById("view-dashboard").style.display = "block";
    document.getElementById("subject-selector-screen").style.display = "none";
    document.getElementById("level-selector-screen").style.display = "block";
    updateBreadcrumbs();
}

function showDashboard() {
    if (!userProfile) {
        showLoginScreen();
        return;
    }
    currentCase = null;
    currentSubject = null;
    clearInterval(examTimerInterval);
    
    document.getElementById("view-workspace").style.display = "none";
    document.getElementById("view-dashboard").style.display = "block";
    
    if (currentLevel) {
        document.getElementById("level-selector-screen").style.display = "none";
        document.getElementById("subject-selector-screen").style.display = "block";
        buildSubjectList();
    } else {
        document.getElementById("level-selector-screen").style.display = "block";
        document.getElementById("subject-selector-screen").style.display = "none";
    }
    updateBreadcrumbs();
    
    // Update global dashboard stats
    updateDashboardStats();
}

function selectLevel(level) {
    currentLevel = level;
    document.getElementById("level-selector-screen").style.display = "none";
    document.getElementById("subject-selector-screen").style.display = "block";
    document.getElementById("level-heading").innerText = `CA ${level} - Subjects`;
    buildSubjectList();
    updateBreadcrumbs();
}

function selectSubject(subjectName) {
    if (!userProfile) return;
    if (!window.EXAM_DATABASE || !window.EXAM_DATABASE[currentLevel]) {
        alert("Exam database loading. Please refresh.");
        return;
    }
    
    const subjectList = window.EXAM_DATABASE[currentLevel];
    currentSubject = subjectList.find(s => s.subject === subjectName);
    
    if (!currentSubject) {
        alert("Subject not found!");
        return;
    }

    // Hide Dashboard, Show Split Workspace
    document.getElementById("view-dashboard").style.display = "none";
    document.getElementById("view-workspace").style.display = "flex";
    
    updateBreadcrumbs();
    
    // Clear search box
    document.getElementById("search-cases").value = "";
    
    // Load first case scenario
    if (currentSubject.cases && currentSubject.cases.length > 0) {
        selectCase(currentSubject.cases[0].case_no);
    } else {
        document.getElementById("case-title").innerText = "No cases available";
        document.getElementById("case-text").innerText = "No case scenarios parsed for this subject.";
        document.getElementById("questions-list-container").innerHTML = "";
    }
}

function selectCase(caseNo) {
    if (!userProfile) return;
    currentCase = currentSubject.cases.find(c => c.case_no === caseNo);
    if (!currentCase) return;
    
    isExamSubmitted = false;
    isPracticeSubmitted = false;
    clearInterval(examTimerInterval);
    
    // Check if previously completed to restore submitted state
    if (progress[currentSubject.subject] && progress[currentSubject.subject][caseNo]) {
        const cProg = progress[currentSubject.subject][caseNo];
        if (cProg.status === 'completed') {
            if (currentMode === 'practice') {
                isPracticeSubmitted = true;
            } else {
                isExamSubmitted = true;
            }
        }
    }
    
    // Reset active question navigation index
    currentQuestionIndex = 0;
    
    // Update active state in sidebar
    renderSidebarList(document.getElementById("search-cases").value);
    
    // Render Case text on the left
    document.getElementById("case-title").innerText = `Case Scenario ${currentCase.case_no}`;
    
    // Render content: support custom highlighter HTML persistence if exists, else load standard formatted description
    const savedHtml = localStorage.getItem(`highlight_${currentSubject.subject}_${currentCase.case_no}`);
    document.getElementById("case-text").innerHTML = savedHtml || formatDescription(currentCase.description);
    
    // Reset Scroll
    document.getElementById("pane-description").scrollTop = 0;
    document.getElementById("pane-questions").scrollTop = 0;
    
    // Show/hide PDF button
    if (currentSubject.pdf_file) {
        document.getElementById("btn-open-pdf").style.display = "inline-flex";
    } else {
        document.getElementById("btn-open-pdf").style.display = "none";
    }
    
    // Setup Mode Configuration
    if (currentMode === 'exam') {
        startExamTimer();
        document.getElementById("exam-timer").style.display = "flex";
        document.getElementById("exam-submit-container").style.display = isExamSubmitted ? "none" : "block";
        document.getElementById("practice-submit-container").style.display = "none";
        document.getElementById("tag-filter-container").style.display = isExamSubmitted ? "flex" : "none";
    } else {
        document.getElementById("exam-timer").style.display = "none";
        document.getElementById("exam-submit-container").style.display = "none";
        document.getElementById("practice-submit-container").style.display = isPracticeSubmitted ? "none" : "block";
        document.getElementById("tag-filter-container").style.display = "flex";
    }
    
    // Render questions on the right
    renderQuestions();
}

function setMode(mode) {
    if (currentMode === mode) return;
    
    if (mode === 'exam' && !isExamSubmitted) {
        const confirmExam = confirm("Switching to Exam Mode will start a timed mock exam and hide direct answers/workings. Ready to start?");
        if (!confirmExam) return;
    }
    
    currentMode = mode;
    document.getElementById("btn-mode-practice").classList.toggle("active", mode === 'practice');
    document.getElementById("btn-mode-exam").classList.toggle("active", mode === 'exam');
    
    if (currentCase) {
        selectCase(currentCase.case_no);
    }
}

// Rendering UI Components
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

function renderCaseList(filterText = "") {
    const container = document.getElementById("case-list-container");
    container.innerHTML = "";
    
    if (!currentSubject || !currentSubject.cases) return;
    
    const filter = filterText.toLowerCase().trim();
    
    currentSubject.cases.forEach(c => {
        // Simple search logic: Match title, description, or question text
        const matchTitle = `case scenario ${c.case_no}`.includes(filter);
        const matchDesc = c.description.toLowerCase().includes(filter);
        const matchQ = c.questions.some(q => q.question_text.toLowerCase().includes(filter));
        
        if (filter && !matchTitle && !matchDesc && !matchQ) return;
        
        const item = document.createElement("div");
        item.className = `case-item ${currentCase && currentCase.case_no === c.case_no ? 'active' : ''}`;
        
        // Find progress status
        let statusClass = "status-not-started";
        if (progress[currentSubject.subject] && progress[currentSubject.subject][c.case_no]) {
            const stat = progress[currentSubject.subject][c.case_no].status;
            if (stat === 'completed') statusClass = "status-completed";
            else if (stat === 'in-progress') statusClass = "status-in-progress";
        }
        
        item.innerHTML = `
            <span class="case-item-title">Case Scenario ${c.case_no}</span>
            <span class="case-item-status ${statusClass}" title="${statusClass.replace('status-', '').replace('-', ' ')}"></span>
        `;
        
        item.addEventListener("click", () => selectCase(c.case_no));
        container.appendChild(item);
    });
}

function renderQuestions() {
    const container = document.getElementById("questions-list-container");
    container.innerHTML = "";
    
    if (!currentCase || !currentCase.questions) return;
    
    const subjectName = currentSubject.subject;
    const caseNo = currentCase.case_no;
    
    // Filter questions by tag if filter is active
    let questionsToRender = currentCase.questions;
    if (currentTagFilter !== 'all') {
        questionsToRender = currentCase.questions.filter(q => {
            const savedDiff = (questionDifficulties[subjectName] && questionDifficulties[subjectName][caseNo])
                ? questionDifficulties[subjectName][caseNo][q.q_no]
                : null;
            return savedDiff === currentTagFilter;
        });
    }
    
    if (questionsToRender.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; padding: 3rem; color: var(--text-muted); background: var(--bg-card); border: 1px solid var(--border); border-radius: 0.75rem; margin-top: 1rem; width: 100%; max-width: 900px;">
                <span style="font-size: 3rem;">🏷️</span>
                <h3 style="margin-top: 1rem; color: var(--text-main); font-size: 1.5rem;">No Questions Found</h3>
                <p style="margin-top: 0.5rem; font-size: 0.95rem;">No questions in this case scenario have been tagged as <strong>${currentTagFilter.toUpperCase()}</strong>.</p>
            </div>
        `;
        document.getElementById("single-question-navigation").style.display = "none";
        return;
    }
    
    // Setup questions depending on Single vs All Layout Mode
    if (layoutMode === 'single') {
        if (currentQuestionIndex >= questionsToRender.length) {
            currentQuestionIndex = questionsToRender.length - 1;
        }
        if (currentQuestionIndex < 0) {
            currentQuestionIndex = 0;
        }
        questionsToRender = [questionsToRender[currentQuestionIndex]];
        document.getElementById("single-question-navigation").style.display = "flex";
        renderQuestionNavigationGrid(currentCase.questions.filter(q => {
            if (currentTagFilter === 'all') return true;
            const savedDiff = (questionDifficulties[subjectName] && questionDifficulties[subjectName][caseNo])
                ? questionDifficulties[subjectName][caseNo][q.q_no]
                : null;
            return savedDiff === currentTagFilter;
        }));
    } else {
        document.getElementById("single-question-navigation").style.display = "none";
    }
    
    questionsToRender.forEach((q, qIndex) => {
        const qBlock = document.createElement("div");
        qBlock.className = "question-block";
        
        // Find saved option selection
        const savedOpt = (userAnswers[subjectName] && userAnswers[subjectName][caseNo]) 
            ? userAnswers[subjectName][caseNo][q.q_no] 
            : null;
            
        // Build option buttons
        let optionsHtml = "";
        const optionKeys = ['a', 'b', 'c', 'd'];
        
        optionKeys.forEach(key => {
            const optVal = q.options[key];
            if (!optVal) return; // Skip if option letter is empty (should not happen)
            
            let btnClass = "";
            
            if (currentMode === 'practice') {
                if (isPracticeSubmitted) {
                    // Show correctness after practice submission
                    if (savedOpt === key) {
                        btnClass = (key === q.correct_option) ? "correct selected" : "incorrect selected";
                    } else if (savedOpt && key === q.correct_option) {
                        btnClass = "correct";
                    }
                } else {
                    // Only show selected option before practice submission
                    if (savedOpt === key) {
                        btnClass = "selected";
                    }
                }
            } else {
                // In Exam mode
                if (isExamSubmitted) {
                    // Review answers after submission
                    if (savedOpt === key) {
                        btnClass = (key === q.correct_option) ? "correct selected" : "incorrect selected";
                    } else if (key === q.correct_option) {
                        btnClass = "correct";
                    }
                } else {
                    // Regular timed solving selection
                    if (savedOpt === key) {
                        btnClass = "selected";
                    }
                }
            }
            
            optionsHtml += `
                <button class="option-btn ${btnClass}" data-q="${q.q_no}" data-opt="${key}">
                    <span class="option-letter">${key.toUpperCase()}</span>
                    <span>${optVal}</span>
                </button>
            `;
        });
        
        // Build Feedback reasoning panel (shown in Practice Mode or post-Exam Review)
        let feedbackHtml = "";
        const showFeedback = (currentMode === 'practice' && isPracticeSubmitted && savedOpt) || (currentMode === 'exam' && isExamSubmitted);
        
        if (showFeedback) {
            const isCorrect = savedOpt === q.correct_option;
            const correctText = q.options[q.correct_option] || q.value_text || "";
            const reason = q.reasoning || "No detailed calculation provided in the original answers booklet.";
            
            feedbackHtml = `
                <div class="feedback-box">
                    <div class="feedback-header ${isCorrect ? 'correct' : 'incorrect'}">
                        <span>${isCorrect ? '✅ Correct' : '❌ Incorrect'}</span>
                        <span style="color: var(--text-main); font-weight: 500; font-size: 0.9rem; margin-left: 0.5rem;">
                            Correct Option: <strong>(${q.correct_option.toUpperCase()})</strong> ${correctText}
                        </span>
                    </div>
                    ${reason ? `<div class="feedback-reason"><strong>Reasoning / Calculation:</strong><br>${reason.replace(/ \| /g, '<br>')}</div>` : ''}
                </div>
            `;
        }
        
        // Build Difficulty Tagging controls
        let difficultyHtml = "";
        if (currentMode === 'practice' || isExamSubmitted) {
            const savedDiff = (questionDifficulties[subjectName] && questionDifficulties[subjectName][caseNo])
                ? questionDifficulties[subjectName][caseNo][q.q_no]
                : null;
                
            difficultyHtml = `
                <div class="difficulty-selector">
                    <span class="difficulty-label">Tag:</span>
                    <button class="difficulty-btn easy ${savedDiff === 'easy' ? 'active' : ''}" data-q="${q.q_no}" data-diff="easy">Easy</button>
                    <button class="difficulty-btn medium ${savedDiff === 'medium' ? 'active' : ''}" data-q="${q.q_no}" data-diff="medium">Medium</button>
                    <button class="difficulty-btn hard ${savedDiff === 'hard' ? 'active' : ''}" data-q="${q.q_no}" data-diff="hard">Hard</button>
                </div>
            `;
        }
        
        // Find current question difficulty
        const currentDiff = (questionDifficulties[subjectName] && questionDifficulties[subjectName][caseNo])
            ? questionDifficulties[subjectName][caseNo][q.q_no]
            : null;
        let diffBadgeHtml = "";
        if (currentDiff) {
            diffBadgeHtml = `<span class="q-diff-indicator ${currentDiff}">${currentDiff}</span>`;
        }
        
        qBlock.innerHTML = `
            <div class="question-meta-row">
                <span class="q-badge">Q ${q.q_no}</span>
                ${diffBadgeHtml}
            </div>
            <div class="question-header">
                <span class="q-text">${q.question_text}</span>
            </div>
            <div class="options-list">
                ${optionsHtml}
            </div>
            ${feedbackHtml}
            ${difficultyHtml}
        `;
        
        // Attach click handlers to options (only if solving is active)
        const optButtons = qBlock.querySelectorAll(".option-btn");
        optButtons.forEach(btn => {
            btn.addEventListener("click", () => {
                if (currentMode === 'exam' && isExamSubmitted) return; // Locked after exam submission
                if (currentMode === 'practice' && isPracticeSubmitted) return; // Locked after practice submission
                const optSelected = btn.getAttribute("data-opt");
                handleOptionSelection(q.q_no, optSelected);
            });
        });
        
        // Attach click handlers to difficulty buttons
        const diffButtons = qBlock.querySelectorAll(".difficulty-btn");
        diffButtons.forEach(btn => {
            btn.addEventListener("click", () => {
                const diffSelected = btn.getAttribute("data-diff");
                handleDifficultySelection(q.q_no, diffSelected);
            });
        });
        
        container.appendChild(qBlock);
    });
}

function handleOptionSelection(qNo, option) {
    const subjectName = currentSubject.subject;
    const caseNo = currentCase.case_no;
    
    // Update local variables
    if (!userAnswers[subjectName]) userAnswers[subjectName] = {};
    if (!userAnswers[subjectName][caseNo]) userAnswers[subjectName][caseNo] = {};
    
    const prevAnswer = userAnswers[subjectName][caseNo][qNo];
    
    // Select/Deselect option logic
    if (prevAnswer === option && currentMode === 'exam') {
        // Toggle off in exam mode if clicked again
        delete userAnswers[subjectName][caseNo][qNo];
    } else {
        userAnswers[subjectName][caseNo][qNo] = option;
    }
    
    // Save to storage
    localStorage.setItem("ca_user_answers", JSON.stringify(userAnswers));
    
    // Update Progress status
    updateProgressStatus();
    
    // Re-render
    renderQuestions();
}

function updateProgressStatus() {
    const subjectName = currentSubject.subject;
    const caseNo = currentCase.case_no;
    const totalQuestions = currentCase.questions.length;
    
    const answeredCount = Object.keys(userAnswers[subjectName][caseNo] || {}).length;
    
    if (!progress[subjectName]) progress[subjectName] = {};
    
    if (answeredCount === 0) {
        delete progress[subjectName][caseNo];
    } else {
        const currentProg = progress[subjectName][caseNo];
        if (currentProg && currentProg.status === 'completed') {
            // If already completed/submitted, update the score
            let score = 0;
            currentCase.questions.forEach(q => {
                const userAns = userAnswers[subjectName][caseNo][q.q_no];
                if (userAns === q.correct_option) score++;
            });
            progress[subjectName][caseNo] = {
                status: 'completed',
                score: score,
                total: totalQuestions
            };
        } else {
            // Keep status as 'in-progress' until explicitly submitted
            progress[subjectName][caseNo] = {
                status: 'in-progress',
                answered: answeredCount,
                total: totalQuestions
            };
        }
    }
    
    localStorage.setItem("ca_user_progress", JSON.stringify(progress));
    
    // Update sidebar counts
    renderSidebarList(document.getElementById("search-cases").value);
}

// Highlighter tools
function handleTextHighlight() {
    if (!highlighterActive) return;
    
    const selection = window.getSelection();
    if (!selection.rangeCount || selection.isCollapsed) return;
    
    const range = selection.getRangeAt(0);
    const span = document.createElement("span");
    span.className = "highlight-yellow";
    
    try {
        range.surroundContents(span);
        selection.removeAllRanges();
        
        // Save the full HTML of case text to persist highlights
        const htmlContent = document.getElementById("case-text").innerHTML;
        localStorage.setItem(`highlight_${currentSubject.subject}_${currentCase.case_no}`, htmlContent);
        console.log("[+] Saved highlights to localStorage");
    } catch (e) {
        console.warn("[-] Selection complex. Try smaller selections.", e);
    }
}

// Timer for Exam Mode
function startExamTimer() {
    examTimerSeconds = 0;
    updateTimerUI();
    
    clearInterval(examTimerInterval);
    examTimerInterval = setInterval(() => {
        examTimerSeconds++;
        updateTimerUI();
    }, 1000);
}

function updateTimerUI() {
    const min = Math.floor(examTimerSeconds / 60).toString().padStart(2, '0');
    const sec = (examTimerSeconds % 60).toString().padStart(2, '0');
    document.getElementById("timer-value").innerText = `${min}:${sec}`;
}

// Exam Submission
function submitExam() {
    const subjectName = currentSubject.subject;
    const caseNo = currentCase.case_no;
    const totalQuestions = currentCase.questions.length;
    
    const answeredAnswers = userAnswers[subjectName] && userAnswers[subjectName][caseNo] 
        ? userAnswers[subjectName][caseNo] 
        : {};
    const answeredCount = Object.keys(answeredAnswers).length;
    
    if (answeredCount < totalQuestions) {
        const confirmIncomplete = confirm(`You have only answered ${answeredCount}/${totalQuestions} questions. Are you sure you want to submit and end the exam?`);
        if (!confirmIncomplete) return;
    }
    
    clearInterval(examTimerInterval);
    isExamSubmitted = true;
    
    // Calculate final score
    let score = 0;
    currentCase.questions.forEach(q => {
        const userAns = answeredAnswers[q.q_no];
        if (userAns === q.correct_option) score++;
    });
    
    // Save completion progress
    if (!progress[subjectName]) progress[subjectName] = {};
    progress[subjectName][caseNo] = {
        status: 'completed',
        score: score,
        total: totalQuestions,
        time_taken: examTimerSeconds
    };
    
    localStorage.setItem("ca_user_progress", JSON.stringify(progress));
    
    // Hide Timer & Submission controls
    document.getElementById("exam-timer").style.display = "none";
    document.getElementById("exam-submit-container").style.display = "none";
    
    // Trigger results modal
    openResultModal(score, totalQuestions);
    
    // Refresh sidebar status dots
    renderSidebarList(document.getElementById("search-cases").value);
}

// Practice Submission
function submitPractice() {
    const subjectName = currentSubject.subject;
    const caseNo = currentCase.case_no;
    const totalQuestions = currentCase.questions.length;
    
    const answeredAnswers = userAnswers[subjectName] && userAnswers[subjectName][caseNo] 
        ? userAnswers[subjectName][caseNo] 
        : {};
    const answeredCount = Object.keys(answeredAnswers).length;
    
    if (answeredCount < totalQuestions) {
        const confirmIncomplete = confirm(`You have only answered ${answeredCount}/${totalQuestions} questions. Would you like to complete this case scenario and calculate your marks anyway?`);
        if (!confirmIncomplete) return;
    } else {
        const confirmSubmit = confirm("Would you like to complete this case scenario and calculate your marks?");
        if (!confirmSubmit) return;
    }
    
    isPracticeSubmitted = true;
    
    // Calculate final score
    let score = 0;
    currentCase.questions.forEach(q => {
        const userAns = answeredAnswers[q.q_no];
        if (userAns === q.correct_option) score++;
    });
    
    // Save completion progress
    if (!progress[subjectName]) progress[subjectName] = {};
    progress[subjectName][caseNo] = {
        status: 'completed',
        score: score,
        total: totalQuestions
    };
    
    localStorage.setItem("ca_user_progress", JSON.stringify(progress));
    
    // Hide Practice Submission controls
    document.getElementById("practice-submit-container").style.display = "none";
    
    // Trigger results modal
    openResultModal(score, totalQuestions);
    
    // Refresh sidebar status dots
    renderSidebarList(document.getElementById("search-cases").value);
    
    // Render questions to show correctness & reasoning
    renderQuestions();
}

function openResultModal(score, total) {
    const percent = Math.round((score / total) * 100);
    
    // Set score text
    document.getElementById("modal-score-num").innerText = `${score}/${total}`;
    
    // Tailor heading and subtitle based on score performance
    const titleEl = document.getElementById("modal-title");
    const subEl = document.getElementById("modal-subtitle");
    
    if (percent === 100) {
        titleEl.innerText = "⭐ Perfect Score! ⭐";
        subEl.innerText = "Flawless execution! You scored 100% on this case scenario.";
    } else if (percent >= 70) {
        titleEl.innerText = "🎉 Outstanding! 🎉";
        subEl.innerText = `Great job! You passed with ${percent}%. Review explanations to lock in a perfect score next time.`;
    } else if (percent >= 40) {
        titleEl.innerText = "👍 Passed 👍";
        subEl.innerText = `You scored ${percent}%. You passed, but review the explanations to master the edge cases.`;
    } else {
        titleEl.innerText = "📚 Keep Studying 📚";
        subEl.innerText = `You scored ${percent}%. Practice makes perfect. Review the reasons to understand your mistakes!`;
    }
    
    document.getElementById("result-modal").classList.add("active");
}

function closeModal() {
    document.getElementById("result-modal").classList.remove("active");
}

// Reset functions
function resetAllData() {
    const confirmReset = confirm("⚠️ WARNING: This will delete all your scores, saved highlights, and answers. This action CANNOT be undone. Are you sure you want to delete everything?");
    if (confirmReset) {
        localStorage.clear();
        userAnswers = {};
        progress = {};
        console.log("[+] LocalStorage cleared successfully!");
        location.reload();
    }
}

// Font adjustments
function changeFontSize(delta) {
    fontSize = Math.max(13, Math.min(28, fontSize + delta));
    document.getElementById("case-text").style.fontSize = `${fontSize}px`;
    console.log(`[+] Font size changed to ${fontSize}px`);
}

function updateBreadcrumbs() {
    const levelBreadcrumb = document.getElementById("breadcrumb-level");
    const subjectBreadcrumb = document.getElementById("breadcrumb-subject");
    
    if (currentLevel) {
        levelBreadcrumb.innerText = `CA ${currentLevel}`;
        levelBreadcrumb.style.display = "inline";
    } else {
        levelBreadcrumb.style.display = "none";
    }
    
    if (currentSubject) {
        subjectBreadcrumb.innerText = ` > ${currentSubject.subject}`;
        subjectBreadcrumb.style.display = "inline";
    } else {
        subjectBreadcrumb.style.display = "none";
    }
}

function getPureQuestionBankUrl(level, pdfFile) {
    if (level === 'Final') {
        const finalMap = {
            "90961bos-aps4227-p1.pdf": "FR_Pure_Question_Bank_Final.pdf",
            "90962bos-aps4227-p2.pdf": "AFM_QB.pdf",
            "90963bos-aps4227-p3.pdf": "Audit_Pure_Question_Bank_Final.pdf",
            "90964bos-aps4227-p4.pdf": "DT_Pure_Question_Bank.pdf",
            "90965bos-aps4227-p5.pdf": "IDT_Pure_Question_Bank.pdf"
        };
        const mapped = finalMap[pdfFile] || pdfFile;
        return `../data/final/${mapped}`;
    } else {
        // CA Intermediate
        const baseName = pdfFile.replace(/\.pdf$/i, "");
        return `../data/intermediate/Pure Question Bank/${baseName}_Pure_Question_Bank.pdf`;
    }
}

/* ==========================================================================
   New Feature Implementation Helpers
   ========================================================================== */

// 1. Layout Mode Setting & Question Navigation
function setLayoutMode(mode) {
    if (layoutMode === mode) return;
    layoutMode = mode;
    
    document.getElementById("btn-layout-single").classList.toggle("active", mode === 'single');
    document.getElementById("btn-layout-all").classList.toggle("active", mode === 'all');
    
    renderQuestions();
}

function navigateQuestion(direction) {
    if (!currentCase || !currentCase.questions) return;
    
    currentQuestionIndex += direction;
    if (currentQuestionIndex < 0) {
        currentQuestionIndex = 0;
    } else if (currentQuestionIndex >= currentCase.questions.length) {
        currentQuestionIndex = currentCase.questions.length - 1;
    }
    
    renderQuestions();
}

function renderQuestionNavigationGrid(filteredList) {
    const grid = document.getElementById("q-nav-grid");
    grid.innerHTML = "";
    
    if (!filteredList) return;
    
    const subjectName = currentSubject.subject;
    const caseNo = currentCase.case_no;
    
    filteredList.forEach((q, idx) => {
        const btn = document.createElement("button");
        btn.className = "q-nav-btn";
        btn.innerText = q.q_no;
        
        if (idx === currentQuestionIndex) {
            btn.classList.add("active");
        }
        
        const isAnswered = (userAnswers[subjectName] && userAnswers[subjectName][caseNo] && userAnswers[subjectName][caseNo][q.q_no]);
        if (isAnswered) {
            btn.classList.add("answered");
        }
        
        btn.addEventListener("click", () => {
            currentQuestionIndex = idx;
            renderQuestions();
        });
        
        grid.appendChild(btn);
    });
}

// 2. Difficulty Tagging handler
function handleDifficultySelection(qNo, difficulty) {
    const subjectName = currentSubject.subject;
    const caseNo = currentCase.case_no;
    
    if (!questionDifficulties[subjectName]) questionDifficulties[subjectName] = {};
    if (!questionDifficulties[subjectName][caseNo]) questionDifficulties[subjectName][caseNo] = {};
    
    const prevDiff = questionDifficulties[subjectName][caseNo][qNo];
    if (prevDiff === difficulty) {
        delete questionDifficulties[subjectName][caseNo][qNo];
    } else {
        questionDifficulties[subjectName][caseNo][qNo] = difficulty;
    }
    
    localStorage.setItem("ca_question_difficulties", JSON.stringify(questionDifficulties));
    renderQuestions();
    renderSidebarList(document.getElementById("search-cases").value);
}

// 3. Global Stats Calculator
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

// 4. Case Description Beautiful Formatting Engine
function formatDescription(desc) {
    if (!desc) return "";
    
    let text = desc.replace(/`/g, '₹').replace(/\u20b9/g, '₹');
    const lines = text.split('\n');
    let formattedHtml = "";
    let inList = false;
    let listType = null;
    let tableLines = [];
    let inTable = false;
    
    function closeList() {
        if (inList) {
            formattedHtml += `</${listType}>`;
            inList = false;
            listType = null;
        }
    }
    
    function closeTable() {
        if (inTable && tableLines.length > 0) {
            formattedHtml += renderHtmlTable(tableLines);
            inTable = false;
            tableLines = [];
        }
    }
    
    for (let i = 0; i < lines.length; i++) {
        let line = lines[i].trim();
        if (!line) {
            closeList();
            closeTable();
            continue;
        }
        
        const bulletMatch = line.match(/^([♦•\-*]|\d+\.|\([a-z]\))\s*(.*)/i);
        const tabSeparatedParts = line.split(/\s{2,}|\t|\|/);
        const isTableLine = tabSeparatedParts.length >= 3 || (tabSeparatedParts.length === 2 && line.includes('₹') && /\d+/.test(line));
        
        if (isTableLine && !bulletMatch) {
            closeList();
            inTable = true;
            tableLines.push(tabSeparatedParts);
            continue;
        } else {
            closeTable();
        }
        
        if (bulletMatch) {
            const marker = bulletMatch[1];
            const content = bulletMatch[2];
            let type = 'ul';
            if (/^\d+\.$/.test(marker)) type = 'ol';
            
            if (inList && listType !== type) {
                closeList();
            }
            
            if (!inList) {
                formattedHtml += `<${type}>`;
                inList = true;
                listType = type;
            }
            
            formattedHtml += `<li>${highlightFinancials(content)}</li>`;
        } else {
            closeList();
            formattedHtml += `<p>${highlightFinancials(line)}</p>`;
        }
    }
    
    closeList();
    closeTable();
    
    return formattedHtml;
}

function highlightFinancials(text) {
    return text.replace(/(₹\s*\d+(?:,\d+)*(?:\.\d+)?(?:\s*(?:Lakhs|Crore|L|Cr|million|billion))?)/gi, '<span class="currency-highlight">$1</span>');
}

function renderHtmlTable(rows) {
    let html = "<table>";
    const firstRowHasDigits = rows[0].some(cell => /^\d+(?:,\d+)*(?:\.\d+)?$/.test(cell.trim()));
    const hasHeader = !firstRowHasDigits;
    
    let startIndex = 0;
    if (hasHeader) {
        html += "<thead><tr>";
        rows[0].forEach(cell => {
            html += `<th>${cell.trim()}</th>`;
        });
        html += "</tr></thead>";
        startIndex = 1;
    }
    
    html += "<tbody>";
    for (let i = startIndex; i < rows.length; i++) {
        html += "<tr>";
        rows[i].forEach(cell => {
            let cellText = cell.trim();
            if (/^\d+(?:,\d+)*(?:\.\d+)?$/.test(cellText)) {
                html += `<td style="text-align: right; font-weight: 500;">${cellText}</td>`;
            } else {
                html += `<td>${highlightFinancials(cellText)}</td>`;
            }
        });
        html += "</tr>";
    }
    html += "</tbody></table>";
    return html;
}

// 5. Various Export Capabilities
function exportCaseToCSV() {
    if (!currentCase || !currentCase.questions) return;
    
    let csvContent = "\ufeff"; // BOM for excel utf8 reading
    csvContent += "Question Number,Question Text,Option A,Option B,Option C,Option D,Correct Option,Explanation/Reasoning\n";
    
    currentCase.questions.forEach(q => {
        const cleanQ = (q.question_text || "").replace(/"/g, '""');
        const optA = (q.options.a || "").replace(/"/g, '""');
        const optB = (q.options.b || "").replace(/"/g, '""');
        const optC = (q.options.c || "").replace(/"/g, '""');
        const optD = (q.options.d || "").replace(/"/g, '""');
        const correct = (q.correct_option || "").toUpperCase();
        const reasoning = (q.reasoning || "").replace(/"/g, '""').replace(/ \| /g, '\n');
        
        csvContent += `"${q.q_no}","${cleanQ}","${optA}","${optB}","${optC}","${optD}","${correct}","${reasoning}"\n`;
    });
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement("a");
    const url = URL.createObjectURL(blob);
    link.setAttribute("href", url);
    link.setAttribute("download", `${currentSubject.subject.replace(/[: ]/g, '_')}_Case_${currentCase.case_no}_Questions.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

function exportProgressReport() {
    let csvContent = "\ufeff"; // BOM for UTF-8 compatibility
    csvContent += "Subject,Case Scenario,Status,Score,Total Questions,Time Taken (Seconds),Accuracy\n";
    
    Object.keys(progress).forEach(subName => {
        if (progress[subName]) {
            Object.keys(progress[subName]).forEach(caseNo => {
                const p = progress[subName][caseNo];
                if (!p) return;
                const status = p.status || "";
                const score = p.score || 0;
                const total = p.total || 0;
                const time = p.time_taken || "N/A";
                const acc = total > 0 ? `${Math.round((score / total) * 100)}%` : "0%";
                
                csvContent += `"${subName}","Case Scenario ${caseNo}","${status}","${score}","${total}","${time}","${acc}"\n`;
            });
        }
    });
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement("a");
    const url = URL.createObjectURL(blob);
    link.setAttribute("href", url);
    link.setAttribute("download", "CA_MCQ_Portal_Progress_Report.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

function exportBackupJSON() {
    const backupData = {
        userAnswers: userAnswers,
        progress: progress,
        questionDifficulties: questionDifficulties,
        highlights: {}
    };
    
    for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key && key.startsWith("highlight_")) {
            backupData.highlights[key] = localStorage.getItem(key);
        }
    }
    
    const blob = new Blob([JSON.stringify(backupData, null, 2)], { type: 'application/json' });
    const link = document.createElement("a");
    const url = URL.createObjectURL(blob);
    link.setAttribute("href", url);
    link.setAttribute("download", "CA_MCQ_Portal_Data_Backup.json");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

function handleBackupImport(e) {
    const file = e.target.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = function(evt) {
        try {
            const backup = JSON.parse(evt.target.result);
            if (backup.userAnswers) {
                localStorage.setItem("ca_user_answers", JSON.stringify(backup.userAnswers));
            }
            if (backup.progress) {
                localStorage.setItem("ca_user_progress", JSON.stringify(backup.progress));
            }
            if (backup.questionDifficulties) {
                localStorage.setItem("ca_question_difficulties", JSON.stringify(backup.questionDifficulties));
            }
            if (backup.highlights) {
                Object.keys(backup.highlights).forEach(key => {
                    localStorage.setItem(key, backup.highlights[key]);
                });
            }
            alert("🎉 Backup data imported successfully! Page will now reload.");
            location.reload();
        } catch (err) {
            alert("❌ Failed to parse backup file. Please ensure it is a valid backup JSON.");
        }
    };
    reader.readAsText(file);
}

// Sidebar Tab switcher & Tag grouped renders
function setSidebarTab(tab) {
    if (currentSidebarTab === tab) return;
    currentSidebarTab = tab;
    
    document.getElementById("btn-sidebar-tab-cases").classList.toggle("active", tab === 'cases');
    document.getElementById("btn-sidebar-tab-tags").classList.toggle("active", tab === 'tags');
    
    document.getElementById("search-cases").value = "";
    renderSidebarList();
}

function renderSidebarList(filterText = "") {
    if (currentSidebarTab === 'cases') {
        renderCaseList(filterText);
    } else {
        renderTagGroupedList(filterText);
    }
}

function renderTagGroupedList(filterText = "") {
    const container = document.getElementById("case-list-container");
    container.innerHTML = "";
    
    if (!currentSubject || !currentSubject.cases) return;
    
    const filter = filterText.toLowerCase().trim();
    const subjectName = currentSubject.subject;
    
    const easyQs = [];
    const mediumQs = [];
    const hardQs = [];
    
    currentSubject.cases.forEach(c => {
        c.questions.forEach(q => {
            const tag = (questionDifficulties[subjectName] && questionDifficulties[subjectName][c.case_no])
                ? questionDifficulties[subjectName][c.case_no][q.q_no]
                : null;
                
            if (!tag) return;
            
            const matchText = q.question_text.toLowerCase().includes(filter) || `case ${c.case_no} q${q.q_no}`.includes(filter);
            if (filter && !matchText) return;
            
            const qInfo = {
                case_no: c.case_no,
                q_no: q.q_no,
                question_text: q.question_text
            };
            
            if (tag === 'easy') easyQs.push(qInfo);
            else if (tag === 'medium') mediumQs.push(qInfo);
            else if (tag === 'hard') hardQs.push(qInfo);
        });
    });
    
    function renderGroupHeader(title, count, colorClass) {
        const header = document.createElement("div");
        header.style.padding = "0.75rem 1rem 0.25rem 1.25rem";
        header.style.fontSize = "0.8rem";
        header.style.fontWeight = "800";
        header.style.textTransform = "uppercase";
        header.style.color = `var(--${colorClass})`;
        header.style.borderBottom = "1px dashed var(--border)";
        header.style.marginTop = "0.75rem";
        header.innerText = `${title} (${count})`;
        container.appendChild(header);
    }
    
    function renderGroupItems(items, colorClass) {
        if (items.length === 0) {
            const empty = document.createElement("div");
            empty.style.padding = "0.5rem 1.25rem";
            empty.style.fontSize = "0.8rem";
            empty.style.color = "var(--text-muted)";
            empty.style.fontStyle = "italic";
            empty.innerText = "No questions tagged.";
            container.appendChild(empty);
            return;
        }
        
        items.forEach(item => {
            const div = document.createElement("div");
            div.className = "case-item";
            
            const isCurrentCase = currentCase && currentCase.case_no === item.case_no;
            let isCurrentQ = false;
            if (isCurrentCase && layoutMode === 'single') {
                const activeQ = currentCase.questions[currentQuestionIndex];
                if (activeQ && activeQ.q_no === item.q_no) {
                    isCurrentQ = true;
                }
            } else if (isCurrentCase && layoutMode === 'all') {
                isCurrentQ = true;
            }
            
            if (isCurrentQ) {
                div.classList.add("active");
            }
            
            div.innerHTML = `
                <div style="display: flex; flex-direction: column; width: 100%;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-weight: 700; font-size: 0.85rem; color: var(--primary);">Case ${item.case_no} - Q ${item.q_no}</span>
                        <span class="q-diff-indicator ${colorClass}" style="font-size: 0.65rem; padding: 0.1rem 0.3rem;">${colorClass}</span>
                    </div>
                    <span style="font-size: 0.8rem; color: var(--text-muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; margin-top: 0.2rem;">${item.question_text}</span>
                </div>
            `;
            
            div.addEventListener("click", () => {
                if (!currentCase || currentCase.case_no !== item.case_no) {
                    selectCase(item.case_no);
                }
                
                if (currentCase) {
                    const qIndex = currentCase.questions.findIndex(q => q.q_no === item.q_no);
                    if (qIndex !== -1) {
                        currentQuestionIndex = qIndex;
                        renderQuestions();
                    }
                }
                
                renderSidebarList(filterText);
            });
            
            container.appendChild(div);
        });
    }
    
    renderGroupHeader("🔴 Hard Questions", hardQs.length, "error");
    renderGroupItems(hardQs, "hard");
    
    renderGroupHeader("🟡 Medium Questions", mediumQs.length, "warning");
    renderGroupItems(mediumQs, "medium");
    
    renderGroupHeader("🟢 Easy Questions", easyQs.length, "success");
    renderGroupItems(easyQs, "easy");
}

function setTagFilter(filter) {
    if (currentTagFilter === filter) return;
    currentTagFilter = filter;
    
    const tagFilterButtons = document.querySelectorAll("#tag-filter-container .layout-toggle-btn");
    tagFilterButtons.forEach(btn => {
        btn.classList.toggle("active", btn.getAttribute("data-filter") === filter);
    });
    
    currentQuestionIndex = 0;
    renderQuestions();
}

// Login & Profile handlers
function showLoginScreen() {
    document.getElementById("view-login").style.display = "flex";
    document.getElementById("view-dashboard").style.display = "none";
    document.getElementById("view-workspace").style.display = "none";
    
    // Hide header dashboard controls
    document.getElementById("btn-dashboard").style.display = "none";
    document.getElementById("btn-logout").style.display = "none";
    document.getElementById("btn-reset-all").style.display = "none";
    document.getElementById("candidate-info-header").style.display = "none";
}

function handleLogin() {
    const nameInput = document.getElementById("login-name").value.trim();
    const regInput = document.getElementById("login-reg").value.trim().toUpperCase();
    
    if (!nameInput || !regInput) return;
    
    userProfile = {
        name: nameInput,
        regNo: regInput
    };
    
    localStorage.setItem("ca_user_profile", JSON.stringify(userProfile));
    
    updateProfileUI();
    showDashboard();
}

function handleLogout() {
    const confirmLogout = confirm("Are you sure you want to log out of the Candidate Portal?");
    if (!confirmLogout) return;
    
    localStorage.removeItem("ca_user_profile");
    userProfile = null;
    
    // Reset inputs
    document.getElementById("login-name").value = "";
    document.getElementById("login-reg").value = "";
    
    showLoginScreen();
}

function updateProfileUI() {
    if (userProfile) {
        document.getElementById("header-candidate-name").innerText = userProfile.name;
        document.getElementById("header-candidate-reg").innerText = `(${userProfile.regNo})`;
        document.getElementById("candidate-info-header").style.display = "flex";
        
        document.getElementById("btn-dashboard").style.display = "inline-flex";
        document.getElementById("btn-logout").style.display = "inline-flex";
        document.getElementById("btn-reset-all").style.display = "inline-flex";
    }
}

// Launch application on DOM ready
document.addEventListener("DOMContentLoaded", init);
