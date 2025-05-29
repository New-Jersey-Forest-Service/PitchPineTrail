# Game logic for Pitch Pine Trail

import random

class Game:
    def __init__(self):
        self.stand = {
            'year': 0,
            'QMD': 6.1,
            'TPA': 553,
            'carbon': 18.0,
            'CI': 15.0,
            'BA': 113,
            'fire_risk': 'High',
            'SPB_risk': 'Moderate',
            'events': []
        }
        self.low_ba_count = 0  # Track consecutive low BA cycles

    def reset_game(self):
        self.stand = {
            'year': 0,
            'QMD': 6.1,
            'TPA': 553,
            'carbon': 18.0,
            'CI': 15.0,
            'BA': 113,
            'fire_risk': 'High',
            'SPB_risk': 'Moderate',
            'events': []
        }
        self.low_ba_count = 0

    def update_stand(self, action):
        if action == '1':
            self.stand['TPA'] = max(self.stand['TPA'] - 20, 50)
            self.stand['QMD'] += 0.5
            self.stand['carbon'] += 0.8
        elif action == '2':
            self.stand['TPA'] = int(self.stand['TPA'] * 0.75)
            self.stand['QMD'] += 0.6
            self.stand['carbon'] *= 0.95
        elif action == '3':
            self.stand['TPA'] = int(self.stand['TPA'] * 0.5)
            self.stand['QMD'] += 0.8
            self.stand['carbon'] *= 0.85
        elif action == '4':
            self.stand['TPA'] = int(self.stand['TPA'] * 0.65)
            self.stand['carbon'] *= 0.9
            self.stand['CI'] += 10

        self.stand['CI'] = max(15, min(self.stand['CI'], 60))
        self.stand['carbon'] = max(0, min(self.stand['carbon'], 40))

        # Correct BA calculation
        self.stand['BA'] = ((self.stand['QMD'] ** 2) * 0.005454) * self.stand['TPA']

        # Update fire_risk based on CI
        if self.stand['CI'] <= 20:
            self.stand['fire_risk'] = 'High'
        elif 20 < self.stand['CI'] < 25:
            self.stand['fire_risk'] = 'Moderate'
        else:
            self.stand['fire_risk'] = 'Low'

        self.stand['SPB_risk'] = 'High' if self.stand['BA'] > 100 else 'Moderate' if self.stand['BA'] > 60 else 'Low'

        # Track consecutive low BA cycles
        if self.stand['BA'] < 35:
            self.low_ba_count += 1
        else:
            self.low_ba_count = 0

    def is_low_ba_game_over(self):
        return self.low_ba_count >= 2

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
            f"BA: {self.stand['BA']:.1f} | "
            f"Carbon: {self.stand['carbon']:.1f} MT/ac | CI: {self.stand['CI']:.1f} | "
            f"Fire Risk: {self.stand['fire_risk']} | SPB Risk: {self.stand['SPB_risk']}"
        )

    def get_status_dict(self):
        return {
            'year': self.stand['year'],
            'QMD': self.stand['QMD'],
            'TPA': self.stand['TPA'],
            'BA': self.stand['BA'],
            'carbon': self.stand['carbon'],
            'CI': self.stand['CI'],
            'fire_risk': self.stand['fire_risk'],
            'SPB_risk': self.stand['SPB_risk']
        }

    def get_summary(self):
        summary = (
            f"Final Stand: QMD: {self.stand['QMD']:.1f}, "
            f"TPA: {self.stand['TPA']}, "
            f"BA: {self.stand['BA']:.1f}, "
            f"Carbon: {self.stand['carbon']:.1f} MT/ac, "
            f"CI: {self.stand['CI']}, "
            f"Fire Risk: {self.stand['fire_risk']}, "
            f"SPB Risk: {self.stand['SPB_risk']}\n\n"
        )
        for yr, evt in self.stand['events']:
            summary += f"Year {yr}: {evt}\n"
        return summary