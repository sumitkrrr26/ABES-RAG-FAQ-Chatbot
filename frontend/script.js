const API_URL = "/api/chat";

const chatMessages = document.getElementById("chatMessages");
const questionInput = document.getElementById("questionInput");
const sendButton = document.getElementById("sendButton");
const characterCount = document.getElementById("characterCount");
const clearButton = document.getElementById("clearButton");

let conversationHistory = [];


/* =====================================================
   CHARACTER COUNTER + TEXTAREA RESIZE
===================================================== */

questionInput.addEventListener("input", () => {

    characterCount.textContent =
        `${questionInput.value.length} / 1000`;

    questionInput.style.height = "auto";

    questionInput.style.height =
        Math.min(questionInput.scrollHeight, 120) + "px";
});


/* =====================================================
   ENTER TO SEND
===================================================== */

questionInput.addEventListener("keydown", (event) => {

    if (event.key === "Enter" && !event.shiftKey) {

        event.preventDefault();

        sendMessage();
    }
});


/* =====================================================
   SEND BUTTON
===================================================== */

sendButton.addEventListener("click", sendMessage);


/* =====================================================
   SUGGESTED QUESTIONS
===================================================== */

document.addEventListener("click", (event) => {

    const suggestion =
        event.target.closest(".suggestion");

    if (!suggestion) {
        return;
    }

    const question =
        suggestion.dataset.question;

    questionInput.value = question;

    characterCount.textContent =
        `${question.length} / 1000`;

    questionInput.style.height = "auto";

    questionInput.style.height =
        Math.min(questionInput.scrollHeight, 120) + "px";

    questionInput.focus();

    sendMessage();
});


/* =====================================================
   CLEAR CHAT
===================================================== */

clearButton.addEventListener("click", clearChat);


function clearChat() {

    const confirmed =
        confirm("Clear the current conversation?");

    if (!confirmed) {
        return;
    }

    conversationHistory = [];

    chatMessages.innerHTML = `
        <div class="message bot-message">

            <div class="avatar bot-avatar">
                AI
            </div>

            <div class="message-content">

                <div class="message-name">
                    ABES Assistant
                </div>

                <div class="message-bubble">

                    <div class="welcome-title">
                        Hello! 👋
                    </div>

                    <p>
                        I'm the ABES AI FAQ Assistant.
                    </p>

                    <p>
                        Ask me about ABES Engineering College,
                        including admissions, courses, departments,
                        hostel, placements, fees and more.
                    </p>

                </div>

            </div>

        </div>

        <div class="suggestions">

            <div class="suggestions-title">
                Try asking
            </div>

            <div class="suggestion-buttons">

                <button
                    class="suggestion"
                    data-question="What courses are offered by ABES?"
                >
                    🎓 Courses offered
                </button>

                <button
                    class="suggestion"
                    data-question="What is the CSE intake?"
                >
                    💻 CSE intake
                </button>

                <button
                    class="suggestion"
                    data-question="What documents are required for admission?"
                >
                    📄 Admission documents
                </button>

                <button
                    class="suggestion"
                    data-question="What hostel facilities are available?"
                >
                    🏠 Hostel facilities
                </button>

            </div>

        </div>
    `;

    questionInput.value = "";

    questionInput.style.height = "auto";

    characterCount.textContent = "0 / 1000";

    questionInput.focus();

    scrollToBottom();
}


/* =====================================================
   USER MESSAGE
===================================================== */

function addUserMessage(text) {

    const message =
        document.createElement("div");

    message.className =
        "message user-message";

    message.innerHTML = `
        <div class="message-content">

            <div class="message-name">
                You
            </div>

            <div class="message-bubble">
                ${escapeHTML(text)}
            </div>

        </div>

        <div class="avatar user-avatar">
            You
        </div>
    `;

    chatMessages.appendChild(message);

    scrollToBottom();
}


/* =====================================================
   BOT MESSAGE
===================================================== */

function addBotMessage(answer, sources = []) {

    const message =
        document.createElement("div");

    message.className =
        "message bot-message";


    /* Convert Gemini Markdown to HTML */

    const formattedAnswer =
        markdownToHTML(answer);


    /* Build source cards */

    let sourcesHTML = "";


    if (sources.length > 0) {

        sourcesHTML = `
            <div class="sources">

                <div class="sources-title">
                    📚 Sources
                </div>

                ${sources.map(source => {

                    const score =
                        Number(source.score);

                    const percentage =
                        Number.isFinite(score)
                            ? Math.round(score * 100)
                            : null;

                    return `
                        <div class="source-card">

                            <div class="source-name">
                                📄

                                <span>
                                    ${escapeHTML(source.document)}
                                    • Page ${source.page}
                                </span>
                            </div>

                            ${
                                percentage !== null
                                ?
                                `<div class="source-score">
                                    Relevance ${percentage}%
                                </div>`
                                :
                                ""
                            }

                        </div>
                    `;

                }).join("")}

            </div>
        `;
    }


    message.innerHTML = `
        <div class="avatar bot-avatar">
            AI
        </div>

        <div class="message-content">

            <div class="message-name">
                ABES Assistant
            </div>

            <div class="message-bubble">
                ${formattedAnswer}
            </div>

            ${sourcesHTML}

        </div>
    `;


    chatMessages.appendChild(message);

    scrollToBottom();
}


/* =====================================================
   LOADING MESSAGE
===================================================== */

function addLoadingMessage() {

    const message =
        document.createElement("div");

    message.className =
        "message bot-message";

    message.id =
        "loadingMessage";

    message.innerHTML = `
        <div class="avatar bot-avatar">
            AI
        </div>

        <div class="message-content">

            <div class="message-name">
                ABES Assistant
            </div>

            <div class="message-bubble">

                <div class="typing">

                    <span></span>
                    <span></span>
                    <span></span>

                </div>

            </div>

        </div>
    `;

    chatMessages.appendChild(message);

    scrollToBottom();
}


/* =====================================================
   REMOVE LOADING
===================================================== */

function removeLoadingMessage() {

    const loading =
        document.getElementById("loadingMessage");

    if (loading) {
        loading.remove();
    }
}


/* =====================================================
   MAIN SEND FUNCTION
===================================================== */

async function sendMessage() {

    const question =
        questionInput.value.trim();


    if (!question) {
        return;
    }


    /* Disable controls */

    sendButton.disabled = true;

    questionInput.disabled = true;


    /* Display user message */

    addUserMessage(question);


    /* Clear input */

    questionInput.value = "";

    questionInput.style.height = "auto";

    characterCount.textContent =
        "0 / 1000";


    /* Show loading */

    addLoadingMessage();


    try {

        const response =
            await fetch(API_URL, {

                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({

                    question: question,

                    history: conversationHistory

                })

            });


        const data =
            await response.json();


        removeLoadingMessage();


        if (!response.ok || !data.success) {

            addBotMessage(
                data.answer ||
                "Sorry, something went wrong."
            );

            return;
        }


        /* Display AI answer */

        addBotMessage(
            data.answer,
            data.sources || []
        );


        /* Save conversation */

        conversationHistory.push({

            role: "user",

            content: question

        });


        conversationHistory.push({

            role: "assistant",

            content: data.answer

        });


        /*
            Keep latest 6 messages.
            This matches the backend history limit.
        */

        if (conversationHistory.length > 6) {

            conversationHistory =
                conversationHistory.slice(-6);
        }

    }

    catch (error) {

        console.error(
            "Chatbot error:",
            error
        );


        removeLoadingMessage();


        addBotMessage(
            "Unable to connect to the ABES chatbot server. Please make sure FastAPI is running."
        );

    }

    finally {

        sendButton.disabled = false;

        questionInput.disabled = false;

        questionInput.focus();
    }
}


/* =====================================================
   BASIC MARKDOWN → HTML
===================================================== */

function markdownToHTML(text) {

    if (!text) {
        return "";
    }


    /*
        Escape HTML first so Gemini output cannot
        inject arbitrary HTML/JavaScript.
    */

    let html =
        escapeHTML(text);


    /*
        Bold:
        **text**
    */

    html =
        html.replace(
            /\*\*(.*?)\*\*/g,
            "<strong>$1</strong>"
        );


    /*
        Convert bullet lines:
        * item
        - item
    */

    html =
        html.replace(
            /^(?:\*|-)\s+(.*)$/gm,
            "<li>$1</li>"
        );


    /*
        Wrap consecutive list items
        inside <ul>.
    */

    html =
        html.replace(
            /((?:<li>.*<\/li>\s*)+)/g,
            "<ul>$1</ul>"
        );


    /*
        Convert numbered lists.
    */

    html =
        html.replace(
            /^(?:\d+\.)\s+(.*)$/gm,
            "<li>$1</li>"
        );


    /*
        Convert remaining line breaks.
    */

    html =
        html.replace(
            /\n{2,}/g,
            "</p><p>"
        );


    html =
        html.replace(
            /\n/g,
            "<br>"
        );


    /*
        If the answer doesn't already contain
        paragraph tags, add them.
    */

    if (
        !html.includes("<p>") &&
        !html.includes("<ul>")
    ) {

        html =
            `<p>${html}</p>`;
    }


    return html;
}


/* =====================================================
   HTML ESCAPING
===================================================== */

function escapeHTML(text) {

    const div =
        document.createElement("div");

    div.textContent =
        text ?? "";

    return div.innerHTML;
}


/* =====================================================
   SCROLL
===================================================== */

function scrollToBottom() {

    const container =
        document.querySelector(
            ".chat-container"
        );

    container.scrollTop =
        container.scrollHeight;
}