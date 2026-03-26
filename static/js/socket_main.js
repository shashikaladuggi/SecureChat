let currentRoomId = null;
let myUsername = null;
let roomCreator = null;
let lastMessageId = -1;
let messageInterval = null;
let participantInterval = null;

// Store user's room credentials for auto-rejoin
let userCredentials = {}; // room_id -> {passphrase, username}

// UI elements
const createBtn = document.getElementById('createRoomBtn');
const createModal = document.getElementById('createModal');
const joinBtn = document.getElementById('joinRoomBtn');
const joinModal = document.getElementById('joinModal');

const messagesEl = document.getElementById('messages');
const participantsList = document.getElementById('participantsList');
const roomTitle = document.getElementById('roomTitle');
const leaveRoomBtn = document.getElementById('leaveRoomBtn');
const deleteRoomBtn = document.getElementById('deleteRoomBtn');
const roomsList = document.getElementById('roomsList');

// Algorithm selection elements
const algoBar = document.getElementById('algoBar');
const messageAlgoSelect = document.getElementById('messageAlgo');
const randomModeCheckbox = document.getElementById('randomMode');
const currentAlgoSpan = document.getElementById('currentAlgo');

// small helper
function appendMessage(text, cls='', algoInfo=''){
  const p = document.createElement('div');
  p.className = 'msg ' + cls;
  p.innerHTML = text + (algoInfo ? `<span class="algo-tag">${algoInfo}</span>` : '');
  messagesEl.appendChild(p);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

// Toggle modals
createBtn.onclick = ()=> createModal.style.display = 'flex';
document.getElementById('createClose').onclick = ()=> createModal.style.display = 'none';
joinBtn.onclick = ()=> joinModal.style.display = 'flex';
document.getElementById('joinClose').onclick = ()=> joinModal.style.display = 'none';

// Delete room button handler
if (deleteRoomBtn) {
  deleteRoomBtn.onclick = async () => {
    if (!currentRoomId || !myUsername) return;
    if (!confirm('Are you sure you want to delete this room? This action cannot be undone.')) return;
    
    try {
      const res = await fetch('/api/delete-room', {
        method:'POST', headers:{'Content-Type':'application/json'},
        body: JSON.stringify({room_id: currentRoomId, username: myUsername})
      });
      const data = await res.json();
      if(data.error) {
        return alert('Delete failed: ' + data.error);
      }
      alert('Room deleted successfully');
      // Clear credentials for deleted room
      delete userCredentials[currentRoomId];
      currentRoomId = null;
      myUsername = null;
      roomCreator = null;
      lastMessageId = -1;
      roomTitle.textContent = 'Select or create a room to begin';
      leaveRoomBtn.style.display = 'none';
      deleteRoomBtn.style.display = 'none';
      messagesEl.innerHTML = '';
      participantsList.innerHTML = '';
      if (messageInterval) clearInterval(messageInterval);
      if (participantInterval) clearInterval(participantInterval);
      messageInterval = null;
      participantInterval = null;
      fetchRooms();
    } catch (error) {
      console.error('Delete room error:', error);
      alert('Network error during delete');
    }
  };
}

// Fetch and display rooms in sidebar
async function fetchRooms() {
  try {
    const res = await fetch('/api/get-rooms');
    const data = await res.json();
    if (data.rooms) {
      roomsList.innerHTML = '';
      data.rooms.forEach(room => {
        const roomDiv = document.createElement('div');
        roomDiv.className = 'room-item';
        
        // Check if user has credentials for this room
        const hasCredentials = userCredentials[room.room_id] !== undefined;
        const statusClass = hasCredentials ? 'joined' : '';
        
        roomDiv.innerHTML = `
          <span class="room-name">${room.name}</span>
          <span class="room-algo">${room.algorithm}</span>
          <span class="room-count">${room.participant_count}</span>
          ${hasCredentials ? '<span class="room-status">Joined</span>' : ''}
        `;
        roomDiv.onclick = () => {
          handleRoomClick(room.room_id);
        };
        roomsList.appendChild(roomDiv);
      });
    }
  } catch (e) {
    console.error('Fetch rooms error:', e);
  }
}

// Handle room click - auto-join if credentials exist
async function handleRoomClick(roomId) {
  const creds = userCredentials[roomId];
  
  if (creds) {
    // Auto-join with stored credentials
    await joinRoomWithCredentials(roomId, creds.passphrase, creds.username);
  } else {
    // No credentials - show join modal
    document.getElementById('joinRoomId').value = roomId;
    joinModal.style.display = 'flex';
  }
}

// Join room with credentials (for auto-rejoin)
async function joinRoomWithCredentials(room_id, passphrase, username) {
  try {
    const res = await fetch('/api/join-room', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({room_id, passphrase, username})
    });
    const data = await res.json();
    if(data.error) {
      // If error (e.g., room was deleted), remove credentials
      delete userCredentials[room_id];
      fetchRooms();
      return alert('Join failed: ' + data.error);
    }
    
    // Successfully joined
    myUsername = username;
    currentRoomId = room_id;
    roomCreator = data.creator || null;
    lastMessageId = -1;
    
    // Check if user is the creator
    const isCreator = userCredentials[room_id] && userCredentials[room_id].isCreator;
    if (isCreator) {
      // Show room name with encrypted ID below for creator
      roomTitle.innerHTML = `${data.room_name}<br><small style="font-size:0.7em;color:#888;">ID: ${room_id}</small>`;
    } else {
      // Show just room name for others
      roomTitle.textContent = `Room: ${data.room_name} (${data.algorithm})`;
    }
    
    leaveRoomBtn.style.display = 'block';
    
    // Show delete button if user is the creator
    if (deleteRoomBtn && roomCreator === myUsername) {
      deleteRoomBtn.style.display = 'block';
    }
    
    // Show algorithm selection bar
    if (algoBar) {
      algoBar.style.display = 'flex';
    }
    
    joinModal.style.display = 'none';
    appendMessage(`You joined room "${data.room_name}" as ${username}`, 'meta');
    
    // Start polling to get messages and participants
    startPolling();
    
    // Refresh rooms list to show "Joined" status
    fetchRooms();
  } catch (error) {
    console.error('Join fetch error:', error);
    alert('Network error during join');
  }
}

// Initial fetch of rooms on page load
fetchRooms();

// Create room
document.getElementById('createSubmit').onclick = async ()=>{
  const creatorName = document.getElementById('creatorName').value;
  const room_name = document.getElementById('roomName').value;
  let algorithm = document.getElementById('algorithm').value;
  const passphrase = document.getElementById('passphrase').value;
  const username = creatorName || ('user-' + Math.floor(Math.random() * 1000));
  if(!room_name || !passphrase) return alert('name+pass required');
  
  // Check if RANDOM algorithm is selected
  let random_mode = false;
  let roomAlgorithm = algorithm;
  
  if (algorithm === 'RANDOM') {
    // Select random algorithm for the room and enable random mode
    const algorithms = ['RSA', 'DES', 'ELGAMAL', 'CRYSTALS-Kyber', 'CRYSTALS-Dilithium', 
                        'Falcon', 'SABER', 'NewHope', 'FrodoKEM', 'NTRUEncrypt'];
    roomAlgorithm = algorithms[Math.floor(Math.random() * algorithms.length)];
    random_mode = true;
  }
  
  const res = await fetch('/api/create-room', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({
      room_name, 
      algorithm: roomAlgorithm, 
      passphrase, 
      creator: username,
      random_mode: random_mode
    })
  });
  const data = await res.json();
  if(data.room_id) {
    alert('Room created: ' + data.room_id);
    createModal.style.display = 'none';
    
    // Store credentials for auto-rejoin
    userCredentials[data.room_id] = { passphrase, username, isCreator: true };
    
    // Refresh rooms list
    fetchRooms();
    
    // Auto-join the created room
    await joinRoomWithCredentials(data.room_id, passphrase, username);
  } else {
    alert('Error: ' + JSON.stringify(data));
  }
};

// Join room
document.getElementById('joinSubmit').onclick = async ()=>{
  const room_id = document.getElementById('joinRoomId').value;
  const passphrase = document.getElementById('joinPass').value;
  const username = document.getElementById('joinName').value || ('user-' + Math.floor(Math.random() * 1000));
  if(!room_id || !passphrase) return alert('room id + pass required');

  try {
    const res = await fetch('/api/join-room', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({room_id, passphrase, username})
    });
    const data = await res.json();
    if(data.error) {
      return alert('Join failed: ' + data.error);
    }
    
    // Store credentials for auto-rejoin
    userCredentials[room_id] = { passphrase, username };
    
    myUsername = username;
    currentRoomId = room_id;
    roomCreator = data.creator || null;
    lastMessageId = -1;
    roomTitle.textContent = `Room: ${data.room_name} (${data.algorithm})`;
    leaveRoomBtn.style.display = 'block';
    
    // Show delete button if user is the creator
    if (deleteRoomBtn && roomCreator === myUsername) {
      deleteRoomBtn.style.display = 'block';
    }
    
    // Show algorithm selection bar
    if (algoBar) {
      algoBar.style.display = 'flex';
    }
    
    joinModal.style.display = 'none';
    appendMessage(`You joined room "${data.room_name}" as ${username}`, 'meta');
    // Start polling
    startPolling();
    
    // Refresh rooms list to show "Joined" status
    fetchRooms();
  } catch (error) {
    console.error('Join fetch error:', error);
    alert('Network error during join');
  }
};

// Sending messages with algorithm selection
async function sendMessage() {
  const input = document.getElementById('msgInput');
  const msg = input.value.trim();
  if(!msg || !currentRoomId || !myUsername) return;
  
  // Get algorithm selection
  const selectedAlgorithm = messageAlgoSelect ? messageAlgoSelect.value : 'RSA';
  const useRandomMode = randomModeCheckbox ? randomModeCheckbox.checked : false;
  
  const payload = {
    room_id: currentRoomId, 
    username: myUsername, 
    message: msg,
    algorithm: selectedAlgorithm,
    random_mode: useRandomMode
  };
  
  try {
    const res = await fetch('/api/send-message', {
      method:'POST', 
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    
    // Update current algorithm display if random mode is on
    if (data.algorithm_used && currentAlgoSpan) {
      currentAlgoSpan.textContent = `Last: ${data.algorithm_used}`;
    }
  } catch (error) {
    console.error('Send message error:', error);
  }
  
  input.value = '';
}

// Send on button click
document.getElementById('sendBtn').onclick = sendMessage;

// Send on Enter key press
document.getElementById('msgInput').addEventListener('keypress', function(e) {
  if (e.key === 'Enter') {
    sendMessage();
  }
});

function leaveRoom() {
  // Keep credentials for rejoin
  currentRoomId = null;
  myUsername = null;
  roomCreator = null;
  lastMessageId = -1;
  roomTitle.textContent = 'Select or create a room to begin';
  leaveRoomBtn.style.display = 'none';
  
  // Hide delete button
  if (deleteRoomBtn) {
    deleteRoomBtn.style.display = 'none';
  }
  
  // Hide algorithm bar
  if (algoBar) {
    algoBar.style.display = 'none';
  }
  
  messagesEl.innerHTML = '';
  participantsList.innerHTML = '';
  appendMessage('You left the room', 'meta');
  if (messageInterval) clearInterval(messageInterval);
  if (participantInterval) clearInterval(participantInterval);
  messageInterval = null;
  participantInterval = null;
  
  // Refresh rooms list (keep credentials so "Joined" status remains)
  fetchRooms();
}

leaveRoomBtn.onclick = leaveRoom;

// Polling functions
function startPolling() {
  pollMessages();
  pollParticipants();
  messageInterval = setInterval(pollMessages, 2000);
  participantInterval = setInterval(pollParticipants, 5000);
}

async function pollMessages() {
  if (!currentRoomId) return;
  try {
    const res = await fetch(`/api/get-messages?room_id=${currentRoomId}`);
    const data = await res.json();
    if (data.messages) {
      data.messages.forEach(msg => {
        if (msg.id > lastMessageId) {
          // Display message without algorithm name
          appendMessage(`${msg.username}: ${msg.message}`, '', '');
          lastMessageId = msg.id;
        }
      });
    }
  } catch (e) {
    console.error('Poll messages error:', e);
  }
}

async function pollParticipants() {
  if (!currentRoomId) return;
  try {
    const res = await fetch(`/api/get-participants?room_id=${currentRoomId}`);
    const data = await res.json();
    if (data.participants) {
      participantsList.innerHTML = '';
      data.participants.forEach(p => {
        const li = document.createElement('li');
        li.textContent = p.username;
        
        // Add admin badge if user is the creator
        if (p.is_admin) {
          const badge = document.createElement('span');
          badge.className = 'admin-badge';
          badge.textContent = 'admin';
          li.appendChild(badge);
        }
        
        participantsList.appendChild(li);
      });
    }
  } catch (e) {
    console.error('Poll participants error:', e);
  }
}
