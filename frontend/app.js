const API_URL = "https://qr2gqnyemwlg35ez6mfc4gxsu0htjrd.lambda-url.us-east-1.on.aws/";

const chatWindow = document.getElementById("chat-window");
const chatForm = document.getElementById("chat-form");
const userInput = document.getElementById("user-input");
const suggestionsDiv = document.getElementById("suggestions");
const typingIndicator = document.getElementById("typing-indicator");

const suggestions = [
  "What are your shipping options?",
  "How do I start a return?",
  "How long does shipping take?",
  "Which payment methods do you accept?",
  "How can I track my order?"
];

function addMessage(text, sender = "bot") {
  const messageEl = document.createElement("div");
  messageEl.className = `message ${sender}`;

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;

  messageEl.appendChild(bubble);
  chatWindow.appendChild(messageEl);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

function showTyping(show) {
  typingIndicator.style.display = show ? "flex" : "none";
}

function renderSuggestions() {
  suggestionsDiv.innerHTML = "";
  suggestions.forEach((q) => {
    const btn = document.createElement("button");
    btn.className = "suggestion-btn";
    btn.textContent = q;
    btn.addEventListener("click", () => {
      userInput.value = q;
      chatForm.dispatchEvent(new Event("submit", { cancelable: true, bubbles: true }));
    });
    suggestionsDiv.appendChild(btn);
  });
}

async function sendMessage(message) {
  addMessage(message, "user");
  showTyping(true);

  try {
    const response = await fetch(API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ message })
    });

    const data = await response.json();

    if (!response.ok || data.error) {
      addMessage("Sorry, something went wrong. Please try again.", "bot");
    } else {
      let answerText = data.answer || "Hmm, I’m not sure about that one.";
      if (data.matched_question) {
        answerText += `\n\n(Closest match: “${data.matched_question}”)`;
      }
      addMessage(answerText, "bot");
    }
  } catch (err) {
    addMessage("Network error. Please check your connection and try again.", "bot");
  } finally {
    showTyping(false);
  }
}

chatForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const message = userInput.value.trim();
  if (!message) return;
  userInput.value = "";
  sendMessage(message);
});

// Initial welcome + suggestions
addMessage("Hi! I’m Nova, your smart FAQ assistant. Ask me about shipping, returns, orders, or payments—or tap a suggestion below.", "bot");
renderSuggestions();
