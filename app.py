from flask import Flask, jsonify, request
from models import Card

app = Flask(__name__)

# In-memory storage for now (will be replaced with database later)
cards = []  # List of Card objects
boxes = {i: [] for i in range(1, 6)}  # 5 Leitner boxes
next_card_id = 1  # Counter for card IDs


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
    global next_card_id

    if request.method == 'GET':
        cards_data = [card.to_dict() for card in cards]
        return jsonify({'cards': cards_data, 'total': len(cards)})

    elif request.method == 'POST':
        data = request.get_json()

        if not data or 'front' not in data or 'back' not in data:
            return jsonify({'error': 'Front and back are required'}), 400

        card = Card(
            front=data['front'],
            back=data['back'],
            card_id=next_card_id
        )

        cards.append(card)
        boxes[1].append(card.id)
        next_card_id += 1

        return jsonify({'message': 'Card created', 'card': card.to_dict()}), 201


@app.route('/api/cards/<int:card_id>', methods=['GET', 'PUT', 'DELETE'])
def card_detail(card_id):
    """Get, update, or delete a specific card"""
    card = next((c for c in cards if c.id == card_id), None)

    if not card:
        return jsonify({'error': 'Card not found'}), 404

    if request.method == 'GET':
        return jsonify({'card': card.to_dict()})

    elif request.method == 'PUT':
        data = request.get_json()
        card.update(
            front=data.get('front'),
            back=data.get('back')
        )
        return jsonify({'message': 'Card updated', 'card': card.to_dict()})

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
        box_cards = [c.to_dict() for c in cards if c.id in card_ids]
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

    card = next((c for c in cards if c.id == card_id), None)

    if not card:
        return jsonify({'error': 'Card not found'}), 404

    current_box = card.box

    # Remove from current box
    if card_id in boxes[current_box]:
        boxes[current_box].remove(card_id)

    # Use Card's review method to update box position
    new_box = card.review(correct)
    boxes[new_box].append(card_id)

    return jsonify({
        'message': 'Card reviewed',
        'card': card.to_dict(),
        'moved_from': current_box,
        'moved_to': new_box
    })


if __name__ == '__main__':
    app.run(debug=True, port=5000)

