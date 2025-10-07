"""
Pitch Pine Trail - Forest Management Simulation Game

NJ Forest Service
William Zipse
Cara Escalona
Justin Gimmillaro
Andrea Brown

---------------------------------------------------
Graphical user interface for the Pitch Pine Trail forest management simulation.
Provides interactive screens for gameplay, status display, and decision making.
"""

import tkinter as tk
from tkinter import messagebox
from game_logic import Game, ACTIONS
from PIL import Image, ImageTk
import pygame

def main():
    pygame.mixer.init()  # <-- Move this here, at the very start of main()

    # Initialize game and UI constants
    game = Game()
    game.current_bg_img = "assets/Evenagestand.png"
    game.thin_lightly_event = False
    game.prescribed_burn_event = False
    game.prescribed_burn_temp_bg = None
    game.thin_lightly_temp_bg = None
    game.thin_heavily_temp_bg = None  # temp bg for heavy-thin animation
    game.summer_tanager_screen_shown = False  
    game.pb_after_first_heavythin_shown = False  #first PB after first heavy-thin has animated
    game.pb_after_heavythin_with_tl_shown = False  # first PB-after-heavythin when TL already chosen
    game.pine_snake_achieved = False
    game.gentian_achieved = False
    game.summer_tanager_achieved = False
    game.tree_frog_achieved = False
    game.tree_frog_screen_shown = False
    game.animation_temp_bg = None
    BG_COLOR = "#FFFFFF"    # White background
    FG_COLOR = "#000000"    # Black text
    FONT = ("Courier New", 12, "bold")

    # Set up the main window
    root = tk.Tk()
    root.title("Pitch Pine Trail")
    root.configure(bg=BG_COLOR)
    root.attributes('-fullscreen', True)  #true fullscreen
    root.bind("<Escape>", lambda e: root.attributes("-fullscreen", False)) #exit fullscreen on Escape key


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
        game.reset_game()
        stop_spb_eating_sound()
        stop_fire_sound()
        game.current_bg_img = "assets/Evenagestand.png"
        game.thin_lightly_event = False
        game.prescribed_burn_event = False
        game.prescribed_burn_temp_bg = None
        game.thin_lightly_temp_bg = None
        game.thin_heavily_temp_bg = None
        game.summer_tanager_screen_shown = False
        game.pb_after_first_heavythin_shown = False
        game.pb_after_heavythin_with_tl_shown = False
        game.pine_snake_achieved = False
        game.gentian_achieved = False
        game.summer_tanager_achieved = False
        game.tree_frog_achieved = False 
        game.tree_frog_screen_shown = False
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
            font=FONT,
            width=14,
            bg="#444466",
            fg=FG_COLOR,
            activebackground="#333355",
            command=show_definitions_screen
        )
        btn.place(relx=1.0, rely=1.0, anchor="se", x=-20, y=-20)  # 20px from bottom right

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
            "assets/zoom_0.png",
            "assets/zoom_1.png",
            "assets/zoom_2.png",
            "assets/zoom_3.png",
            "assets/zoom_4.png",
            "assets/zoom_5.png",
            "assets/zoom_6.png",
            "assets/zoom_7.png"
        ]

        def show_next_zoom(index=0):
            if index < len(zoom_images):
                img = Image.open(zoom_images[index]).resize((1920, 1080))
                photo = ImageTk.PhotoImage(img)
                img_label.config(image=photo)
                img_label.image = photo  # Prevent garbage collection
                root.after(15, lambda: show_next_zoom(index + 1))
            else:
                # Show zoom_6.png and overlay the button
                img = Image.open("assets/zoom_8.png").resize((1920, 1080))
                photo = ImageTk.PhotoImage(img)
                img_label.config(image=photo)
                img_label.image = photo

                # Overlay frame for the "Let's Play" button
                overlay = tk.Frame(zoom_frame, bg="", bd=0)
                overlay.place(relx=0.55, rely=0.71, anchor="center")
                tk.Button(
                    overlay,
                    text="Let's Play!",
                    font=("Courier", 18, "bold"),
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
                    font=FONT,
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
    bg_img = bg_img.resize((1920, 1080))  # Or use root.winfo_screenwidth(), etc.
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
        font=("Courier", 14, "bold"),
        width=14,
        bg="#f7d79e",
        fg="#663e1d",
        activebackground="#13471C",
        command=start_zoom_sequence  # <-- Use this instead of show_game_screen
    ).pack(side="left", padx=5)

    tk.Button(
        button_row,
        text="Exit",
        font=("Courier", 14, "bold"),
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


        # Choose background image
        if qmd < 21:
            if ach_snake and ach_gent and ach_tan and ach_frog:
                bg_img_path = "assets/bad_snake-gentian-tanager-frogmedal.png"
            elif ach_snake and ach_gent and not ach_tan and ach_frog:
                bg_img_path = "assets/bad_snake-gentian-frogmedal.png"
            elif ach_snake and not ach_gent and ach_tan and ach_frog:
                bg_img_path = "assets/bad_snake-tanager-frogmedal.png"
            elif ach_snake and not ach_gent and not ach_tan and ach_frog:
                bg_img_path = "assets/bad_snake-frogmedal.png"
            elif not ach_snake and ach_gent and ach_tan and ach_frog:
                bg_img_path = "assets/bad_gentian-tanager-frogmedal.png"
            elif not ach_snake and ach_gent and not ach_tan and ach_frog:
                bg_img_path = "assets/bad_gentian-frogmedal.png"
            elif not ach_snake and not ach_gent and ach_tan and ach_frog:
                bg_img_path = "assets/bad_tanager-frogmedal.png"
            elif ach_frog and not ach_snake and not ach_gent and not ach_tan:
                bg_img_path = "assets/bad_frogmedal.png"
            elif ach_snake and ach_gent and ach_tan and not ach_frog:
                bg_img_path = "assets/bad_snake-gentian-tanagermedal.png"
            elif ach_snake and ach_gent and not ach_tan and not ach_frog:
                bg_img_path = "assets/bad_snake-gentianmedal.png"
            elif ach_snake and not ach_gent and ach_tan and not ach_frog:
                bg_img_path = "assets/bad_snake-tanagermedal.png"
            elif ach_snake and not ach_gent and not ach_tan and not ach_frog:
                bg_img_path = "assets/bad_snakemedal.png"
            elif not ach_snake and ach_gent and ach_tan and not ach_frog:
                bg_img_path = "assets/bad_gentian-tanagermedal.png"
            elif not ach_snake and ach_gent and not ach_tan and not ach_frog:
                bg_img_path = "assets/bad_gentianmedal.png"
            elif not ach_snake and not ach_gent and ach_tan and not ach_frog:
                bg_img_path = "assets/bad_tanagermedal.png"
            else:
                bg_img_path = "assets/bad_nomedal.png"
        elif qmd > 21:
            if ach_snake and ach_gent and ach_tan and ach_frog:
                bg_img_path = "assets/okay_snake-gentian-tanager-frogmedal.png"
            elif ach_snake and ach_gent and not ach_tan and ach_frog:
                bg_img_path = "assets/okay_snake-gentian-frogmedal.png"
            elif ach_snake and not ach_gent and ach_tan and ach_frog:
                bg_img_path = "assets/okay_snake-tanager-frogmedal.png"
            elif ach_snake and not ach_gent and not ach_tan and ach_frog:
                bg_img_path = "assets/okay_snake-frogmedal.png"
            elif not ach_snake and ach_gent and ach_tan and ach_frog:
                bg_img_path = "assets/okay_gentian-tanager-frogmedal.png"
            elif not ach_snake and ach_gent and not ach_tan and ach_frog:
                bg_img_path = "assets/okay_gentian-frogmedal.png"
            elif not ach_snake and not ach_gent and ach_tan and ach_frog:
                bg_img_path = "assets/okay_tanager-frogmedal.png"
            elif ach_frog and not ach_snake and not ach_gent and not ach_tan:
                bg_img_path = "assets/okay_frogmedal.png"
            elif ach_snake and ach_gent and ach_tan and not ach_frog:
                bg_img_path = "assets/okay_snake-gentian-tanagermedal.png"
            elif ach_snake and ach_gent and not ach_tan and not ach_frog:
                bg_img_path = "assets/okay_snake-gentianmedal.png"
            elif ach_snake and not ach_gent and ach_tan and not ach_frog:
                bg_img_path = "assets/okay_snake-tanagermedal.png"
            elif ach_snake and not ach_gent and not ach_tan and not ach_frog:
                bg_img_path = "assets/okay_snakemedal.png"
            elif not ach_snake and ach_gent and ach_tan and not ach_frog:
                bg_img_path = "assets/okay_gentian-tanagermedal.png"
            elif not ach_snake and ach_gent and not ach_tan and not ach_frog:
                bg_img_path = "assets/okay_gentianmedal.png"
            elif not ach_snake and not ach_gent and ach_tan and not ach_frog:
                bg_img_path = "assets/okay_tanagermedal.png"
            else:
                bg_img_path = "assets/okay_nomedal.png"
        else:
            bg_img_path = "assets/okay_nomedal.png"
        
        # Load and display the background image in a label
        bg_img = Image.open(bg_img_path)
        bg_img = bg_img.resize((1920, 1080))
        bg_photo = ImageTk.PhotoImage(bg_img)
        bg_label = tk.Label(closing_frame, image=bg_photo)
        bg_label.image = bg_photo  # Prevent garbage collection
        bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)

        # --- Metrics Frame (same as main game screen) ---
        metrics_frame = tk.Frame(closing_frame, bg="#FFFFFF", bd=0)
        metrics_frame.place(relx=0.845, rely=0.73, anchor="center")
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
            font=("Courier",13, "bold")
        )
        game_status_message.pack()
        fire_risk_label = tk.Label(metrics_frame, wraplength=400, justify="left", padx=10, pady=0, bg="#FFFFFF", font=("Courier", 14, "bold"))
        fire_risk_label.pack()
        spb_risk_label = tk.Label(metrics_frame, wraplength=400, justify="left", padx=10, pady=0, bg="#FFFFFF", font=("Courier", 14, "bold"))
        spb_risk_label.pack()
        fire_risk_label.config(
            text=f"\nFire Risk: {summary['fire_risk']}",
            fg=get_risk_color(summary['fire_risk'])
        )
        spb_risk_label.config(
            text=f"Southern Pine Beetle Risk: {summary['SPB_risk']}",
            fg=get_risk_color(summary['SPB_risk'])
        )
        narration = tk.StringVar()
        narration.set("Thank you for playing Pitch Pine Trail!")
        narration_label = tk.Label(
            metrics_frame, textvariable=narration, wraplength=400, justify="left",
            padx=10, pady=5, bg="#FFFFFF", fg=FG_COLOR, font=FONT
        )
        narration_label.pack()

        # --- Text Frame ---
        text_frame = tk.Frame(closing_frame, bg="#1b2336", bd=0)
        text_frame.place(relx=0.88, rely=0.23, anchor="center")
        tk.Label(
            text_frame,
            text=game.get_action_summary(),
            bg="#1b2336", fg="#05dd4c", font=("Courier New", 17, "bold"),
            wraplength=400, justify="left"
        ).pack()

        # --- Button Frame ---
        button_frame = tk.Frame(closing_frame, bg="#FFFFFF", bd=0)
        button_frame.place(relx=0.845, rely=0.91, anchor="center")
        tk.Button(
            button_frame, text="Try Again", font=("Courier", 14, "bold"), width=15,
            bg="#23ac23", fg="#023a02", activebackground="#10612B",
            command=lambda: restart_game(closing_frame)
        ).pack(side="left", padx=10, pady=0)
        tk.Button(
            button_frame, text="Exit", font=("Courier", 14, "bold"), width=15,
            bg="#9c3432", fg="#2c0505", activebackground="#611010",
            command=root.destroy
        ).pack(side="left", padx=10, pady=0)

    #LOSING SCREEN
    # --- Low Basal Area Screen ---
    def show_low_ba_screen():
        """Display the game over screen for low basal area condition."""
        stop_forest_sound()
        play_losing_trombone_sound()
        play_wind_sound()  # <-- Play wind sound at the same time
        for widget in root.winfo_children():
            widget.pack_forget()
        low_ba_frame = tk.Frame(root, bg=BG_COLOR)
        low_ba_frame.pack(fill="both", expand=True)

        # Load and display the background image in a label
        bg_img = Image.open("assets/LowStocking.png")
        bg_img = bg_img.resize((1920, 1080))
        bg_photo = ImageTk.PhotoImage(bg_img)
        bg_label = tk.Label(low_ba_frame, image=bg_photo)
        bg_label.image = bg_photo  # Prevent garbage collection
        bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)

        # --- Metrics Frame ---
        metrics_frame = tk.Frame(low_ba_frame, bg="#FFFFFF", bd=0)
        metrics_frame.place(relx=0.845, rely=0.73, anchor="center")
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
            font=("Courier",13, "bold")
        )
        game_status_message.pack()
        fire_risk_label = tk.Label(metrics_frame, wraplength=400, justify="left", padx=10, pady=0, bg="#FFFFFF", font=("Courier", 14, "bold"))
        fire_risk_label.pack()
        spb_risk_label = tk.Label(metrics_frame, wraplength=400, justify="left", padx=10, pady=0, bg="#FFFFFF", font=("Courier", 14, "bold"))
        spb_risk_label.pack()
        fire_risk_label.config(
            text=f"\n\n\nFire Risk: {status_dict['fire_risk']}",
            fg=get_risk_color(status_dict['fire_risk'])
        )
        spb_risk_label.config(
            text=f"Southern Pine Beetle Risk: {status_dict['SPB_risk']}",
            fg=get_risk_color(status_dict['SPB_risk'])
        )
        narration = tk.StringVar()
        narration.set("Better luck next time!")
        narration_label = tk.Label(
            metrics_frame, textvariable=narration, wraplength=400, justify="left",
            padx=10, pady=5, bg="#FFFFFF", fg=FG_COLOR, font=FONT
        )
        narration_label.pack()

        # --- Text Frame ---
        text_frame = tk.Frame(low_ba_frame, bg="#1b2336", bd=0)
        text_frame.place(relx=0.88, rely=0.19, anchor="center")

        tk.Label(
            text_frame,
            text="The forest's growing stock trees have been depleted! \n\nWe're supposed to be growing a forest!",
            bg="#1b2336", fg="#05dd4c", font=("Courier New", 18, "bold"),
            pady=0, wraplength=400, justify="center"
        ).pack()

        # --- Button Frame ---
        button_frame = tk.Frame(low_ba_frame, bg="#1b2336", bd=0)
        button_frame.place(relx=0.88, rely=0.315, anchor="center")

        tk.Button(
            button_frame, text="Try Again", font=("Courier", 14, "bold"), width=16,
            bg="#05dd4c", fg="#1b2336", activebackground="#10612B",
            command=lambda: [stop_losing_trombone_sound(), stop_wind_sound(), restart_game(low_ba_frame)]
        ).pack(side="left", padx=10, pady=5)
        tk.Button(
            button_frame, text="Exit", font=("Courier", 14, "bold"), width=16,
            bg="#05dd4c", fg="#1b2336", activebackground="#611010",
            command=root.destroy
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
        bg_img = bg_img.resize((1920, 1080))
        bg_photo = ImageTk.PhotoImage(bg_img)
        bg_label = tk.Label(fire_frame, image=bg_photo)
        bg_label.image = bg_photo  # Prevent garbage collection
        bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)

        # --- Metrics Frame (copied from main game screen) ---
        metrics_frame = tk.Frame(fire_frame, bg="#FFFFFF", bd=0)
        metrics_frame.place(relx=0.845, rely=0.73, anchor="center")
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
            font=("Courier",13, "bold")
        )
        game_status_message.pack()
        fire_risk_label = tk.Label(metrics_frame, wraplength=400, justify="left", padx=10, pady=0, bg="#FFFFFF", font=("Courier", 14, "bold"))
        fire_risk_label.pack()
        spb_risk_label = tk.Label(metrics_frame, wraplength=400, justify="left", padx=10, pady=0, bg="#FFFFFF", font=("Courier", 14, "bold"))
        spb_risk_label.pack()
        fire_risk_label.config(
            text=f"\n\n\nFire Risk: {status_dict['fire_risk']}",
            fg=get_risk_color(status_dict['fire_risk'])
        )
        spb_risk_label.config(
            text=f"Southern Pine Beetle Risk: {status_dict['SPB_risk']}",
            fg=get_risk_color(status_dict['SPB_risk'])
        )
        narration = tk.StringVar()
        narration.set("Better luck next time!")
        narration_label = tk.Label(
            metrics_frame, textvariable=narration, wraplength=400, justify="left",
            padx=10, pady=5, bg="#FFFFFF", fg=FG_COLOR, font=FONT
        )
        narration_label.pack()

        # --- Text Frame ---
        text_frame = tk.Frame(fire_frame, bg="#1b2336", bd=0)
        text_frame.place(relx=0.88, rely=0.2, anchor="center")  # Same as SPB loss

        tk.Label(
            text_frame,
            text="A catastrophic wildfire has occurred!\n\nWe might get a new stand of pitch pine, but we're trying to grow a mature stand!",
            bg="#1b2336", fg="#05dd4c", font=("Courier", 18, "bold"),
            pady=0, wraplength=400, justify="center"
        ).pack()

        # --- Button Frame ---
        button_frame = tk.Frame(fire_frame, bg="#1b2336", bd=0)
        button_frame.place(relx=0.88, rely=0.33, anchor="center")  # Same as SPB loss

        tk.Button(
            button_frame, text="Try Again", font=("Courier", 14, "bold"), width=16,
            bg="#05dd4c", fg="#1b2336", activebackground="#10612B",
            command=lambda: [stop_fire_sound(), restart_game(fire_frame)]
        ).pack(side="left", padx=10, pady=5)
        tk.Button(
            button_frame, text="Exit", font=("Courier", 14, "bold"), width=16,
            bg="#05dd4c", fg="#1b2336", activebackground="#611010",
            command=root.destroy
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
        bg_img = bg_img.resize((1920, 1080))
        bg_photo = ImageTk.PhotoImage(bg_img)
        bg_label = tk.Label(spb_frame, image=bg_photo)
        bg_label.image = bg_photo  # Prevent garbage collection
        bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)

        # --- Metrics Frame (copied from main game screen) ---
        metrics_frame = tk.Frame(spb_frame, bg="#FFFFFF", bd=0)
        metrics_frame.place(relx=0.845, rely=0.73, anchor="center")
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
            font=("Courier",13, "bold")
        )
        game_status_message.pack()
        fire_risk_label = tk.Label(metrics_frame, wraplength=400, justify="left", padx=10, pady=0, bg="#FFFFFF", font=("Courier", 14, "bold"))
        fire_risk_label.pack()
        spb_risk_label = tk.Label(metrics_frame, wraplength=400, justify="left", padx=10, pady=0, bg="#FFFFFF", font=("Courier", 14, "bold"))
        spb_risk_label.pack()
        fire_risk_label.config(
            text=f"\n\n\nFire Risk: {status_dict['fire_risk']}",
            fg=get_risk_color(status_dict['fire_risk'])
        )
        spb_risk_label.config(
            text=f"Southern Pine Beetle Risk: {status_dict['SPB_risk']}",
            fg=get_risk_color(status_dict['SPB_risk'])
        )
        narration = tk.StringVar()
        narration.set("Better luck next time!")
        narration_label = tk.Label(
            metrics_frame, textvariable=narration, wraplength=400, justify="left",
            padx=10, pady=5, bg="#FFFFFF", fg=FG_COLOR, font=FONT
        )
        narration_label.pack()

        # --- Text Frame ---
        text_frame = tk.Frame(spb_frame, bg="#1b2336", bd=0)
        text_frame.place(relx=0.88, rely=0.19, anchor="center")  # Adjust as needed

        tk.Label(
            text_frame,
            text="A Southern Pine Beetle outbreak has devastated your stand!\n\nWe're trying to grow a healthy forest!",
            bg="#1b2336", fg="#05dd4c", font=("Courier", 18, "bold"),
            pady=20, wraplength=400, justify="center"
        ).pack()

        # --- Button Frame ---
        button_frame = tk.Frame(spb_frame, bg="#1b2336", bd=0)
        button_frame.place(relx=0.88, rely=0.325, anchor="center")  # Adjust as needed

        tk.Button(
            button_frame, text="Try Again", font=("Courier", 14, "bold"), width=16,
            bg="#05dd4c", fg="#1b2336", activebackground="#10612B",
            command=lambda: [stop_spb_eating_sound(), restart_game(spb_frame)]
        ).pack(side="left", padx=10, pady=5)
        tk.Button(
            button_frame, text="Exit", font=("Courier", 14, "bold"), width=16,
            bg="#05dd4c", fg="#1b2336", activebackground="#611010",
            command=root.destroy
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
        bg_img = bg_img.resize((1920, 1080))
        bg_photo = ImageTk.PhotoImage(bg_img)
        bg_label = tk.Label(snake_frame, image=bg_photo)
        bg_label.image = bg_photo  # Prevent garbage collection
        bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)

        # --- Metrics Frame (copied from main game screen) ---
        metrics_frame = tk.Frame(snake_frame, bg="#FFFFFF", bd=0)
        metrics_frame.place(relx=0.845, rely=0.73, anchor="center")
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
            font=("Courier",13, "bold")
        )
        game_status_message.pack()
        fire_risk_label = tk.Label(metrics_frame, wraplength=400, justify="left", padx=10, pady=0, bg="#FFFFFF", font=("Courier", 14, "bold"))
        fire_risk_label.pack()
        spb_risk_label = tk.Label(metrics_frame, wraplength=400, justify="left", padx=10, pady=0, bg="#FFFFFF", font=("Courier", 14, "bold"))
        spb_risk_label.pack()
        fire_risk_label.config(
            text=f"\n\n\nFire Risk: {status_dict['fire_risk']}",
            fg=get_risk_color(status_dict['fire_risk'])
        )
        spb_risk_label.config(
            text=f"Southern Pine Beetle Risk: {status_dict['SPB_risk']}",
            fg=get_risk_color(status_dict['SPB_risk'])
        )
        narration = tk.StringVar()
        narration.set("What will you do next?")
        narration_label = tk.Label(
            metrics_frame, textvariable=narration, wraplength=400, justify="left",
            padx=10, pady=5, bg="#FFFFFF", fg=FG_COLOR, font=FONT
        )
        narration_label.pack()

        # --- Text Frame ---
        text_frame = tk.Frame(snake_frame, bg="#1b2336", bd=0)
        text_frame.place(relx=0.88, rely=0.2, anchor="center")  # Adjust relx/rely as needed

        tk.Label(
            text_frame,
            text="Congratulations! This forest is excellent northern pine snake habitat.\n\nPine snakes are utilizing the stand!",
            bg="#1b2336", fg="#05dd4c", font=("Courier New", 18, "bold"),
            pady=10, wraplength=370, justify="center"
        ).pack()

        # --- Button Frame ---
        button_frame = tk.Frame(snake_frame, bg="#000000", bd=0)
        button_frame.place(relx=0.88, rely=0.33, anchor="center")  # Adjust relx/rely as needed

        tk.Button(
            button_frame, text="Continue", font=("Courier", 16, "bold"), width=16,
            bg="#05dd4c", fg="#1b2336", activebackground="#069134",
            command=lambda: [snake_frame.pack_forget(), (show_closing_screen() if game.stand['year'] >= 100 else show_game_screen())]
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
        bg_img = bg_img.resize((1920, 1080))
        bg_photo = ImageTk.PhotoImage(bg_img)
        bg_label = tk.Label(gentian_frame, image=bg_photo)
        bg_label.image = bg_photo  # Prevent garbage collection
        bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)
    
        # --- Metrics Frame (copied from main game screen) ---
        metrics_frame = tk.Frame(gentian_frame, bg="#FFFFFF", bd=0)
        metrics_frame.place(relx=0.845, rely=0.73, anchor="center")
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
            font=("Courier",13, "bold")
        )
        game_status_message.pack()
        fire_risk_label = tk.Label(metrics_frame, wraplength=400, justify="left", padx=10, pady=0, bg="#FFFFFF", font=("Courier", 14, "bold"))
        fire_risk_label.pack()
        spb_risk_label = tk.Label(metrics_frame, wraplength=400, justify="left", padx=10, pady=0, bg="#FFFFFF", font=("Courier", 14, "bold"))
        spb_risk_label.pack()
        fire_risk_label.config(
            text=f"\n\n\nFire Risk: {status_dict['fire_risk']}",
            fg=get_risk_color(status_dict['fire_risk'])
        )
        spb_risk_label.config(
            text=f"Southern Pine Beetle Risk: {status_dict['SPB_risk']}",
            fg=get_risk_color(status_dict['SPB_risk'])
        )
        narration = tk.StringVar()
        narration.set("What will you do next?")
        narration_label = tk.Label(
            metrics_frame, textvariable=narration, wraplength=400, justify="left",
            padx=10, pady=5, bg="#FFFFFF", fg=FG_COLOR, font=FONT
        )
        narration_label.pack()
    
        # --- Text Frame ---
        text_frame = tk.Frame(gentian_frame, bg="#1b2336", bd=0)
        text_frame.place(relx=0.88, rely=0.2, anchor="center")
    
        tk.Label(
            text_frame,
            text="Congratulations! This forest now supports rare Pine Barrens gentian!\n\nGentian is growing in the stand!",
            bg="#1b2336", fg="#05dd4c", font=("Courier New", 18, "bold"),
            pady=10, wraplength=370, justify="center"
        ).pack()
    
        # --- Button Frame ---
        button_frame = tk.Frame(gentian_frame, bg="#000000", bd=0)
        button_frame.place(relx=0.88, rely=0.33, anchor="center")
    
        tk.Button(
            button_frame, text="Continue", font=("Courier", 16, "bold"), width=16,
            bg="#05dd4c", fg="#1b2336", activebackground="#069134",
            command=lambda: [gentian_frame.pack_forget(), (show_closing_screen() if game.stand['year'] >= 100 else show_game_screen())]
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
        bg_img = bg_img.resize((1920, 1080))
        bg_photo = ImageTk.PhotoImage(bg_img)
        bg_label = tk.Label(tanager_frame, image=bg_photo)
        bg_label.image = bg_photo
        bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Metrics (copied pattern)
        metrics_frame = tk.Frame(tanager_frame, bg="#FFFFFF", bd=0)
        metrics_frame.place(relx=0.845, rely=0.73, anchor="center")
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
            font=("Courier",13, "bold")
        )
        game_status_message.pack()
        fire_risk_label = tk.Label(metrics_frame, wraplength=400, justify="left",
                                   padx=10, pady=0, bg="#FFFFFF", font=("Courier", 14, "bold"))
        fire_risk_label.pack()
        spb_risk_label = tk.Label(metrics_frame, wraplength=400, justify="left",
                                  padx=10, pady=0, bg="#FFFFFF", font=("Courier", 14, "bold"))
        spb_risk_label.pack()
        fire_risk_label.config(
            text=f"\n\n\nFire Risk: {status_dict['fire_risk']}",
            fg=get_risk_color(status_dict['fire_risk'])
        )
        spb_risk_label.config(
            text=f"Southern Pine Beetle Risk: {status_dict['SPB_risk']}",
            fg=get_risk_color(status_dict['SPB_risk'])
        )
        narration = tk.StringVar()
        narration.set("What will you do next?")
        tk.Label(
            metrics_frame, textvariable=narration, wraplength=400, justify="left",
            padx=10, pady=5, bg="#FFFFFF", fg=FG_COLOR, font=FONT
        ).pack()

        # Text frame
        text_frame = tk.Frame(tanager_frame, bg="#1b2336", bd=0)
        text_frame.place(relx=0.88, rely=0.2, anchor="center")
        tk.Label(
            text_frame,
            text="Congratulations! This forest is being visited by Summer Tanagers.\n\nThese neotropical birds are migrating through the stand!",
            bg="#1b2336", fg="#05dd4c", font=("Courier New", 18, "bold"),
            pady=10, wraplength=370, justify="center"
        ).pack()

        # Button frame
        button_frame = tk.Frame(tanager_frame, bg="#000000", bd=0)
        button_frame.place(relx=0.88, rely=0.33, anchor="center")
        tk.Button(
            button_frame, text="Continue", font=("Courier", 16, "bold"), width=16,
            bg="#05dd4c", fg="#1b2336", activebackground="#069134",
            command=lambda: [tanager_frame.pack_forget(), (show_closing_screen() if game.stand['year'] >= 100 else show_game_screen())]
        ).pack(pady=0)

    # --- Tree Frog Screen ---
    def show_tree_frog_screen():
        """Display the screen for Pine Barrens tree frog colonization."""
        play_tree_frog_sound()
        for widget in root.winfo_children():
            widget.pack_forget()
        frog_frame = tk.Frame(root, bg=BG_COLOR)
        frog_frame.pack(fill="both", expand=True)

        # Background image
        bg_img = Image.open("assets/treefrog.png")
        bg_img = bg_img.resize((1920, 1080))
        bg_photo = ImageTk.PhotoImage(bg_img)
        bg_label = tk.Label(frog_frame, image=bg_photo)
        bg_label.image = bg_photo
        bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Metrics (copied pattern)
        metrics_frame = tk.Frame(frog_frame, bg="#FFFFFF", bd=0)
        metrics_frame.place(relx=0.845, rely=0.73, anchor="center")
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
            font=("Courier", 13, "bold")
        )
        game_status_message.pack()
        fire_risk_label = tk.Label(metrics_frame, wraplength=400, justify="left",
                                   padx=10, pady=0, bg="#FFFFFF", font=("Courier", 14, "bold"))
        fire_risk_label.pack()
        spb_risk_label = tk.Label(metrics_frame, wraplength=400, justify="left",
                                  padx=10, pady=0, bg="#FFFFFF", font=("Courier", 14, "bold"))
        spb_risk_label.pack()
        fire_risk_label.config(
            text=f"\n\n\nFire Risk: {status_dict['fire_risk']}",
            fg=get_risk_color(status_dict['fire_risk'])
        )
        spb_risk_label.config(
            text=f"Southern Pine Beetle Risk: {status_dict['SPB_risk']}",
            fg=get_risk_color(status_dict['SPB_risk'])
        )

        # Text
        text_frame = tk.Frame(frog_frame, bg="#1b2336", bd=0)
        text_frame.place(relx=0.88, rely=0.2, anchor="center")
        tk.Label(
            text_frame,
            text="Congratulations! Pine Barrens tree frogs have colonized this forest.\n\nTree frogs are calling from the stand!",
            bg="#1b2336", fg="#05dd4c", font=("Courier New", 18, "bold"),
            pady=10, wraplength=370, justify="center"
        ).pack()

        # Continue button
        button_frame = tk.Frame(frog_frame, bg="#000000", bd=0)
        button_frame.place(relx=0.88, rely=0.33, anchor="center")
        tk.Button(
            button_frame, text="Continue", font=("Courier", 16, "bold"), width=16,
            bg="#05dd4c", fg="#1b2336", activebackground="#069134",
            command=lambda: [stop_tree_frog_sound(), frog_frame.pack_forget(), (show_closing_screen() if game.stand['year'] >= 100 else show_game_screen())]
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
        bg_img = bg_img.resize((1920, 1080))
        bg_photo = ImageTk.PhotoImage(bg_img)
        bg_label = tk.Label(fg_frame, image=bg_photo)
        bg_label.image = bg_photo
        bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Metrics (same as definitions)
        metrics_frame = tk.Frame(fg_frame, bg="#FFFFFF", bd=0)
        metrics_frame.place(relx=0.845, rely=0.73, anchor="center")
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
            font=("Courier",13,"bold")
        )
        game_status_message.pack()
        fire_risk_label = tk.Label(metrics_frame, wraplength=400, justify="left",
                                   padx=10, pady=0, bg="#FFFFFF", font=("Courier", 14, "bold"))
        fire_risk_label.pack()
        spb_risk_label = tk.Label(metrics_frame, wraplength=400, justify="left",
                                  padx=10, pady=0, bg="#FFFFFF", font=("Courier", 14, "bold"))
        spb_risk_label.pack()
        fire_risk_label.config(
            text=f"\n\n\nFire Risk: {status_dict['fire_risk']}",
            fg=get_risk_color(status_dict['fire_risk'])
        )
        spb_risk_label.config(
            text=f"Southern Pine Beetle Risk: {status_dict['SPB_risk']}",
            fg=get_risk_color(status_dict['SPB_risk'])
        )
        narration = tk.StringVar()
        narration.set("Field Guide")
        narration_label = tk.Label(
            metrics_frame, textvariable=narration, wraplength=400, justify="left",
            padx=10, pady=5, bg="#FFFFFF", fg=FG_COLOR, font=FONT
        )
        narration_label.pack()

        tk.Button(
            fg_frame, text="Return to Game", font=("Courier", 18, "bold"), width=16,
            bg="#929292", fg="#000000", activebackground="#FFFFFF",
            command=lambda: [play_page_close_sound(), fg_frame.pack_forget(), show_game_screen()]
        ).place(relx=0.225, rely=0.915, anchor="center")

    # --- Definitions Screen ---
    def show_definitions_screen():
        play_page_turn_sound()  # Play page turn sound over forest sound
        for widget in root.winfo_children():
            widget.pack_forget()
        def_frame = tk.Frame(root, bg=BG_COLOR)
        def_frame.pack(fill="both", expand=True)
        # Load and display the definitions background image in a label
        bg_img = Image.open("assets/definitions.png")
        bg_img = bg_img.resize((1920, 1080))
        bg_photo = ImageTk.PhotoImage(bg_img)
        bg_label = tk.Label(def_frame, image=bg_photo)
        bg_label.image = bg_photo
        bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)

        # --- Metrics Frame (copied from show_game_screen) ---
        metrics_frame = tk.Frame(def_frame, bg="#FFFFFF", bd=0)
        metrics_frame.place(relx=0.845, rely=0.73, anchor="center")
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
            font=("Courier",13, "bold")
        )
        game_status_message.pack()
        fire_risk_label = tk.Label(metrics_frame, wraplength=400, justify="left", padx=10, pady=0, bg="#FFFFFF", font=("Courier", 14, "bold"))
        fire_risk_label.pack()
        spb_risk_label = tk.Label(metrics_frame, wraplength=400, justify="left", padx=10, pady=0, bg="#FFFFFF", font=("Courier", 14, "bold"))
        spb_risk_label.pack()
        fire_risk_label.config(
            text=f"\n\n\nFire Risk: {status_dict['fire_risk']}",
            fg=get_risk_color(status_dict['fire_risk'])
        )
        spb_risk_label.config(
            text=f"Southern Pine Beetle Risk: {status_dict['SPB_risk']}",
            fg=get_risk_color(status_dict['SPB_risk'])
        )
        narration = tk.StringVar()
        narration.set("What will you do next?")
        narration_label = tk.Label(
            metrics_frame, textvariable=narration, wraplength=400, justify="left",
            padx=10, pady=5, bg="#FFFFFF", fg=FG_COLOR, font=FONT
        )
        narration_label.pack()

        # Back button
        tk.Button(
            def_frame, text="Return to Game", font=("Courier", 18, "bold"), width=16,
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
        bg_img = bg_img.resize((1920, 1080))
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

        # --- Welcome Frame ---
        welcome_frame = tk.Frame(game_frame, bg="#FFFFFF", bd=0)
        welcome_frame.place(relx=0.88, rely=0.13, anchor="center")
        status_label = tk.Label(
            welcome_frame,
            text="Welcome to Pitch Pine Trail! \nClick an action to begin →",
            wraplength=600, justify="center",
            padx=10, pady=10, bg="#1b2336", fg="#05dd4c", font=FONT
        )
        status_label.pack()

        # --- Metrics Frame ---
        metrics_frame = tk.Frame(game_frame, bg="#FFFFFF", bd=0)
        metrics_frame.place(relx=0.845, rely=0.73, anchor="center")
        game_status = tk.StringVar()
        game_status_message = tk.Message(
            metrics_frame,
            textvariable=game_status,
            width=450,
            justify="center",
            bg="#FFFFFF",
            fg=FG_COLOR,
            font=("Courier",13, "bold")
        )
        game_status_message.pack()
        fire_risk_label = tk.Label(metrics_frame, wraplength=400, justify="left", padx=10, pady=0, bg="#FFFFFF", font=("Courier", 14, "bold"))
        fire_risk_label.pack()
        spb_risk_label = tk.Label(metrics_frame, wraplength=400, justify="left", padx=10, pady=0, bg="#FFFFFF", font=("Courier", 14, "bold"))
        spb_risk_label.pack()
        narration = tk.StringVar()
        narration.set("What will you do next?")
        narration_label = tk.Label(
            metrics_frame, textvariable=narration, wraplength=400, justify="left",
            padx=10, pady=5, bg="#FFFFFF", fg=FG_COLOR, font=FONT
        )
        narration_label.pack()

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
                text=f"\n\n\nFire Risk: {status_dict['fire_risk']}",
                fg=get_risk_color(status_dict['fire_risk'])
            )
            spb_risk_label.config(
                text=f"Southern Pine Beetle Risk: {status_dict['SPB_risk']}",
                fg=get_risk_color(status_dict['SPB_risk'])
            )
        
        def next_turn(action):
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
            gentian_before = game.gentian_colonized
            tanager_before = getattr(game, 'summer_tanager_colonized', False)
            tree_frog_before = getattr(game, 'pine_barrens_tree_frog_colonized', False)
            pine_snakes_before = game.pine_snakes_colonized
            achievement_shown_this_turn = False

            # Helper: show newly-triggered Tanager or Tree Frog and return True if shown
            def show_new_achievement(final_bg_img):
                # Pine snake
                if (not pine_snakes_before and game.pine_snakes_colonized):
                    game.pine_snake_achieved = True
                    game.current_bg_img = final_bg_img
                    show_pine_snake_screen()
                    return True
                # Gentian
                if (not gentian_before and game.gentian_colonized and not game.gentian_screen_shown):
                    game.gentian_screen_shown = True
                    game.gentian_achieved = True
                    game.current_bg_img = final_bg_img
                    show_gentian_screen()
                    return True
                # Summer Tanager
                if (not tanager_before
                    and getattr(game, 'summer_tanager_colonized', False)
                    and not getattr(game, 'summer_tanager_screen_shown', False)):
                    game.summer_tanager_screen_shown = True
                    game.summer_tanager_achieved = True
                    show_summer_tanager_screen()
                    return True
                # Tree Frog
                if (not tree_frog_before
                    and getattr(game, 'pine_barrens_tree_frog_colonized', False)
                    and not getattr(game, 'tree_frog_screen_shown', False)):
                    game.tree_frog_screen_shown = True
                    game.tree_frog_achieved = True
                    show_tree_frog_screen()
                    return True
                return False

            # Final decade fast-path — no animations between year 90 and 100
            if 90 <= game.stand['year'] < 100:
                pine_snakes_before = game.pine_snakes_colonized
                game.update_stand(action)
                event = game.simulate_event()
                game.stand['year'] += 10
                welcome_frame.place_forget()
                update_status_labels()

                # Loss checks first
                if game.is_low_ba_game_over():
                    show_low_ba_screen()
                    return
                if getattr(game.stand, 'catastrophic_wildfire', False) or game.stand.get('catastrophic_wildfire', False):
                    show_fire_loss_screen()
                    return
                if event == 'SPB outbreak!' and game.stand['SPB_risk'] == 'High':
                    show_spb_loss_screen()
                    return

                # Achievements before win so they show first at year 100
                if not pine_snakes_before and game.pine_snakes_colonized:
                    game.pine_snake_achieved = True
                    show_pine_snake_screen()
                    return
                if (not gentian_before and game.gentian_colonized and not game.gentian_screen_shown):
                    game.gentian_screen_shown = True
                    game.gentian_achieved = True
                    show_gentian_screen()
                    return
                if (not tanager_before
                    and getattr(game, 'summer_tanager_colonized', False)
                    and not getattr(game, 'summer_tanager_screen_shown', False)):
                    game.summer_tanager_screen_shown = True
                    game.summer_tanager_achieved = True
                    show_summer_tanager_screen()
                    return
                if (not tree_frog_before
                    and getattr(game, 'pine_barrens_tree_frog_colonized', False)
                    and not getattr(game, 'tree_frog_screen_shown', False)):
                    game.tree_frog_screen_shown = True
                    game.tree_frog_achieved = True
                    show_tree_frog_screen()
                    return

                # Win check after achievements
                if game.stand['year'] >= 100:
                    show_closing_screen()
                    return

                # Default narration if still < 100
                if event:
                    narration.set(event)
                else:
                    narration.set("What will you do next?")
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
                if show_new_achievement('assets/afterburn_treedown.png'):
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
                if show_new_achievement('assets/afterburn_treedown.png'):
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
                if show_new_achievement('assets/afterburn.png'):
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
                if show_new_achievement('assets/afterburn_treedown.png'):
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

                # Achievement checks (persist final)
                if show_new_achievement('assets/heavythin_treedown.png'):
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
                if show_new_achievement('assets/heavythin_afterburn.png'):
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
                if show_new_achievement('assets/heavythin_treedown.png'):
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
                if show_new_achievement('assets/heavythin.png'):
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
                if show_new_achievement('assets/heavythin_afterburn_treedown.png'):
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
                if show_new_achievement('assets/afterburn_heavythin.png'):
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
                if show_new_achievement('assets/heavythin_afterburn_treedown.png'):
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
                    if show_new_achievement('assets/afterburn_heavythin_treedown.png'):
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
                if show_new_achievement('assets/afterburn_heavythin_treedown.png'):
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
                if show_new_achievement('assets/afterburn_heavythin.png'):
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
                if show_new_achievement('assets/afterburn_heavythin_treedown.png'):
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
                if show_new_achievement('assets/afterburn_heavythin_treedown.png'):
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
                if show_new_achievement('assets/afterburn_heavythin_treedown.png'):
                    return

                # Animation: chainsaw_afterburn_heavythin.png for 1.5s, then afterburn_heavythin_treedown.png
                start_animation('assets/chainsaw_afterburn_heavythin.png', 1500, 'assets/afterburn_heavythin_treedown.png')
                return

            pine_snakes_before = game.pine_snakes_colonized
            game.update_stand(action)
            event = game.simulate_event()
            game.stand['year'] += 10
            welcome_frame.place_forget()
            update_status_labels()

            # --- Loss checks first ---
            if game.is_low_ba_game_over():
                show_low_ba_screen()
                return
            if getattr(game.stand, 'catastrophic_wildfire', False) or game.stand.get('catastrophic_wildfire', False):
                show_fire_loss_screen()
                return
            if event == 'SPB outbreak!' and game.stand['SPB_risk'] == 'High':
                show_spb_loss_screen()
                return

            # --- Achievements before win screen so they show at year 100 ---
            if not pine_snakes_before and game.pine_snakes_colonized:
                game.pine_snake_achieved = True
                show_pine_snake_screen()
                return
            if (not gentian_before and game.gentian_colonized and not game.gentian_screen_shown):
                game.gentian_screen_shown = True
                game.gentian_achieved = True
                show_gentian_screen()
                return
            if (not tanager_before and getattr(game, 'summer_tanager_colonized', False)
                and not getattr(game, 'summer_tanager_screen_shown', False)):
                game.summer_tanager_screen_shown = True
                game.summer_tanager_achieved = True
                show_summer_tanager_screen()
                return
            if (not tree_frog_before and getattr(game, 'pine_barrens_tree_frog_colonized', False)  # NEW
                and not getattr(game, 'tree_frog_screen_shown', False)):
                game.tree_frog_screen_shown = True
                game.tree_frog_achieved = True
                show_tree_frog_screen()
                return

            # --- Win check after achievements ---
            if game.stand['year'] >= 100:
                show_closing_screen()
                return

            if event:
                narration.set(event)
            else:
                narration.set("What will you do next?")
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
                width=22, font=("Courier", 14, "bold"),
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

        # --- Green Exit Button (top right) ---
        exit_frame = tk.Frame(game_frame, bg="#FFFFFF")
        exit_frame.place(relx=0.02, rely=0.02, anchor="nw")  

        exit_button = tk.Button(
            exit_frame,
            text="Exit",
            font=("Courier", 17, "bold"),
            width=10,
            bg="#9c3432",      
            fg="#3d0606",
            activebackground="#FFFFFF",
            command=root.destroy
        )
        exit_button.pack()

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

def play_page_close_sound():
    try:
        sound = pygame.mixer.Sound("assets/page_close.wav")
        sound.play()
    except Exception as e:
        print("Error playing page close sound:", e)

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

def play_tree_frog_sound():
    try:
        sound = pygame.mixer.Sound("assets/treefrog.wav")
        # store channel so we can stop it later
        play_tree_frog_sound.sound = sound
        play_tree_frog_sound.channel = sound.play()
    except Exception as e:
        print("Error playing tree frog sound:", e)

def stop_tree_frog_sound():
    try:
        if hasattr(play_tree_frog_sound, "channel") and play_tree_frog_sound.channel is not None:
            play_tree_frog_sound.channel.stop()
    except Exception as e:
        print("Error stopping tree frog sound:", e)

if __name__ == "__main__":
    main()