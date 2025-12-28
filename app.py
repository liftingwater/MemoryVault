from flask import Flask, jsonify, request
from datetime import datetime

app = Flask(__name__)

# In-memory storage for now (will be replaced with database later)
cards = []
boxes = {i: [] for i in range(1, 6)}  # 5 Leitner boxes


@app.route('/')
def home():
    """Home endpoint"""
    return jsonify({
        'message': 'Welcome to MemoryVault - Leitner Box System',
        'version': '0.1.0',
        'endpoints': {
            'cards': '/api/cards',
            'boxes': '/api/boxes',
            'review': '/api/review'
        }
    })


@app.route('/api/cards', methods=['GET', 'POST'])
def manage_cards():
    """Get all cards or create a new card"""
    if request.method == 'GET':
        return jsonify({'cards': cards, 'total': len(cards)})
    
    elif request.method == 'POST':
        data = request.get_json()
        
        if not data or 'front' not in data or 'back' not in data:
            return jsonify({'error': 'Front and back are required'}), 400
        
        card = {
            'id': len(cards) + 1,
            'front': data['front'],
            'back': data['back'],
            'box': 1,  # All new cards start in box 1
            'created_at': datetime.now().isoformat(),
            'last_reviewed': None,
            'review_count': 0
        }
        
        cards.append(card)
        boxes[1].append(card['id'])
        
        return jsonify({'message': 'Card created', 'card': card}), 201


@app.route('/api/cards/<int:card_id>', methods=['GET', 'PUT', 'DELETE'])
def card_detail(card_id):
    """Get, update, or delete a specific card"""
    card = next((c for c in cards if c['id'] == card_id), None)
    
    if not card:
        return jsonify({'error': 'Card not found'}), 404
    
    if request.method == 'GET':
        return jsonify({'card': card})
    
    elif request.method == 'PUT':
        data = request.get_json()
        if 'front' in data:
            card['front'] = data['front']
        if 'back' in data:
            card['back'] = data['back']
        return jsonify({'message': 'Card updated', 'card': card})
    
    elif request.method == 'DELETE':
        cards.remove(card)
        # Remove from boxes
        for box_cards in boxes.values():
            if card_id in box_cards:
                box_cards.remove(card_id)
        return jsonify({'message': 'Card deleted'}), 200


@app.route('/api/boxes', methods=['GET'])
def get_boxes():
    """Get all boxes with their cards"""
    box_data = {}
    for box_num, card_ids in boxes.items():
        box_cards = [c for c in cards if c['id'] in card_ids]
        box_data[f'box_{box_num}'] = {
            'number': box_num,
            'card_count': len(box_cards),
            'cards': box_cards
        }
    return jsonify({'boxes': box_data})


@app.route('/api/review', methods=['POST'])
def review_card():
    """Review a card and move it to appropriate box"""
    data = request.get_json()
    
    if not data or 'card_id' not in data or 'correct' not in data:
        return jsonify({'error': 'card_id and correct are required'}), 400
    
    card_id = data['card_id']
    correct = data['correct']
    
    card = next((c for c in cards if c['id'] == card_id), None)
    
    if not card:
        return jsonify({'error': 'Card not found'}), 404
    
    current_box = card['box']
    
    # Remove from current box
    if card_id in boxes[current_box]:
        boxes[current_box].remove(card_id)
    
    # Leitner box logic
    if correct:
        # Move to next box (max box 5)
        new_box = min(current_box + 1, 5)
    else:
        # Move back to box 1
        new_box = 1
    
    card['box'] = new_box
    card['last_reviewed'] = datetime.now().isoformat()
    card['review_count'] += 1
    boxes[new_box].append(card_id)
    
    return jsonify({
        'message': 'Card reviewed',
        'card': card,
        'moved_from': current_box,
        'moved_to': new_box
    })


if __name__ == '__main__':
    app.run(debug=True, port=5000)

