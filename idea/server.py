from flask import Flask, send_file, jsonify, request
from flask_socketio import SocketIO, emit, join_room
import json
import uuid
import random
from questions import R1_QUESTIONS, R2_QUESTIONS, R3_QUESTIONS

app = Flask(__name__)
app.config['SECRET_KEY'] = 'kaustubh-game-secret'
socketio = SocketIO(app, cors_allowed_origins="*")

rooms = {}

def create_room():
    room_id = str(uuid.uuid4())[:8]
    return room_id

@app.route('/')
def index():
    return send_file('index.html')

@app.route('/api/create-room', methods=['POST'])
def api_create_room():
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
        },
        'r3_claimed': {}
    }
    return jsonify({'room_id': room_id})

@app.route('/api/join-room/<room_id>', methods=['POST'])
def api_join_room(room_id):
    if room_id not in rooms:
        return jsonify({'error': 'Room not found'}), 404
    data = request.json
    player_name = data.get('player_name', f'Player {len(rooms[room_id]["players"]) + 1}')
    default_colors = ['🔴', '🔵', '🟢']
    default_color = default_colors[len(rooms[room_id]['players'])] if len(rooms[room_id]['players']) < len(default_colors) else '🔴'
    player_color = data.get('player_color', default_color)
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
    if room_id not in rooms:
        return jsonify({'error': 'Room not found'}), 404
    return jsonify(rooms[room_id])

@socketio.on('join_room')
def handle_join_room(data):
    room_id = data['room_id']
    player_id = data['player_id']
    if room_id in rooms:
        join_room(room_id)
        emit('player_joined', {'player_id': player_id, 'players': rooms[room_id]['players']}, room=room_id)

@socketio.on('update_game')
def handle_update_game(data):
    room_id = data['room_id']
    game_state = data['game_state']
    if room_id in rooms:
        rooms[room_id]['game_state'] = game_state
        # Reset r3_claimed when round 3 is initialized
        if game_state.get('action') == 'r3_init':
            rooms[room_id]['r3_claimed'] = {}
        emit('game_updated', game_state, room=room_id, include_self=False)

@socketio.on('r3_claim')
def handle_r3_claim(data):
    """
    Atomically claim an answer in Round 3.
    Multiple players may submit at the same time; only the first claimant wins.
    """
    room_id = data['room_id']
    answer_idx = str(data['answer_idx'])
    player_id = data['player_id']
    player_css_class = data['player_css_class']
    player_score_delta = data.get('score_delta', 10)
    bonus = data.get('bonus', False)

    if room_id not in rooms:
        return

    claimed = rooms[room_id].setdefault('r3_claimed', {})

    if answer_idx in claimed:
        # Already claimed — reject silently (client will see no confirmation)
        emit('r3_claim_rejected', {
            'answer_idx': int(answer_idx),
            'player_id': player_id
        })
        return

    # Claim is valid — lock it server-side
    claimed[answer_idx] = {
        'player_id': player_id,
        'css_class': player_css_class
    }

    # Build the full revealed map so all clients can sync their board authoritatively.
    # Keys are ints so JS can use them directly as array indices.
    full_revealed = {int(k): v['css_class'] for k, v in claimed.items()}

    # Broadcast the successful claim to ALL players (including sender)
    emit('r3_claim_accepted', {
        'answer_idx': int(answer_idx),
        'player_id': player_id,
        'player_css_class': player_css_class,
        'score_delta': player_score_delta,
        'r3_revealed': full_revealed
    }, room=room_id)

@socketio.on('player_action')
def handle_player_action(data):
    room_id = data['room_id']
    action = data['action']
    if room_id in rooms:
        emit('action_received', action, room=room_id, include_self=False)

@socketio.on('next_turn')
def handle_next_turn(data):
    room_id = data['room_id']
    if room_id in rooms:
        emit('turn_changed', data, room=room_id, include_self=False)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', debug=True, port=5000)
