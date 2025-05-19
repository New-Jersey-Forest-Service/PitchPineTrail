# Game logic for Pitch Pine Trail

import random

class Game:
    def __init__(self):
        self.state = {
            'current_room': 'start',
            'inventory': [],
            'score': 0,
            'game_over': False
        }
        self.rooms = {
            'start': {
                'description': 'You are at the starting point of the Pitch Pine Trail. Choose your path.',
                'options': {
                    '1': 'Go to the forest',
                    '2': 'Visit the village',
                }
            },
            'forest': {
                'description': 'You are in a dense forest. It feels mysterious here.',
                'options': {
                    '1': 'Search for resources',
                    '2': 'Return to start',
                }
            },
            'village': {
                'description': 'You are in a small village. The locals greet you warmly.',
                'options': {
                    '1': 'Trade with locals',
                    '2': 'Return to start',
                }
            }
        }

        self.stand = {
            'year': 0,
            'QMD': 6.1,
            'TPA': 553,
            'carbon': 18.0,
            'CI': 26.0,
            'BA': 113,
            'fire_risk': 'High',
            'SPB_risk': 'Moderate',
            'events': []
        }

    def get_current_room(self):
        return self.rooms[self.state['current_room']]

    def move_to_room(self, room_name):
        if room_name in self.rooms:
            self.state['current_room'] = room_name
        else:
            raise ValueError("Room does not exist.")

    def update_inventory(self, item):
        self.state['inventory'].append(item)

    def change_score(self, points):
        self.state['score'] += points

    def check_game_over(self):
        return self.state['game_over']

    def set_game_over(self, status):
        self.state['game_over'] = status

    def reset_game(self):
        self.state = {
            'current_room': 'start',
            'inventory': [],
            'score': 0,
            'game_over': False
        }
        self.stand = {
            'year': 0,
            'QMD': 6.1,
            'TPA': 553,
            'carbon': 18.0,
            'CI': 26.0,
            'BA': 113,
            'fire_risk': 'High',
            'SPB_risk': 'Moderate',
            'events': []
        }

    def update_stand(self, action):
        if action == '1':
            self.stand['TPA'] = max(self.stand['TPA'] - 20, 50)
            self.stand['QMD'] += 0.5
            self.stand['carbon'] += 0.8
        elif action == '2':
            self.stand['TPA'] = int(self.stand['TPA'] * 0.75)
            self.stand['QMD'] += 0.6
            self.stand['carbon'] *= 0.95
            self.stand['BA'] *= 0.75
        elif action == '3':
            self.stand['TPA'] = int(self.stand['TPA'] * 0.5)
            self.stand['QMD'] += 0.8
            self.stand['carbon'] *= 0.85
            self.stand['BA'] *= 0.55
        elif action == '4':
            self.stand['TPA'] = int(self.stand['TPA'] * 0.65)
            self.stand['carbon'] *= 0.9
            self.stand['CI'] += 10
            self.stand['BA'] *= 0.7

        self.stand['CI'] = max(15, min(self.stand['CI'], 60))
        self.stand['carbon'] = max(0, min(self.stand['carbon'], 40))

        self.stand['fire_risk'] = 'High' if self.stand['CI'] < 25 else 'Moderate' if self.stand['CI'] < 35 else 'Low'
        self.stand['SPB_risk'] = 'High' if self.stand['BA'] > 100 else 'Moderate' if self.stand['BA'] > 60 else 'Low'

    def simulate_event(self):
        event_log = None
        if random.random() < 0.15 and self.stand['fire_risk'] == 'High':
            self.stand['carbon'] *= 0.6
            self.stand['TPA'] = int(self.stand['TPA'] * 0.4)
            self.stand['CI'] += 15
            event_log = 'Wildfire occurred!'
        elif random.random() < 0.10 and self.stand['SPB_risk'] == 'High':
            self.stand['TPA'] = int(self.stand['TPA'] * 0.7)
            self.stand['BA'] *= 0.8
            event_log = 'SPB outbreak!'
        if event_log:
            self.stand['events'].append((self.stand['year'], event_log))
            return event_log
        return None

    def get_status(self):
        return (
            f"Year: {self.stand['year']} | QMD: {self.stand['QMD']:.1f} | TPA: {self.stand['TPA']} | "
            f"Carbon: {self.stand['carbon']:.1f} MT/ac | CI: {self.stand['CI']:.1f} | "
            f"Fire Risk: {self.stand['fire_risk']} | SPB Risk: {self.stand['SPB_risk']}"
        )

    def get_summary(self):
        summary = f"Final Stand: QMD: {self.stand['QMD']:.1f}, TPA: {self.stand['TPA']}, Carbon: {self.stand['carbon']:.1f} MT/ac, CI: {self.stand['CI']}, Fire Risk: {self.stand['fire_risk']}, SPB Risk: {self.stand['SPB_risk']}\n\n"
        for yr, evt in self.stand['events']:
            summary += f"Year {yr}: {evt}\n"
        return summary