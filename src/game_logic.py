"""
Pitch Pine Trail - Forest Management Simulation Game

NJ Forest Service
William Zipse
Andrea Brown
Cara Escalona
Justin Gimmillaro
Andrea Brown

---------------------------------------------------
Core game logic for simulating a pitch pine forest stand over time
with different management strategies and random events.
"""

import random
import math

ACTIONS = {
    '1': 'Do nothing',
    '2': 'Thin lightly',
    '3': 'Thin heavily',
    '4': 'Prescribed burn'
}

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

        # Track consecutive low TPA cycles (used for game-over)
        self.low_tpa_count = 0
        self.action_history = []
        # Colonization state (always defined)
        self.pine_snakes_colonized = False
        self.gentian_colonized = False
        self.suitable_tanager_ba_reached = False
        self.summer_tanager_colonized = False
        self.suitable_bunting_ba_reached = False
        self.indigo_bunting_colonized = False
        self.pine_barrens_tree_frog_colonized = False
        # Achievement (persistent trophies)
        self.pine_snake_achieved = False
        self.gentian_achieved = False
        self.summer_tanager_achieved = False
        self.tree_frog_achieved = False
        self.indigo_bunting_achieved = False
        self.turkey_beard_achieved = False
        # Recruitment scheduling: pending additions (applied next cycle) and handled thresholds
        self.recruitment_pending = []        # list of dicts: {'threshold': int, 'ba_at_detection': float}
        self.recruitment_handled = set()     # thresholds already scheduled until BA recovers above threshold+margin
        # One-time popup guards
        self.summer_tanager_screen_shown = False
        self.tree_frog_screen_shown = False
        self.gentian_screen_shown = False
        self.indigo_bunting_screen_shown = False

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

        # Track consecutive low TPA cycles (used for game-over)
        self.low_tpa_count = 0
        self.action_history = []
        # Colonization state (always defined)
        self.pine_snakes_colonized = False
        self.gentian_colonized = False
        self.suitable_tanager_ba_reached = False
        self.summer_tanager_colonized = False
        self.pine_barrens_tree_frog_colonized = False
        self.suitable_bunting_ba_reached = False
        self.indigo_bunting_colonized = False
        # Achievement (persistent trophies)
        self.pine_snake_achieved = False
        self.gentian_achieved = False
        self.summer_tanager_achieved = False
        self.tree_frog_achieved = False
        self.indigo_bunting_achieved = False
        self.turkey_beard_achieved = False
        # Recruitment scheduling: pending additions (applied next cycle) and handled thresholds
        self.recruitment_pending = []        # list of dicts: {'threshold': int, 'ba_at_detection': float}
        self.recruitment_handled = set()     # thresholds already scheduled until BA recovers above threshold+margin
        # One-time popup guards
        self.summer_tanager_screen_shown = False
        self.tree_frog_screen_shown = False
        self.gentian_screen_shown = False
        self.indigo_bunting_screen_shown = False
        
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

        # --- Apply any pending recruitment scheduled last cycle ---
        # Each pending entry was queued when BA dropped below a threshold; now we add many small trees
        # (increase TPA) and reduce QMD (small-diameter recruits). Magnitude scales roughly with
        # log10(threshold / observed_BA) so lower BA => larger recruitment effect.
        if self.recruitment_pending:
            # allow early cancellation: if current BA has recovered above threshold+margin,
            # cancel any pending entries for that threshold (so a rebound before application cancels the one-time add)
            curr_ba = self.stand.get('BA', 0.0)
            filtered = []
            for e in self.recruitment_pending:
                thr = e.get('threshold')
                if thr is not None and curr_ba > (thr + 5):
                    # cancel this scheduled recruitment and clear handled marker so future drops can re-schedule
                    self.recruitment_handled.discard(thr)
                    continue
                filtered.append(e)
            self.recruitment_pending = filtered

            # base additions per threshold (keep your current tuning)
            base_add = {70: 5, 50: 30, 40: 50, 30: 70}
            # Decrement the delay counter for each pending entry; apply only when cycles_remaining <= 0
            for entry in self.recruitment_pending:
                entry['cycles_remaining'] = entry.get('cycles_remaining', 2) - 1

            to_apply = [e for e in self.recruitment_pending if e.get('cycles_remaining', 0) <= 0]
            remaining = [e for e in self.recruitment_pending if e.get('cycles_remaining', 0) > 0]

            for entry in to_apply:
                thr = entry.get('threshold', 70)
                ba_ref = max(0.1, entry.get('ba_at_detection', self.stand['BA']))
                # severity grows with log ratio; ensure non-negative
                severity = max(0.0, math.log10(thr / ba_ref))
                if severity <= 0:
                    continue
                add_tpa = int(base_add.get(thr, 80) * (1.0 + severity))
                # QMD reduction factor: stronger drop that scales with severity and recruits
                # scale by severity and recruit count (clamped)
                qmd_drop_frac = min(0.90, 0.12 * (1.0 + severity) + 0.0012 * add_tpa)
                tpa_next = max(1, int(tpa_next + add_tpa))
                qmd_next = max(2.0, qmd_next * (1.0 - qmd_drop_frac))
            # keep any entries still waiting
            self.recruitment_pending = remaining

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

        # --- Schedule recruitment if BA dropped under thresholds (delayed one cycle) ---
        # Thresholds (from highest to lowest). When BA falls below a threshold and it hasn't been
        # recently handled, schedule an addition for the next cycle.
        thresholds = [70, 50, 40, 30]
        for thr in thresholds:
            if ba_next < thr and thr not in self.recruitment_handled:
                # schedule for application after 2 cycles using the BA observed now
                self.recruitment_pending.append({
                    'threshold': thr,
                    'ba_at_detection': ba_next,
                    'cycles_remaining': 2
                })
                self.recruitment_handled.add(thr)
            # clear handled flag if BA recovers above thr + margin so future drops can schedule again
            elif ba_next > (thr + 5) and thr in self.recruitment_handled:
                self.recruitment_handled.discard(thr)
                # also remove any pending entries for this threshold (cancel scheduled addition)
                self.recruitment_pending = [e for e in self.recruitment_pending if e.get('threshold') != thr]

        # Step 9: record if BA ever in 30–45 window for summer tanager colonization
        if 30 <= ba_next <= 50:
            self.suitable_tanager_ba_reached = True
            self.suitable_bunting_ba_reached = True

        # Step 10: Track low TPA for game-over
        if tpa_next <= 20:
            self.low_tpa_count += 1
        else:
            self.low_tpa_count = 0

        # Step 11: Pine snake logic
        if (45 <= ba_next <= 70) and not self.pine_snakes_colonized:
            if random.random() < 0.3:
                self.pine_snakes_colonized = True

        # Step 12: Gentian logic (only after prescribed burn)
        if action == '4' and not self.gentian_colonized:
            if random.random() < 0.2:
                self.gentian_colonized = True

        # Step 13: Turkey Beard achievement (50% chance when prescribed burn and BA < 60)
        if action == '4' and ba_next < 60 and not self.turkey_beard_achieved:
            if random.random() < 0.5:
                self.turkey_beard_achieved = True

        # Step 14: Summer Tanager logic (0.4 probability once conditions met)
        if (not self.summer_tanager_colonized
            and self.suitable_tanager_ba_reached
            and len(self.action_history) >= 2
            and self.action_history[-1][1] == '1'
            and self.action_history[-2][1] == '1'):
            if random.random() < 0.4:
                self.summer_tanager_colonized = True

        # Step 15Indigo Bunting logic (0.4 probability once conditions met)
        if (not self.indigo_bunting_colonized
            and self.suitable_bunting_ba_reached
            and len(self.action_history) >= 2
            and self.action_history[-1][1] == '1'
            and self.action_history[-2][1] == '1'):
            if random.random() < 0.4:
                self.indigo_bunting_colonized = True

        # Step 16: Pine Barrens tree frog logic
        # Colonize after sequence: heavy thin ('3') -> prescribed burn ('4') -> >=2 consecutive '1's
        if not self.pine_barrens_tree_frog_colonized:
            # Include current action in the sequence check (since we append after logic)
            actions = [a for (_, a) in self.action_history] + [action]
            if len(actions) >= 4:
                # Count trailing 'Do nothing' ('1') actions
                i = len(actions) - 1
                trailing_no_mgmt = 0
                while i >= 0 and actions[i] == '1':
                    trailing_no_mgmt += 1
                    i -= 1
                # Require at least two '1's and that they are immediately preceded by '4' then '3'
                if trailing_no_mgmt >= 2 and i >= 1 and actions[i] == '4' and actions[i - 1] == '3':
                    if random.random() < 0.8:  # 80% chance to colonize
                        self.pine_barrens_tree_frog_colonized = True

        # After updating the stand/year, record the action:
        self.action_history.append((self.stand['year'], action))

        

    def is_low_tpa_game_over(self):
        """Check if game should end due to one-time (rather than consecutive low TPA conditions. change 1 to 2 for consecutive low conditions"""
        return getattr(self, 'low_tpa_count', 0) >= 1

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
            
        if self.gentian_colonized:
            summary += "\nGentian is now growing in this stand!\n"

        if self.summer_tanager_colonized:
            summary += "\nSummer tanager has colonized this stand!\n"

        if self.indigo_bunting_colonized:
            summary += "\nIndigo bunting has colonized this stand!\n"

        if self.pine_barrens_tree_frog_colonized:
            summary += "\nPine Barrens tree frog has colonized this stand!\n"

        if self.turkey_beard_achieved:
            summary += "\nTurkey Beard is now growing in this stand!\n"

        return summary

    def get_action_summary(self):
        lines = []
        for year, action in self.action_history:
            action_name = ACTIONS.get(str(action), str(action))
            lines.append(f"Year {year}: {action_name}")
        return "\n".join(lines) if lines else "No actions taken."