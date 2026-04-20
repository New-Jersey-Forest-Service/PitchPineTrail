"""
Pitch Pine Trail - Forest Management Simulation Game

NJ Forest Service
William Zipse
Andrea Brown
Cara Escalona
Justin Gimmillaro

---------------------------------------------------
Graphical user interface for the Pitch Pine Trail forest management simulation.
Provides interactive screens for gameplay, status display, and decision making.
"""

import tkinter as tk
from tkinter import messagebox
from game_logic import Game, ACTIONS
import os
import logging
from PIL import Image, ImageTk, ImageGrab
import pygame
import random
import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import webbrowser
from tkinter import filedialog

# Track which ambient/looping sounds are currently active so we can pause/restore
# when switching to modal screens like the analysis lab.
SOUND_STATE = {}

def main():
    pygame.mixer.init()

    # Initialize game and UI constants
    game = Game()  # Model handles its own colonization & achievement flags
    # GUI-only state
    game.current_bg_img = "assets/Evenagestand.jpg"
    game.animation_temp_bg = None
    game.achievement_queue = []
    game.achievement_final_bg = None
    # Action/animation sequencing flags
    game.thin_lightly_event = False
    game.prescribed_burn_event = False
    game.pb_after_first_heavythin_shown = False
    game.pb_after_heavythin_with_tl_shown = False
    # Temp backgrounds for multi-step animations
    game.prescribed_burn_temp_bg = None
    game.thin_lightly_temp_bg = None
    game.thin_heavily_temp_bg = None
    # Track first choice so we can remove welcome banner permanently
    game.has_made_first_choice = False
    # Color constants
    BG_COLOR = "#FFFFFF"    # White background
    FG_COLOR = "#000000"    # Black text
    game.summer_tanager_screen_shown = False
    game.tree_frog_screen_shown = False
    game.gentian_screen_shown = False
    game.indigo_bunting_screen_shown = False
    game.turkey_beard_screen_shown = False
    # Hurricane event pending flag (shows after any achievements this turn)
    game.hurricane_pending = False
    game.hurricane_last_shown_year = None

    # Set up the main window
    root = tk.Tk()
    root.title("Pitch Pine Trail")
    root.configure(bg=BG_COLOR)
    root.attributes('-fullscreen', True)  #true fullscreen
    root.bind("<Escape>", lambda e: root.attributes("-fullscreen", False)) #exit fullscreen on Escape key

    # Detect screen size and define scaling helpers
    SCREEN_W = root.winfo_screenwidth()
    SCREEN_H = root.winfo_screenheight()

    # Baseline your current design to SCREEN_WxSCREEN_H
    BASE_W = 1920
    BASE_H = 1080

    def scale_x(px):
        return int(px * SCREEN_W / BASE_W)

    def scale_y(px):
        return int(px * SCREEN_H / BASE_H)
    
    # Optional: convenience scale for font sizes (tweak factor if needed)
    def scale_font(sz):
        return max(1, int(sz * (SCREEN_W / BASE_W + SCREEN_H / BASE_H) / 2))

    # Font constants    
    FONT = ("Courier New", scale_font(12), "bold")

    # Get color code based on risk level
    def get_risk_color(risk):
        """Return color code based on risk level.
        
        Args:
            risk (str): Risk level ('Low', 'Moderate', or 'High')
            
        Returns:
            str: Hex color code
        """
        if risk == "Low":
            return "#228B22"  # Green
        elif risk == "Moderate":
            return "#FFA600"  # Yellow
        else:
            return "#B22222"  # Red


    def restart_game(frame_to_remove):
        # Reset game model (stats, colonization, achievements, popups)
        game.reset_game()
        # Ensure hurricane flag is cleared when restarting via Try Again
        try:
            game.hurricane_occurred = False
        except Exception:
            pass

        # Ensure wildfire modal flags are cleared when restarting via Try Again
        try:
            game.wildfire_screen_shown = False
        except Exception:
            pass
        try:
            game.wildfire_active = False
        except Exception:
            pass
        try:
            game.wildfire_pending = False
        except Exception:
            pass
        try:
            game.wildfire_last_shown_year = None
        except Exception:
            pass

        # Stop any looping/active sounds
        stop_spb_eating_sound()
        stop_fire_sound()
        try:
            stop_tree_frog_sound()
        except Exception:
            pass

        # Reset GUI-only state
        game.current_bg_img = "assets/Evenagestand.jpg"
        game.animation_temp_bg = None
        game.achievement_queue = []
        game.achievement_final_bg = None

        game.thin_lightly_event = False
        game.prescribed_burn_event = False
        game.pb_after_first_heavythin_shown = False
        game.pb_after_heavythin_with_tl_shown = False

        # Legacy temp fields (safe to keep if referenced elsewhere)
        game.prescribed_burn_temp_bg = None
        game.thin_lightly_temp_bg = None
        game.thin_heavily_temp_bg = None

        # Ensure all achievement/colonization GUI flags are cleared so popups & medals reset
        game.pine_snake_achieved = False
        game.gentian_achieved = False
        game.summer_tanager_achieved = False
        game.tree_frog_achieved = False
        game.indigo_bunting_achieved = False
        game.turkey_beard_achieved = False

        game.summer_tanager_screen_shown = False
        game.tree_frog_screen_shown = False
        game.gentian_screen_shown = False
        game.indigo_bunting_screen_shown = False
        game.turkey_beard_screen_shown = False

        # Rebuild UI
        for widget in root.winfo_children():
            widget.pack_forget()
        show_game_screen()

    def create_fullscreen_image_screen(parent, image_path, overlay_builder, x=30, y=30):
        """
        Helper to create a fullscreen, resizable image background with overlay widgets.
        Args:
            parent: tk.Frame or tk.Tk to pack the canvas into.
            image_path: Path to the background image.
            overlay_builder: Function that takes the overlay frame and populates it with widgets.
            x, y: Position of the overlay frame (default 30, 30)
        """
        # Remove all children from parent
        for widget in parent.winfo_children():
            widget.pack_forget()

        # Full-window canvas
        canvas = tk.Canvas(parent, bg=BG_COLOR, highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        # Dynamically resize and display background image
        def update_bg_image(event=None):
            try:
                image = Image.open(image_path)
                w = canvas.winfo_width()
                h = canvas.winfo_height()
                if w < 10 or h < 10:
                    return
                img = image.resize((w, h), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                canvas.photo = photo
                if hasattr(canvas, "bg_img_id"):
                    canvas.itemconfig(canvas.bg_img_id, image=photo)
                else:
                    canvas.bg_img_id = canvas.create_image(0, 0, anchor="nw", image=photo)
            except Exception:
                pass

        canvas.bind("<Configure>", update_bg_image)

        # Overlay frame for stats and buttons
        overlay = tk.Frame(canvas, bg="", bd=0)  # Transparent background
        overlay_id = canvas.create_window(x, y, anchor="nw", window=overlay)

        # Let the caller populate the overlay
        overlay_builder(overlay)
        return canvas  
    
    def show_exit_survey_overlay_in(parent):
        """Show the exit survey overlay centered over the given parent frame."""
         # Create centered overlay frame
        overlay = tk.Frame(parent, bg="#FFFFFF", bd=0)
        overlay.place(relx=0.02, rely=0.02, anchor="nw")

        # Load survey image
        try:
            img = Image.open("assets/exitsurvey.jpg")
            try:
                img = img.resize((scale_x(900), scale_y(494)), Image.Resampling.LANCZOS)
            except Exception:
                img = img.resize((scale_x(900), scale_y(494)), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            img_label = tk.Label(overlay, image=photo, bg="#FFFFFF", bd=0)
            img_label.image = photo
            img_label.pack()
        except Exception as e:
            print("Exit survey overlay error:", e)
            tk.Label(
                overlay,
                text="Exit Survey",
                bg="#FFFFFF", fg="#000000",
                font=("Courier", scale_font(16), "bold"), padx=12, pady=12
            )
            img_label.pack()
        
        # Buttons created after image; place them and lift to top
        open_btn = tk.Button(
            overlay,
            text="Open Feedback Survey",
            font=("Courier", scale_font(14), "bold"),
            width=22,
            bg="#d29e76",
            fg="#39220d",
            activebackground="#1c6213",
            command=lambda: webbrowser.open("https://forms.office.com/g/N38DQhPe2V", new=1)
        )
        exit_btn = tk.Button(
            overlay,
            text="Exit",
            font=("Courier", scale_font(17), "bold"),
            width=10,
            bg="#9c3432",
            fg="#3d0606",
            activebackground="#FFFFFF",
            command=root.destroy
        )

        # Place independently (row near bottom of overlay)
        open_btn.place(relx=0.52, rely=0.63, anchor="nw")
        exit_btn.place(relx=0.73, rely=0.8, anchor="nw")

    #define zoom sequence images
    def start_zoom_sequence():
        play_zoom_sound()  # Play zoom sound over forest sound
        for widget in root.winfo_children():
            widget.pack_forget()
        zoom_frame = tk.Frame(root, bg=BG_COLOR)
        zoom_frame.pack(fill="both", expand=True)
        img_label = tk.Label(zoom_frame)
        img_label.pack(fill="both", expand=True)

        zoom_images = [
            "assets/zoom_1.jpg",
            "assets/zoom_2.jpg",
            "assets/zoom_3.jpg",
            "assets/zoom_4.jpg",
            "assets/zoom_5.jpg",
            "assets/zoom_6.jpg",
            "assets/zoom_7.jpg",
            "assets/zoom_8.jpg",
            "assets/zoom_9.jpg"
        ]

        def show_next_zoom(index=0):
            if index < len(zoom_images):
                img = Image.open(zoom_images[index]).resize((SCREEN_W, SCREEN_H))
                photo = ImageTk.PhotoImage(img)
                img_label.config(image=photo)
                img_label.image = photo  # Prevent garbage collection
                root.after(10, lambda: show_next_zoom(index + 1))
            else:
                # Show zoom_10.jpg and overlay the button
                img = Image.open("assets/zoom_10.jpg").resize((SCREEN_W, SCREEN_H))
                photo = ImageTk.PhotoImage(img)
                img_label.config(image=photo)
                img_label.image = photo

                # Overlay frame for the "Let's Play" button
                overlay = tk.Frame(zoom_frame, bg="", bd=0)
                overlay.place(relx=0.55, rely=0.71, anchor="center")
                tk.Button(
                    overlay,
                    text="Let's Play!",
                    font=("Courier", scale_font(18), "bold"),
                    width=16,
                    bg="#f7d79e",
                    fg="#663e1d",
                    activebackground="#069134",
                    command=lambda: [play_lets_play_sound(), zoom_frame.pack_forget(), show_game_screen()]
                ).pack(pady=10)

                # --- Definitions Button Frame (same placement as main screen) ---
                definitions_frame = tk.Frame(zoom_frame, bg="#FFFFFF")
                definitions_frame.place(relx=0.05, rely=0.96, anchor="sw")
                definitions_button = tk.Button(
                    definitions_frame,
                    text="Click for Definitions",
                    font=("Courier New", scale_font(12), "bold"),
                    width=23,
                    bg="#000000",
                    fg="#ffffff",
                    activebackground="#FFE208",
                    command=show_definitions_screen
                )
                definitions_button.pack()

        show_next_zoom()
    
    # --- Intro Screen ---
    intro_frame = tk.Frame(root, bg=BG_COLOR)
    intro_frame.pack(fill="both", expand=True)

    # Load and display the background image in a label
    bg_img = Image.open("assets/introscreen.jpg")
    bg_img = bg_img.resize((SCREEN_W, SCREEN_H))  # Or use root.winfo_screenwidth(), etc.
    bg_photo = ImageTk.PhotoImage(bg_img)
    bg_label = tk.Label(intro_frame, image=bg_photo)
    bg_label.image = bg_photo  # Prevent garbage collection
    bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)

    # Play forest sound on intro screen
    play_forest_sound()

    # Create a frame for the buttons, centered near the bottom
    button_row = tk.Frame(intro_frame, bg="#854a2d")
    button_row.place(relx=0.795, rely=0.828, anchor="center")  

    tk.Button(
        button_row,
        text="Begin",
        font=("Courier", scale_font(14), "bold"),
        width=14,
        bg="#f7d79e",
        fg="#663e1d",
        activebackground="#13471C",
        command=start_zoom_sequence  # <-- Use this instead of show_game_screen
    ).pack(side="left", padx=5)

    tk.Button(
        button_row,
        text="Exit",
        font=("Courier", scale_font(14), "bold"),
        width=14,
        bg="#f7d79e",
        fg="#663e1d",
        activebackground="#531717",
        command=root.destroy
    ).pack(side="left", padx=5)

    # --- Main Game Screen Functions ---
    # ---WINNING SCREEN---
    def show_closing_screen():
        play_trumpet_win_sound()
        for widget in root.winfo_children():
            widget.pack_forget()
            
        closing_frame = tk.Frame(root, bg=BG_COLOR)
        closing_frame.pack(fill="both", expand=True)

         # Get QMD value
        qmd = game.get_status_dict()['QMD']

        # NEW: use persistent achievement flags (fallback to current colonized)
        ach_snake = getattr(game, 'pine_snake_achieved', False) or getattr(game, 'pine_snakes_colonized', False)
        ach_gent  = getattr(game, 'gentian_achieved', False) or getattr(game, 'gentian_colonized', False)
        ach_tan   = getattr(game, 'summer_tanager_achieved', False) or getattr(game, 'summer_tanager_colonized', False)
        ach_frog  = getattr(game, 'tree_frog_achieved', False) or getattr(game, 'pine_barrens_tree_frog_colonized', False)
        ach_bunt   = getattr(game, 'indigo_bunting_achieved', False) or getattr(game, 'indigo_bunting_colonized', False)
        ach_turkey = getattr(game, 'turkey_beard_achieved', False) or getattr(game, 'turkey_beard_colonized', False)
        ach_short = getattr(game, 'short_achieved', False) or getattr(game, 'short_colonized', False)


        # Choose background image (build filename based on achievements)
        status = game.get_status_dict()  # ensure we have current risks
        fire_high = status.get('fire_risk') == 'High'
        spb_high = status.get('SPB_risk') == 'High'
        if qmd < 13 or fire_high or spb_high:
            base = "bad"
        elif 13 <= qmd < 15:
            base = "okay"
        else:
            base = "good"
        ordered = [
            ("snake",   ach_snake),
            ("gentian", ach_gent),
            ("tanager", ach_tan),
            ("frog",    ach_frog),
            ("bunting", ach_bunt),
            ("turkey",  ach_turkey),
            ("short",   ach_short),
        ]
        medals = "-".join(name for name, present in ordered if present)
        if medals:
            bg_img_path = f"assets/{base}_{medals}medal.jpg"
        else:
            bg_img_path = f"assets/{base}_nomedal.jpg"
        
        # Load and display the background image in a label
        bg_img = Image.open(bg_img_path)
        bg_img = bg_img.resize((SCREEN_W, SCREEN_H))
        bg_photo = ImageTk.PhotoImage(bg_img)
        bg_label = tk.Label(closing_frame, image=bg_photo)
        bg_label.image = bg_photo  # Prevent garbage collection
        bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)

        # --- Metrics Frame (same as main game screen) ---
        metrics_frame = tk.Frame(closing_frame, bg="#FFFFFF", bd=0)
        metrics_frame.place(relx=0.841, rely=0.57, anchor="n")
        game_status = tk.StringVar()
        summary = game.get_status_dict()
        game_status.set(
            f"Year: {summary['year']}\n"
            f"\nBasal Area (BA): {summary['BA']:.1f} sqft/acre\n"
            f"\nTrees Per Acre (TPA): {summary['TPA']}\n"
            f"\nQuadratic Mean Diameter (QMD): {summary['QMD']:.1f} inches\n"
            f"\nCarbon per Acre: {summary['carbon']:.1f} Metric Tons/acre\n"
            f"\nCrowning Index: {summary['CI']:.1f}"
        )
        game_status_message = tk.Message(
            metrics_frame,
            textvariable=game_status,
            width=450,
            justify="center",
            bg="#FFFFFF",
            fg=FG_COLOR,
            font=FONT
        )
        game_status_message.pack()
        fire_risk_label = tk.Label(metrics_frame, wraplength=scale_x(400), justify="left", padx=10, pady=0, bg="#FFFFFF", font=("Courier", scale_font(14), "bold"))
        fire_risk_label.pack()
        spb_risk_label = tk.Label(metrics_frame, wraplength=scale_x(400), justify="left", padx=10, pady=0, bg="#FFFFFF", font=("Courier", scale_font(14), "bold"))
        spb_risk_label.pack()
        fire_risk_label.config(
            text=f"\n\nFire Risk: {summary['fire_risk']}",
            fg=get_risk_color(summary['fire_risk'])
        )
        spb_risk_label.config(
            text=f"Southern Pine Beetle Risk: {summary['SPB_risk']}",
            fg=get_risk_color(summary['SPB_risk'])
        )
        narration = tk.StringVar()
        narration.set("Thank you for playing Pitch Pine Trail!")
        narration_label = tk.Label(
            metrics_frame, textvariable=narration, wraplength=scale_x(400), justify="left",
            padx=10, pady=5, bg="#FFFFFF", fg=FG_COLOR, font=("Courier New", scale_font(10), "bold")
        )
        narration_label.pack()

        # --- Text Frame ---
        text_frame = tk.Frame(closing_frame, bg="#1b2336", bd=0)
        text_frame.place(relx=0.88, rely=0.1, anchor="n")
        tk.Label(
            text_frame,
            text=game.get_action_summary(),
            bg="#1b2336", fg="#05dd4c", font=("Courier New", scale_font(15), "bold"),
            wraplength=scale_x(400), justify="left"
        ).pack()

        # --- Analyze Button (separate frame for independent placement) ---
        analyze_frame = tk.Frame(closing_frame, bg="#FFFFFF", bd=0)
        analyze_frame.place(relx=0.6, rely=0.91, anchor="center")
        tk.Button(
            analyze_frame, text="Analyze My Management", font=("Courier", scale_font(17), "bold"), width=22,
            bg="#1b2336", fg="#b5c3d8", activebackground="#8B580A",
            command=lambda: [play_computer_startup(), show_analysis_lab(closing_frame)]
        ).pack()

        # --- Button Frame (Try Again / Exit) ---
        button_frame = tk.Frame(closing_frame, bg="#FFFFFF", bd=0)
        button_frame.place(relx=0.845, rely=0.91, anchor="center")
        tk.Button(
            button_frame, text="Try Again", font=("Courier", scale_font(14), "bold"), width=15,
            bg="#23ac23", fg="#023a02", activebackground="#10612B",
            command=lambda: restart_game(closing_frame)
        ).pack(side="left", padx=10, pady=0)
        tk.Button(
            button_frame, text="Exit", font=("Courier", scale_font(14), "bold"), width=15,
            bg="#9c3432", fg="#2c0505", activebackground="#611010",
            command=lambda: [play_page_turn_sound(), show_exit_survey_overlay_in(closing_frame)]
        ).pack(side="left", padx=10, pady=0)

        # --- Certificate button and overlay ---
        def show_certificate_overlay():
            # Overlay frame for nameplate
            cert_overlay = tk.Frame(closing_frame, bg="#FFFFFF", bd=0)
            cert_overlay.place(relx=0.48, rely=0.05, anchor="nw")

            # Load nameplate image
            try:
                img = Image.open("assets/nameplate.jpg")
                try:
                    img = img.resize((scale_x(550), scale_y(194)), Image.Resampling.LANCZOS)
                except Exception:
                    img = img.resize((scale_x(550), scale_y(194)), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                img_label = tk.Label(cert_overlay, image=photo, bg="#FFFFFF", bd=0)
                img_label.image = photo
                img_label.pack()
            except Exception as e:
                print("Certificate overlay error:", e)
                img_label = tk.Label(
                    cert_overlay,
                    text="Certificate nameplate",
                    bg="#FFFFFF", fg="#000000",
                    font=("Courier", scale_font(16), "bold"), padx=8, pady=8
                )
                img_label.pack()

            # Name entry on top of the image
            entry = tk.Entry(cert_overlay, width=17, font=("Courier", scale_font(29), "bold"), justify="center", bd=2)
            entry.insert(0, "your name here")
            entry.place(relx=0.59, rely=0.39, anchor="n")
            entry.focus_set()
            try:
                entry.selection_range(0, tk.END)
            except Exception:
                pass

            # Create Save button in the closing_frame (independent of cert_overlay)
            save_btn = tk.Button(
                closing_frame,
                text="Save",
                font=("Courier", scale_font(14), "bold"),
                width=10,
                bg="#d38e0f",
                fg="#473308",
                activebackground="#8B580A"
            )
            # Position anywhere you like on the screen (independent)
            save_btn.place(relx=0.734, rely=0.23, anchor="n")  # adjust relx/rely as needed

            def do_save():
                play_save_sound()

                # Hide the save button before capture so it won't appear in the screenshot
                try:
                    save_btn.place_forget()
                except Exception:
                    pass

                # Prompt for save location
                from datetime import datetime
                default_name = datetime.now().strftime("PitchPineTrail_certificate_%Y%m%d_%H%M%S.jpg")
                file_path = filedialog.asksaveasfilename(
                    title="Save Screenshot",
                    defaultextension=".jpg",
                    initialfile=default_name,
                    filetypes=[("PNG Image", "*.jpg"), ("JPEG Image", "*.jpg;*.jpeg"), ("All Files", "*.*")]
                )
                if not file_path:
                    return  # user canceled

                # Capture the current app window (without the Save button)
                try:
                    x = root.winfo_rootx()
                    y = root.winfo_rooty()
                    w = root.winfo_width()
                    h = root.winfo_height()
                    img = ImageGrab.grab(bbox=(x, y, x + w, y + h))
                    img.save(file_path)
                    print(f"Saved screenshot: {file_path}")
                except Exception as e:
                    print("Error saving screenshot:", e)

            # Wire up save action
            save_btn.config(command=do_save)

        # Button to open the certificate overlay (place near the Exit/Try Again buttons)
        tk.Button(
            closing_frame,
            text="Save your successful \nmanagement certificate",
            font=("Courier", scale_font(18), "bold"),
            width=25,
            bg="#d38e0f",
            fg="#473308",
            activebackground="#8B580A",
            command=show_certificate_overlay
        ).place(relx=0.5, rely=0.07, anchor="nw")

    #LOSING SCREEN
    # --- Low TPA Screen ---
    def show_low_tpa_screen():
        """Display the game over screen for low TPA condition."""
        stop_forest_sound()
        play_losing_trombone_sound()
        play_wind_sound()  # <-- Play wind sound at the same time
        for widget in root.winfo_children():
            widget.pack_forget()
        low_tpa_frame = tk.Frame(root, bg=BG_COLOR)
        low_tpa_frame.pack(fill="both", expand=True)

        # Load and display the background image in a label
        bg_img = Image.open("assets/LowStocking.jpg")
        bg_img = bg_img.resize((SCREEN_W, SCREEN_H))
        bg_photo = ImageTk.PhotoImage(bg_img)
        bg_label = tk.Label(low_tpa_frame, image=bg_photo)
        bg_label.image = bg_photo  # Prevent garbage collection
        bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)

        # --- Metrics Frame ---
        metrics_frame = tk.Frame(low_tpa_frame, bg="#FFFFFF", bd=0)
        metrics_frame.place(relx=0.841, rely=0.57, anchor="n")
        game_status = tk.StringVar()
        status_dict = game.get_status_dict()
        game_status.set(
            f"Year: {status_dict['year']}\n"
            f"\nBasal Area (BA): {status_dict['BA']:.1f} sqft/acre\n"
            f"\nTrees Per Acre (TPA): {status_dict['TPA']}\n"
            f"\nQuadratic Mean Diameter (QMD): {status_dict['QMD']:.1f} inches\n"
            f"\nCarbon per Acre: {status_dict['carbon']:.1f} Metric Tons/acre\n"
            f"\nCrowning Index: {status_dict['CI']:.1f}"
        )
        game_status_message = tk.Message(
            metrics_frame,
            textvariable=game_status,
            width=450,
            justify="center",
            bg="#FFFFFF",
            fg=FG_COLOR,
            font=FONT
        )
        game_status_message.pack()
        fire_risk_label = tk.Label(metrics_frame, wraplength=scale_x(400), justify="left", padx=10, pady=0, bg="#FFFFFF", font=("Courier", scale_font(14), "bold"))
        fire_risk_label.pack()
        spb_risk_label = tk.Label(metrics_frame, wraplength=scale_x(400), justify="left", padx=10, pady=0, bg="#FFFFFF", font=("Courier", scale_font(14), "bold"))
        spb_risk_label.pack()
        fire_risk_label.config(
            text=f"\n\nFire Risk: {status_dict['fire_risk']}",
            fg=get_risk_color(status_dict['fire_risk'])
        )
        spb_risk_label.config(
            text=f"Southern Pine Beetle Risk: {status_dict['SPB_risk']}",
            fg=get_risk_color(status_dict['SPB_risk'])
        )
        narration = tk.StringVar()
        narration.set("Better luck next time!")
        narration_label = tk.Label(
            metrics_frame, textvariable=narration, wraplength=scale_x(400), justify="left",
            padx=10, pady=5, bg="#FFFFFF", fg=FG_COLOR, font=FONT
        )
        narration_label.pack()

        # --- Text Frame ---
        text_frame = tk.Frame(low_tpa_frame, bg="#1b2336", bd=0)
        text_frame.place(relx=0.88, rely=0.19, anchor="center")

        tk.Label(
            text_frame,
            text="The forest's growing stock trees have been depleted! \n\nWe're supposed to be growing a forest!",
            bg="#1b2336", fg="#05dd4c", font=("Courier New", scale_font(18), "bold"),
            pady=0, wraplength=scale_x(400), justify="center"
        ).pack()

        # --- Analyze Button (separate frame for independent placement) ---
        analyze_frame = tk.Frame(low_tpa_frame, bg="#FFFFFF", bd=0)
        analyze_frame.place(relx=0.6, rely=0.91, anchor="center")
        tk.Button(
            analyze_frame, text="Analyze My Management", font=("Courier", scale_font(17), "bold"), width=22,
            bg="#1b2336", fg="#b5c3d8", activebackground="#8B580A",
            command=lambda: [play_computer_startup(), show_analysis_lab(low_tpa_frame)]
        ).pack()

        # --- Button Frame (Try Again / Exit) ---
        button_frame = tk.Frame(low_tpa_frame, bg="#1b2336", bd=0)
        button_frame.place(relx=0.88, rely=0.315, anchor="center")

        tk.Button(
            button_frame, text="Try Again", font=("Courier", scale_font(14), "bold"), width=16,
            bg="#05dd4c", fg="#1b2336", activebackground="#10612B",
            command=lambda: [stop_losing_trombone_sound(), stop_wind_sound(), restart_game(low_tpa_frame)]
        ).pack(side="left", padx=10, pady=5)
        tk.Button(
            button_frame, text="Exit", font=("Courier", scale_font(14), "bold"), width=16,
            bg="#05dd4c", fg="#1b2336", activebackground="#611010",
            command=lambda: [play_page_turn_sound(), show_exit_survey_overlay_in(low_tpa_frame)]
        ).pack(side="left", padx=10, pady=5)

    # --- Fire Loss Screen ---
    def show_fire_loss_screen():
        """Display the catastrophic wildfire end screen."""
        stop_forest_sound()
        play_fire_sound()
        for widget in root.winfo_children():
            widget.pack_forget()
        fire_frame = tk.Frame(root, bg=BG_COLOR)
        fire_frame.pack(fill="both", expand=True)

        # Load and display the background image in a label
        bg_img = Image.open("assets/LossByFire.jpg")
        bg_img = bg_img.resize((SCREEN_W, SCREEN_H))
        bg_photo = ImageTk.PhotoImage(bg_img)
        bg_label = tk.Label(fire_frame, image=bg_photo)
        bg_label.image = bg_photo  # Prevent garbage collection
        bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)

        # --- Metrics Frame (copied from main game screen) ---
        metrics_frame = tk.Frame(fire_frame, bg="#FFFFFF", bd=0)
        metrics_frame.place(relx=0.841, rely=0.57, anchor="n")
        game_status = tk.StringVar()
        status_dict = game.get_status_dict()
        game_status.set(
            f"Year: {status_dict['year']}\n"
            f"\nBasal Area (BA): {status_dict['BA']:.1f} sqft/acre\n"
            f"\nTrees Per Acre (TPA): {status_dict['TPA']}\n"
            f"\nQuadratic Mean Diameter (QMD): {status_dict['QMD']:.1f} inches\n"
            f"\nCarbon per Acre: {status_dict['carbon']:.1f} Metric Tons/acre\n"
            f"\nCrowning Index: {status_dict['CI']:.1f}"
        )
        game_status_message = tk.Message(
            metrics_frame,
            textvariable=game_status,
            width=450,
            justify="center",
            bg="#FFFFFF",
            fg=FG_COLOR,
            font=FONT
        )
        game_status_message.pack()
        fire_risk_label = tk.Label(metrics_frame, wraplength=scale_x(400), justify="left", padx=10, pady=0, bg="#FFFFFF", font=("Courier", scale_font(14), "bold"))
        fire_risk_label.pack()
        spb_risk_label = tk.Label(metrics_frame, wraplength=scale_x(400), justify="left", padx=10, pady=0, bg="#FFFFFF", font=("Courier", scale_font(14), "bold"))
        spb_risk_label.pack()
        fire_risk_label.config(
            text=f"\n\nFire Risk: {status_dict['fire_risk']}",
            fg=get_risk_color(status_dict['fire_risk'])
        )
        spb_risk_label.config(
            text=f"Southern Pine Beetle Risk: {status_dict['SPB_risk']}",
            fg=get_risk_color(status_dict['SPB_risk'])
        )
        narration = tk.StringVar()
        narration.set("Better luck next time!")
        narration_label = tk.Label(
            metrics_frame, textvariable=narration, wraplength=scale_x(400), justify="left",
            padx=10, pady=5, bg="#FFFFFF", fg=FG_COLOR, font=FONT
        )
        narration_label.pack()

        # --- Text Frame ---
        text_frame = tk.Frame(fire_frame, bg="#1b2336", bd=0)
        text_frame.place(relx=0.88, rely=0.2, anchor="center")  # Same as SPB loss

        tk.Label(
            text_frame,
            text="A catastrophic wildfire has occurred!\n\nWe might get a new stand of pitch pine, but we're trying to grow a mature stand!",
            bg="#1b2336", fg="#05dd4c", font=("Courier", scale_font(18), "bold"),
            pady=0, wraplength=scale_x(400), justify="center"
        ).pack()

        # --- Analyze Button (separate frame for independent placement) ---
        analyze_frame = tk.Frame(fire_frame, bg="#FFFFFF", bd=0)
        analyze_frame.place(relx=0.6, rely=0.91, anchor="center")
        tk.Button(
            analyze_frame, text="Analyze My Management", font=("Courier", scale_font(17), "bold"), width=22,
            bg="#1b2336", fg="#b5c3d8", activebackground="#8B580A",
            command=lambda: [play_computer_startup(), show_analysis_lab(fire_frame)]
        ).pack()

        # --- Button Frame (Try Again / Exit) ---
        button_frame = tk.Frame(fire_frame, bg="#1b2336", bd=0)
        button_frame.place(relx=0.88, rely=0.33, anchor="center")  # Same as SPB loss

        tk.Button(
            button_frame, text="Try Again", font=("Courier", scale_font(14), "bold"), width=16,
            bg="#05dd4c", fg="#1b2336", activebackground="#10612B",
            command=lambda: [stop_fire_sound(), restart_game(fire_frame)]
        ).pack(side="left", padx=10, pady=5)
        tk.Button(
            button_frame, text="Exit", font=("Courier", scale_font(14), "bold"), width=16,
            bg="#05dd4c", fg="#1b2336", activebackground="#611010",
            command=lambda: [play_page_turn_sound(), show_exit_survey_overlay_in(fire_frame)]
        ).pack(side="left", padx=10, pady=5)

    # --- SPB Loss Screen ---
    def show_spb_loss_screen():
        """Display the SPB outbreak end screen."""
        stop_forest_sound()
        play_spb_eating_sound()
        for widget in root.winfo_children():
            widget.pack_forget()
        spb_frame = tk.Frame(root, bg=BG_COLOR)
        spb_frame.pack(fill="both", expand=True)

        # Load and display the background image in a label
        bg_img = Image.open("assets/LossBySPB.jpg")
        bg_img = bg_img.resize((SCREEN_W, SCREEN_H))
        bg_photo = ImageTk.PhotoImage(bg_img)
        bg_label = tk.Label(spb_frame, image=bg_photo)
        bg_label.image = bg_photo  # Prevent garbage collection
        bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)

        # --- Metrics Frame (copied from main game screen) ---
        metrics_frame = tk.Frame(spb_frame, bg="#FFFFFF", bd=0)
        metrics_frame.place(relx=0.841, rely=0.57, anchor="n")
        game_status = tk.StringVar()
        status_dict = game.get_status_dict()
        game_status.set(
            f"Year: {status_dict['year']}\n"
            f"\nBasal Area (BA): {status_dict['BA']:.1f} sqft/acre\n"
            f"\nTrees Per Acre (TPA): {status_dict['TPA']}\n"
            f"\nQuadratic Mean Diameter (QMD): {status_dict['QMD']:.1f} inches\n"
            f"\nCarbon per Acre: {status_dict['carbon']:.1f} Metric Tons/acre\n"
            f"\nCrowning Index: {status_dict['CI']:.1f}"
        )
        game_status_message = tk.Message(
            metrics_frame,
            textvariable=game_status,
            width=450,
            justify="center",
            bg="#FFFFFF",
            fg=FG_COLOR,
            font=FONT
        )
        game_status_message.pack()
        fire_risk_label = tk.Label(metrics_frame, wraplength=scale_x(400), justify="left", padx=10, pady=0, bg="#FFFFFF", font=("Courier", scale_font(14), "bold"))
        fire_risk_label.pack()
        spb_risk_label = tk.Label(metrics_frame, wraplength=scale_x(400), justify="left", padx=10, pady=0, bg="#FFFFFF", font=("Courier", scale_font(14), "bold"))
        spb_risk_label.pack()
        fire_risk_label.config(
            text=f"\n\nFire Risk: {status_dict['fire_risk']}",
            fg=get_risk_color(status_dict['fire_risk'])
        )
        spb_risk_label.config(
            text=f"Southern Pine Beetle Risk: {status_dict['SPB_risk']}",
            fg=get_risk_color(status_dict['SPB_risk'])
        )
    

        # --- Text Frame ---
        text_frame = tk.Frame(spb_frame, bg="#1b2336", bd=0)
        text_frame.place(relx=0.88, rely=0.19, anchor="center")  # Adjust as needed

        tk.Label(
            text_frame,
            text="A Southern Pine Beetle outbreak has devastated your stand!\n\nWe're trying to grow a healthy forest!",
            bg="#1b2336", fg="#05dd4c", font=("Courier", scale_font(18), "bold"),
            pady=20, wraplength=scale_x(400), justify="center"
        ).pack()

        # --- Analyze Button (separate frame for independent placement) ---
        analyze_frame = tk.Frame(spb_frame, bg="#FFFFFF", bd=0)
        analyze_frame.place(relx=0.6, rely=0.91, anchor="center")
        tk.Button(
            analyze_frame, text="Analyze My Management", font=("Courier", scale_font(17), "bold"), width=22,
            bg="#1b2336", fg="#b5c3d8", activebackground="#8B580A",
            command=lambda: [play_computer_startup(), show_analysis_lab(spb_frame)]
        ).pack()

        # --- Button Frame (Try Again / Exit) ---
        button_frame = tk.Frame(spb_frame, bg="#1b2336", bd=0)
        button_frame.place(relx=0.88, rely=0.325, anchor="center")  # Adjust as needed

        tk.Button(
            button_frame, text="Try Again", font=("Courier", scale_font(14), "bold"), width=16,
            bg="#05dd4c", fg="#1b2336", activebackground="#10612B",
            command=lambda: [stop_spb_eating_sound(), restart_game(spb_frame)]
        ).pack(side="left", padx=10, pady=5)
        tk.Button(
            button_frame, text="Exit", font=("Courier", scale_font(14), "bold"), width=16,
            bg="#05dd4c", fg="#1b2336", activebackground="#611010",
            command=lambda: [play_page_turn_sound(),show_exit_survey_overlay_in(spb_frame)]
        ).pack(side="left", padx=10, pady=5)

    # --- Analysis Lab Screen ---
    def show_analysis_lab(prev_frame):
        """Show the analysis_lab screen using analyze.jpg and the game's action summary.

        prev_frame: the frame to return to when the player clicks 'Return to Game'.
        """
        # Hide current UI
        for widget in root.winfo_children():
            widget.pack_forget()

        # Snapshot which ambient/looping sounds are currently active so we can
        # resume them when the player returns to the previous screen.
        prev_sounds = SOUND_STATE.copy()
        # persist the snapshot so nested navigation (definitions -> back)
        SOUND_STATE['analysis_prev_sounds'] = prev_sounds

        # Stop any losing/foreground forest sounds so analysis audio can play cleanly
        try:
            stop_losing_trombone_sound()
        except Exception:
            pass
        try:
            stop_forest_sound()
        except Exception:
            pass
        try:
            stop_wind_sound()
        except Exception:
            pass
        try:
            stop_spb_eating_sound()
        except Exception:
            pass

        analysis_frame = tk.Frame(root, bg=BG_COLOR)
        analysis_frame.pack(fill="both", expand=True)
        # keep a reference so other screens (definitions) can restore this frame
        try:
            game.analysis_frame = analysis_frame
        except Exception:
            pass

        # Background image: show a short loading screen first, then swap
        # to the full analysis background after 1000ms. The decadal data
        # frame will be created only after the final background is shown.
        try:
            img = Image.open("assets/analyze_load.jpg")
            try:
                img = img.resize((SCREEN_W, SCREEN_H), Image.Resampling.LANCZOS)
            except Exception:
                img = img.resize((SCREEN_W, SCREEN_H), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            bg_label = tk.Label(analysis_frame, image=photo)
            bg_label.image = photo
            bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)
        except Exception:
            # If loading the loading-screen fails, fall back to blank frame
            bg_label = tk.Label(analysis_frame, bg=BG_COLOR)
            bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Prepare df placeholder that will be filled once the full
        # analysis background is displayed.
        df = None

        def finish_analysis_setup():
            nonlocal df
            # Swap to the full analysis background image
            try:
                img2 = Image.open("assets/analyze.jpg")
                try:
                    img2 = img2.resize((SCREEN_W, SCREEN_H), Image.Resampling.LANCZOS)
                except Exception:
                    img2 = img2.resize((SCREEN_W, SCREEN_H), Image.LANCZOS)
                photo2 = ImageTk.PhotoImage(img2)
                try:
                    bg_label.config(image=photo2)
                    bg_label.image = photo2
                except Exception:
                    # If bg_label was a simple frame, recreate a label
                    bg_label2 = tk.Label(analysis_frame, image=photo2)
                    bg_label2.image = photo2
                    bg_label2.place(relx=0, rely=0, relwidth=1, relheight=1)
            except Exception:
                pass

            # Start analysis lab ambient sound after the transition
            try:
                play_analysis_lab_sound()
            except Exception:
                pass

            # Create and populate the decadal DataFrame display now
            try:
                df = game.get_decadal_dataframe(10)
                try:
                    df_text = df.to_string()
                except Exception:
                    df_text = str(df)
            except Exception as e:
                df_text = f"Decadal data unavailable: {e}"

            df_frame = tk.Frame(analysis_frame, bg="#1f3339", bd=0)
            df_frame.place(relx=0.135, rely=0.235, anchor="nw")
            w_scale = max(1, SCREEN_W / BASE_W)
            h_scale = max(1, SCREEN_H / BASE_H)
            df_width_chars = max(30, int(60 * w_scale))
            df_height_lines = max(8, int(16 * h_scale))
            df_text_widget = tk.Text(
                df_frame,
                width=df_width_chars,
                height=df_height_lines,
                wrap="none",
                font=("Courier New", max(8, scale_font(15))),
                bg="#1f3339",
                fg="#05dd4c",
                insertbackground="#05dd4c",
                selectbackground="#30515a",
                bd=0,
                relief="flat"
            )
            df_text_widget.grid(row=0, column=0, sticky="nsew")
            df_frame.grid_rowconfigure(0, weight=1)
            df_frame.grid_columnconfigure(0, weight=1)
            df_text_widget.insert("1.0", df_text)
            df_text_widget.tag_add("df_color", "1.0", "end")
            df_text_widget.tag_config("df_color", foreground="#05dd4c")

            # Create Save Data button on top of the DataFrame so it appears after loading
            try:
                save_frame = tk.Frame(analysis_frame, bg="#2c404b", bd=0)
                save_frame.place(relx=0.575, rely=0.557, anchor="center")
                save_btn = tk.Button(
                    save_frame,
                    text="Save Data",
                    font=("Courier", scale_font(12), "bold"),
                    width=10,
                    bg="#bb0b09",
                    fg="#320001",
                    activebackground="#f0ebda",
                    command=do_save_dataframe
                )
                save_btn.pack()
                try:
                    save_frame.lift()
                except Exception:
                    pass
            except Exception:
                pass

            # Load blink image and start continuous background cycling
            try:
                img_blink = Image.open("assets/analyze_blink.jpg")
                try:
                    img_blink = img_blink.resize((SCREEN_W, SCREEN_H), Image.Resampling.LANCZOS)
                except Exception:
                    img_blink = img_blink.resize((SCREEN_W, SCREEN_H), Image.LANCZOS)
                photo_blink = ImageTk.PhotoImage(img_blink)
            except Exception:
                photo_blink = None

            # Continuous cycle: analyze.jpg for 1000ms, analyze_blink.jpg for 500ms
            try:
                state = {"show_blink": False, "after_id": None}

                def cycle_step():
                    # stop if frame or label gone
                    if not analysis_frame.winfo_exists() or not bg_label.winfo_exists():
                        return
                    try:
                        if not state["show_blink"]:
                            # show steady image
                            bg_label.config(image=photo2)
                            bg_label.image = photo2
                            delay = 1000
                        else:
                            # show blink image (if available)
                            if photo_blink is not None:
                                bg_label.config(image=photo_blink)
                                bg_label.image = photo_blink
                            delay = 500
                        state["show_blink"] = not state["show_blink"]
                        # schedule next
                        try:
                            state["after_id"] = root.after(delay, cycle_step)
                            analysis_frame.analysis_cycle_after = state["after_id"]
                        except Exception:
                            state["after_id"] = None
                    except Exception:
                        pass

                # start cycling
                cycle_step()
            except Exception:
                pass

        # Schedule the transition from loading -> analysis (1000ms)
        try:
            root.after(1000, finish_analysis_setup)
        except Exception:
            finish_analysis_setup()

        # --- action summary ---
        text_frame = tk.Frame(analysis_frame, bg="#1b2336", bd=0)
        text_frame.place(relx=0.88, rely=0.1, anchor="n")
        tk.Label(
            text_frame,
            text=game.get_action_summary(),
            bg="#1b2336", fg="#05dd4c", font=("Courier New", scale_font(15), "bold"),
            wraplength=scale_x(400), justify="left"
        ).pack()

        # --- achievements (separate frame under action summary) ---
        try:
            achievements = game.get_achievements_list()
        except Exception:
            achievements = []

        ach_frame = tk.Frame(analysis_frame, bg="#1b2336", bd=0)
        ach_frame.place(relx=0.81, rely=0.44, anchor="nw")

        ach_width_chars = max(12, int(40 * SCREEN_W / BASE_W))
        ach_height_lines = max(6, int(13 * SCREEN_H / BASE_H))
        # Prepare achievement text and compute required number of lines so the widget
        # can size to the content rather than a fixed height.
        if achievements:
            grouped = {}
            for year, name in achievements:
                grouped.setdefault(year, []).append(name)
            # build content lines and count
            ach_lines = []
            for year in sorted(grouped.keys()):
                ach_lines.append(f"Year {year}:")
                for name in grouped[year]:
                    ach_lines.append(f"   {name}")
        else:
            ach_lines = ["No achievements."]

        # Determine widget height: match number of lines, constrained to reasonable limits
        lines_count = len(ach_lines)
        max_lines_cap = max(ach_height_lines, 40)
        widget_height = max(3, min(lines_count, max_lines_cap))

        ach_text = tk.Text(
            ach_frame,
            width=ach_width_chars,
            height=widget_height,
            wrap="word",
            font=("Courier New", max(8, scale_font(13)), "bold"),
            bg="#1b2336",
            fg="#05dd4c",
            insertbackground="#05dd4c",
            bd=0,
            relief="flat"
        )
        ach_text.pack()
        for line in ach_lines:
            ach_text.insert("end", line + "\n")
        ach_text.config(state="disabled")

        # Return button (restore previous ambient sounds on return)
        button_frame = tk.Frame(analysis_frame, bg="#fff3dd", bd=0)
        button_frame.place(relx=0.18, rely=0.75, anchor="center")

        def return_to_prev():
            try:
                play_computer_shutdown()
            except Exception:
                pass
            try:
                stop_analysis_lab_sound()
            except Exception:
                pass
            # Restore previously-active ambient sounds (use persisted snapshot)
            try:
                saved = SOUND_STATE.pop('analysis_prev_sounds', prev_sounds if 'prev_sounds' in locals() else {})
                music = saved.get('music')
                if music == 'forest':
                    play_forest_sound()
                if music == 'fire':
                    play_fire_sound()
                if saved.get('wind'):
                    play_wind_sound()
                if saved.get('spb'):
                    play_spb_eating_sound()
            except Exception:
                pass

            # Cancel background cycling if active
            try:
                aid = getattr(analysis_frame, 'analysis_cycle_after', None)
                if aid:
                    try:
                        root.after_cancel(aid)
                    except Exception:
                        pass
                    analysis_frame.analysis_cycle_after = None
            except Exception:
                pass

            analysis_frame.pack_forget()
            prev_frame.pack(fill="both", expand=True)

        tk.Button(
            button_frame, text="Return to Game", font=("Courier", scale_font(13), "bold"), width=16,
            bg="#f0ebda", fg="#736e58", activebackground="#9b917f",
            command=return_to_prev
        ).pack()

        # --- Save Data button will be created after loading completes ---

        def do_save_dataframe():
            try:
                play_save_sound()
            except Exception:
                pass

            # Show a floppy overlay while saving (scales with screen)
            overlay = None
            try:
                overlay = tk.Frame(analysis_frame, bg="#c6d1d8", bd=0)
                overlay.place(relx=0.575, rely=0.57, anchor="center")
                try:
                    floppy_img = Image.open("assets/floppy.jpg")
                    try:
                        fw = max(24, scale_x(135))
                        fh = max(16, scale_y(108))
                        floppy_img = floppy_img.resize((fw, fh), Image.Resampling.LANCZOS)
                    except Exception:
                        floppy_img = floppy_img.resize((scale_x(135), scale_y(108)), Image.LANCZOS)
                    floppy_photo = ImageTk.PhotoImage(floppy_img)
                    floppy_label = tk.Label(overlay, image=floppy_photo, bg="#c6d1d8")
                    floppy_label.image = floppy_photo
                    floppy_label.pack()
                except Exception:
                    # fallback: simple text label if floppy image can't be shown
                    tk.Label(overlay, text="Saving...", bg="#c6d1d8", fg="#000000").pack(padx=10, pady=10)
                try:
                    overlay.lift()
                except Exception:
                    pass
                try:
                    root.update_idletasks()
                except Exception:
                    pass

                from datetime import datetime
                default_name = datetime.now().strftime("PitchPineTrail_data_%Y%m%d_%H%M%S.csv")
                file_path = filedialog.asksaveasfilename(
                    title="Save decadal data as CSV",
                    defaultextension=".csv",
                    initialfile=default_name,
                    filetypes=[("CSV (comma-separated)", "*.csv"), ("All files", "*.*")]
                )
                if not file_path:
                    return
                try:
                    # use df captured from earlier in this function
                    # add an Actions column mapping game.action_history to each saved year
                    try:
                        save_df = df.copy()
                        # build mapping year -> list of action names
                        actions_map = {}
                        for y, a in getattr(game, 'action_history', []):
                            try:
                                name = ACTIONS.get(str(a), str(a))
                            except Exception:
                                name = str(a)
                            try:
                                actions_map.setdefault(int(y), []).append(name)
                            except Exception:
                                # fallback if year isn't int-convertible
                                actions_map.setdefault(y, []).append(name)

                        # build mapping year -> list of achievements
                        achievements_map = {}
                        for y, n in getattr(game, 'achievements_history', []):
                            try:
                                achievements_map.setdefault(int(y), []).append(n)
                            except Exception:
                                achievements_map.setdefault(y, []).append(n)

                        def _index_to_year(idx):
                            # df index may contain 'Start' or integers
                            try:
                                if str(idx).lower() == 'start':
                                    return -1
                            except Exception:
                                pass
                            try:
                                return int(idx)
                            except Exception:
                                return idx

                        actions_col = []
                        achievements_col = []
                        for idx in save_df.index:
                            yr = _index_to_year(idx)
                            acts = actions_map.get(yr, [])
                            # actions separated by semicolon (existing behavior)
                            actions_col.append('; '.join(acts) if acts else '')
                            achs = achievements_map.get(yr, [])
                            # achievements separated by dash for CSV (user request)
                            achievements_col.append(' - '.join(achs) if achs else '')

                        save_df['Actions'] = actions_col
                        save_df['Achievements'] = achievements_col
                        save_df.to_csv(file_path, index=True)
                    except Exception:
                        # fallback: try saving original df
                        df.to_csv(file_path, index=True)
                    try:
                        messagebox.showinfo("Saved", f"Data saved to:\n{file_path}")
                    except Exception:
                        print(f"Saved data to: {file_path}")
                except Exception as e:
                    try:
                        messagebox.showerror("Save error", f"Could not save CSV: {e}")
                    except Exception:
                        print("Save error:", e)
            except Exception as e:
                print("Unexpected error during save:", e)
            finally:
                try:
                    if overlay and overlay.winfo_exists():
                        overlay.destroy()
                except Exception:
                    pass

        # --- Variable buttons (stacked) to plot each metric vs Year ---
        try:
            from matplotlib.figure import Figure
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        except Exception:
            Figure = None
            FigureCanvasTkAgg = None

        vars_list = ['QMD', 'TPA', 'BA', 'carbon', 'CI', 'fire_risk', 'SPB_risk']
        # Per-variable display titles for plots (allows button name to differ from graph title)
        graph_titles = {
            'QMD': "Quadratic Mean Diameter over time ",
            'TPA': "Trees per Acre over time",
            'BA': "Basal Area over time",
            'carbon': "Carbon in Metric Tons/acre over time",
            'CI': "Crowning Index over time",
            'fire_risk': "Fire Risk over time",
            'SPB_risk': "SPB Risk over time",
        }
        # Per-variable button labels (customize what each graph button displays)
        graph_button_labels = {
            'QMD': 'QMD',
            'TPA': 'TPA',
            'BA': 'BA',
            'carbon': 'Carbon',
            'CI': 'CI',
            'fire_risk': 'Fire Risk',
            'SPB_risk': 'SPB Risk',
        }
        buttons_frame = tk.Frame(analysis_frame, bg="#1b2336", bd=0)
        buttons_frame.place(relx=0.88, rely=0.72, anchor="n")

        # Keep track of the currently shown graph overlay so we only have one at a time
        current_graph = {"frame": None}

        def show_variable_plot(var):
            if Figure is None or FigureCanvasTkAgg is None:
                try:
                    messagebox.showerror("Plot error", "matplotlib not available")
                except Exception:
                    pass
                return

            try:
                # Use the current df if available, otherwise request fresh data
                try:
                    plot_df = df.copy()
                except Exception:
                    plot_df = game.get_decadal_dataframe(10)

                # remove spacer row if present
                if '' in plot_df.index:
                    plot_df = plot_df.loc[plot_df.index != '']
                if plot_df.empty:
                    messagebox.showinfo("No data", "No decadal data available to plot.")
                    return

                # Build numeric x positions for plotting. Keep DataFrame index labels (e.g. 'Start')
                x_positions = []
                for y in plot_df.index:
                    try:
                        if str(y).lower() == 'start':
                            x_positions.append(-1)
                        else:
                            x_positions.append(int(y))
                    except Exception:
                        try:
                            x_positions.append(int(str(y)))
                        except Exception:
                            x_positions.append(None)

                # Map GUI variable keys to DataFrame column names (DataFrame uses some different labels)
                col_map = {'carbon': 'Carbon', 'fire_risk': 'Fire risk', 'SPB_risk': 'SPB risk'}
                col = col_map.get(var, var)
                vals = plot_df[col].tolist() if col in plot_df.columns else []

                # Handle categorical risk variables by mapping to numeric scale
                if var in ('fire_risk', 'SPB_risk'):
                    mapping = {'Low': 1, 'Moderate': 2, 'High': 3}
                    y_vals = [mapping.get(v, float('nan')) for v in vals]
                    y_ticks = [1, 2, 3]
                    y_ticklabels = ['Low', 'Moderate', 'High']
                else:
                    y_vals = []
                    for v in vals:
                        try:
                            y_vals.append(float(v))
                        except Exception:
                            y_vals.append(float('nan'))

                # If a graph is already open, close it before opening a new one
                try:
                    if current_graph.get("frame") and current_graph["frame"].winfo_exists():
                        current_graph["frame"].destroy()
                except Exception:
                    pass

                # Overlay frame placed to cover the data frame area. Use a
                # pixel-sized frame so the Matplotlib canvas has a predictable
                # size on different displays.
                # Constrain graph size to a fraction of the available window
                # so it doesn't overflow on small displays.
                graph_px_w = min(scale_x(700), int(SCREEN_W * 0.7))
                graph_px_w = max(240, graph_px_w)
                graph_px_h = min(scale_y(430), int(SCREEN_H * 0.6))
                graph_px_h = max(160, graph_px_h)
                graph_frame = tk.Frame(analysis_frame, bg="#FFFFFF", bd=0)
                graph_frame.place(relx=0.135, rely=0.235, anchor="nw", width=graph_px_w, height=graph_px_h)
                current_graph["frame"] = graph_frame

                # Figure/axis styling to match the app theme. Convert pixel
                # dimensions to inches for figsize (inches = pixels / dpi).
                dpi = 100
                fig = Figure(figsize=(graph_px_w / dpi, graph_px_h / dpi), dpi=dpi, facecolor='#1f3339')
                ax = fig.add_subplot(111)
                ax.set_facecolor('#121e22')
                # Matplotlib font sizing scaled to screen so labels don't get
                # cut off on small displays.
                title_fs = max(8, scale_font(12))
                label_fs = max(7, scale_font(10))
                tick_fs = max(6, scale_font(9))
                marker_sz = max(3, int(scale_x(6) / (SCREEN_W / BASE_W)))
                # For categorical risk variables show colored bars; otherwise plot line+markers
                if var in ('fire_risk', 'SPB_risk'):
                    # Map risk labels to colors and draw bars at x positions
                    color_map = {'Low': '#228B22', 'Moderate': '#FFA600', 'High': '#B22222'}
                    bar_colors = [color_map.get(v, '#b5c3d8') for v in vals]
                    # Use a modest width so bars are visible across decadal spacing
                    span = max(x_positions or [0]) - min(x_positions or [0]) if x_positions else 0
                    bar_width = (6 if span > 20 else 0.6) * max(0.6, SCREEN_W / BASE_W)
                    ax.bar(x_positions, y_vals, width=bar_width, color=bar_colors, edgecolor='#1b2336')
                else:
                    ax.plot(x_positions, y_vals, marker='o', linestyle='-', color='#05dd4c',
                            markerfacecolor='#05dd4c', markeredgecolor='#121e22', markersize=marker_sz)
                ax.set_xlabel('Year', color='#b5c3d8', fontsize=label_fs)
                ax.set_title(graph_titles.get(var, var), color='#b5c3d8', fontsize=title_fs)
                ax.tick_params(colors='#b5c3d8', labelsize=tick_fs)
                fig.subplots_adjust(left=0.12, right=0.98, top=0.9, bottom=0.12)
                # Force x-axis to always span Years 1-100 with ticks every 10 years
                try:
                    # Expand x-axis to include the starting snapshot at Year -1
                    ax.set_xlim(-10, 100)
                    xt = [-10] + list(range(0, 101, 10))
                    ax.set_xticks(xt)
                    # Remove the word 'Start' from axis labels per user request (leave blank for -1)
                    xt_labels = [''] + [str(x) for x in range(0, 101, 10)]
                    ax.set_xticklabels(xt_labels, color='#b5c3d8')
                except Exception:
                    # If anything goes wrong setting ticks, ignore and continue
                    pass
                # Make spines match theme
                for spine in ax.spines.values():
                    spine.set_color('#2c404b')
                if var in ('fire_risk', 'SPB_risk'):
                    ax.set_yticks(y_ticks)
                    ax.set_yticklabels(y_ticklabels, color='#b5c3d8')

                # Per-variable y-axis labels and fixed limits
                try:
                    y_axis_configs = {
                        'QMD': ("Quadratic Mean Diameter (inches)", 0, 25),
                        'TPA': ("Trees per Acre", 0, 650),
                        'BA': ("Basal Area (sq ft/acre)", 0, 150),
                        'carbon': ("Carbon (Metric Tons/acre)", 0, 25),
                        'CI': ("Crowning Index (mph)", 0, 50),
                        'fire_risk': ("", None, None),
                        'SPB_risk': ("", None, None),
                    }
                    if var in y_axis_configs:
                        y_label, y_min, y_max = y_axis_configs[var]
                        ax.set_ylabel(y_label, color='#b5c3d8')
                        if y_min is not None and y_max is not None:
                            try:
                                ax.set_ylim(y_min, y_max)
                            except Exception:
                                pass
                    else:
                        ax.set_ylabel(var, color='#b5c3d8')
                except Exception:
                    pass

                canvas = FigureCanvasTkAgg(fig, master=graph_frame)
                canvas.draw()
                canvas.get_tk_widget().pack(fill='both', expand=True)

                # Close button for the graph overlay
                def close_graph():
                    try:
                        # Destroy any FAQ overlay/widgets first
                        try:
                            faq_btn = current_graph.get('faq_btn')
                            if faq_btn and faq_btn.winfo_exists():
                                faq_btn.destroy()
                        except Exception:
                            pass
                        try:
                            close_faq_btn = current_graph.get('close_faq_btn')
                            if close_faq_btn and close_faq_btn.winfo_exists():
                                close_faq_btn.destroy()
                        except Exception:
                            pass
                        try:
                            faq_overlay = current_graph.get('faq_overlay')
                            if faq_overlay and faq_overlay.winfo_exists():
                                faq_overlay.destroy()
                        except Exception:
                            pass
                        if current_graph.get("frame") and current_graph["frame"].winfo_exists():
                            current_graph["frame"].destroy()
                    finally:
                        current_graph["frame"] = None

                # Close Graph button
                tk.Button(graph_frame, text="Close Graph", font=("Courier", scale_font(11), "bold"),
                          bg="#121e22", fg="#b5c3d8", command=close_graph).place(relx=0.02, rely=0.0)

                # FAQ overlay support: button shown under the Close Graph button
                def show_faq():
                    # If already showing, do nothing
                    if current_graph.get('faq_overlay') and current_graph['faq_overlay'].winfo_exists():
                        return

                    img_path = os.path.join('assets', 'FAQs.jpg') if os.path.exists(os.path.join('assets', 'FAQs.jpg')) else 'FAQs.jpg'

                    # Wait until graph_frame has non-zero size, else try again shortly
                    w = graph_frame.winfo_width()
                    h = graph_frame.winfo_height()
                    if w < 10 or h < 10:
                        graph_frame.after(100, show_faq)
                        return

                    try:
                        img = Image.open(img_path)
                        try:
                            img = img.resize((w, h), Image.Resampling.LANCZOS)
                        except Exception:
                            img = img.resize((w, h), Image.LANCZOS)
                        photo = ImageTk.PhotoImage(img)

                        # Overlay label covering the graph
                        overlay = tk.Label(graph_frame, image=photo, bd=0)
                        overlay.image = photo
                        overlay.place(x=0, y=0, relwidth=1, relheight=1)
                        current_graph['faq_overlay'] = overlay

                        # Close FAQs button (only visible while FAQ is shown)
                        def hide_faq():
                            try:
                                if current_graph.get('faq_overlay') and current_graph['faq_overlay'].winfo_exists():
                                    current_graph['faq_overlay'].destroy()
                            except Exception:
                                pass
                            try:
                                if current_graph.get('close_faq_btn') and current_graph['close_faq_btn'].winfo_exists():
                                    current_graph['close_faq_btn'].destroy()
                            except Exception:
                                pass

                        close_btn = tk.Button(graph_frame, text="Close FAQs", font=("Courier", scale_font(11), "bold"),
                                              bg="#20333a", fg="#00e43a", command=hide_faq)
                        # place slightly lower than the FAQ trigger button
                        close_btn.place(relx=0.77, rely=0.93)
                        current_graph['close_faq_btn'] = close_btn
                    except Exception:
                        try:
                            messagebox.showinfo("FAQ", "Could not load FAQs image.")
                        except Exception:
                            pass

                # FAQ trigger button (appears alongside Close Graph)
                faq_btn = tk.Button(graph_frame, text="Why does my graph look like that?", font=("Courier", scale_font(10), "bold"),
                                    bg="#20333a", fg="#b5c3d8", command=show_faq)
                # place lower than the Close Graph button
                faq_btn.place(relx=0.02, rely=0.94)
                current_graph['faq_btn'] = faq_btn
                graph_frame.lift()
            except Exception as e:
                try:
                    messagebox.showerror("Plot error", str(e))
                except Exception:
                    pass

        # Button sizing: width is in characters. Scale down on smaller screens
        btn_width = max(8, int(18 * SCREEN_W / BASE_W))
        btn_font_size = max(8, scale_font(11))
        for var in vars_list:
            tk.Button(
                buttons_frame,
                text=graph_button_labels.get(var, var),
                width=btn_width,
                font=("Courier", btn_font_size, "bold"),
                bg="#05dd4c",
                fg="#1b2336",
                activebackground="#228a44",
                command=lambda v=var: show_variable_plot(v)
            ).pack(pady=2)

        # --- Definitions Button Frame (same placement as main screen) ---
        definitions_frame = tk.Frame(analysis_frame, bg="#FFFFFF")
        definitions_frame.place(relx=0.05, rely=0.96, anchor="sw")
        definitions_button = tk.Button(
            definitions_frame,
            text="Click for Definitions",
            font=("Courier New", scale_font(12), "bold"),
            width=23,
            bg="#000000",
            fg="#ffffff",
            activebackground="#FFE208",
            command=lambda: show_analysis_definitions(prev_frame)
        )
        definitions_button.pack()


    # ACHIEVMENT SCREENS
    # --- Pine Snake Screen ---
    def show_pine_snake_screen():
        """Display the screen for successful pine snake habitat."""
        play_pine_snake_sound()  # Play over forest sound
        for widget in root.winfo_children():
            widget.pack_forget()
        snake_frame = tk.Frame(root, bg=BG_COLOR)
        snake_frame.pack(fill="both", expand=True)

        # Load and display the background image in a label
        bg_img = Image.open("assets/pinesnake.jpg")
        bg_img = bg_img.resize((SCREEN_W, SCREEN_H))
        bg_photo = ImageTk.PhotoImage(bg_img)
        bg_label = tk.Label(snake_frame, image=bg_photo)
        bg_label.image = bg_photo  # Prevent garbage collection
        bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)

        # --- Metrics Frame (copied from main game screen) ---
        metrics_frame = tk.Frame(snake_frame, bg="#FFFFFF", bd=0)
        metrics_frame.place(relx=0.841, rely=0.57, anchor="n")
        game_status = tk.StringVar()
        status_dict = game.get_status_dict()
        game_status.set(
            f"Year: {status_dict['year']}\n"
            f"\nBasal Area (BA): {status_dict['BA']:.1f} sqft/acre\n"
            f"\nTrees Per Acre (TPA): {status_dict['TPA']}\n"
            f"\nQuadratic Mean Diameter (QMD): {status_dict['QMD']:.1f} inches\n"
            f"\nCarbon per Acre: {status_dict['carbon']:.1f} Metric Tons/acre\n"
            f"\nCrowning Index: {status_dict['CI']:.1f}"
        )
        game_status_message = tk.Message(
            metrics_frame,
            textvariable=game_status,
            width=450,
            justify="center",
            bg="#FFFFFF",
            fg=FG_COLOR,
            font=FONT
        )
        game_status_message.pack()
        fire_risk_label = tk.Label(metrics_frame, wraplength=scale_x(400), justify="left", padx=10, pady=0, bg="#FFFFFF", font=("Courier", scale_font(14), "bold"))
        fire_risk_label.pack()
        spb_risk_label = tk.Label(metrics_frame, wraplength=scale_x(400), justify="left", padx=10, pady=0, bg="#FFFFFF", font=("Courier", scale_font(14), "bold"))
        spb_risk_label.pack()
        fire_risk_label.config(
            text=f"\n\nFire Risk: {status_dict['fire_risk']}",
            fg=get_risk_color(status_dict['fire_risk'])
        )
        spb_risk_label.config(
            text=f"Southern Pine Beetle Risk: {status_dict['SPB_risk']}",
            fg=get_risk_color(status_dict['SPB_risk'])
        )
        narration = tk.StringVar()
        narration.set("")
        narration_label = tk.Label(
            metrics_frame, textvariable=narration, wraplength=scale_x(400), justify="left",
            padx=10, pady=5, bg="#FFFFFF", fg=FG_COLOR, font=FONT
        )
        narration_label.pack()

        # --- Text Frame ---
        text_frame = tk.Frame(snake_frame, bg="#1b2336", bd=0)
        text_frame.place(relx=0.88, rely=0.2, anchor="center")  # Adjust relx/rely as needed

        tk.Label(
            text_frame,
            text="Congratulations! This forest is excellent northern pine snake habitat.\n\nPine snakes are utilizing the stand!",
            bg="#1b2336", fg="#05dd4c", font=("Courier New", scale_font(18), "bold"),
            pady=10, wraplength=scale_x(370), justify="center"
        ).pack()

        # --- Button Frame ---
        button_frame = tk.Frame(snake_frame, bg="#000000", bd=0)
        button_frame.place(relx=0.88, rely=0.33, anchor="center")  # Adjust relx/rely as needed

        tk.Button(
            button_frame, text="Continue", font=("Courier", scale_font(16), "bold"), width=16,
            bg="#05dd4c", fg="#1b2336", activebackground="#069134",
            command=lambda: [snake_frame.pack_forget(), show_next_queued_achievement_or_game()]
        ).pack(pady=0)

    # --- Gentian Screen ---
    def show_gentian_screen():
        """Display the screen for successful gentian colonization."""
        play_gentian_sound()
        for widget in root.winfo_children():
            widget.pack_forget()
        gentian_frame = tk.Frame(root, bg=BG_COLOR)
        gentian_frame.pack(fill="both", expand=True)
    
        # Load and display the background image in a label
        bg_img = Image.open("assets/gentian.jpg")
        bg_img = bg_img.resize((SCREEN_W, SCREEN_H))
        bg_photo = ImageTk.PhotoImage(bg_img)
        bg_label = tk.Label(gentian_frame, image=bg_photo)
        bg_label.image = bg_photo  # Prevent garbage collection
        bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)
    
        # --- Metrics Frame (copied from main game screen) ---
        metrics_frame = tk.Frame(gentian_frame, bg="#FFFFFF", bd=0)
        metrics_frame.place(relx=0.841, rely=0.57, anchor="n")
        game_status = tk.StringVar()
        status_dict = game.get_status_dict()
        game_status.set(
            f"Year: {status_dict['year']}\n"
            f"\nBasal Area (BA): {status_dict['BA']:.1f} sqft/acre\n"
            f"\nTrees Per Acre (TPA): {status_dict['TPA']}\n"
            f"\nQuadratic Mean Diameter (QMD): {status_dict['QMD']:.1f} inches\n"
            f"\nCarbon per Acre: {status_dict['carbon']:.1f} Metric Tons/acre\n"
            f"\nCrowning Index: {status_dict['CI']:.1f}"
        )
        game_status_message = tk.Message(
            metrics_frame,
            textvariable=game_status,
            width=450,
            justify="center",
            bg="#FFFFFF",
            fg=FG_COLOR,
            font=FONT
        )
        game_status_message.pack()
        fire_risk_label = tk.Label(metrics_frame, wraplength=scale_x(400), justify="left", padx=10, pady=0, bg="#FFFFFF", font=("Courier", scale_font(14), "bold"))
        fire_risk_label.pack()
        spb_risk_label = tk.Label(metrics_frame, wraplength=scale_x(400), justify="left", padx=10, pady=0, bg="#FFFFFF", font=("Courier", scale_font(14), "bold"))
        spb_risk_label.pack()
        fire_risk_label.config(
            text=f"\n\nFire Risk: {status_dict['fire_risk']}",
            fg=get_risk_color(status_dict['fire_risk'])
        )
        spb_risk_label.config(
            text=f"Southern Pine Beetle Risk: {status_dict['SPB_risk']}",
            fg=get_risk_color(status_dict['SPB_risk'])
        )
        narration = tk.StringVar()
        narration.set("")
        narration_label = tk.Label(
            metrics_frame, textvariable=narration, wraplength=scale_x(400), justify="left",
            padx=10, pady=5, bg="#FFFFFF", fg=FG_COLOR, font=FONT
        )
        narration_label.pack()
    
        # --- Text Frame ---
        text_frame = tk.Frame(gentian_frame, bg="#1b2336", bd=0)
        text_frame.place(relx=0.88, rely=0.2, anchor="center")
    
        tk.Label(
            text_frame,
            text="Congratulations! This forest now supports rare Pine Barrens gentian!\n\nGentian is growing in the stand!",
            bg="#1b2336", fg="#05dd4c", font=("Courier New", scale_font(18), "bold"),
            pady=10, wraplength=scale_x(370), justify="center"
        ).pack()
    
        # --- Button Frame ---
        button_frame = tk.Frame(gentian_frame, bg="#000000", bd=0)
        button_frame.place(relx=0.88, rely=0.33, anchor="center")
    
        tk.Button(
            button_frame, text="Continue", font=("Courier", scale_font(16), "bold"), width=16,
            bg="#05dd4c", fg="#1b2336", activebackground="#069134",
            command=lambda: [gentian_frame.pack_forget(), show_next_queued_achievement_or_game()]
        ).pack(pady=0)

    # --- Shortleaf Pine Screen ---
    def show_shortleaf_screen():
        """Display the screen for Shortleaf pine establishment."""
        play_gentian_sound()
        for widget in root.winfo_children():
            widget.pack_forget()
        short_frame = tk.Frame(root, bg=BG_COLOR)
        short_frame.pack(fill="both", expand=True)

        # Background image
        bg_img = Image.open("assets/shortleaf.jpg")
        bg_img = bg_img.resize((SCREEN_W, SCREEN_H))
        bg_photo = ImageTk.PhotoImage(bg_img)
        bg_label = tk.Label(short_frame, image=bg_photo)
        bg_label.image = bg_photo
        bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Metrics (copied pattern)
        metrics_frame = tk.Frame(short_frame, bg="#FFFFFF", bd=0)
        metrics_frame.place(relx=0.841, rely=0.57, anchor="n")
        game_status = tk.StringVar()
        status_dict = game.get_status_dict()
        game_status.set(
            f"Year: {status_dict['year']}\n"
            f"\nBasal Area (BA): {status_dict['BA']:.1f} sqft/acre\n"
            f"\nTrees Per Acre (TPA): {status_dict['TPA']}\n"
            f"\nQuadratic Mean Diameter (QMD): {status_dict['QMD']:.1f} inches\n"
            f"\nCarbon per Acre: {status_dict['carbon']:.1f} Metric Tons/acre\n"
            f"\nCrowning Index: {status_dict['CI']:.1f}"
        )
        game_status_message = tk.Message(
            metrics_frame,
            textvariable=game_status,
            width=450,
            justify="center",
            bg="#FFFFFF",
            fg=FG_COLOR,
            font=FONT
        )
        game_status_message.pack()
        fire_risk_label = tk.Label(metrics_frame, wraplength=scale_x(400), justify="left", padx=10, pady=0, bg="#FFFFFF", font=("Courier", scale_font(14), "bold"))
        fire_risk_label.pack()
        spb_risk_label = tk.Label(metrics_frame, wraplength=scale_x(400), justify="left", padx=10, pady=0, bg="#FFFFFF", font=("Courier", scale_font(14), "bold"))
        spb_risk_label.pack()
        fire_risk_label.config(
            text=f"\n\nFire Risk: {status_dict['fire_risk']}",
            fg=get_risk_color(status_dict['fire_risk'])
        )
        spb_risk_label.config(
            text=f"Southern Pine Beetle Risk: {status_dict['SPB_risk']}",
            fg=get_risk_color(status_dict['SPB_risk'])
        )

        # --- Text Frame ---
        text_frame = tk.Frame(short_frame, bg="#1b2336", bd=0)
        text_frame.place(relx=0.88, rely=0.2, anchor="center")

        tk.Label(
            text_frame,
            text="Congratulations! You created sunny spots in your forest & received funding to plant seedlings... \n\nYou earned the Shortleaf Pine achievement!",
            bg="#1b2336", fg="#05dd4c", font=("Courier New", scale_font(16), "bold"),
            pady=10, wraplength=scale_x(370), justify="center"
        ).pack()

        # --- Button Frame ---
        button_frame = tk.Frame(short_frame, bg="#000000", bd=0)
        button_frame.place(relx=0.88, rely=0.33, anchor="center")

        tk.Button(
            button_frame, text="Continue", font=("Courier", scale_font(16), "bold"), width=16,
            bg="#05dd4c", fg="#1b2336", activebackground="#069134",
            command=lambda: [short_frame.pack_forget(), show_next_queued_achievement_or_game()]
        ).pack(pady=0)
    
    # --- Turkey Beard Screen ---
    def show_turkey_beard_screen():
        """Display the screen for Turkey Beard achievement."""
        play_gentian_sound()
        for widget in root.winfo_children():
            widget.pack_forget()
        turkey_frame = tk.Frame(root, bg=BG_COLOR)
        turkey_frame.pack(fill="both", expand=True)

        # Background image
        bg_img = Image.open("assets/turkeybeard.jpg")
        bg_img = bg_img.resize((SCREEN_W, SCREEN_H))
        bg_photo = ImageTk.PhotoImage(bg_img)
        bg_label = tk.Label(turkey_frame, image=bg_photo)
        bg_label.image = bg_photo
        bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Metrics (copied pattern)
        metrics_frame = tk.Frame(turkey_frame, bg="#FFFFFF", bd=0)
        metrics_frame.place(relx=0.841, rely=0.57, anchor="n")
        game_status = tk.StringVar()
        status_dict = game.get_status_dict()
        game_status.set(
            f"Year: {status_dict['year']}\n"
            f"\nBasal Area (BA): {status_dict['BA']:.1f} sqft/acre\n"
            f"\nTrees Per Acre (TPA): {status_dict['TPA']}\n"
            f"\nQuadratic Mean Diameter (QMD): {status_dict['QMD']:.1f} inches\n"
            f"\nCarbon per Acre: {status_dict['carbon']:.1f} Metric Tons/acre\n"
            f"\nCrowning Index: {status_dict['CI']:.1f}"
        )
        game_status_message = tk.Message(
            metrics_frame,
            textvariable=game_status,
            width=450,
            justify="center",
            bg="#FFFFFF",
            fg=FG_COLOR,
            font=FONT
        )
        game_status_message.pack()
        fire_risk_label = tk.Label(metrics_frame, wraplength=scale_x(400), justify="left",
                                   padx=10, pady=0, bg="#FFFFFF", font=("Courier", scale_font(14), "bold"))
        fire_risk_label.pack()
        spb_risk_label = tk.Label(metrics_frame, wraplength=scale_x(400), justify="left",
                                  padx=10, pady=0, bg="#FFFFFF", font=("Courier", scale_font(14), "bold"))
        spb_risk_label.pack()
        fire_risk_label.config(
            text=f"\n\nFire Risk: {status_dict['fire_risk']}",
            fg=get_risk_color(status_dict['fire_risk'])
        )
        spb_risk_label.config(
            text=f"Southern Pine Beetle Risk: {status_dict['SPB_risk']}",
            fg=get_risk_color(status_dict['SPB_risk'])
        )

        # Text frame
        text_frame = tk.Frame(turkey_frame, bg="#1b2336", bd=0)
        text_frame.place(relx=0.88, rely=0.2, anchor="center")
        tk.Label(
            text_frame,
            text="Congratulations! Turkey Beard is now growing in this stand!\n\nYou earned the Turkey Beard achievement!",
            bg="#1b2336", fg="#05dd4c", font=("Courier New", scale_font(18), "bold"),
            pady=10, wraplength=scale_x(370), justify="center"
        ).pack()

        # Button frame
        button_frame = tk.Frame(turkey_frame, bg="#000000", bd=0)
        button_frame.place(relx=0.88, rely=0.33, anchor="center")
        tk.Button(
            button_frame, text="Continue", font=("Courier", scale_font(16), "bold"), width=16,
            bg="#05dd4c", fg="#1b2336", activebackground="#069134",
            command=lambda: [turkey_frame.pack_forget(), show_next_queued_achievement_or_game()]
        ).pack(pady=0)
    
    # --- Summer Tanager Screen ---
    def show_summer_tanager_screen():
        """Display the screen for Summer Tanager visitation."""
        play_tanager_sound()
        for widget in root.winfo_children():
            widget.pack_forget()
        tanager_frame = tk.Frame(root, bg=BG_COLOR)
        tanager_frame.pack(fill="both", expand=True)

        # Background image
        bg_img = Image.open("assets/Tanager.jpg")
        bg_img = bg_img.resize((SCREEN_W, SCREEN_H))
        bg_photo = ImageTk.PhotoImage(bg_img)
        bg_label = tk.Label(tanager_frame, image=bg_photo)
        bg_label.image = bg_photo
        bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Metrics (copied pattern)
        metrics_frame = tk.Frame(tanager_frame, bg="#FFFFFF", bd=0)
        metrics_frame.place(relx=0.841, rely=0.57, anchor="n")
        game_status = tk.StringVar()
        status_dict = game.get_status_dict()
        game_status.set(
            f"Year: {status_dict['year']}\n"
            f"\nBasal Area (BA): {status_dict['BA']:.1f} sqft/acre\n"
            f"\nTrees Per Acre (TPA): {status_dict['TPA']}\n"
            f"\nQuadratic Mean Diameter (QMD): {status_dict['QMD']:.1f} inches\n"
            f"\nCarbon per Acre: {status_dict['carbon']:.1f} Metric Tons/acre\n"
            f"\nCrowning Index: {status_dict['CI']:.1f}"
        )
        game_status_message = tk.Message(
            metrics_frame,
            textvariable=game_status,
            width=450,
            justify="center",
            bg="#FFFFFF",
            fg=FG_COLOR,
            font=FONT
        )
        game_status_message.pack()
        fire_risk_label = tk.Label(metrics_frame, wraplength=scale_x(400), justify="left",
                                   padx=10, pady=0, bg="#FFFFFF", font=("Courier", scale_font(14), "bold"))
        fire_risk_label.pack()
        spb_risk_label = tk.Label(metrics_frame, wraplength=scale_x(400), justify="left",
                                  padx=10, pady=0, bg="#FFFFFF", font=("Courier", scale_font(14), "bold"))
        spb_risk_label.pack()
        fire_risk_label.config(
            text=f"\n\nFire Risk: {status_dict['fire_risk']}",
            fg=get_risk_color(status_dict['fire_risk'])
        )
        spb_risk_label.config(
            text=f"Southern Pine Beetle Risk: {status_dict['SPB_risk']}",
            fg=get_risk_color(status_dict['SPB_risk'])
        )
        narration = tk.StringVar()
        narration.set("")
        tk.Label(
            metrics_frame, textvariable=narration, wraplength=scale_x(400), justify="left",
            padx=10, pady=5, bg="#FFFFFF", fg=FG_COLOR, font=FONT
        ).pack()

        # Text frame
        text_frame = tk.Frame(tanager_frame, bg="#1b2336", bd=0)
        text_frame.place(relx=0.88, rely=0.2, anchor="center")
        tk.Label(
            text_frame,
            text="Congratulations! This forest is being visited by Summer Tanagers.\n\nThese neotropical birds are migrating through the stand!",
            bg="#1b2336", fg="#05dd4c", font=("Courier New", scale_font(18), "bold"),
            pady=10, wraplength=scale_x(370), justify="center"
        ).pack()

        # Button frame
        button_frame = tk.Frame(tanager_frame, bg="#000000", bd=0)
        button_frame.place(relx=0.88, rely=0.33, anchor="center")
        tk.Button(
            button_frame, text="Continue", font=("Courier", scale_font(16), "bold"), width=16,
            bg="#05dd4c", fg="#1b2336", activebackground="#069134",
            command=lambda: [tanager_frame.pack_forget(), show_next_queued_achievement_or_game()]
        ).pack(pady=0)

    # --- Indigo Bunting Screen ---
    def show_indigo_bunting_screen():
        """Display the screen for Indigo Bunting visitation."""
        try:
            play_bunting_sound()
        except Exception:
            pass
        for widget in root.winfo_children():
            widget.pack_forget()
        bunting_frame = tk.Frame(root, bg=BG_COLOR)
        bunting_frame.pack(fill="both", expand=True)

        # Background image
        bg_img = Image.open("assets/bunting.jpg")
        bg_img = bg_img.resize((SCREEN_W, SCREEN_H))
        bg_photo = ImageTk.PhotoImage(bg_img)
        bg_label = tk.Label(bunting_frame, image=bg_photo)
        bg_label.image = bg_photo
        bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Metrics (copied pattern)
        metrics_frame = tk.Frame(bunting_frame, bg="#FFFFFF", bd=0)
        metrics_frame.place(relx=0.841, rely=0.57, anchor="n")
        game_status = tk.StringVar()
        status_dict = game.get_status_dict()
        game_status.set(
            f"Year: {status_dict['year']}\n"
            f"\nBasal Area (BA): {status_dict['BA']:.1f} sqft/acre\n"
            f"\nTrees Per Acre (TPA): {status_dict['TPA']}\n"
            f"\nQuadratic Mean Diameter (QMD): {status_dict['QMD']:.1f} inches\n"
            f"\nCarbon per Acre: {status_dict['carbon']:.1f} Metric Tons/acre\n"
            f"\nCrowning Index: {status_dict['CI']:.1f}"
        )
        game_status_message = tk.Message(
            metrics_frame,
            textvariable=game_status,
            width=450,
            justify="center",
            bg="#FFFFFF",
            fg=FG_COLOR,
            font=FONT
        )
        game_status_message.pack()
        fire_risk_label = tk.Label(metrics_frame, wraplength=scale_x(400), justify="left",
                                   padx=10, pady=0, bg="#FFFFFF", font=("Courier", scale_font(14), "bold"))
        fire_risk_label.pack()
        spb_risk_label = tk.Label(metrics_frame, wraplength=scale_x(400), justify="left",
                                  padx=10, pady=0, bg="#FFFFFF", font=("Courier", scale_font(14), "bold"))
        spb_risk_label.pack()
        fire_risk_label.config(
            text=f"\n\nFire Risk: {status_dict['fire_risk']}",
            fg=get_risk_color(status_dict['fire_risk'])
        )
        spb_risk_label.config(
            text=f"Southern Pine Beetle Risk: {status_dict['SPB_risk']}",
            fg=get_risk_color(status_dict['SPB_risk'])
        )
        narration = tk.StringVar()
        narration.set("")
        tk.Label(
            metrics_frame, textvariable=narration, wraplength=scale_x(400), justify="left",
            padx=10, pady=5, bg="#FFFFFF", fg=FG_COLOR, font=FONT
        ).pack()

        # Text frame
        text_frame = tk.Frame(bunting_frame, bg="#1b2336", bd=0)
        text_frame.place(relx=0.88, rely=0.2, anchor="center")
        tk.Label(
            text_frame,
            text="Congratulations! This forest is being visited by Indigo Buntings.\n\nThese neotropical birds are migrating through the stand!",
            bg="#1b2336", fg="#05dd4c", font=("Courier New", scale_font(18), "bold"),
            pady=10, wraplength=scale_x(370), justify="center"
        ).pack()

        # Button frame
        button_frame = tk.Frame(bunting_frame, bg="#000000", bd=0)
        button_frame.place(relx=0.88, rely=0.33, anchor="center")
        tk.Button(
            button_frame, text="Continue", font=("Courier", scale_font(16), "bold"), width=16,
            bg="#05dd4c", fg="#1b2336", activebackground="#069134",
            command=lambda: [stop_bunting_sound(), bunting_frame.pack_forget(), show_next_queued_achievement_or_game()]
        ).pack(pady=0)

    # --- Tree Frog Screen ---
    def show_tree_frog_screen():
        """Display the screen for Pine Barrens tree frog colonization (random blinking until Continue)."""
        play_tree_frog_sound()
        for widget in root.winfo_children():
            widget.pack_forget()
        frog_frame = tk.Frame(root, bg=BG_COLOR)
        frog_frame.pack(fill="both", expand=True)

        img_a = Image.open("assets/treefrog.jpg").resize((SCREEN_W, SCREEN_H))
        img_b = Image.open("assets/treefrog_1.jpg").resize((SCREEN_W, SCREEN_H))
        photo_a = ImageTk.PhotoImage(img_a)
        photo_b = ImageTk.PhotoImage(img_b)

        bg_label = tk.Label(frog_frame, image=photo_a)
        bg_label.image = photo_a
        bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Random toggle state + scheduled callback id
        state = {
            "running": True,
            "use_a": False,
            "min_ms": 200,
            "max_ms": 800,
            "after_id": None,
        }

        def schedule_next():
            delay = random.randint(state["min_ms"], state["max_ms"])
            state["after_id"] = root.after(delay, do_toggle)

        def do_toggle():
            # If stopped or widgets gone, just exit without touching them
            if (not state["running"]
                or not frog_frame.winfo_exists()
                or not bg_label.winfo_exists()):
                return

            # Flip image
            if state["use_a"]:
                bg_label.config(image=photo_a)
                bg_label.image = photo_a
            else:
                bg_label.config(image=photo_b)
                bg_label.image = photo_b
            state["use_a"] = not state["use_a"]

            # Re-schedule at a random interval
            schedule_next()

        # Start random blinking
        schedule_next()

        # --- Metrics (unchanged) ---
        metrics_frame = tk.Frame(frog_frame, bg="#FFFFFF", bd=0)
        metrics_frame.place(relx=0.841, rely=0.57, anchor="n")
        game_status = tk.StringVar()
        status_dict = game.get_status_dict()
        game_status.set(
            f"Year: {status_dict['year']}\n"
            f"\nBasal Area (BA): {status_dict['BA']:.1f} sqft/acre\n"
            f"\nTrees Per Acre (TPA): {status_dict['TPA']}\n"
            f"\nQuadratic Mean Diameter (QMD): {status_dict['QMD']:.1f} inches\n"
            f"\nCarbon per Acre: {status_dict['carbon']:.1f} Metric Tons/acre\n"
            f"\nCrowning Index: {status_dict['CI']:.1f}"
        )
        game_status_message = tk.Message(
            metrics_frame,
            textvariable=game_status,
            width=450,
            justify="center",
            bg="#FFFFFF",
            fg=FG_COLOR,
            font=FONT
        )
        game_status_message.pack()
        fire_risk_label = tk.Label(metrics_frame, wraplength=scale_x(400), justify="left",
                                   padx=10, pady=0, bg="#FFFFFF", font=("Courier", scale_font(14), "bold"))
        fire_risk_label.pack()
        spb_risk_label = tk.Label(metrics_frame, wraplength=scale_x(400), justify="left",
                                  padx=10, pady=0, bg="#FFFFFF", font=("Courier", scale_font(14), "bold"))
        spb_risk_label.pack()
        fire_risk_label.config(
            text=f"\n\nFire Risk: {status_dict['fire_risk']}",
            fg=get_risk_color(status_dict['fire_risk'])
        )
        spb_risk_label.config(
            text=f"Southern Pine Beetle Risk: {status_dict['SPB_risk']}",
            fg=get_risk_color(status_dict['SPB_risk'])
        )
        narration = tk.StringVar()
        narration.set("")
        tk.Label(
            metrics_frame, textvariable=narration, wraplength=scale_x(400), justify="left",
            padx=10, pady=5, bg="#FFFFFF", fg=FG_COLOR, font=FONT
        ).pack()

        # Text
        text_frame = tk.Frame(frog_frame, bg="#1b2336", bd=0)
        text_frame.place(relx=0.88, rely=0.2, anchor="center")
        tk.Label(
            text_frame,
            text="Congratulations! Pine Barrens tree frogs have colonized this forest.\n\nTree frogs are calling from the stand!",
            bg="#1b2336", fg="#05dd4c", font=("Courier New", scale_font(18), "bold"),
            pady=10, wraplength=scale_x(370), justify="center"
        ).pack()

        # Continue button stops blinking, cancels callback, and returns
        def on_continue():
            state["running"] = False
            if state.get("after_id"):
                try:
                    root.after_cancel(state["after_id"])
                except Exception:
                    pass
                state["after_id"] = None
            stop_tree_frog_sound()
            # leave final image on treefrog.jpg if still present
            if frog_frame.winfo_exists() and bg_label.winfo_exists():
                bg_label.config(image=photo_a)
                bg_label.image = photo_a
            frog_frame.pack_forget()
            show_next_queued_achievement_or_game()

        button_frame = tk.Frame(frog_frame, bg="#000000", bd=0)
        button_frame.place(relx=0.88, rely=0.33, anchor="center")
        tk.Button(
            button_frame, text="Continue", font=("Courier", scale_font(16), "bold"), width=16,
            bg="#05dd4c", fg="#1b2336", activebackground="#069134",
            command=on_continue
        ).pack(pady=0)

    # --- Hurricane Screen ---
    def show_hurricane_screen():
        """Show hurricane sequence: lightning -> rain -> lightning -> rain -> after (wait for Continue)."""
        # Skip if we've already shown the hurricane screen this game
        try:
            if getattr(game, 'hurricane_screen_shown', False):
                return
        except Exception:
            pass
        # Mark screen shown immediately to prevent re-entry from other code paths
        try:
            game.hurricane_screen_shown = True
        except Exception:
            pass
        try:
            play_hurricane_sound()
        except Exception:
            pass
        # mark modal active so animations defer applying their final frame
        game.hurricane_active = True
        # Mark the hurricane as shown for its event year so it won't be re-displayed
        try:
            events = game.stand.get('events', [])
            if events:
                last = events[-1]
                evt_year = last[0] if (isinstance(last, (list, tuple)) and len(last) > 0) else None
                if evt_year is not None:
                    game.hurricane_last_shown_year = int(evt_year)
        except Exception:
            pass
        # clear pending flag
        try:
            game.hurricane_pending = False
        except Exception:
            pass
        # show_hurricane_screen started
        for widget in root.winfo_children():
            widget.pack_forget()
        h_frame = tk.Frame(root, bg=BG_COLOR)
        h_frame.pack(fill="both", expand=True)

        # Load images (resize to screen)
        img_light = Image.open("assets/hurricane_lightning.jpg").resize((SCREEN_W, SCREEN_H))
        img_rain = Image.open("assets/hurricane_rain.jpg").resize((SCREEN_W, SCREEN_H))
        img_after = Image.open("assets/hurricane_after.jpg").resize((SCREEN_W, SCREEN_H))
        photo_light = ImageTk.PhotoImage(img_light)
        photo_rain = ImageTk.PhotoImage(img_rain)
        photo_after = ImageTk.PhotoImage(img_after)

        bg_label = tk.Label(h_frame, image=photo_light)
        bg_label.image = photo_light
        bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Sequence: (image, duration_ms) - None duration means final static
        seq = [ (photo_light, 200), (photo_rain, 2900), (photo_light, 200), (photo_rain, 5100), (photo_after, None) ]
        state = {"running": True, "index": 0, "after_id": None}

        def show_step(idx=0):
            if not state["running"] or not h_frame.winfo_exists() or not bg_label.winfo_exists():
                return
            if idx >= len(seq):
                return
            photo, dur = seq[idx]
            bg_label.config(image=photo)
            bg_label.image = photo
            state["index"] = idx
            if dur is None:
                return
            # schedule next step
            try:
                state["after_id"] = root.after(dur, lambda: show_step(idx + 1))
            except Exception:
                pass

        # Start sequence
        show_step(0)

        # Metrics (same layout as other achievement screens)
        metrics_frame = tk.Frame(h_frame, bg="#FFFFFF", bd=0)
        metrics_frame.place(relx=0.841, rely=0.57, anchor="n")
        game_status = tk.StringVar()
        status_dict = game.get_status_dict()
        game_status.set(
            f"Year: {status_dict['year']}\n"
            f"\nBasal Area (BA): {status_dict['BA']:.1f} sqft/acre\n"
            f"\nTrees Per Acre (TPA): {status_dict['TPA']}\n"
            f"\nQuadratic Mean Diameter (QMD): {status_dict['QMD']:.1f} inches\n"
            f"\nCarbon per Acre: {status_dict['carbon']:.1f} Metric Tons/acre\n"
            f"\nCrowning Index: {status_dict['CI']:.1f}"
        )
        game_status_message = tk.Message(
            metrics_frame,
            textvariable=game_status,
            width=450,
            justify="center",
            bg="#FFFFFF",
            fg=FG_COLOR,
            font=FONT
        )
        game_status_message.pack()
        fire_risk_label = tk.Label(metrics_frame, wraplength=scale_x(400), justify="left",
                                   padx=10, pady=0, bg="#FFFFFF", font=("Courier", scale_font(14), "bold"))
        fire_risk_label.pack()
        spb_risk_label = tk.Label(metrics_frame, wraplength=scale_x(400), justify="left",
                                  padx=10, pady=0, bg="#FFFFFF", font=("Courier", scale_font(14), "bold"))
        spb_risk_label.pack()
        fire_risk_label.config(
            text=f"\n\nFire Risk: {status_dict['fire_risk']}",
            fg=get_risk_color(status_dict['fire_risk'])
        )
        spb_risk_label.config(
            text=f"Southern Pine Beetle Risk: {status_dict['SPB_risk']}",
            fg=get_risk_color(status_dict['SPB_risk'])
        )
        narration = tk.StringVar()
        narration.set("")
        tk.Label(
            metrics_frame, textvariable=narration, wraplength=scale_x(400), justify="left",
            padx=10, pady=5, bg="#FFFFFF", fg=FG_COLOR, font=FONT
        ).pack()

        # Text
        text_frame = tk.Frame(h_frame, bg="#1b2336", bd=0)
        text_frame.place(relx=0.88, rely=0.2, anchor="center")
        tk.Label(
            text_frame,
            text="Oh no! A hurricane passed through your forest. \n\n Your forest is still living but this may have significantly changes your forest metrics.",
            bg="#1b2336", fg="#05dd4c", font=("Courier New", scale_font(18), "bold"),
            pady=10, wraplength=scale_x(370), justify="center"
        ).pack()

        def on_continue():
            state["running"] = False
            if state.get("after_id"):
                try:
                    root.after_cancel(state.get("after_id"))
                except Exception:
                    pass
                state["after_id"] = None
            try:
                stop_hurricane_sound()
            except Exception:
                pass
            # unset modal flag so pending animations can apply
            game.hurricane_active = False
            # leave final image on screen
            if h_frame.winfo_exists() and bg_label.winfo_exists():
                bg_label.config(image=photo_after)
                bg_label.image = photo_after
            h_frame.pack_forget()
            # If the hurricane event occurred in year 100 (or later), go to the closing/winning
            # screen like achievements do; otherwise return to the main game screen.
            try:
                events = game.stand.get('events', [])
                if events:
                    last = events[-1]
                    evt_str = last[1] if (isinstance(last, (list, tuple)) and len(last) > 1) else last
                    evt_year = last[0] if (isinstance(last, (list, tuple)) and len(last) > 0) else None
                    if evt_str == 'Hurricane passed through' and evt_year is not None and int(evt_year) >= 90:
                        show_closing_screen()
                        return
            except Exception:
                pass

            # show the main game screen and clear any temp animation marker shortly after
            show_game_screen()
            try:
                if getattr(game, 'animation_temp_bg', None):
                    root.after(100, lambda: setattr(game, 'animation_temp_bg', None))
            except Exception:
                pass

        button_frame = tk.Frame(h_frame, bg="#000000", bd=0)
        button_frame.place(relx=0.88, rely=0.33, anchor="center")
        tk.Button(
            button_frame, text="Continue", font=("Courier", scale_font(16), "bold"), width=16,
            bg="#05dd4c", fg="#1b2336", activebackground="#069134",
            command=on_continue
        ).pack(pady=0)

    # --- Non-losing Wildfire Screen ---
    def show_wildfire_screen():
        """Display the non-losing wildfire screen triggered by the scheduled WILDFIRE event."""
        # Skip if we've already shown the wildfire screen this game
        try:
            if getattr(game, 'wildfire_screen_shown', False):
                return
        except Exception:
            pass
        # Mark screen shown immediately to prevent re-entry from other code paths
        try:
            game.wildfire_screen_shown = True
        except Exception:
            pass
        try:
            play_fire_sound()
        except Exception:
            pass
        # modal active so other UI updates defer
        game.wildfire_active = True
        # clear pending flag
        try:
            game.wildfire_pending = False
        except Exception:
            pass

        for widget in root.winfo_children():
            widget.pack_forget()
        w_frame = tk.Frame(root, bg=BG_COLOR)
        w_frame.pack(fill="both", expand=True)

        # Static background image for non-losing wildfire
        try:
            img_after = Image.open("assets/nonlosing_fire.jpg").resize((SCREEN_W, SCREEN_H))
            photo_after = ImageTk.PhotoImage(img_after)
            bg_label = tk.Label(w_frame, image=photo_after)
            bg_label.image = photo_after
            bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)
        except Exception:
            bg_label = tk.Label(w_frame, bg=BG_COLOR)
            bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Metrics (same layout as hurricane)
        metrics_frame = tk.Frame(w_frame, bg="#FFFFFF", bd=0)
        metrics_frame.place(relx=0.841, rely=0.57, anchor="n")
        game_status = tk.StringVar()
        status_dict = game.get_status_dict()
        game_status.set(
            f"Year: {status_dict['year']}\n"
            f"\nBasal Area (BA): {status_dict['BA']:.1f} sqft/acre\n"
            f"\nTrees Per Acre (TPA): {status_dict['TPA']}\n"
            f"\nQuadratic Mean Diameter (QMD): {status_dict['QMD']:.1f} inches\n"
            f"\nCarbon per Acre: {status_dict['carbon']:.1f} Metric Tons/acre\n"
            f"\nCrowning Index: {status_dict['CI']:.1f}"
        )
        game_status_message = tk.Message(
            metrics_frame,
            textvariable=game_status,
            width=450,
            justify="center",
            bg="#FFFFFF",
            fg=FG_COLOR,
            font=FONT
        )
        game_status_message.pack()
        fire_risk_label = tk.Label(metrics_frame, wraplength=scale_x(400), justify="left", padx=10, pady=0, bg="#FFFFFF", font=("Courier", scale_font(14), "bold"))
        fire_risk_label.pack()
        spb_risk_label = tk.Label(metrics_frame, wraplength=scale_x(400), justify="left", padx=10, pady=0, bg="#FFFFFF", font=("Courier", scale_font(14), "bold"))
        spb_risk_label.pack()
        fire_risk_label.config(
            text=f"\n\nFire Risk: {status_dict['fire_risk']}",
            fg=get_risk_color(status_dict['fire_risk'])
        )
        spb_risk_label.config(
            text=f"Southern Pine Beetle Risk: {status_dict['SPB_risk']}",
            fg=get_risk_color(status_dict['SPB_risk'])
        )

        # Text
        text_frame = tk.Frame(w_frame, bg="#1b2336", bd=0)
        text_frame.place(relx=0.88, rely=0.2, anchor="center")
        tk.Label(
            text_frame,
            text="Oh no! Your prescribed burn got out of control because your forest was already at high risk for fire. \n\n Your forest is still living but this may have significantly changes your forest metrics.",
            bg="#1b2336", fg="#05dd4c", font=("Courier New", scale_font(16), "bold"),
            pady=10, wraplength=scale_x(370), justify="center"
        ).pack()

        def on_continue():
            try:
                stop_fire_sound()
            except Exception:
                pass
            # unset modal flag
            try:
                game.wildfire_active = False
            except Exception:
                pass
            w_frame.pack_forget()
            show_next_queued_achievement_or_game()

        button_frame = tk.Frame(w_frame, bg="#000000", bd=0)
        button_frame.place(relx=0.88, rely=0.33, anchor="center")
        tk.Button(
            button_frame, text="Continue", font=("Courier", scale_font(16), "bold"), width=16,
            bg="#05dd4c", fg="#1b2336", activebackground="#069134",
            command=on_continue
        ).pack(pady=0)

    # GAME ASSITANCE SCREENS
    # --- Field Guide Screen ---
    def show_field_guide_screen():
        play_page_turn_sound()  # reuse page turn sound
        for widget in root.winfo_children():
            widget.pack_forget()
        fg_frame = tk.Frame(root, bg=BG_COLOR)
        fg_frame.pack(fill="both", expand=True)

        # Background image (field guide)
        bg_img = Image.open("assets/fieldguide.jpg")
        bg_img = bg_img.resize((SCREEN_W, SCREEN_H))
        bg_photo = ImageTk.PhotoImage(bg_img)
        bg_label = tk.Label(fg_frame, image=bg_photo)
        bg_label.image = bg_photo
        bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Metrics (same as definitions)
        metrics_frame = tk.Frame(fg_frame, bg="#FFFFFF", bd=0)
        metrics_frame.place(relx=0.841, rely=0.57, anchor="n")
        game_status = tk.StringVar()
        status_dict = game.get_status_dict()
        game_status.set(
            f"Year: {status_dict['year']}\n"
            f"\nBasal Area (BA): {status_dict['BA']:.1f} sqft/acre\n"
            f"\nTrees Per Acre (TPA): {status_dict['TPA']}\n"
            f"\nQuadratic Mean Diameter (QMD): {status_dict['QMD']:.1f} inches\n"
            f"\nCarbon per Acre: {status_dict['carbon']:.1f} Metric Tons/acre\n"
            f"\nCrowning Index: {status_dict['CI']:.1f}"
        )
        game_status_message = tk.Message(
            metrics_frame,
            textvariable=game_status,
            width=450,
            justify="center",
            bg="#FFFFFF",
            fg=FG_COLOR,
            font=FONT
        )
        game_status_message.pack()
        fire_risk_label = tk.Label(metrics_frame, wraplength=scale_x(400), justify="left",
                                   padx=10, pady=0, bg="#FFFFFF", font=("Courier", scale_font(14), "bold"))
        fire_risk_label.pack()
        spb_risk_label = tk.Label(metrics_frame, wraplength=scale_x(400), justify="left",
                                  padx=10, pady=0, bg="#FFFFFF", font=("Courier", scale_font(14), "bold"))
        spb_risk_label.pack()
        fire_risk_label.config(
            text=f"\n\nFire Risk: {status_dict['fire_risk']}",
            fg=get_risk_color(status_dict['fire_risk'])
        )
        spb_risk_label.config(
            text=f"Southern Pine Beetle Risk: {status_dict['SPB_risk']}",
            fg=get_risk_color(status_dict['SPB_risk'])
        )
        narration = tk.StringVar()
        narration.set("")
        narration_label = tk.Label(
            metrics_frame, textvariable=narration, wraplength=scale_x(400), justify="left",
            padx=10, pady=5, bg="#FFFFFF", fg=FG_COLOR, font=FONT
        )
        narration_label.pack()

        tk.Button(
            fg_frame, text="Return to Game", font=("Courier", scale_font(18), "bold"), width=16,
            bg="#929292", fg="#000000", activebackground="#FFFFFF",
            command=lambda: [play_page_close_sound(), fg_frame.pack_forget(), show_game_screen()]
        ).place(relx=0.6, rely=0.915, anchor="center")

    # --- Definitions Screen ---
    def show_definitions_screen():
        play_page_turn_sound()  # Play page turn sound over forest sound
        for widget in root.winfo_children():
            widget.pack_forget()
        def_frame = tk.Frame(root, bg=BG_COLOR)
        def_frame.pack(fill="both", expand=True)
        # Load and display the definitions background image in a label
        bg_img = Image.open("assets/definitions.jpg")
        bg_img = bg_img.resize((SCREEN_W, SCREEN_H))
        bg_photo = ImageTk.PhotoImage(bg_img)
        bg_label = tk.Label(def_frame, image=bg_photo)
        bg_label.image = bg_photo
        bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)

        # --- Metrics Frame (copied from show_game_screen) ---
        metrics_frame = tk.Frame(def_frame, bg="#FFFFFF", bd=0)
        metrics_frame.place(relx=0.841, rely=0.57, anchor="n")
        game_status = tk.StringVar()
        status_dict = game.get_status_dict()
        game_status.set(
            f"Year: {status_dict['year']}\n"
            f"\nBasal Area (BA): {status_dict['BA']:.1f} sqft/acre\n"
            f"\nTrees Per Acre (TPA): {status_dict['TPA']}\n"
            f"\nQuadratic Mean Diameter (QMD): {status_dict['QMD']:.1f} inches\n"
            f"\nCarbon per Acre: {status_dict['carbon']:.1f} Metric Tons/acre\n"
            f"\nCrowning Index: {status_dict['CI']:.1f}"
        )
        game_status_message = tk.Message(
            metrics_frame,
            textvariable=game_status,
            width=450,
            justify="center",
            bg="#FFFFFF",
            fg=FG_COLOR,
            font=FONT
        )
        game_status_message.pack()
        fire_risk_label = tk.Label(metrics_frame, wraplength=scale_x(400), justify="left", padx=10, pady=0, bg="#FFFFFF", font=("Courier", scale_font(14), "bold"))
        fire_risk_label.pack()
        spb_risk_label = tk.Label(metrics_frame, wraplength=scale_x(400), justify="left", padx=10, pady=0, bg="#FFFFFF", font=("Courier", scale_font(14), "bold"))
        spb_risk_label.pack()
        fire_risk_label.config(
            text=f"\n\nFire Risk: {status_dict['fire_risk']}",
            fg=get_risk_color(status_dict['fire_risk'])
        )
        spb_risk_label.config(
            text=f"Southern Pine Beetle Risk: {status_dict['SPB_risk']}",
            fg=get_risk_color(status_dict['SPB_risk'])
        )
        narration = tk.StringVar()
        narration.set("")
        narration_label = tk.Label(
            metrics_frame, textvariable=narration, wraplength=scale_x(400), justify="left",
            padx=10, pady=5, bg="#FFFFFF", fg=FG_COLOR, font=FONT
        )
        narration_label.pack()

        # Back button
        tk.Button(
            def_frame, text="Return to Game", font=("Courier", scale_font(18), "bold"), width=16,
            bg="#e21fae", fg="#000000", activebackground="#FFFFFF",
            command=lambda: [play_page_close_sound(), def_frame.pack_forget(), show_game_screen()]
        ).place(relx=0.225, rely=0.915, anchor="center")

    # --- definitions screen for analysis lab ---
    def show_analysis_definitions(prev_frame):
        """Definitions screen variant for the Analysis Lab.

        Uses `assets/analyze_definitions.jpg` as background and does not show
        any game metrics. `prev_frame` is packed back when the user returns.
        """
        play_page_turn_sound()
        for widget in root.winfo_children():
            widget.pack_forget()
        def_frame = tk.Frame(root, bg=BG_COLOR)
        def_frame.pack(fill="both", expand=True)

        # Load and display the definitions background image in a label
        try:
            bg_img = Image.open("assets/analyze_definitions.jpg")
            bg_img = bg_img.resize((SCREEN_W, SCREEN_H))
            bg_photo = ImageTk.PhotoImage(bg_img)
            bg_label = tk.Label(def_frame, image=bg_photo)
            bg_label.image = bg_photo
            bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)
        except Exception:
            pass

        # --- action summary (same as Analysis Lab) ---
        text_frame = tk.Frame(def_frame, bg="#1b2336", bd=0)
        text_frame.place(relx=0.88, rely=0.1, anchor="n")
        tk.Label(
            text_frame,
            text=game.get_action_summary(),
            bg="#1b2336", fg="#05dd4c", font=("Courier New", scale_font(15), "bold"),
            wraplength=scale_x(400), justify="left"
        ).pack()

        # Return button: go back to the Analysis Lab screen. Prefer to
        # repack the existing analysis frame (avoid restarting analysis sounds)
        def return_to_analysis():
            try:
                play_page_close_sound()
            except Exception:
                pass
            try:
                def_frame.pack_forget()
            except Exception:
                pass
            # If the original analysis frame still exists, just show it.
            try:
                if getattr(game, 'analysis_frame', None) and game.analysis_frame.winfo_exists():
                    game.analysis_frame.pack(fill="both", expand=True)
                    return
            except Exception:
                pass
            # Fallback: recreate the analysis lab
            try:
                show_analysis_lab(prev_frame)
            except Exception:
                pass

        tk.Button(
            def_frame, text="Return to Analysis", font=("Courier", scale_font(18), "bold"), width=19,
            bg="#e21fae", fg="#000000", activebackground="#FFFFFF",
            command=return_to_analysis
        ).place(relx=0.225, rely=0.915, anchor="center")

    def show_game_screen():
        stop_forest_sound()
        play_forest_sound()
        for widget in root.winfo_children():
            widget.pack_forget()

        # If a hurricane event was just recorded and hasn't been shown yet, show it now
        try:
            events = game.stand.get('events', [])
            # debug logging removed to avoid noisy output from external libs
            if events:
                last = events[-1]
                evt_str = last[1] if (isinstance(last, (list, tuple)) and len(last) > 1) else last
                evt_year = last[0] if (isinstance(last, (list, tuple)) and len(last) > 0) else None
                if evt_str == 'Hurricane passed through' and getattr(game, 'hurricane_last_shown_year', None) != evt_year:
                    # detected hurricane event; show once
                    game.hurricane_last_shown_year = evt_year
                    # Do not emit GUI debug here to avoid noisy logs from external libs
                    show_hurricane_screen()
                    return
                if evt_str == 'WILDFIRE' and getattr(game, 'wildfire_last_shown_year', None) != evt_year:
                    # detected non-losing wildfire event; show once
                    game.wildfire_last_shown_year = evt_year
                    show_wildfire_screen()
                    return
        except Exception:
            pass

        game_frame = tk.Frame(root, bg=BG_COLOR)
        game_frame.pack(fill="both", expand=True)

        # --- Conditional background image (single temp + persisted final) ---
        if getattr(game, 'animation_temp_bg', None):
            bg_img_path = game.animation_temp_bg
        elif getattr(game, 'current_bg_img', None):
            bg_img_path = game.current_bg_img
        else:
            bg_img_path = "assets/Evenagestand.jpg"

        bg_img = Image.open(bg_img_path)
        bg_img = bg_img.resize((SCREEN_W, SCREEN_H))
        bg_photo = ImageTk.PhotoImage(bg_img)
        bg_label = tk.Label(game_frame, image=bg_photo)
        bg_label.image = bg_photo
        bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Helper to run a 1-step animation (start -> final, then clear temp)
        def start_animation(start_path, duration_ms, final_path):
            game.animation_temp_bg = start_path
            show_game_screen()
            root.after(duration_ms, lambda: finish_animation(final_path))

        def finish_animation(final_path):
            # If a hurricane or wildfire (or other modal) screen is active, defer replacing the UI
            if getattr(game, 'hurricane_active', False) or getattr(game, 'wildfire_active', False):
                # Persist final scene so it will be visible after modal closes
                game.animation_temp_bg = final_path
                game.current_bg_img = final_path
                return

            game.animation_temp_bg = final_path
            game.current_bg_img = final_path  # persist final scene
            show_game_screen()
            root.after(100, lambda: setattr(game, 'animation_temp_bg', None))

        
        # --- Metrics Frame ---
        metrics_frame = tk.Frame(game_frame, bg="#FFFFFF", bd=0)
        metrics_frame.place(relx=0.841, rely=0.57, anchor="n")
        game_status = tk.StringVar()
        game_status_message = tk.Message(
            metrics_frame,
            textvariable=game_status,
            width=450,
            justify="center",
            bg="#FFFFFF",
            fg=FG_COLOR,
            font=FONT
        )
        game_status_message.pack()
        fire_risk_label = tk.Label(metrics_frame, wraplength=scale_x(400), justify="left", padx=10, pady=0, bg="#FFFFFF", font=("Courier", scale_font(14), "bold"))
        fire_risk_label.pack()
        spb_risk_label = tk.Label(metrics_frame, wraplength=scale_x(400), justify="left", padx=10, pady=0, bg="#FFFFFF", font=("Courier", scale_font(14), "bold"))
        spb_risk_label.pack()
        narration = tk.StringVar()
        narration.set("")
        narration_label = tk.Label(
            metrics_frame, textvariable=narration, wraplength=scale_x(400), justify="left",
            padx=10, pady=5, bg="#FFFFFF", fg=FG_COLOR, font=FONT
        )
        narration_label.pack()

        # --- Welcome / Status Frame (created AFTER metrics so it stays on top) ---
        welcome_frame = tk.Frame(game_frame, bg="#FFFFFF", bd=0)
        welcome_frame.place(relx=0.88, rely=0.13, anchor="center")
        # Show welcome text only until first choice, then persistent "What will you do next?"
        initial_text = "What will you do next?" if getattr(game, "has_made_first_choice", False) else "Welcome to Pitch Pine Trail! \nClick an action to begin →"
        status_label = tk.Label(
            welcome_frame,
            text=initial_text,
            wraplength=scale_x(600), justify="center",
            padx=10, pady=10, bg="#1b2336", fg="#05dd4c", font=("Courier New", scale_font(14), "bold")
        )
        status_label.pack()

        # Helper to update the welcome/status text when first choice occurs
        def set_post_first_choice_text():
            try:
                game.has_made_first_choice = True
                status_label.config(text="What will you do next?")
                # ensure it is visually on top
                status_label.lift()
                welcome_frame.lift()
                root.update_idletasks()
            except Exception:
                pass

        # --- Button frame ---
        button_frame = tk.Frame(game_frame, bg="#1b2336")
        button_frame.place(relx=0.88, rely=0.26, anchor="center")
        def update_status_labels():
            status_dict = game.get_status_dict()
            game_status.set(
                f"Year: {status_dict['year']}\n"
                f"\nBasal Area (BA): {status_dict['BA']:.1f} sqft/acre\n"
                f"\nTrees Per Acre (TPA): {status_dict['TPA']}\n"
                f"\nQuadratic Mean Diameter (QMD): {status_dict['QMD']:.1f} inches\n"
                f"\nCarbon per Acre: {status_dict['carbon']:.1f} Metric Tons/acre\n"
                f"\nCrowning Index: {status_dict['CI']:.1f}"
            )
            fire_risk_label.config(
                text=f"\n\nFire Risk: {status_dict['fire_risk']}",
                fg=get_risk_color(status_dict['fire_risk'])
            )
            spb_risk_label.config(
                text=f"Southern Pine Beetle Risk: {status_dict['SPB_risk']}",
                fg=get_risk_color(status_dict['SPB_risk'])
            )
        
        def next_turn(action):
            # First-choice handling: mark and update the welcome/status label
            if not getattr(game, "has_made_first_choice", False):
                set_post_first_choice_text()

            
            
            # Precompute PB/HT ordering flags
            burn_indices = [i for i, (_, a) in enumerate(game.action_history) if a == '4']
            heavy_indices = [i for i, (_, a) in enumerate(game.action_history) if a == '3']
            first_burn_idx = burn_indices[0] if burn_indices else None
            first_heavy_idx = heavy_indices[0] if heavy_indices else None
            pb_before_heavy = (first_burn_idx is not None and first_heavy_idx is not None 
                               and any(i < first_heavy_idx for i in burn_indices))
            pb_after_heavy = (first_burn_idx is not None and first_heavy_idx is not None 
                              and any(i > first_heavy_idx for i in burn_indices))
            pb_both_sides = pb_before_heavy and pb_after_heavy

            # Heavy-thin relative to the first prescribed burn
            heavy_before_first_burn = (first_burn_idx is not None and any(i < first_burn_idx for i in heavy_indices))
            heavy_after_first_burn  = (first_burn_idx is not None and any(i > first_burn_idx for i in heavy_indices))

            # Track achievement state from BEFORE this action + per-turn guard
            pine_snakes_before = game.pine_snakes_colonized
            gentian_before = game.gentian_colonized
            tanager_before = getattr(game, 'summer_tanager_colonized', False)
            bunting_before = getattr(game, 'indigo_bunting_colonized', False)
            tree_frog_before = getattr(game, 'pine_barrens_tree_frog_colonized', False)
            turkey_before = getattr(game, 'turkey_beard_achieved', False)
            short_before = getattr(game, 'short_colonized', False)

            # queue all achievements earned THIS turn; show first if any.
            def queue_achievements_and_show(final_bg_img):
                new_snake = (not pine_snakes_before and game.pine_snakes_colonized)
                new_gent  = (not gentian_before and game.gentian_colonized and not game.gentian_screen_shown)
                new_tan   = (not tanager_before and getattr(game, 'summer_tanager_colonized', False)
                             and not getattr(game, 'summer_tanager_screen_shown', False))
                new_bun   = (not bunting_before and getattr(game, 'indigo_bunting_colonized', False)
                             and not getattr(game, 'indigo_bunting_screen_shown', False))
                new_frog  = (not tree_frog_before and getattr(game, 'pine_barrens_tree_frog_colonized', False)
                             and not getattr(game, 'tree_frog_screen_shown', False))
                new_turkey = (not turkey_before and getattr(game, 'turkey_beard_achieved', False)
                              and not getattr(game, 'turkey_beard_screen_shown', False))
                new_short = (not short_before and getattr(game, 'short_colonized', False)
                             and not getattr(game, 'short_screen_shown', False))

                queue = []
                # Order here defines popup order within the turn; adjust if desired
                if new_snake: queue.append('snake')
                if new_gent:  queue.append('gentian')
                if new_tan:   queue.append('tanager')
                if new_bun:   queue.append('bunting')
                if new_frog:  queue.append('frog')
                if new_turkey: queue.append('turkey')
                if new_short: queue.append('short')

                if queue:
                    game.current_bg_img = final_bg_img       # persist this turn’s final scene
                    game.achievement_final_bg = final_bg_img  # keep if needed later
                    # If the simulation recorded a hurricane event this turn, show it after achievements
                    try:
                        events = game.stand.get('events', [])
                        if events:
                            last = events[-1]
                            # events are stored as (year, description) tuples
                            evt_str = last[1] if (isinstance(last, (list, tuple)) and len(last) > 1) else last
                            if evt_str == 'Hurricane passed through':
                                try:
                                    if not getattr(game, 'hurricane_screen_shown', False):
                                        game.hurricane_pending = True
                                        # queued hurricane pending
                                    else:
                                        # already shown this game; nothing to do
                                        pass
                                except Exception:
                                    game.hurricane_pending = True
                    except Exception:
                        pass
                    game.achievement_queue = queue
                    show_next_queued_achievement_or_game()
                    return True
                return False

            # Final decade fast-path — no animations between year 90 and 100
            if 90 <= game.stand['year'] < 100:
                pine_snakes_before = game.pine_snakes_colonized
                game.update_stand(action)
                event = game.simulate_event()
                game.stand['year'] += 10
                update_status_labels()

                # Loss checks first
                if game.is_low_tpa_game_over():
                    show_low_tpa_screen()
                    return
                if getattr(game.stand, 'catastrophic_wildfire', False) or game.stand.get('catastrophic_wildfire', False):
                    show_fire_loss_screen()
                    return
                if event == 'SPB outbreak!' and game.stand['SPB_risk'] == 'High':
                    show_spb_loss_screen()
                    return

                # Achievements before win so they show first at year 100
                final_img = getattr(game, 'current_bg_img', "assets/Evenagestand.jpg")
                if queue_achievements_and_show(final_img):
                    return

                # Win check after achievements
                if game.stand['year'] >= 100:
                    show_closing_screen()
                    return

            #TURN ANIMATIONS
            # --- Prescribed burn after thin lightly but not thin heavily ---
            if (action == '4'
                and not game.prescribed_burn_event
                and game.thin_lightly_event
                and not any(a in ['3'] for _, a in game.action_history)):
                game.prescribed_burn_event = True

                pine_snakes_before = game.pine_snakes_colonized
                game.update_stand(action)
                event = game.simulate_event()
                game.stand['year'] += 10

                # Achievement check
                if queue_achievements_and_show('assets/afterburn_treedown.jpg'):
                    return

                # Animation: prescribedburn_treedown.jpg for 2s, then afterburn_treedown.jpg
                start_animation('assets/prescribedburn_treedown.jpg', 2000, 'assets/afterburn_treedown.jpg')
                return

            # --- Thin lightly after prescribed burn but not thin heavily ---
            if (action == '2'
                and not game.thin_lightly_event
                and game.prescribed_burn_event
                and not any(a in ['3'] for _, a in game.action_history)):
                game.thin_lightly_event = True

                pine_snakes_before = game.pine_snakes_colonized
                game.update_stand(action)
                event = game.simulate_event()
                game.stand['year'] += 10

                # Achievement check (skip animation but persist final)
                if queue_achievements_and_show('assets/afterburn_treedown.jpg'):
                    return

                # Animation: chainsaw_afterburn.jpg for 1.5s, then afterburn_treedown.jpg
                start_animation('assets/chainsaw_afterburn.jpg', 1500, 'assets/afterburn_treedown.jpg')
                return
            
            # --- Prescribed burn event logic ---
            if (action == '4' and
                not game.prescribed_burn_event and
                not any(a in ['2', '3'] for _, a in game.action_history)):
                game.prescribed_burn_event = True
                pine_snakes_before = game.pine_snakes_colonized
                game.update_stand(action)
                event = game.simulate_event()
                game.stand['year'] += 10

                # Achievement check
                if queue_achievements_and_show('assets/afterburn.jpg'):
                    return

                # Animation: prescribedburn.jpg for 2s, then afterburn.jpg
                start_animation('assets/prescribedburn.jpg', 2000, 'assets/afterburn.jpg')
                return

            # --- Thin lightly event logic ---
            if (action == '2' and
                not game.thin_lightly_event and
                not any(a in ['3', '4'] for _, a in game.action_history)):
                game.thin_lightly_event = True
                pine_snakes_before = game.pine_snakes_colonized
                game.update_stand(action)
                event = game.simulate_event()
                game.stand['year'] += 10

                # Achievement check
                if queue_achievements_and_show('assets/treedown.jpg'):
                    return

                # Animation: chainsaw.jpg for 1.5, then treedown.jpg
                start_animation('assets/chainsaw.jpg', 1500, 'assets/treedown.jpg')
                return
            
            # --- Thin lightly after thin heavily but not prescribed burn (first thin-lightly only) ---
            if (action == '2'
                and not game.thin_lightly_event
                and any(a == '3' for _, a in game.action_history)   # heavy-thin was chosen earlier
                and not game.prescribed_burn_event):

                game.thin_lightly_event = True

                pine_snakes_before = game.pine_snakes_colonized
                game.update_stand(action)
                event = game.simulate_event()
                game.stand['year'] += 10

                # Achievement checks (skip animation but persist final)
                if queue_achievements_and_show('assets/heavythin_treedown.jpg'):
                    return

                # Animation: chainsaw_heavythin.jpg for 1.5s, then heavythin_treedown.jpg
                start_animation('assets/chainsaw_heavythin.jpg', 1500, 'assets/heavythin_treedown.jpg')
                return

            # --- Thin heavily after prescribed burn but not thin lightly (first heavy-thin only) ---
            if (action == '3'
                and not any(a == '3' for _, a in game.action_history)  # first time heavy-thin
                and game.prescribed_burn_event                         # after prescribed burn
                and not game.thin_lightly_event):                      # thin lightly not yet chosen

                pine_snakes_before = game.pine_snakes_colonized
                game.update_stand(action)
                event = game.simulate_event()
                game.stand['year'] += 10

                # Achievement checks (persist final)
                if queue_achievements_and_show('assets/heavythin_afterburn.jpg'):
                    return

                # Animation: mower_afterburn.jpg for 2s, then heavythin_afterburn.jpg
                start_animation('assets/mower_afterburn.jpg', 2000, 'assets/heavythin_afterburn.jpg')
                return

            # --- Thin heavily after thin lightly but not prescribed burn (first heavy-thin only) ---
            if (action == '3'
                and not any(a == '3' for _, a in game.action_history)  # first time heavy-thin
                and game.thin_lightly_event                            # after thin lightly
                and not game.prescribed_burn_event):                   # prescribed burn not yet chosen

                pine_snakes_before = game.pine_snakes_colonized
                game.update_stand(action)
                event = game.simulate_event()
                game.stand['year'] += 10

                # Achievement checks (persist final)
                if queue_achievements_and_show('assets/heavythin_treedown.jpg'):
                    return

                # Animation: mower_treedown.jpg for 2s, then heavythin_treedown.jpg
                start_animation('assets/mower_treedown.jpg', 2000, 'assets/heavythin_treedown.jpg')
                return

            # One-time heavy thin animation (only if TL and PB not yet chosen)
            if (action == '3'
                and not any(a == '3' for _, a in game.action_history)
                and not game.thin_lightly_event
                and not game.prescribed_burn_event):

                pine_snakes_before = game.pine_snakes_colonized
                game.update_stand(action)
                event = game.simulate_event()
                game.stand['year'] += 10

                # Achievement checks (persist final)
                if queue_achievements_and_show('assets/heavythin.jpg'):
                    return

                # Animation: mower.jpg for 2s, then heavythin.jpg
                start_animation('assets/mower.jpg', 2000, 'assets/heavythin.jpg')
                return

            # --- Thin heavily after thin lightly AND prescribed burn (first heavy-thin only) ---
            if (action == '3'
                and not any(a == '3' for _, a in game.action_history)
                and game.prescribed_burn_event
                and game.thin_lightly_event):

                pine_snakes_before = game.pine_snakes_colonized
                game.update_stand(action)
                event = game.simulate_event()
                game.stand['year'] += 10

                # Achievement checks (persist final)
                if queue_achievements_and_show('assets/heavythin_afterburn_treedown.jpg'):
                    return

                # Animation: mower_afterburn_treedown.jpg for 2s, then heavythin_afterburn_treedown.jpg
                start_animation('assets/mower_afterburn_treedown.jpg', 2000, 'assets/heavythin_afterburn_treedown.jpg')
                return

            # NEW: Prescribed burn after thin heavily but not thin lightly (first PB only)
            if (action == '4'
                and not game.prescribed_burn_event
                and any(a == '3' for _, a in game.action_history)  # heavy-thin happened earlier
                and not game.thin_lightly_event):

                game.prescribed_burn_event = True

                pine_snakes_before = game.pine_snakes_colonized
                game.update_stand(action)
                event = game.simulate_event()
                game.stand['year'] += 10

                # Achievement check (persist final)
                if queue_achievements_and_show('assets/afterburn_heavythin.jpg'):
                    return

                # Animation: prescribedburn_heavythin.jpg for 2s, then afterburn_heavythin.jpg
                start_animation('assets/prescribedburn_heavythin.jpg', 2000, 'assets/afterburn_heavythin.jpg')
                return

            # --- Thin lightly after heavy-thin that occurred after prescribed burn (first thin-lightly only) ---
            if (action == '2'
                and not game.thin_lightly_event
                and game.prescribed_burn_event
                and any(a == '3' for _, a in game.action_history)
                and heavy_after_first_burn
                and not heavy_before_first_burn):

                game.thin_lightly_event = True

                pine_snakes_before = game.pine_snakes_colonized
                game.update_stand(action)
                event = game.simulate_event()
                game.stand['year'] += 10

                # Achievement checks (persist final)
                if queue_achievements_and_show('assets/heavythin_afterburn_treedown.jpg'):
                    return

                # Animation: chainsaw_heavythin_afterburn.jpg for 1.5s, then heavythin_afterburn_treedown.jpg
                start_animation('assets/chainsaw_heavythin_afterburn.jpg', 1500, 'assets/heavythin_afterburn_treedown.jpg')
                return

            # --- Thin lightly after heavy-thin that occurred before prescribed burn (first thin-lightly only) ---
            if (action == '2'
                and not game.thin_lightly_event
                and game.prescribed_burn_event
                and any(a == '3' for _, a in game.action_history)):  # heavy-thin happened sometime

                # Ensure the first heavy-thin occurred BEFORE the first prescribed burn
                first_burn_idx = next((i for i, (_, a) in enumerate(game.action_history) if a == '4'), None)
                first_heavy_idx = next((i for i, (_, a) in enumerate(game.action_history) if a == '3'), None)
                if first_burn_idx is not None and first_heavy_idx is not None and first_heavy_idx < first_burn_idx:
                    game.thin_lightly_event = True
                    pine_snakes_before = game.pine_snakes_colonized
                    game.update_stand(action)
                    event = game.simulate_event()
                    game.stand['year'] += 10

                    # Achievement checks (persist final)
                    if queue_achievements_and_show('assets/afterburn_heavythin_treedown.jpg'):
                        return

                    # Animation: chainsaw_afterburn_heavythin.jpg for 1.5s, then afterburn_heavythin_treedown.jpg
                    start_animation('assets/chainsaw_afterburn_heavythin.jpg', 1500, 'assets/afterburn_heavythin_treedown.jpg')
                    return

            # --- Prescribed burn after BOTH thin lightly and thin heavily (first PB only) ---
            if (action == '4'
                and not game.prescribed_burn_event
                and game.thin_lightly_event
                and any(a == '3' for _, a in game.action_history)):  # heavy-thin occurred earlier

                game.prescribed_burn_event = True

                pine_snakes_before = game.pine_snakes_colonized
                game.update_stand(action)
                event = game.simulate_event()
                game.stand['year'] += 10

                # Achievement checks (persist final)
                if queue_achievements_and_show('assets/afterburn_heavythin_treedown.jpg'):
                    return

                # Animation: prescribedburn_treedown_heavythin.jpg for 2s, then afterburn_heavythin_treedown.jpg
                start_animation('assets/prescribedburn_treedown_heavythin.jpg', 2000, 'assets/afterburn_heavythin_treedown.jpg')
                return

            # Prescribed burn chosen (again) for the first time AFTER first heavy-thin, with no thin lightly ever
            if (action == '4'
                and game.prescribed_burn_event
                and any(a == '3' for _, a in game.action_history)
                and not game.thin_lightly_event
                and pb_before_heavy
                and not getattr(game, 'pb_after_first_heavythin_shown', False)):

                game.pb_after_first_heavythin_shown = True  # mark so we only animate once

                pine_snakes_before = game.pine_snakes_colonized
                game.update_stand(action)
                event = game.simulate_event()
                game.stand['year'] += 10

                # Achievement check (persist final)
                if queue_achievements_and_show('assets/afterburn_heavythin.jpg'):
                    return

                # Animation: prescribedburn2_heavythin.jpg for 2s, then afterburn_heavythin.jpg
                start_animation('assets/prescribedburn2_heavythin.jpg', 2000, 'assets/afterburn_heavythin.jpg')
                return

            # Prescribed burn chosen again after heavy-thin WHEN thin lightly has been chosen (animate once)
            if (action == '4'
                and game.prescribed_burn_event
                and any(a == '3' for _, a in game.action_history)
                and game.thin_lightly_event
                and pb_before_heavy
                and not getattr(game, 'pb_after_heavythin_with_tl_shown', False)):

                game.pb_after_heavythin_with_tl_shown = True  # mark so we only animate once

                pine_snakes_before = game.pine_snakes_colonized
                game.update_stand(action)
                event = game.simulate_event()
                game.stand['year'] += 10

                # Achievement checks (persist final)
                if queue_achievements_and_show('assets/afterburn_heavythin_treedown.jpg'):
                    return

                # Animation: prescribedburn2_heavythin_treedown.jpg for 2s, then afterburn_heavythin_treedown.jpg
                start_animation('assets/prescribedburn2_heavythin_treedown.jpg', 2000, 'assets/afterburn_heavythin_treedown.jpg')
                return

            # --- Thin lightly (first time) when PB occurred both BEFORE and AFTER first heavy-thin ---
            if (action == '2'
                and not game.thin_lightly_event
                and pb_both_sides):

                game.thin_lightly_event = True

                pine_snakes_before = game.pine_snakes_colonized
                game.update_stand(action)
                event = game.simulate_event()
                game.stand['year'] += 10

                # Achievement checks (persist final)
                if queue_achievements_and_show('assets/afterburn_heavythin_treedown.jpg'):
                    return

                # Animation: chainsaw_afterburn_heavythin.jpg for 1.5s, then afterburn_heavythin_treedown.jpg
                start_animation('assets/chainsaw_afterburn_heavythin.jpg', 1500, 'assets/afterburn_heavythin_treedown.jpg')
                return

            # --- Thin lightly after FIRST heavy-thin and BEFORE FIRST prescribed burn (first TL only) ---
            if (action == '2'
                and not game.thin_lightly_event
                and not game.prescribed_burn_event                      # PB has not happened yet
                and any(a == '3' for _, a in game.action_history)       # HT already chosen
                and first_heavy_idx is not None
                and (first_burn_idx is None or first_heavy_idx < first_burn_idx)):

                game.thin_lightly_event = True

                pine_snakes_before = game.pine_snakes_colonized
                game.update_stand(action)
                event = game.simulate_event()
                game.stand['year'] += 10

                # Achievement checks (persist final)
                if queue_achievements_and_show('assets/afterburn_heavythin_treedown.jpg'):
                    return

                # Animation: chainsaw_afterburn_heavythin.jpg for 1.5s, then afterburn_heavythin_treedown.jpg
                start_animation('assets/chainsaw_afterburn_heavythin.jpg', 1500, 'assets/afterburn_heavythin_treedown.jpg')
                return

            pine_snakes_before = game.pine_snakes_colonized
            game.update_stand(action)
            event = game.simulate_event()
            game.stand['year'] += 10
            update_status_labels()

            # --- Loss checks first ---
            if game.is_low_tpa_game_over():
                show_low_tpa_screen()
                return
            if getattr(game.stand, 'catastrophic_wildfire', False) or game.stand.get('catastrophic_wildfire', False):
                show_fire_loss_screen()
                return
            if event == 'SPB outbreak!' and game.stand['SPB_risk'] == 'High':
                show_spb_loss_screen()
                return

            # --- Achievements (use queue; no animation in default path) ---
            final_img = getattr(game, 'current_bg_img', "assets/Evenagestand.jpg")
            if queue_achievements_and_show(final_img):
                return

            # --- Win check after achievements ---
            if game.stand['year'] >= 100:
                show_closing_screen()
                return

            if event:
                try:
                    last = events[-1]
                    evt_str = last[1] if (isinstance(last, (list, tuple)) and len(last) > 1) else last
                    evt_year = last[0] if (isinstance(last, (list, tuple)) and len(last) > 0) else None
                    # If hurricane event pending display
                    if evt_str == 'Hurricane passed through' and not getattr(game, 'hurricane_screen_shown', False):
                        show_hurricane_screen()
                        return
                    # If non-losing wildfire event pending display
                    if evt_str == 'WILDFIRE' and not getattr(game, 'wildfire_screen_shown', False):
                        show_wildfire_screen()
                        return
                except Exception:
                    pass
                narration.set(event)
            else:
                narration.set("")
        update_status_labels()
        for k, v in ACTIONS.items():
            if k == '1':
                btn_command = lambda k=k: [play_do_nothing_sound(), next_turn(k)]
            elif k == '2':
                btn_command = lambda k=k: [play_thin_lightly_sound(), next_turn(k)]
            elif k == '3':
                btn_command = lambda k=k: [play_thin_heavily_sound(), next_turn(k)]
            elif k == '4':
                btn_command = lambda k=k: [play_prescribed_burn_sound(), next_turn(k)]
            else:
                btn_command = lambda k=k: next_turn(k)
            tk.Button(
                button_frame,
                text=f"{k}. {v}",
                width=22, font=("Courier", scale_font(14), "bold"),
                bg="#404d6d",
                fg="#05dd4c",
                activebackground="#05dd4c",
                command=btn_command
            ).pack(pady=5)
            
        # --- Field Guide & Definitions Buttons on Main Screen ---
        field_guide_frame = tk.Frame(game_frame, bg="#FFFFFF")
        field_guide_frame.place(relx=0.05, rely=0.725, anchor="sw")
        tk.Button(
            field_guide_frame,
            text="Click for Field Guide",
            font=FONT,
            width=23,
            bg="#000000",
            fg="#ffffff",
            activebackground="#257416",
            command=show_field_guide_screen
        ).pack()

        definitions_frame = tk.Frame(game_frame, bg="#FFFFFF")
        definitions_frame.place(relx=0.05, rely=0.96, anchor="sw")
        tk.Button(
            definitions_frame,
            text="Click for Definitions",
            font=FONT,
            width=23,
            bg="#000000",
            fg="#ffffff",
            activebackground="#FFE208",
            command=show_definitions_screen
        ).pack()

        # --- Exit Button (top right) ---
        exit_frame = tk.Frame(game_frame, bg="#FFFFFF")
        exit_frame.place(relx=0.02, rely=0.02, anchor="nw")  

        # Use the reusable overlay function
        tk.Button(
            exit_frame,
            text="Exit",
            font=("Courier", scale_font(17), "bold"),
            width=10,
            bg="#9c3432",
            fg="#3d0606",
            activebackground="#FFFFFF",
            command=lambda: [play_page_turn_sound(), show_exit_survey_overlay_in(game_frame)]
        ).pack()

        # --- Hint button (top center) ---
        hint_images = ["assets/hint1.jpg", 
                       "assets/hint2.jpg", 
                       "assets/hint3.jpg", 
                       "assets/hint4.jpg",
                       "assets/hint5.jpg",
                       "assets/hint6.jpg",
                       "assets/hint7.jpg",
                       "assets/hint8.jpg",
                       "assets/hint9.jpg",
                       "assets/hint10.jpg",
                       "assets/hint11.jpg",
                       "assets/hint12.jpg"]
        if not hasattr(game, "hint_index"):
            game.hint_index = 0
        if not hasattr(game, "hint_overlay"):
            game.hint_overlay = None

        # Button (define before overlay so we can lift it)
        hint_button_frame = tk.Frame(game_frame, bg="#FFFFFF")
        # Top-center button
        hint_button_frame.place(relx=0.67, rely=0.03, anchor="n")
        tk.Button(
            hint_button_frame,
            text="Click for a Hint",
            font=("Courier", scale_font(12), "bold"),
            width=18,
            bg="#1d1a7e",
            fg="#FFFFFF",
            activebackground="#5b82ff",
            command=lambda: [play_hint_open_sound(), show_hint_overlay()]
        ).pack()

        def show_hint_overlay():
            # Destroy previous overlay (only one at a time)
            if game.hint_overlay and game.hint_overlay.winfo_exists():
                try:
                    game.hint_overlay.destroy()
                except Exception:
                    pass
                game.hint_overlay = None

            # Pick image and advance index
            img_path = hint_images[game.hint_index % len(hint_images)]
            game.hint_index = (game.hint_index + 1) % len(hint_images)

            # Create overlay below the button, same X (stacking)
            hint_overlay = tk.Frame(game_frame, bg="#FFFFFF", bd=0)
            hint_overlay.place(relx=0.5, rely=0.02, anchor="n")  # under the button
            game.hint_overlay = hint_overlay  # remember it

            # Load image
            try:
                img = Image.open(img_path)
                try:
                    img = img.resize((scale_x(900), scale_y(350)), Image.Resampling.LANCZOS)
                except Exception:
                    img = img.resize((scale_x(900), scale_y(350)), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                img_label = tk.Label(hint_overlay, image=photo, bg="#FFFFFF", bd=0)
                img_label.image = photo
                img_label.pack()
            except Exception as e:
                print(f"Hint overlay error for {img_path}:", e)
                img_label = tk.Label(
                    hint_overlay,
                    text=f"Hint unavailable ({img_path})",
                    bg="#e6f2ff", fg="#000",
                    font=("Courier", scale_font(14), "bold"), padx=10, pady=10
                )
                img_label.pack()

            # Close hint
            def close_hint():
                play_hint_close_sound()
                if game.hint_overlay and game.hint_overlay.winfo_exists():
                    game.hint_overlay.destroy()
                game.hint_overlay = None

            # Close button layered on the overlay (top-right)
            close_frame = tk.Frame(hint_overlay, bg="#FFFFFF", bd=0)
            close_frame.place(relx=0.14, rely=0.86, anchor="ne")
            tk.Button(
                close_frame,
                text="Close Hint",
                font=("Courier", scale_font(11), "bold"),
                width=12,
                bg="#9c3432",
                fg="#FFFFFF",
                activebackground="#c26967",
                command=close_hint
            ).pack()

            # Ensure the hint button stays visible on top
            hint_button_frame.lift()

    # Helper to show next queued achievement or return to game/closing
    def show_next_queued_achievement_or_game():
        """Show next queued achievement popup, else return to game/closing."""
        q = getattr(game, 'achievement_queue', [])
        if q:
            code = q.pop(0)
            if code == 'snake':
                game.pine_snake_achieved = True
                try:
                    game.add_achievement('Pine snake', game.stand.get('year', 0))
                except Exception:
                    pass
                show_pine_snake_screen()
                return
            if code == 'gentian':
                game.gentian_screen_shown = True
                game.gentian_achieved = True
                try:
                    game.add_achievement('Gentian', game.stand.get('year', 0))
                except Exception:
                    pass
                show_gentian_screen()
                return
            if code == 'tanager':
                game.summer_tanager_screen_shown = True
                game.summer_tanager_achieved = True
                try:
                    game.add_achievement('Summer Tanager', game.stand.get('year', 0))
                except Exception:
                    pass
                show_summer_tanager_screen()
                return
            if code == 'bunting':
                game.indigo_bunting_screen_shown = True
                game.indigo_bunting_achieved = True
                try:
                    game.add_achievement('Indigo Bunting', game.stand.get('year', 0))
                except Exception:
                    pass
                show_indigo_bunting_screen()
                return
            if code == 'frog':
                game.tree_frog_screen_shown = True
                game.tree_frog_achieved = True
                try:
                    game.add_achievement('Pine Barrens tree frog', game.stand.get('year', 0))
                except Exception:
                    pass
                show_tree_frog_screen()
                return
            if code == 'turkey':
                game.turkey_beard_screen_shown = True
                game.turkey_beard_achieved = True
                try:
                    game.add_achievement('Turkey Beard', game.stand.get('year', 0))
                except Exception:
                    pass
                show_turkey_beard_screen()
                return
            if code == 'short':
                game.short_screen_shown = True
                game.short_achieved = True
                try:
                    game.add_achievement('Shortleaf pine', game.stand.get('year', 0))
                except Exception:
                    pass
                show_shortleaf_screen()
                return
            
        # No more queued achievements
        # If a hurricane occurred this turn, show that screen next (after achievements)
        if getattr(game, 'hurricane_pending', False):
            game.hurricane_pending = False
            show_hurricane_screen()
            return

        if game.stand['year'] >= 100:
            show_closing_screen()
        else:
            show_game_screen()

    # Start the main event loop
    #show_analysis_lab()  # <-- TEMP: Jump directly to screen for testing
    root.mainloop()

#DEFINING SOUND FUNCTIONS
def play_forest_sound():
    try:
        pygame.mixer.music.load("assets/forest_sound.wav")
        pygame.mixer.music.play(-1)  # -1 means loop forever
        SOUND_STATE['music'] = 'forest'
    except Exception as e:
        print("Error playing sound:", e)

def stop_forest_sound():
    pygame.mixer.music.stop()
    try:
        if SOUND_STATE.get('music') == 'forest':
            SOUND_STATE.pop('music', None)
    except Exception:
        pass

def play_fire_sound():
    try:
        pygame.mixer.music.load("assets/fire.wav")
        pygame.mixer.music.play(-1)  # Loop forever
        SOUND_STATE['music'] = 'fire'
    except Exception as e:
        print("Error playing fire sound:", e)

def stop_fire_sound():
    pygame.mixer.music.stop()
    try:
        if SOUND_STATE.get('music') == 'fire':
            SOUND_STATE.pop('music', None)
    except Exception:
        pass

def play_trumpet_win_sound():
    try:
        sound = pygame.mixer.Sound("assets/trumpet_win.wav")
        sound.play()
    except Exception as e:
        print("Error playing win sound:", e)

def stop_trumprt_win_sound():
    pygame.mixer.music.stop()

def play_losing_trombone_sound():
    try:
        pygame.mixer.music.load("assets/losing_trombone.wav")
        pygame.mixer.music.play()
        SOUND_STATE['music'] = 'trombone'
    except Exception as e:
        print("Error playing trombone sound:", e)

def stop_losing_trombone_sound():
    pygame.mixer.music.stop()
    try:
        if SOUND_STATE.get('music') == 'trombone':
            SOUND_STATE.pop('music', None)
    except Exception:
        pass

def play_pine_snake_sound():
    try:
        sound = pygame.mixer.Sound("assets/pine_snake.wav")
        sound.play()
    except Exception as e:
        print("Error playing pine snake sound:", e)

def play_spb_eating_sound():
    try:
        # Store the sound and channel so we can stop it later
        play_spb_eating_sound.sound = pygame.mixer.Sound("assets/SPB_eating.wav")
        play_spb_eating_sound.channel = play_spb_eating_sound.sound.play(loops=-1)  # Loop forever
        SOUND_STATE['spb'] = True
    except Exception as e:
        print("Error playing SPB eating sound:", e)

def stop_spb_eating_sound():
    try:
        if hasattr(play_spb_eating_sound, "channel") and play_spb_eating_sound.channel is not None:
            play_spb_eating_sound.channel.stop()
        try:
            SOUND_STATE.pop('spb', None)
        except Exception:
            pass
    except Exception as e:
        print("Error stopping SPB eating sound:", e)

def play_page_turn_sound():
    try:
        sound = pygame.mixer.Sound("assets/page_turn.wav")
        sound.play()
    except Exception as e:
        print("Error playing page turn sound:", e)

def play_page_close_sound():
    try:
        sound = pygame.mixer.Sound("assets/page_close.wav")
        sound.play()
    except Exception as e:
        print("Error playing page close sound:", e)

def play_zoom_sound():
    try:
        sound = pygame.mixer.Sound("assets/zoom.wav")
        sound.play()
    except Exception as e:
        print("Error playing zoom sound:", e)

def play_wind_sound():
    try:
        sound = pygame.mixer.Sound("assets/wind.wav")
        play_wind_sound.channel = sound.play(loops=-1)
        SOUND_STATE['wind'] = True
    except Exception as e:
        print("Error playing wind sound:", e)

def stop_wind_sound():
    try:
        if hasattr(play_wind_sound, "channel") and play_wind_sound.channel is not None:
            play_wind_sound.channel.stop()
        try:
            SOUND_STATE.pop('wind', None)
        except Exception:
            pass
    except Exception as e:
        print("Error stopping wind sound:", e)

def play_hint_open_sound():
    try:
        sound = pygame.mixer.Sound("assets/hintopen.wav")
        sound.play()
    except Exception as e:
        print("Error playing hint open sound:", e)

def play_hint_close_sound():
    try:
        sound = pygame.mixer.Sound("assets/hintclose.wav")
        sound.play()
    except Exception as e:
        print("Error playing hint close sound:", e)

def play_do_nothing_sound():
    try:
        sound = pygame.mixer.Sound("assets/do_nothing.wav")
        sound.play()
    except Exception as e:
        print("Error playing do nothing sound:", e)

def play_thin_lightly_sound():
    try:
        sound = pygame.mixer.Sound("assets/thin_lightly.wav")
        sound.play()
    except Exception as e:
        print("Error playing thin lightly sound:", e)

def play_thin_heavily_sound():
    try:
        sound = pygame.mixer.Sound("assets/thin_heavily.wav")
        sound.play()
    except Exception as e:
        print("Error playing thin heavily sound:", e)

def play_prescribed_burn_sound():
    try:
        sound = pygame.mixer.Sound("assets/prescribed_burn.wav")
        sound.play()
    except Exception as e:
        print("Error playing prescribed burn sound:", e)

def play_lets_play_sound():
    try:
        sound = pygame.mixer.Sound("assets/lets_play.wav")
        sound.play()
    except Exception as e:
        print("Error playing lets play sound:", e)

def play_gentian_sound():
    try:
        sound = pygame.mixer.Sound("assets/gentian.wav")
        sound.play()
    except Exception as e:
        print("Error playing gentian sound:", e)

def play_tanager_sound():
    try:
        sound = pygame.mixer.Sound("assets/tanager.wav")
        sound.play()
    except Exception as e:
        print("Error playing tanager sound:", e)

def play_bunting_sound():
    try:
        sound = pygame.mixer.Sound("assets/bunting.wav")
        # store channel so we can stop it on Continue
        play_bunting_sound.sound = sound
        play_bunting_sound.channel = sound.play()
        SOUND_STATE['bunting'] = True
    except Exception as e:
        print("Error playing bunting sound:", e)

def stop_bunting_sound():
    try:
        if hasattr(play_bunting_sound, "channel") and play_bunting_sound.channel is not None:
            play_bunting_sound.channel.stop()
        try:
            SOUND_STATE.pop('bunting', None)
        except Exception:
            pass
    except Exception as e:
        print("Error stopping bunting sound:", e)

def play_tree_frog_sound():
    try:
        sound = pygame.mixer.Sound("assets/treefrog.wav")
        # store channel so we can stop it later
        play_tree_frog_sound.sound = sound
        play_tree_frog_sound.channel = sound.play(loops=-1)
        SOUND_STATE['tree_frog'] = True
    except Exception as e:
        print("Error playing tree frog sound:", e)

def stop_tree_frog_sound():
    try:
        if hasattr(play_tree_frog_sound, "channel") and play_tree_frog_sound.channel is not None:
            play_tree_frog_sound.channel.stop()
            play_tree_frog_sound.channel = None
        try:
            SOUND_STATE.pop('tree_frog', None)
        except Exception:
            pass
    except Exception as e:
        print("Error stopping tree frog sound:", e)

def play_hurricane_sound():
    try:
        sound = pygame.mixer.Sound("assets/hurricane.wav")
        play_hurricane_sound.sound = sound
        play_hurricane_sound.channel = sound.play(loops=-1)
        SOUND_STATE['hurricane'] = True
    except Exception as e:
        print("Error playing hurricane sound:", e)

def stop_hurricane_sound():
    try:
        if hasattr(play_hurricane_sound, "channel") and play_hurricane_sound.channel is not None:
            play_hurricane_sound.channel.stop()
            play_hurricane_sound.channel = None
        try:
            SOUND_STATE.pop('hurricane', None)
        except Exception:
            pass
    except Exception as e:
        print("Error stopping hurricane sound:", e)

def play_save_sound():
    try:
        sound = pygame.mixer.Sound("assets/save.wav")
        sound.play()
    except Exception as e:
        print("Error playing save sound:", e)

def play_computer_startup():
    try:
        sound = pygame.mixer.Sound("assets/computer_startup.wav")
        sound.play()
    except Exception as e:
        print("Error playing computer startup sound:", e)

def play_computer_shutdown():
    try:
        sound = pygame.mixer.Sound("assets/computer_shutdown.wav")
        sound.play()
    except Exception as e:
        print("Error playing computer shutdown sound:", e)

def play_analysis_lab_sound():
    try:
        # loop analysis ambience until stopped
        play_analysis_lab_sound.sound = pygame.mixer.Sound("assets/analysis_lab.wav")
        play_analysis_lab_sound.channel = play_analysis_lab_sound.sound.play(loops=-1)
        SOUND_STATE['analysis_lab'] = True
    except Exception as e:
        print("Error playing analysis lab sound:", e)

def stop_analysis_lab_sound():
    try:
        if hasattr(play_analysis_lab_sound, "channel") and play_analysis_lab_sound.channel is not None:
            play_analysis_lab_sound.channel.stop()
            play_analysis_lab_sound.channel = None
        try:
            SOUND_STATE.pop('analysis_lab', None)
        except Exception:
            pass
    except Exception as e:
        print("Error stopping analysis lab sound:", e)

if __name__ == "__main__":
    main()