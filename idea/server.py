from flask import Flask, send_file, jsonify, request
from flask_socketio import SocketIO, emit, join_room
import json
import uuid
import random
from questions import R1_QUESTIONS, R2_QUESTIONS, R3_QUESTIONS

app = Flask(__name__)
app.config['SECRET_KEY'] = 'kaustubh-game-secret'
socketio = SocketIO(app, cors_allowed_origins="*")

# Game rooms storage
rooms = {}

def create_room():
    room_id = str(uuid.uuid4())[:8]
    return room_id

@app.route('/')
def index():
    return send_file('index.html')

# API Routes
@app.route('/api/create-room', methods=['POST'])
def api_create_room():
    """Create a new game room"""
    room_id = create_room()
    rooms[room_id] = {
        'players': [],
        'game_state': {
            'current_round': 0,
            'used_questions': [],
            'r1_questions': random.sample(R1_QUESTIONS, len(R1_QUESTIONS)),
            'r1_revealed': {},
            'r2_questions': random.sample(R2_QUESTIONS, len(R2_QUESTIONS)),
            'r2_revealed': {},
            'r3_questions': random.sample(R3_QUESTIONS, len(R3_QUESTIONS)),
            'r3_revealed': {}
        }
    }
    return jsonify({'room_id': room_id})

@app.route('/api/join-room/<room_id>', methods=['POST'])
def api_join_room(room_id):
    """Join an existing room"""
    if room_id not in rooms:
        return jsonify({'error': 'Room not found'}), 404
    
    data = request.json
    player_name = data.get('player_name', f'Player {len(rooms[room_id]["players"]) + 1}')
    player_color = data.get('player_color', '🔴')
    
    if len(rooms[room_id]['players']) >= 3:
        return jsonify({'error': 'Room is full'}), 400
    
    player = {
        'id': len(rooms[room_id]['players']),
        'name': player_name,
        'color': player_color,
        'score': 0
    }
    rooms[room_id]['players'].append(player)
    
    return jsonify({'player': player, 'room': rooms[room_id]})

@app.route('/api/room/<room_id>', methods=['GET'])
def api_get_room(room_id):
    """Get room info"""
    if room_id not in rooms:
        return jsonify({'error': 'Room not found'}), 404
    return jsonify(rooms[room_id])

# WebSocket Events
@socketio.on('join_room')
def handle_join_room(data):
    room_id = data['room_id']
    player_id = data['player_id']
    
    if room_id in rooms:
        join_room(room_id)
        emit('player_joined', {'player_id': player_id, 'players': rooms[room_id]['players']}, room=room_id)

@socketio.on('update_game')
def handle_update_game(data):
    """Broadcast game state updates"""
    room_id = data['room_id']
    game_state = data['game_state']
    
    if room_id in rooms:
        rooms[room_id]['game_state'] = game_state
        emit('game_updated', game_state, room=room_id, include_self=False)

@socketio.on('player_action')
def handle_player_action(data):
    """Handle player actions (guesses, etc.)"""
    room_id = data['room_id']
    action = data['action']
    
    if room_id in rooms:
        emit('action_received', action, room=room_id, include_self=False)

@socketio.on('next_turn')
def handle_next_turn(data):
    """Signal to move to next turn"""
    room_id = data['room_id']
    if room_id in rooms:
        emit('turn_changed', data, room=room_id, include_self=False)

if __name__ == '__main__':
    print("=" * 50)
    print("🎮 Kaustubh Game Server")
    print("=" * 50)
    print("\nTo play with friends:")
    print("1. Run this server (it will show a local URL)")
    print("2. Share the URL with your friends")
    print("3. One player creates a room")
    print("4. Others join using the room code")
    print("\nStarting server...")
    socketio.run(app, host='0.0.0.0', debug=True, port=5000)
