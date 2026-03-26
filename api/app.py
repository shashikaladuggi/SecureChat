from flask import Flask, render_template, request, jsonify
from passlib.hash import pbkdf2_sha256
import uuid
import secrets

app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.config['SECRET_KEY'] = 'replace-with-a-secure-secret'

# In-memory room store
rooms = {}

# Algorithm pool for random selection
ALGORITHM_POOL = [
    "DES",
    "ELGAMAL", 
    "RSA",
    "CRYSTALS-Kyber",
    "CRYSTALS-Dilithium",
    "Falcon",
    "SABER",
    "NewHope",
    "FrodoKEM",
    "NTRUEncrypt",
    "NTRUPrime",
    "Classic McEliece",
    "BIKE",
    "HQC",
    "Rainbow",
    "SPHINCS+",
    "CSIDH",
    "Picnic"
]

# Algorithm number mapping (for backward compatibility)
ALGORITHM_NUM_MAP = {
    "DES": "1",
    "ELGAMAL": "2",
    "RSA": "3",
    "CRYSTALS-Kyber": "4",
    "CRYSTALS-Dilithium": "5",
    "Falcon": "6",
    "SABER": "7",
    "NewHope": "8",
    "FrodoKEM": "9",
    "NTRUEncrypt": "10",
    "NTRUPrime": "11",
    "Classic McEliece": "12",
    "BIKE": "13",
    "HQC": "14",
    "Rainbow": "15",
    "SPHINCS+": "16",
    "CSIDH": "17",
    "Picnic": "18"
}

def get_random_algorithm():
    """
    Cryptographically secure random algorithm selection.
    Uses secrets.choice for uniform distribution.
    """
    return secrets.choice(ALGORITHM_POOL)

def get_random_algorithm_with_999_probability(base_algorithm=None):
    """
    Random algorithm selection with 99.9% probability of different algorithm.
    This ensures that consecutive messages almost always use different algorithms.
    
    Args:
        base_algorithm: The algorithm used in the previous message
        
    Returns:
        Selected algorithm name
    """
    # Use cryptographically secure random
    rand_val = secrets.randbelow(10000)  # 0-9999 range
    
    # 99.9% chance (0-9989) to select a different algorithm
    if rand_val < 9990:
        # Exclude the base algorithm if provided
        available_algos = [a for a in ALGORITHM_POOL if a != base_algorithm]
        if not available_algos:  # fallback if only one algorithm
            available_algos = ALGORITHM_POOL
        return secrets.choice(available_algos)
    else:
        # 0.1% chance (9990-9999) to use the same algorithm (unpredictable)
        if base_algorithm:
            return base_algorithm
        return get_random_algorithm()

@app.route('/')
def index():
    return render_template('index_socketio.html')

# Create a room
@app.route('/api/create-room', methods=['POST'])
def create_room():
    data = request.json or {}
    room_name = data.get('room_name')
    algorithm = data.get('algorithm', 'RSA')
    passphrase = data.get('passphrase')
    creator = data.get('creator', 'unknown')
    random_mode = data.get('random_mode', False)

    if not room_name or not passphrase:
        return jsonify({'error': 'room_name and passphrase required'}), 400

    # If random mode is enabled, select a random algorithm for the room
    if random_mode:
        algorithm = get_random_algorithm()

    room_id = str(uuid.uuid4())
    pass_hash = pbkdf2_sha256.hash(passphrase)
    rooms[room_id] = {
        'name': room_name,
        'algorithm': algorithm,
        'pass_hash': pass_hash,
        'creator': creator,
        'participants': {},
        'messages': [],
        'next_message_id': 0,
        'random_mode': random_mode
    }
    return jsonify({'room_id': room_id, 'message': 'room created', 'algorithm': algorithm, 'random_mode': random_mode})

# Join room
@app.route('/api/join-room', methods=['POST'])
def join_room_http():
    data = request.json or {}
    room_id = data.get('room_id')
    passphrase = data.get('passphrase')
    username = data.get('username') or 'guest'

    room = rooms.get(room_id)
    if not room:
        return jsonify({'error': 'room not found'}), 404

    if not pbkdf2_sha256.verify(passphrase, room['pass_hash']):
        return jsonify({'error': 'invalid passphrase'}), 403

    if username not in room['participants']:
        room['participants'][username] = True
    
    return jsonify({
        'room_id': room_id, 
        'message': 'ok', 
        'algorithm': room['algorithm'], 
        'creator': room['creator'], 
        'room_name': room['name']
    })

# Delete room
@app.route('/api/delete-room', methods=['POST'])
def delete_room():
    data = request.json or {}
    room_id = data.get('room_id')
    username = data.get('username')

    room = rooms.get(room_id)
    if not room:
        return jsonify({'error': 'room not found'}), 404

    if room['creator'] != username:
        return jsonify({'error': 'Only the room creator can delete this room'}), 403

    del rooms[room_id]
    return jsonify({'success': True, 'message': 'Room deleted'})

# Send message with dynamic algorithm selection
@app.route('/api/send-message', methods=['POST'])
def send_message():
    data = request.json or {}
    room_id = data.get('room_id')
    username = data.get('username')
    message = data.get('message')
    
    room = rooms.get(room_id)
    if not room or username not in room['participants']:
        return jsonify({'error': 'unauthorized'}), 403
    
    # Get algorithm selection from request
    selected_algorithm = data.get('algorithm')
    use_random_mode = data.get('random_mode', False)
    
    # Determine the algorithm to use for this message
    message_algorithm = selected_algorithm
    
    if use_random_mode:
        # Get the last algorithm used in this room (for 99.9% probability logic)
        last_algorithm = None
        if room['messages']:
            last_msg = room['messages'][-1]
            last_algorithm = last_msg.get('algorithm')
        
        if selected_algorithm and selected_algorithm != "RANDOM":
            # Use 99.9% probability to switch from the selected algorithm
            message_algorithm = get_random_algorithm_with_999_probability(selected_algorithm)
        else:
            # Pure random selection
            message_algorithm = get_random_algorithm()
    elif not message_algorithm or message_algorithm == "RANDOM":
        # Default to room's algorithm if none specified
        message_algorithm = room['algorithm']
    
    msg_id = room['next_message_id']
    room['next_message_id'] += 1
    room['messages'].append({
        'id': msg_id, 
        'username': username, 
        'message': message,
        'algorithm': message_algorithm
    })
    
    return jsonify({'success': True, 'algorithm_used': message_algorithm})

# Get messages
@app.route('/api/get-messages', methods=['GET'])
def get_messages():
    room_id = request.args.get('room_id')
    room = rooms.get(room_id)
    
    if not room:
        return jsonify({'error': 'room not found'}), 404
    return jsonify({'messages': room['messages'], 'next_id': room['next_message_id']})

# Get participants
@app.route('/api/get-participants', methods=['GET'])
def get_participants():
    room_id = request.args.get('room_id')
    room = rooms.get(room_id)
    
    if not room:
        return jsonify({'error': 'room not found'}), 404
    
    participants = []
    for p in room['participants']:
        participant = {'username': p}
        if p == room['creator']:
            participant['is_admin'] = True
        participants.append(participant)
    
    return jsonify({'participants': participants, 'creator': room['creator']})

# Leave room
@app.route('/api/leave-room', methods=['POST'])
def leave_room():
    data = request.json or {}
    room_id = data.get('room_id')
    username = data.get('username')
    
    room = rooms.get(room_id)
    if room and username in room['participants']:
        del room['participants'][username]
    
    return jsonify({'success': True})

# Get all rooms
@app.route('/api/get-rooms', methods=['GET'])
def get_rooms_endpoint():
    room_list = []
    for room_id, room in rooms.items():
        room_list.append({
            'room_id': room_id,
            'name': room['name'],
            'algorithm': room['algorithm'],
            'participant_count': len(room['participants']),
            'creator': room['creator']
        })
    return jsonify({'rooms': room_list})

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5001, debug=True)
