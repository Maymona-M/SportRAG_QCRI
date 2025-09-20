const queryInput = document.getElementById('queryInput');
const sendButton = document.getElementById('sendButton');
const chatWindow = document.getElementById('chatWindow');
const suggestedQueriesContainer = document.getElementById('suggestedQueries');
const chatHistoryList = document.getElementById('chatHistoryList');
const newChatBtn = document.getElementById('newChatBtn');

const API_URL = 'http://127.0.0.1:9610/ask';

// Store chats in-memory; each chat is an array of messages {sender, text}
let chats = [];
let currentChatIndex = -1;  // -1 means no chat loaded

function appendMessageToWindow(sender, text) {
  const div = document.createElement('div');
  div.classList.add('message', `${sender}-message`);

  if (/^- /.test(text.trim().split('\n')[0])) {
    const ul = document.createElement('ul');
    text.split('\n').forEach(line => {
      const trimmed = line.trim();
      if (trimmed.startsWith('- ')) {
        const li = document.createElement('li');
        li.textContent = trimmed.slice(2);
        ul.appendChild(li);
      }
    });
    div.appendChild(ul);
  } else {
    div.innerHTML = text.replace(/\n/g, '<br>');
  }

  chatWindow.appendChild(div);
  chatWindow.scrollTop = chatWindow.scrollHeight;
  return div;
}

function renderChatWindow(chatIndex) {
  chatWindow.innerHTML = '';
  if (chatIndex < 0 || chatIndex >= chats.length) return;
  const chat = chats[chatIndex];
  chat.forEach(({ sender, text }) => {
    appendMessageToWindow(sender, text);
  });
  currentChatIndex = chatIndex;
  updateChatHistoryUI();
}

function updateChatHistoryUI() {
  chatHistoryList.innerHTML = '';
  if (chats.length === 0) {
    const li = document.createElement('li');
    li.className = 'no-chats';
    li.textContent = 'No previous chats';
    chatHistoryList.appendChild(li);
    return;
  }
  chats.forEach((chat, idx) => {
    const li = document.createElement('li');
    li.textContent = `Chat ${idx + 1}`;
    li.classList.toggle('active', idx === currentChatIndex);
    li.style.cursor = 'pointer';
    li.addEventListener('click', () => {
      renderChatWindow(idx);
    });
    chatHistoryList.appendChild(li);
  });
}

// Add message to current chat (create chat if none)
function addMessageToCurrentChat(sender, text) {
  if (currentChatIndex === -1) {
    chats.push([]);
    currentChatIndex = chats.length - 1;
  }
  chats[currentChatIndex].push({ sender, text });
  updateChatHistoryUI();
}

// Clear current chat and start a new one
function startNewChat() {
  // Only add chat if current chat has messages
  if (currentChatIndex !== -1 && chats[currentChatIndex].length === 0) {
    // empty chat, do nothing special
  }
  // Start new chat
  chats.push([]);
  currentChatIndex = chats.length - 1;
  chatWindow.innerHTML = '';
  queryInput.value = '';
  updateChatHistoryUI();
}

// Append and save user message
function appendUserMessage(text) {
  appendMessageToWindow('user', text);
  addMessageToCurrentChat('user', text);
}

// Append and save bot message
function appendBotMessage(text) {
  appendMessageToWindow('bot', text);
  addMessageToCurrentChat('bot', text);
}

async function sendMessage(textFromSuggested = null) {
  const query = textFromSuggested || queryInput.value.trim();
  if (!query) return;

  appendUserMessage(query);
  if (!textFromSuggested) queryInput.value = '';
  sendButton.disabled = true;

  try {
    const response = await fetch(API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      let boundary = buffer.indexOf('\n\n');
      while (boundary !== -1) {
        const chunk = buffer.slice(0, boundary);
        buffer = buffer.slice(boundary + 2);

        const lines = chunk.split('\n');
        let jsonStr = '';
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            jsonStr = line.slice(6).trim();
            break;
          }
        }

        if (jsonStr) {
          try {
            const data = JSON.parse(jsonStr);
            if (data.type === 'bot_response') {
              appendBotMessage(data.message);

              if (data.image_path) {
                const lastBotMsg = document.querySelector('.bot-message:last-child');
                if (lastBotMsg) {
                  const img = document.createElement('img');
                  img.src = data.image_path;
                  img.alt = 'Pose Visualization';
                  img.style.maxWidth = '300px';
                  img.style.marginTop = '8px';
                  img.style.borderRadius = '8px';
                  lastBotMsg.appendChild(img);
                  chatWindow.scrollTop = chatWindow.scrollHeight;
                }
              }
            } else if (data.type === 'error') {
              appendMessageToWindow('error', data.message);
            }
          } catch (e) {
            appendMessageToWindow('error', 'Error parsing server response.');
          }
        }

        boundary = buffer.indexOf('\n\n');
      }
    }
  } catch (err) {
    appendMessageToWindow('error', `Request failed: ${err.message}`);
  } finally {
    sendButton.disabled = false;
  }
}

// Event Listeners

sendButton.addEventListener('click', () => sendMessage());
queryInput.addEventListener('keypress', e => { if (e.key === 'Enter') sendMessage(); });

newChatBtn.addEventListener('click', () => {
  startNewChat();
});

// Suggested queries buttons
document.querySelectorAll('.suggested-query-button').forEach(button => {
  button.addEventListener('click', e => {
    sendMessage(e.target.textContent);
  });
});

// On page load, initialize
startNewChat();

// Pose Image Upload Handler
document.getElementById('poseCheckBtn').addEventListener('click', async () => {
  const fileInput = document.getElementById('poseImageInput');
  const file = fileInput.files[0];
  if (!file) {
    appendMessageToWindow('error', 'Please select an image before checking pose.');
    return;
  }

  const formData = new FormData();
  formData.append('image', file);

  appendUserMessage("📷 Uploaded image for pose check...");

  // Show loading message
  const loadingDiv = appendMessageToWindow('bot', '⏳ Processing pose...');
  
  sendButton.disabled = true;
  document.getElementById('poseCheckBtn').disabled = true;

  try {
    const response = await fetch('http://127.0.0.1:9610/check_pose', {
      method: 'POST',
      body: formData,
    });

    const data = await response.json();

    // Remove loading message
    loadingDiv.remove();

    appendBotMessage(data.message);

    if (data.image_path) {
      const img = document.createElement('img');
      img.src = data.image_path;
      img.alt = 'Pose Analysis';
      img.style.maxWidth = '300px';
      img.style.marginTop = '8px';
      img.style.borderRadius = '8px';

      const lastBotMsg = document.querySelector('.bot-message:last-child');
      if (lastBotMsg) {
        lastBotMsg.appendChild(img);
        chatWindow.scrollTop = chatWindow.scrollHeight;
      }
    }
  } catch (err) {
    loadingDiv.remove();
    appendMessageToWindow('error', `Pose check failed: ${err.message}`);
  } finally {
    sendButton.disabled = false;
    document.getElementById('poseCheckBtn').disabled = false;
  }
});
