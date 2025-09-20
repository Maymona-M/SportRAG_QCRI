const queryInput = document.getElementById('queryInput');
const sendButton = document.getElementById('sendButton');
const chatWindow = document.getElementById('chatWindow');
const suggestedQueriesContainer = document.getElementById('suggestedQueries');
const newChatBtn = document.getElementById('newChatBtn');

const API_URL = 'http://127.0.0.1:9610/ask';

function appendMessage(sender, text) {
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

async function sendMessage() {
  const query = queryInput.value.trim();
  if (!query) return;

  appendMessage('user', query);
  queryInput.value = '';
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
              appendMessage('bot', data.message);

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
              appendMessage('error', data.message);
            }
          } catch (e) {
            appendMessage('error', 'Error parsing server response.');
          }
        }

        boundary = buffer.indexOf('\n\n');
      }
    }
  } catch (err) {
    appendMessage('error', `Request failed: ${err.message}`);
  } finally {
    sendButton.disabled = false;
  }
}

function startNewChat() {
  chatWindow.innerHTML = '';
  appendMessage('bot', 'Hello! Ask me anything about sports — from rules and stats to training tips.');
  queryInput.value = '';
  sendButton.disabled = false;
}

newChatBtn.addEventListener('click', startNewChat);

suggestedQueriesContainer.addEventListener('click', e => {
  if (e.target.classList.contains('suggested-query-button')) {
    queryInput.value = e.target.textContent;
    sendMessage();
  }
});

sendButton.addEventListener('click', sendMessage);
queryInput.addEventListener('keypress', e => { if (e.key === 'Enter') sendMessage(); });
