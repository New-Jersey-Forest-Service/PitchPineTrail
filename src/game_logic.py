"""
Pitch Pine Trail - Forest Management Simulation Game

William Zipse
Cara Escalona
Justin Gimmillaro
NJ Forest Service
---------------------------------------------------
Core game logic for simulating a pitch pine forest stand over time
with different management strategies and random events.
"""

import random

class Game:
    """
    Manages the forest stand simulation, including tree growth, management actions,
    natural events, and tracking of forest health metrics.
    
    Attributes:
        stand (dict): Forest stand characteristics and history
        low_ba_count (int): Tracks consecutive cycles with low basal area
    """
    
    def __init__(self):
        """Initialize a new game with default forest stand values."""
        self.stand = {
            'year': 0,
            'QMD': 6.1,         # Quadratic Mean Diameter (inches)
            'TPA': 553,         # Trees Per Acre
            'carbon': 18.0,     # Carbon storage (MT/ac)
            'CI': 15.0,         # Competition Index
            'BA': 113,          # Basal Area (sq ft/acre)
            'fire_risk': 'High',
            'SPB_risk': 'Moderate',  # Southern Pine Beetle risk
            'events': [],
            'catastrophic_wildfire': False
        }
        self.low_ba_count = 0   # Track consecutive low BA cycles

    def reset_game(self):
        """Reset the game to initial conditions."""
        self.stand = {
            'year': 0,
            'QMD': 6.1,
            'TPA': 553,
            'carbon': 18.0,
            'CI': 15.0,
            'BA': 113,
            'fire_risk': 'High',
            'SPB_risk': 'Moderate',
            'events': [],
            'catastrophic_wildfire': False
        }
        self.low_ba_count = 0

    def update_stand(self, action):
        """
        Update forest stand characteristics based on management action.
        
        Args:
            action (str): The selected management action ('1'-'4')
                '1': Do nothing (natural growth)
                '2': Thin lightly
                '3': Thin heavily
                '4': Prescribed burn
        """
        # Apply management action effects
        if action == '1':  # Do nothing
            self.stand['TPA'] = max(self.stand['TPA'] - 20, 50)  # Natural mortality
            self.stand['QMD'] += 0.5  # Natural growth
            self.stand['carbon'] += 0.8
        elif action == '2':  # Thin lightly
            self.stand['TPA'] = int(self.stand['TPA'] * 0.75)
            self.stand['QMD'] += 0.6
            self.stand['carbon'] *= 0.95
        elif action == '3':  # Thin heavily
            self.stand['TPA'] = int(self.stand['TPA'] * 0.5)
            self.stand['QMD'] += 0.8
            self.stand['carbon'] *= 0.85
        elif action == '4':  # Prescribed burn
            self.stand['TPA'] = int(self.stand['TPA'] * 0.65)
            self.stand['carbon'] *= 0.9
            self.stand['CI'] += 10  # Reduce competition

        # Apply constraints to prevent unrealistic values
        self.stand['CI'] = max(15, min(self.stand['CI'], 60))
        self.stand['carbon'] = max(0, min(self.stand['carbon'], 40))

        # Calculate Basal Area using forestry formula: BA = (QMD² × 0.005454) × TPA
        self.stand['BA'] = ((self.stand['QMD'] ** 2) * 0.005454) * self.stand['TPA']

        # Update fire risk based on Competition Index
        if self.stand['CI'] <= 20:
            self.stand['fire_risk'] = 'High'
        elif 20 < self.stand['CI'] < 25:
            self.stand['fire_risk'] = 'Moderate'
        else:
            self.stand['fire_risk'] = 'Low'

        # Update Southern Pine Beetle risk based on Basal Area
        self.stand['SPB_risk'] = 'High' if self.stand['BA'] > 100 else 'Moderate' if self.stand['BA'] > 60 else 'Low'

        # Track consecutive low BA cycles for game-over condition
        if self.stand['BA'] < 35:
            self.low_ba_count += 1
        else:
            self.low_ba_count = 0

    def is_low_ba_game_over(self):
        """Check if game should end due to consecutive low BA conditions."""
        return self.low_ba_count >= 2

    def simulate_event(self):
        """
        Simulate random forest events based on current risk factors.

        Returns:
            str or None: Description of event that occurred, or None if no event
        """
        event_log = None

        # Wildfire chance increases with high fire risk
        if random.random() < 0.15 and self.stand['fire_risk'] == 'High':
            self.stand['carbon'] *= 0.6
            self.stand['TPA'] = int(self.stand['TPA'] * 0.4)
            self.stand['CI'] += 15
            event_log = 'Wildfire occurred!'
            # Signal catastrophic wildfire for GUI
            self.stand['catastrophic_wildfire'] = True
        else:
            self.stand['catastrophic_wildfire'] = False

        # SPB outbreak chance increases with high SPB risk
        if not event_log and random.random() < 0.10 and self.stand['SPB_risk'] == 'High':
            self.stand['TPA'] = int(self.stand['TPA'] * 0.7)
            self.stand['BA'] *= 0.8
            event_log = 'SPB outbreak!'

        if event_log:
            self.stand['events'].append((self.stand['year'], event_log))
            return event_log
        return None

    def get_status(self):
        """Get current stand status as a formatted string."""
        return (
            f"Year: {self.stand['year']} | QMD: {self.stand['QMD']:.1f} | TPA: {self.stand['TPA']} | "
            f"BA: {self.stand['BA']:.1f} | "
            f"Carbon: {self.stand['carbon']:.1f} MT/ac | CI: {self.stand['CI']:.1f} | "
            f"Fire Risk: {self.stand['fire_risk']} | SPB Risk: {self.stand['SPB_risk']}"
        )

    def get_status_dict(self):
        """Get current stand status as a dictionary."""
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
        """Get summary of final stand conditions and event history."""
        summary = (
            f"Final Stand: QMD: {self.stand['QMD']:.1f}, "
            f"TPA: {self.stand['TPA']}, "
            f"BA: {self.stand['BA']:.1f}, "
            f"Carbon: {self.stand['carbon']:.1f} MT/ac, "
            f"CI: {self.stand['CI']}, "
            f"Fire Risk: {self.stand['fire_risk']}, "
            f"SPB Risk: {self.stand['SPB_risk']}\n\n"
        )
        
        if self.stand['events']:
            summary += "Events during your management:\n"
            for yr, evt in self.stand['events']:
                summary += f"  Year {yr}: {evt}\n"
        else:
            summary += "No major events occurred during your management.\n"
        return summary