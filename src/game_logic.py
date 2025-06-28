"""
Pitch Pine Trail - Forest Management Simulation Game

NJ Forest Service
William Zipse
Cara Escalona
Justin Gimmillaro

---------------------------------------------------
Core game logic for simulating a pitch pine forest stand over time
with different management strategies and random events.
"""

import random
import math

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
        qmd = 5.5
        tpa = 650
        ba = round(0.005454 * tpa * (qmd ** 2), 1)

        self.stand = {
            'year': 0,
            'QMD': qmd,               # Quadratic Mean Diameter (inches)
            'TPA': tpa,               # Trees Per Acre
            'carbon': 20.0,           # Carbon storage (MT/ac)
            'CI': 18.0,               # Crowning Index (20-ft wind speed in mph)
            'BA': ba,                 # Basal Area (sq ft/acre)
            'fire_risk': 'High',
            'SPB_risk': 'Moderate',
            'events': [],
            'catastrophic_wildfire': False
        }

        self.low_ba_count = 0   # Track consecutive low BA cycles
        self.pine_snakes_colonized = False  # Track pine snake colonization

    def reset_game(self):
        """Reset the game to initial conditions."""
        qmd = 5.5
        tpa = 650
        ba = round(0.005454 * tpa * (qmd ** 2), 1)

        self.stand = {
            'year': 0,
            'QMD': qmd,
            'TPA': tpa,
            'carbon': 20.0,
            'CI': 18.0,
            'BA': ba,
            'fire_risk': 'High',
            'SPB_risk': 'Moderate',
            'events': [],
            'catastrophic_wildfire': False
        }

        self.low_ba_count = 0
        self.pine_snakes_colonized = False

    def update_stand(self, action):
        """
        Update forest stand characteristics using Reineke-based growth and Crowning Index logic.

        Args:
            action (str): Management action ('1'=none, '2'=thin_light, '3'=thin_heavy, '4'=fire)
        """
        import math

        def max_tpa_reineke(qmd, a=4.253, b=1.6):
            return 10 ** (a - b * math.log10(qmd))

        def calculate_ba(qmd, tpa):
            return 0.005454 * tpa * (qmd ** 2)

        def grow_qmd(qmd, management):
            annual_growth = {
                '1': 0.009,  # none (~9.4% over 10 yrs)
                '2': 0.015,
                '3': 0.022,
                '4': 0.013
            }
            rate = annual_growth.get(management, 0.009)
            return qmd * ((1 + rate) ** 10)

        def apply_management_tpa(tpa, management):
            if management == '2':
                return tpa * 0.75
            elif management == '3':
                return tpa * 0.50
            elif management == '4':
                return tpa * 0.65
            else:
                return tpa * 0.97  # natural mortality

        # Step 1: Apply management effects
        tpa_next = apply_management_tpa(self.stand['TPA'], action)
        qmd_next = grow_qmd(self.stand['QMD'], action)

        # Step 2: Enforce Reineke limit
        max_tpa = max_tpa_reineke(qmd_next)
        tpa_next = min(tpa_next, max_tpa)

        # Step 3: Recalculate BA
        ba_next = calculate_ba(qmd_next, tpa_next)

        # Step 4: Carbon update
        carbon = self.stand['carbon']
        if action == '1':
            carbon += 0.5
        elif action == '2':
            carbon *= 0.96
        elif action == '3':
            carbon *= 0.88
        elif action == '4':
            carbon *= 0.90
        carbon = min(max(carbon, 0), 40)

        # Step 5: Crowning Index logic
        CI = self.stand['CI']
        if action in ['2', '3', '4']:
            CI = min(60, CI + 3)
        else:
            CI = max(15, CI - 2)

        # Step 6: Fire Risk from CI
        fire_risk = (
            "High" if CI <= 20 else
            "Moderate" if CI < 25 else
            "Low"
        )

        # Step 7: SPB risk from BA
        spb_risk = (
            "High" if ba_next > 100 else
            "Moderate" if ba_next > 60 else
            "Low"
        )

        # Step 8: Update internal state
        self.stand['TPA'] = round(tpa_next)
        self.stand['QMD'] = round(qmd_next, 2)
        self.stand['BA'] = round(ba_next, 1)
        self.stand['carbon'] = round(carbon, 1)
        self.stand['CI'] = CI
        self.stand['fire_risk'] = fire_risk
        self.stand['SPB_risk'] = spb_risk

        # Step 9: Track low BA for game-over
        if ba_next < 35:
            self.low_ba_count += 1
        else:
            self.low_ba_count = 0

        # Step 10: Pine snake logic
        if (45 <= ba_next <= 70) and not self.pine_snakes_colonized:
            if random.random() < 0.5:
                self.pine_snakes_colonized = True

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

        if self.pine_snakes_colonized:
            summary += "\nPine snakes are utilizing this stand!\n"
            
        return summary