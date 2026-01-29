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
from PIL import Image, ImageTk, ImageGrab
import pygame
import random
import webbrowser
from tkinter import filedialog

def main():
    pygame.mixer.init()

    # Initialize game and UI constants
    game = Game()  # Model handles its own colonization & achievement flags
    # GUI-only state
    game.current_bg_img = "assets/Evenagestand.png"
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

        # Stop any looping/active sounds
        stop_spb_eating_sound()
        stop_fire_sound()
        try:
            stop_tree_frog_sound()
        except Exception:
            pass

        # Reset GUI-only state
        game.current_bg_img = "assets/Evenagestand.png"
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

    def add_definitions_button(overlay):
        """Add a definitions button to the bottom right of the overlay."""
        btn = tk.Button(
            overlay,
            text="Definitions",
            font=("Courier New", scale_font(13), "bold"),
            width=14,
            bg="#444466",
            fg=FG_COLOR,
            activebackground="#333355",
            command=show_definitions_screen
        )
        btn.place(relx=1.0, rely=1.0, anchor="se", x=-20, y=-20)  # 20px from bottom right

    def show_exit_survey_overlay_in(parent):
        """Show the exit survey overlay centered over the given parent frame."""
         # Create centered overlay frame
        overlay = tk.Frame(parent, bg="#FFFFFF", bd=0)
        overlay.place(relx=0.02, rely=0.02, anchor="nw")

        # Load survey image
        try:
            img = Image.open("assets/exitsurvey.png")
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
            "assets/zoom_1.png",
            "assets/zoom_2.png",
            "assets/zoom_3.png",
            "assets/zoom_4.png",
            "assets/zoom_5.png",
            "assets/zoom_6.png",
            "assets/zoom_7.png",
            "assets/zoom_8.png",
            "assets/zoom_9.png"
        ]

        def show_next_zoom(index=0):
            if index < len(zoom_images):
                img = Image.open(zoom_images[index]).resize((SCREEN_W, SCREEN_H))
                photo = ImageTk.PhotoImage(img)
                img_label.config(image=photo)
                img_label.image = photo  # Prevent garbage collection
                root.after(10, lambda: show_next_zoom(index + 1))
            else:
                # Show zoom_10.png and overlay the button
                img = Image.open("assets/zoom_10.png").resize((SCREEN_W, SCREEN_H))
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
    bg_img = Image.open("assets/introscreen.png")
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
        ]
        medals = "-".join(name for name, present in ordered if present)
        if medals:
            bg_img_path = f"assets/{base}_{medals}medal.png"
        else:
            bg_img_path = f"assets/{base}_nomedal.png"
        
        # Load and display the background image in a label
        bg_img = Image.open(bg_img_path)
        bg_img = bg_img.resize((SCREEN_W, SCREEN_H))
        bg_photo = ImageTk.PhotoImage(bg_img)
        bg_label = tk.Label(closing_frame, image=bg_photo)
        bg_label.image = bg_photo  # Prevent garbage collection
        bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)

        # --- Metrics Frame (same as main game screen) ---
        metrics_frame = tk.Frame(closing_frame, bg="#FFFFFF", bd=0)
        metrics_frame.place(relx=0.841, rely=0.72, anchor="center")
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
        text_frame.place(relx=0.88, rely=0.23, anchor="center")
        tk.Label(
            text_frame,
            text=game.get_action_summary(),
            bg="#1b2336", fg="#05dd4c", font=("Courier New", scale_font(17), "bold"),
            wraplength=scale_x(400), justify="left"
        ).pack()

        # --- Button Frame ---
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
                img = Image.open("assets/nameplate.png")
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
                default_name = datetime.now().strftime("PitchPineTrail_certificate_%Y%m%d_%H%M%S.png")
                file_path = filedialog.asksaveasfilename(
                    title="Save Screenshot",
                    defaultextension=".png",
                    initialfile=default_name,
                    filetypes=[("PNG Image", "*.png"), ("JPEG Image", "*.jpg;*.jpeg"), ("All Files", "*.*")]
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
        bg_img = Image.open("assets/LowStocking.png")
        bg_img = bg_img.resize((SCREEN_W, SCREEN_H))
        bg_photo = ImageTk.PhotoImage(bg_img)
        bg_label = tk.Label(low_tpa_frame, image=bg_photo)
        bg_label.image = bg_photo  # Prevent garbage collection
        bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)

        # --- Metrics Frame ---
        metrics_frame = tk.Frame(low_tpa_frame, bg="#FFFFFF", bd=0)
        metrics_frame.place(relx=0.841, rely=0.73, anchor="center")
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

        # --- Button Frame ---
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
        bg_img = Image.open("assets/LossByFire.png")
        bg_img = bg_img.resize((SCREEN_W, SCREEN_H))
        bg_photo = ImageTk.PhotoImage(bg_img)
        bg_label = tk.Label(fire_frame, image=bg_photo)
        bg_label.image = bg_photo  # Prevent garbage collection
        bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)

        # --- Metrics Frame (copied from main game screen) ---
        metrics_frame = tk.Frame(fire_frame, bg="#FFFFFF", bd=0)
        metrics_frame.place(relx=0.841, rely=0.73, anchor="center")
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

        # --- Button Frame ---
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
        bg_img = Image.open("assets/LossBySPB.png")
        bg_img = bg_img.resize((SCREEN_W, SCREEN_H))
        bg_photo = ImageTk.PhotoImage(bg_img)
        bg_label = tk.Label(spb_frame, image=bg_photo)
        bg_label.image = bg_photo  # Prevent garbage collection
        bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)

        # --- Metrics Frame (copied from main game screen) ---
        metrics_frame = tk.Frame(spb_frame, bg="#FFFFFF", bd=0)
        metrics_frame.place(relx=0.841, rely=0.73, anchor="center")
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
        text_frame = tk.Frame(spb_frame, bg="#1b2336", bd=0)
        text_frame.place(relx=0.88, rely=0.19, anchor="center")  # Adjust as needed

        tk.Label(
            text_frame,
            text="A Southern Pine Beetle outbreak has devastated your stand!\n\nWe're trying to grow a healthy forest!",
            bg="#1b2336", fg="#05dd4c", font=("Courier", scale_font(18), "bold"),
            pady=20, wraplength=scale_x(400), justify="center"
        ).pack()

        # --- Button Frame ---
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
        bg_img = Image.open("assets/pinesnake.png")
        bg_img = bg_img.resize((SCREEN_W, SCREEN_H))
        bg_photo = ImageTk.PhotoImage(bg_img)
        bg_label = tk.Label(snake_frame, image=bg_photo)
        bg_label.image = bg_photo  # Prevent garbage collection
        bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)

        # --- Metrics Frame (copied from main game screen) ---
        metrics_frame = tk.Frame(snake_frame, bg="#FFFFFF", bd=0)
        metrics_frame.place(relx=0.841, rely=0.73, anchor="center")
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
        bg_img = Image.open("assets/gentian.png")
        bg_img = bg_img.resize((SCREEN_W, SCREEN_H))
        bg_photo = ImageTk.PhotoImage(bg_img)
        bg_label = tk.Label(gentian_frame, image=bg_photo)
        bg_label.image = bg_photo  # Prevent garbage collection
        bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)
    
        # --- Metrics Frame (copied from main game screen) ---
        metrics_frame = tk.Frame(gentian_frame, bg="#FFFFFF", bd=0)
        metrics_frame.place(relx=0.841, rely=0.73, anchor="center")
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
    
    # --- Turkey Beard Screen ---
    def show_turkey_beard_screen():
        """Display the screen for Turkey Beard achievement."""
        play_gentian_sound()
        for widget in root.winfo_children():
            widget.pack_forget()
        turkey_frame = tk.Frame(root, bg=BG_COLOR)
        turkey_frame.pack(fill="both", expand=True)

        # Background image
        bg_img = Image.open("assets/turkeybeard.png")
        bg_img = bg_img.resize((SCREEN_W, SCREEN_H))
        bg_photo = ImageTk.PhotoImage(bg_img)
        bg_label = tk.Label(turkey_frame, image=bg_photo)
        bg_label.image = bg_photo
        bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Metrics (copied pattern)
        metrics_frame = tk.Frame(turkey_frame, bg="#FFFFFF", bd=0)
        metrics_frame.place(relx=0.841, rely=0.73, anchor="center")
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
        bg_img = Image.open("assets/Tanager.png")
        bg_img = bg_img.resize((SCREEN_W, SCREEN_H))
        bg_photo = ImageTk.PhotoImage(bg_img)
        bg_label = tk.Label(tanager_frame, image=bg_photo)
        bg_label.image = bg_photo
        bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Metrics (copied pattern)
        metrics_frame = tk.Frame(tanager_frame, bg="#FFFFFF", bd=0)
        metrics_frame.place(relx=0.841, rely=0.73, anchor="center")
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
        bg_img = Image.open("assets/bunting.png")
        bg_img = bg_img.resize((SCREEN_W, SCREEN_H))
        bg_photo = ImageTk.PhotoImage(bg_img)
        bg_label = tk.Label(bunting_frame, image=bg_photo)
        bg_label.image = bg_photo
        bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Metrics (copied pattern)
        metrics_frame = tk.Frame(bunting_frame, bg="#FFFFFF", bd=0)
        metrics_frame.place(relx=0.841, rely=0.73, anchor="center")
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

        img_a = Image.open("assets/treefrog.png").resize((SCREEN_W, SCREEN_H))
        img_b = Image.open("assets/treefrog_1.png").resize((SCREEN_W, SCREEN_H))
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
        metrics_frame.place(relx=0.841, rely=0.73, anchor="center")
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
            # leave final image on treefrog.png if still present
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

    # GAME ASSITANCE SCREENS
    # --- Field Guide Screen ---
    def show_field_guide_screen():
        play_page_turn_sound()  # reuse page turn sound
        for widget in root.winfo_children():
            widget.pack_forget()
        fg_frame = tk.Frame(root, bg=BG_COLOR)
        fg_frame.pack(fill="both", expand=True)

        # Background image (field guide)
        bg_img = Image.open("assets/fieldguide.png")
        bg_img = bg_img.resize((SCREEN_W, SCREEN_H))
        bg_photo = ImageTk.PhotoImage(bg_img)
        bg_label = tk.Label(fg_frame, image=bg_photo)
        bg_label.image = bg_photo
        bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Metrics (same as definitions)
        metrics_frame = tk.Frame(fg_frame, bg="#FFFFFF", bd=0)
        metrics_frame.place(relx=0.841, rely=0.73, anchor="center")
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
        ).place(relx=0.5, rely=0.915, anchor="center")

    # --- Definitions Screen ---
    def show_definitions_screen():
        play_page_turn_sound()  # Play page turn sound over forest sound
        for widget in root.winfo_children():
            widget.pack_forget()
        def_frame = tk.Frame(root, bg=BG_COLOR)
        def_frame.pack(fill="both", expand=True)
        # Load and display the definitions background image in a label
        bg_img = Image.open("assets/definitions.png")
        bg_img = bg_img.resize((SCREEN_W, SCREEN_H))
        bg_photo = ImageTk.PhotoImage(bg_img)
        bg_label = tk.Label(def_frame, image=bg_photo)
        bg_label.image = bg_photo
        bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)

        # --- Metrics Frame (copied from show_game_screen) ---
        metrics_frame = tk.Frame(def_frame, bg="#FFFFFF", bd=0)
        metrics_frame.place(relx=0.841, rely=0.73, anchor="center")
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

    def show_game_screen():
        stop_forest_sound()
        play_forest_sound()
        for widget in root.winfo_children():
            widget.pack_forget()

        game_frame = tk.Frame(root, bg=BG_COLOR)
        game_frame.pack(fill="both", expand=True)

        # --- Conditional background image (single temp + persisted final) ---
        if getattr(game, 'animation_temp_bg', None):
            bg_img_path = game.animation_temp_bg
        elif getattr(game, 'current_bg_img', None):
            bg_img_path = game.current_bg_img
        else:
            bg_img_path = "assets/Evenagestand.png"

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
            game.animation_temp_bg = final_path
            game.current_bg_img = final_path  # persist final scene
            show_game_screen()
            root.after(100, lambda: setattr(game, 'animation_temp_bg', None))

        
        # --- Metrics Frame ---
        metrics_frame = tk.Frame(game_frame, bg="#FFFFFF", bd=0)
        metrics_frame.place(relx=0.841, rely=0.73, anchor="center")
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

                queue = []
                # Order here defines popup order within the turn; adjust if desired
                if new_snake: queue.append('snake')
                if new_gent:  queue.append('gentian')
                if new_tan:   queue.append('tanager')
                if new_bun:   queue.append('bunting')
                if new_frog:  queue.append('frog')
                if new_turkey: queue.append('turkey')

                if queue:
                    game.current_bg_img = final_bg_img       # persist this turn’s final scene
                    game.achievement_final_bg = final_bg_img  # keep if needed later
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
                final_img = getattr(game, 'current_bg_img', "assets/Evenagestand.png")
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
                if queue_achievements_and_show('assets/afterburn_treedown.png'):
                    return

                # Animation: prescribedburn_treedown.png for 2s, then afterburn_treedown.png
                start_animation('assets/prescribedburn_treedown.png', 2000, 'assets/afterburn_treedown.png')
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
                if queue_achievements_and_show('assets/afterburn_treedown.png'):
                    return

                # Animation: chainsaw_afterburn.png for 1.5s, then afterburn_treedown.png
                start_animation('assets/chainsaw_afterburn.png', 1500, 'assets/afterburn_treedown.png')
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
                if queue_achievements_and_show('assets/afterburn.png'):
                    return

                # Animation: prescribedburn.png for 2s, then afterburn.png
                start_animation('assets/prescribedburn.png', 2000, 'assets/afterburn.png')
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
                if queue_achievements_and_show('assets/treedown.png'):
                    return

                # Animation: chainsaw.png for 1.5, then treedown.png
                start_animation('assets/chainsaw.png', 1500, 'assets/treedown.png')
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
                if queue_achievements_and_show('assets/heavythin_treedown.png'):
                    return

                # Animation: chainsaw_heavythin.png for 1.5s, then heavythin_treedown.png
                start_animation('assets/chainsaw_heavythin.png', 1500, 'assets/heavythin_treedown.png')
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
                if queue_achievements_and_show('assets/heavythin_afterburn.png'):
                    return

                # Animation: mower_afterburn.png for 2s, then heavythin_afterburn.png
                start_animation('assets/mower_afterburn.png', 2000, 'assets/heavythin_afterburn.png')
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
                if queue_achievements_and_show('assets/heavythin_treedown.png'):
                    return

                # Animation: mower_treedown.png for 2s, then heavythin_treedown.png
                start_animation('assets/mower_treedown.png', 2000, 'assets/heavythin_treedown.png')
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
                if queue_achievements_and_show('assets/heavythin.png'):
                    return

                # Animation: mower.png for 2s, then heavythin.png
                start_animation('assets/mower.png', 2000, 'assets/heavythin.png')
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
                if queue_achievements_and_show('assets/heavythin_afterburn_treedown.png'):
                    return

                # Animation: mower_afterburn_treedown.png for 2s, then heavythin_afterburn_treedown.png
                start_animation('assets/mower_afterburn_treedown.png', 2000, 'assets/heavythin_afterburn_treedown.png')
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
                if queue_achievements_and_show('assets/afterburn_heavythin.png'):
                    return

                # Animation: prescribedburn_heavythin.png for 2s, then afterburn_heavythin.png
                start_animation('assets/prescribedburn_heavythin.png', 2000, 'assets/afterburn_heavythin.png')
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
                if queue_achievements_and_show('assets/heavythin_afterburn_treedown.png'):
                    return

                # Animation: chainsaw_heavythin_afterburn.png for 1.5s, then heavythin_afterburn_treedown.png
                start_animation('assets/chainsaw_heavythin_afterburn.png', 1500, 'assets/heavythin_afterburn_treedown.png')
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
                    if queue_achievements_and_show('assets/afterburn_heavythin_treedown.png'):
                        return

                    # Animation: chainsaw_afterburn_heavythin.png for 1.5s, then afterburn_heavythin_treedown.png
                    start_animation('assets/chainsaw_afterburn_heavythin.png', 1500, 'assets/afterburn_heavythin_treedown.png')
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
                if queue_achievements_and_show('assets/afterburn_heavythin_treedown.png'):
                    return

                # Animation: prescribedburn_treedown_heavythin.png for 2s, then afterburn_heavythin_treedown.png
                start_animation('assets/prescribedburn_treedown_heavythin.png', 2000, 'assets/afterburn_heavythin_treedown.png')
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
                if queue_achievements_and_show('assets/afterburn_heavythin.png'):
                    return

                # Animation: prescribedburn2_heavythin.png for 2s, then afterburn_heavythin.png
                start_animation('assets/prescribedburn2_heavythin.png', 2000, 'assets/afterburn_heavythin.png')
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
                if queue_achievements_and_show('assets/afterburn_heavythin_treedown.png'):
                    return

                # Animation: prescribedburn2_heavythin_treedown.png for 2s, then afterburn_heavythin_treedown.png
                start_animation('assets/prescribedburn2_heavythin_treedown.png', 2000, 'assets/afterburn_heavythin_treedown.png')
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
                if queue_achievements_and_show('assets/afterburn_heavythin_treedown.png'):
                    return

                # Animation: chainsaw_afterburn_heavythin.png for 1.5s, then afterburn_heavythin_treedown.png
                start_animation('assets/chainsaw_afterburn_heavythin.png', 1500, 'assets/afterburn_heavythin_treedown.png')
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
                if queue_achievements_and_show('assets/afterburn_heavythin_treedown.png'):
                    return

                # Animation: chainsaw_afterburn_heavythin.png for 1.5s, then afterburn_heavythin_treedown.png
                start_animation('assets/chainsaw_afterburn_heavythin.png', 1500, 'assets/afterburn_heavythin_treedown.png')
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
            final_img = getattr(game, 'current_bg_img', "assets/Evenagestand.png")
            if queue_achievements_and_show(final_img):
                return

            # --- Win check after achievements ---
            if game.stand['year'] >= 100:
                show_closing_screen()
                return

            if event:
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
        hint_images = ["assets/hint1.png", 
                       "assets/hint2.png", 
                       "assets/hint3.png", 
                       "assets/hint4.png",
                       "assets/hint5.png",
                       "assets/hint6.png",
                       "assets/hint7.png",
                       "assets/hint8.png",
                       "assets/hint9.png"]
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
                show_pine_snake_screen()
                return
            if code == 'gentian':
                game.gentian_screen_shown = True
                game.gentian_achieved = True
                show_gentian_screen()
                return
            if code == 'tanager':
                game.summer_tanager_screen_shown = True
                game.summer_tanager_achieved = True
                show_summer_tanager_screen()
                return
            if code == 'bunting':
                game.indigo_bunting_screen_shown = True
                game.indigo_bunting_achieved = True
                show_indigo_bunting_screen()
                return
            if code == 'frog':
                game.tree_frog_screen_shown = True
                game.tree_frog_achieved = True
                show_tree_frog_screen()
                return
            if code == 'turkey':
                game.turkey_beard_screen_shown = True
                game.turkey_beard_achieved = True
                show_turkey_beard_screen()
                return
        # No more queued achievements
        if game.stand['year'] >= 100:
            show_closing_screen()
        else:
            show_game_screen()

    # Start the main event loop
    #show_gentian_screen()  # <-- TEMP: Jump directly to screen for testing
    root.mainloop()

#DEFINING SOUND FUNCTIONS
def play_forest_sound():
    try:
        pygame.mixer.music.load("assets/forest_sound.wav")
        pygame.mixer.music.play(-1)  # -1 means loop forever
    except Exception as e:
        print("Error playing sound:", e)

def stop_forest_sound():
    pygame.mixer.music.stop()

def play_fire_sound():
    try:
        pygame.mixer.music.load("assets/fire.wav")
        pygame.mixer.music.play(-1)  # Loop forever
    except Exception as e:
        print("Error playing fire sound:", e)

def stop_fire_sound():
    pygame.mixer.music.stop()

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
    except Exception as e:
        print("Error playing trombone sound:", e)

def stop_losing_trombone_sound():
    pygame.mixer.music.stop()

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
    except Exception as e:
        print("Error playing SPB eating sound:", e)

def stop_spb_eating_sound():
    try:
        if hasattr(play_spb_eating_sound, "channel") and play_spb_eating_sound.channel is not None:
            play_spb_eating_sound.channel.stop()
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
    except Exception as e:
        print("Error playing wind sound:", e)

def stop_wind_sound():
    try:
        if hasattr(play_wind_sound, "channel") and play_wind_sound.channel is not None:
            play_wind_sound.channel.stop()
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
    except Exception as e:
        print("Error playing bunting sound:", e)

def stop_bunting_sound():
    try:
        if hasattr(play_bunting_sound, "channel") and play_bunting_sound.channel is not None:
            play_bunting_sound.channel.stop()
    except Exception as e:
        print("Error stopping bunting sound:", e)

def play_tree_frog_sound():
    try:
        sound = pygame.mixer.Sound("assets/treefrog.wav")
        # store channel so we can stop it later
        play_tree_frog_sound.sound = sound
        play_tree_frog_sound.channel = sound.play(loops=-1)
    except Exception as e:
        print("Error playing tree frog sound:", e)

def stop_tree_frog_sound():
    try:
        if hasattr(play_tree_frog_sound, "channel") and play_tree_frog_sound.channel is not None:
            play_tree_frog_sound.channel.stop()
            play_tree_frog_sound.channel = None
    except Exception as e:
        print("Error stopping tree frog sound:", e)

def play_save_sound():
    try:
        sound = pygame.mixer.Sound("assets/save.wav")
        sound.play()
    except Exception as e:
        print("Error playing save sound:", e)

if __name__ == "__main__":
    main()