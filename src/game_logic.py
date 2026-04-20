"""
Pitch Pine Trail - Forest Management Simulation Game

NJ Forest Service
William Zipse
Andrea Brown
Cara Escalona
Justin Gimmillaro

---------------------------------------------------
Core game logic for simulating a pitch pine forest stand over time
with different management strategies and random events.
"""

import random
import math
from copy import deepcopy
import pandas as pd

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
        # Preserve the initial starting conditions so we can show them as Year -1
        self.initial_stand = deepcopy(self.stand)

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
        self.short_colonized = False
        # Achievement (persistent trophies)
        self.pine_snake_achieved = False
        self.gentian_achieved = False
        self.summer_tanager_achieved = False
        self.tree_frog_achieved = False
        self.indigo_bunting_achieved = False
        self.short_achieved = False
        self.turkey_beard_achieved = False
        # History of achievements: list of tuples (year, name)
        self.achievements_history = []
        # Recruitment scheduling: pending additions (applied next cycle) and handled thresholds
        self.recruitment_pending = []        # list of dicts: {'threshold': int, 'ba_at_detection': float}
        self.recruitment_handled = set()     # thresholds already scheduled until BA recovers above threshold+margin
        # One-time popup guards
        self.summer_tanager_screen_shown = False
        self.tree_frog_screen_shown = False
        self.gentian_screen_shown = False
        self.indigo_bunting_screen_shown = False
        self.short_screen_shown = False
        # Track whether a hurricane has occurred in this game (only allow once)
        self.hurricane_occurred = False
        # Track whether the hurricane screen has already been shown this game
        self.hurricane_screen_shown = False

        # History: snapshot of stand state after each update_stand call
        # Each entry: dict with keys 'year','QMD','TPA','BA','carbon','CI','fire_risk','SPB_risk','events'
        self.history = []

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
        # Preserve the initial starting conditions so we can show them as Year -1
        self.initial_stand = deepcopy(self.stand)

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
        self.short_colonized = False
        # Achievement (persistent trophies)
        self.pine_snake_achieved = False
        self.gentian_achieved = False
        self.summer_tanager_achieved = False
        self.tree_frog_achieved = False
        self.indigo_bunting_achieved = False
        self.short_achieved = False
        self.turkey_beard_achieved = False
        # History of achievements: list of tuples (year, name)
        self.achievements_history = []
        # Recruitment scheduling: pending additions (applied next cycle) and handled thresholds
        self.recruitment_pending = []        # list of dicts: {'threshold': int, 'ba_at_detection': float}
        self.recruitment_handled = set()     # thresholds already scheduled until BA recovers above threshold+margin
        # One-time popup guards
        self.summer_tanager_screen_shown = False
        self.tree_frog_screen_shown = False
        self.gentian_screen_shown = False
        self.indigo_bunting_screen_shown = False
        self.short_screen_shown = False

        # Clear runtime history
        self.history = []
        # Reset one-time hurricane flag
        self.hurricane_occurred = False
        # Reset hurricane-screen-shown flag
        self.hurricane_screen_shown = False

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

        # Record the fire risk prior to applying this management (used for certain event triggers)
        prev_fire_risk = self.stand.get('fire_risk', None)

        # --- Apply any pending recruitment scheduled last cycle ---
        # Track carbon added by recruitment (TPA increases should raise carbon)
        recruited_carbon_increase = 0.0
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
                # Carbon increase due to recruitment: small per-tree increment scaled by severity
                # (units: MT per acre). Tune `carbon_per_tree` if needed.
                carbon_per_tree = 0.02
                carb_inc = add_tpa * carbon_per_tree * (1.0 + severity)
                recruited_carbon_increase += carb_inc
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
        # Add carbon contributed by recruitment (TPA increases)
        carbon += recruited_carbon_increase
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

        # Step 9: record if BA ever in 30–50 window for summer tanager colonization
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
                # record achievement event
                try:
                    self.add_achievement('Pine snake', self.stand.get('year', 0))
                except Exception:
                    pass

        # Step 12: Gentian logic (only after prescribed burn)
        if action == '4' and not self.gentian_colonized:
            if random.random() < 0.2:
                self.gentian_colonized = True
                try:
                    self.add_achievement('Gentian', self.stand.get('year', 0))
                except Exception:
                    pass

        # Step 13: Turkey Beard achievement (50% chance when prescribed burn and BA < 60)
        if action == '4' and ba_next < 60 and not self.turkey_beard_achieved:
            if random.random() < 0.5:
                self.turkey_beard_achieved = True
                try:
                    self.add_achievement('Turkey Beard', self.stand.get('year', 0))
                except Exception:
                    pass

        # Step 14: Summer Tanager logic (0.4 probability once conditions met)
        # Include the current action when checking for two consecutive 'Do nothing' ('1')
        actions = [a for (_, a) in self.action_history] + [action]
        if (not self.summer_tanager_colonized
            and self.suitable_tanager_ba_reached
            and len(actions) >= 2
            and actions[-1] == '1'
            and actions[-2] == '1'):
            if random.random() < 0.4:
                self.summer_tanager_colonized = True
                try:
                    self.add_achievement('Summer Tanager', self.stand.get('year', 0))
                except Exception:
                    pass

        # Step 15: Indigo Bunting logic (0.4 probability once conditions met)
        # Include the current action when checking for two consecutive 'Do nothing' ('1')
        actions = [a for (_, a) in self.action_history] + [action]
        if (not self.indigo_bunting_colonized
            and self.suitable_bunting_ba_reached
            and len(actions) >= 2
            and actions[-1] == '1'
            and actions[-2] == '1'):
            if random.random() < 0.4:
                self.indigo_bunting_colonized = True
                try:
                    self.add_achievement('Indigo Bunting', self.stand.get('year', 0))
                except Exception:
                    pass

        # Step 16: Shortleaf pine ("short") logic - mimics pine snake but 20% chance
        if (45 <= ba_next <= 70) and not getattr(self, 'short_colonized', False):
            if random.random() < 0.2:
                self.short_colonized = True
                self.short_achieved = True
                try:
                    self.add_achievement('Shortleaf pine', self.stand.get('year', 0))
                except Exception:
                    pass

        # Step 17: Pine Barrens tree frog logic
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
                        try:
                            self.add_achievement('Pine Barrens tree frog', self.stand.get('year', 0))
                        except Exception:
                            pass

        # After updating the stand/year, record the action:
        # Step 18: Hurricane event (5% chance, non-losing)
        # If a hurricane occurs, record its metric impacts as occurring 1 year after
        # the action (e.g., year 50 -> effects recorded at year 51) while still
        # applying the changes to the live stand so the UI can display them.
        hurricane_occurred = False
        try:
            events = self.stand.get('events', [])
            curr_year = self.stand.get('year', 0)
            already_this_year = any(
                (isinstance(e, (list, tuple)) and len(e) > 1 and e[0] == curr_year and e[1] == 'Hurricane passed through')
                or (isinstance(e, str) and e == 'Hurricane passed through')
                for e in events
            )
        except Exception:
            already_this_year = False

        # Only allow a single hurricane per game. Check the game-level flag
        # (`hurricane_occurred`) and also ensure no prior hurricane event exists
        # in the stand event list. Use a 5% chance.
        try:
            prior_hurricane_exists = any(
                (isinstance(e, (list, tuple)) and len(e) > 1 and e[1] == 'Hurricane passed through')
                or (isinstance(e, str) and e == 'Hurricane passed through')
                for e in self.stand.get('events', [])
            )
        except Exception:
            prior_hurricane_exists = False

        if (not getattr(self, 'hurricane_occurred', False)) and (not prior_hurricane_exists) and random.random() < 0.05:
            # Build a pre-hurricane snapshot reflecting the stand immediately after
            # management but before the hurricane (events list before hurricane)
            pre_snapshot = {
                'year': int(curr_year),
                'QMD': float(self.stand.get('QMD', 0.0)),
                'TPA': int(round(self.stand.get('TPA', 0))),
                'BA': float(self.stand.get('BA', 0.0)),
                'carbon': float(self.stand.get('carbon', 0.0)),
                'CI': float(self.stand.get('CI', 0.0)),
                'fire_risk': self.stand.get('fire_risk'),
                'SPB_risk': self.stand.get('SPB_risk'),
                'events': deepcopy(self.stand.get('events', []))
            }

            # Choose a random post-decade year offset (2–9 years after the
            # triggering decadal year) so hurricane effects are recorded within
            # the same decade rather than always +1.
            offset = random.randint(2, 9)
            post_year = int(curr_year) + offset

            # Apply hurricane metric changes immediately so UI displays them
            new_tpa = int(max(1, round(self.stand.get('TPA', 0) * 0.8)))
            new_carbon = round(max(0.0, float(self.stand.get('carbon', 0.0)) * 0.9), 1)
            self.stand['TPA'] = new_tpa
            self.stand['carbon'] = round(new_carbon, 1)
            # Recalculate BA based on updated TPA and current QMD
            try:
                ba_after = calculate_ba(self.stand.get('QMD', 0.0), new_tpa)
            except Exception:
                ba_after = 0.0
            self.stand['BA'] = round(ba_after, 1)
            # Update SPB risk based on new BA
            spb_after = (
                "High" if ba_after > 100 else
                "Moderate" if ba_after > 60 else
                "Low"
            )
            self.stand['SPB_risk'] = spb_after
            # Increase CI by 1 due to hurricane impact and update fire risk
            try:
                ci_after = int(round(self.stand.get('CI', 0))) + 1
                # enforce upper bound consistent with CI logic elsewhere
                ci_after = min(60, ci_after)
            except Exception:
                ci_after = self.stand.get('CI', 0)
            self.stand['CI'] = ci_after
            fire_risk_after = (
                "High" if ci_after <= 20 else
                "Moderate" if ci_after < 25 else
                "Low"
            )
            self.stand['fire_risk'] = fire_risk_after
            evt = 'Hurricane passed through'
            # Append event only if not already present to avoid duplicates
            try:
                events = self.stand.setdefault('events', [])
                if not any((isinstance(e, (list, tuple)) and len(e) > 1 and e[0] == post_year and e[1] == evt) or (isinstance(e, str) and e == evt) for e in events):
                    events.append((post_year, evt))
            except Exception:
                try:
                    self.stand.setdefault('events', []).append((post_year, evt))
                except Exception:
                    pass

            try:
                if not hasattr(self, 'hurricane_years'):
                    self.hurricane_years = set()
                self.hurricane_years.add(post_year)
                # mark that a hurricane has occurred so it cannot happen again this game
                self.hurricane_occurred = True
            except Exception:
                pass

            # Post-hurricane snapshot recorded as year+1
            post_snapshot = {
                'year': int(post_year),
                'QMD': float(self.stand.get('QMD', 0.0)),
                'TPA': int(round(self.stand.get('TPA', 0))),
                'BA': float(self.stand.get('BA', 0.0)),
                'carbon': float(self.stand.get('carbon', 0.0)),
                'CI': float(self.stand.get('CI', 0.0)),
                'fire_risk': self.stand.get('fire_risk'),
                'SPB_risk': self.stand.get('SPB_risk'),
                'events': deepcopy(self.stand.get('events', []))
            }

            # Append both snapshots so the hurricane effect is visible at year+1
            self.history.append(pre_snapshot)
            self.history.append(post_snapshot)
            hurricane_occurred = True

        # --- Non-losing wildfire event (scheduled at year+1 when triggered) ---
        wildfire_occurred = False
        try:
            # Trigger: prescribed burn (action '4') while PRE-ACTION Fire Risk was High -> 50% chance
            # Use the prior fire risk (`prev_fire_risk`) because CI/fire_risk is updated by the management action.
            curr_year = self.stand.get('year', 0)
            if action == '4' and prev_fire_risk == 'High' and random.random() < 0.5:
                # Pre-snapshot (immediately after management, before wildfire effects)
                pre_snapshot = {
                    'year': int(curr_year),
                    'QMD': float(self.stand.get('QMD', 0.0)),
                    'TPA': int(round(self.stand.get('TPA', 0))),
                    'BA': float(self.stand.get('BA', 0.0)),
                    'carbon': float(self.stand.get('carbon', 0.0)),
                    'CI': float(self.stand.get('CI', 0.0)),
                    'fire_risk': self.stand.get('fire_risk'),
                    'SPB_risk': self.stand.get('SPB_risk'),
                    'events': deepcopy(self.stand.get('events', []))
                }

                post_year = int(curr_year) + 1

                # Apply immediate metric changes for the wildfire event
                new_tpa = int(max(1, round(self.stand.get('TPA', 0) * 0.5)))  # decrease by 50%
                new_carbon = round(max(0.0, float(self.stand.get('carbon', 0.0)) * 0.6), 1)  # decrease by 40%
                self.stand['TPA'] = new_tpa
                self.stand['carbon'] = new_carbon

                # Recalculate BA based on updated TPA and current QMD
                try:
                    ba_after = calculate_ba(self.stand.get('QMD', 0.0), new_tpa)
                except Exception:
                    ba_after = 0.0
                self.stand['BA'] = round(ba_after, 1)

                # Update SPB risk based on new BA
                spb_after = (
                    "High" if ba_after > 100 else
                    "Moderate" if ba_after > 60 else
                    "Low"
                )
                self.stand['SPB_risk'] = spb_after

                # Increase CI by 3
                try:
                    ci_after = int(round(self.stand.get('CI', 0))) + 3
                    ci_after = min(60, ci_after)
                except Exception:
                    ci_after = self.stand.get('CI', 0)
                self.stand['CI'] = ci_after

                # Update fire risk based on new CI
                fire_risk_after = (
                    "High" if ci_after <= 20 else
                    "Moderate" if ci_after < 25 else
                    "Low"
                )
                self.stand['fire_risk'] = fire_risk_after

                evt = 'WILDFIRE'
                # Append event for both the current (pre_snapshot) and post_year snapshot
                # (avoid duplicates). Recording an immediate/current-year event ensures the
                # UI can present the non-losing wildfire screen the turn it was triggered.
                try:
                    events = self.stand.setdefault('events', [])
                    # add post-year event if not present
                    if not any((isinstance(e, (list, tuple)) and len(e) > 1 and e[0] == post_year and e[1] == evt) or (isinstance(e, str) and e == evt) for e in events):
                        events.append((post_year, evt))
                    # also add an immediate/current-year event so pre_snapshot reflects the trigger
                    if not any((isinstance(e, (list, tuple)) and len(e) > 1 and e[0] == curr_year and e[1] == evt) or (isinstance(e, str) and e == evt) for e in events):
                        events.append((curr_year, evt))
                except Exception:
                    try:
                        self.stand.setdefault('events', []).append((post_year, evt))
                        self.stand.setdefault('events', []).append((curr_year, evt))
                    except Exception:
                        pass

                # Ensure both snapshots include the updated events list
                post_snapshot = {
                    'year': int(post_year),
                    'QMD': float(self.stand.get('QMD', 0.0)),
                    'TPA': int(round(self.stand.get('TPA', 0))),
                    'BA': float(self.stand.get('BA', 0.0)),
                    'carbon': float(self.stand.get('carbon', 0.0)),
                    'CI': float(self.stand.get('CI', 0.0)),
                    'fire_risk': self.stand.get('fire_risk'),
                    'SPB_risk': self.stand.get('SPB_risk'),
                    'events': deepcopy(self.stand.get('events', []))
                }

                # Update pre_snapshot events so the immediate trigger is visible now
                try:
                    pre_snapshot['events'] = deepcopy(self.stand.get('events', []))
                except Exception:
                    pass

                # Append both snapshots so the wildfire effect is visible at year+1 and
                # the trigger is visible immediately in the pre-snapshot
                self.history.append(pre_snapshot)
                self.history.append(post_snapshot)
                wildfire_occurred = True
        except Exception:
            wildfire_occurred = False

        # Record the action in history
        self.action_history.append((self.stand['year'], action))

        # If hurricane already appended detailed snapshots above, record a HURRICANE
        # action for the post-year snapshot so exports include it, then skip default snapshot
        if hurricane_occurred:
            try:
                base = int(curr_year)
            except Exception:
                base = int(self.stand.get('year', 0))
            offset_val = offset if 'offset' in locals() else 1
            post_action_year = base + offset_val
            # avoid duplicate entries for the same year/action
            exists = any((y == post_action_year and a == 'HURRICANE') for (y, a) in self.action_history)
            if not exists:
                self.action_history.append((post_action_year, 'HURRICANE'))
            return

        # If a scheduled non-losing wildfire was just applied above, record a WILDFIRE
        # action for the post-year snapshot (year+1) so exports include it, then skip default snapshot
        if wildfire_occurred:
            try:
                base = int(curr_year)
            except Exception:
                base = int(self.stand.get('year', 0))
            post_action_year = base + 1
            # avoid duplicate entries for the same year/action
            exists = any((y == post_action_year and a == 'WILDFIRE') for (y, a) in self.action_history)
            if not exists:
                self.action_history.append((post_action_year, 'WILDFIRE'))
            return

        # --- Snapshot current stand into history for later analysis/plotting ---
        snapshot = {
            'year': int(self.stand.get('year', 0)),
            'QMD': float(self.stand.get('QMD', 0.0)),
            'TPA': int(round(self.stand.get('TPA', 0))),
            'BA': float(self.stand.get('BA', 0.0)),
            'carbon': float(self.stand.get('carbon', 0.0)),
            'CI': float(self.stand.get('CI', 0.0)),
            'fire_risk': self.stand.get('fire_risk'),
            'SPB_risk': self.stand.get('SPB_risk'),
            # store a deep copy of events up to this year
            'events': deepcopy(self.stand.get('events', []))
        }
        self.history.append(snapshot)

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
        if getattr(self, 'short_colonized', False):
            summary += "\nShortleaf pine has established in this stand!\n"
            
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

    def add_achievement(self, name, year=None):
        """Record an achievement with the year it occurred.

        Avoid duplicates: if the same achievement already recorded, do nothing.
        """
        try:
            yr = int(year) if year is not None else int(self.stand.get('year', 0))
        except Exception:
            yr = self.stand.get('year', 0)
        # avoid duplicates
        for y, n in self.achievements_history:
            if n == name:
                return
        self.achievements_history.append((yr, name))

    def get_achievements_list(self):
        """Return achievements history as list of (year,name), sorted by year."""
        return sorted(self.achievements_history, key=lambda x: x[0])

    def get_action_summary(self):
        lines = []
        for year, action in self.action_history:
            action_name = ACTIONS.get(str(action), str(action))
            lines.append(f"Year {year}: {action_name}")
        return "\n".join(lines) if lines else "No actions taken."

    def get_decadal_dataframe(self, interval=10):
        """
        Return a pandas DataFrame containing snapshots at every `interval` years.
        - Rows: years (one row per decadal year)
        - Columns: variables ['Year','QMD','TPA','BA','carbon','CI','fire_risk','SPB_risk','events']
        If pandas is not available this will raise ImportError.
        """
        # Ensure we have history; include current stand if not already present
        if not self.history:
            # create a single-row snapshot from current stand
            current = {
                'year': int(self.stand.get('year', 0)),
                'QMD': float(self.stand.get('QMD', 0.0)),
                'TPA': int(round(self.stand.get('TPA', 0))),
                'BA': float(self.stand.get('BA', 0.0)),
                'carbon': float(self.stand.get('carbon', 0.0)),
                'CI': float(self.stand.get('CI', 0.0)),
                'fire_risk': self.stand.get('fire_risk'),
                'SPB_risk': self.stand.get('SPB_risk'),
            }
            snaps = [current]
        else:
            snaps = self.history.copy()
            # also ensure current stand is represented (avoid duplicate years)
            curr_year = int(self.stand.get('year', 0))
            if not any(s['year'] == curr_year for s in snaps):
                snaps.append({
                    'year': curr_year,
                    'QMD': float(self.stand.get('QMD', 0.0)),
                    'TPA': int(round(self.stand.get('TPA', 0))),
                    'BA': float(self.stand.get('BA', 0.0)),
                    'carbon': float(self.stand.get('carbon', 0.0)),
                    'CI': float(self.stand.get('CI', 0.0)),
                    'fire_risk': self.stand.get('fire_risk'),
                    'SPB_risk': self.stand.get('SPB_risk'),
                })

        # Ensure the initial starting conditions are included as Year -1
        try:
            init = getattr(self, 'initial_stand', None)
            if init is not None:
                if not any(s.get('year') == -1 for s in snaps):
                    snaps.append({
                        'year': -1,
                        'QMD': float(init.get('QMD', 0.0)),
                        'TPA': int(round(init.get('TPA', 0))),
                        'BA': float(init.get('BA', 0.0)),
                        'carbon': float(init.get('carbon', 0.0)),
                        'CI': float(init.get('CI', 0.0)),
                        'fire_risk': init.get('fire_risk'),
                        'SPB_risk': init.get('SPB_risk'),
                    })
        except Exception:
            pass

        # Build dict year->snapshot (prefer latest snapshot for duplicate years)
        year_map = {}
        for s in snaps:
            year_map[int(s['year'])] = s

        # Select years to include in the decadal dataframe.
        # Always include Year -1. Include standard decadal years (y % interval == 0).
        # Additionally include any off-decade snapshot that immediately follows a decadal year
        # (e.g., hurricane post-snapshot at year 51 following year 50) so the effect is visible.
        base_years = set(y for y in year_map.keys() if (y == -1) or (interval == 1) or (y % interval == 0))
        # Include off-decade snapshots that fall within the same decade after a
        # decadal base year (e.g., a hurricane recorded at year 42 after base 40).
        extra_years = set()
        decadal_bases = set(y for y in year_map.keys() if (y != -1) and (interval != 1) and (y % interval == 0))
        for y in year_map.keys():
            if y in base_years:
                continue
            for d in decadal_bases:
                if d < y <= d + (interval - 1):
                    extra_years.add(y)
                    break

        years = sorted(base_years.union(extra_years))

        # If no decadal years found, return empty dataframe with expected columns
        columns = ['Year', 'QMD', 'TPA', 'BA', 'Carbon', 'CI', 'Fire risk', 'SPB risk']
        if not years:
            return pd.DataFrame(columns=columns)

        rows = []
        for y in years:
            s = year_map.get(y, {})
            # Label the initial snapshot (year -1) as 'Start' for display
            year_label = 'Start' if int(y) == -1 else int(y)
            row = {
                'Year': year_label,
                'QMD': s.get('QMD'),
                'TPA': s.get('TPA'),
                'BA': s.get('BA'),
                'Carbon': s.get('carbon'),
                'CI': s.get('CI'),
                'Fire risk': s.get('fire_risk'),
                'SPB risk': s.get('SPB_risk'),
            }
            rows.append(row)

        df = pd.DataFrame(rows, columns=columns)

        # Use Year as the row index so printed rows show years instead of 0..N-1
        df = df.set_index('Year')

        # Insert a blank row between the column names and the data for visual spacing.
        # Create an empty row with empty strings so to_string shows a blank line.
        #empty_row = pd.DataFrame([['' for _ in df.columns]], columns=df.columns, index=[''])
        #df = pd.concat([empty_row, df])

        df.index.name = 'Year'

        

        return df