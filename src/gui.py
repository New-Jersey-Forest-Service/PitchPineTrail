"""
Pitch Pine Trail - Forest Management Simulation Game

NJ Forest Service
William Zipse
Cara Escalona
Justin Gimmillaro
Andrea Pfaff

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
    BG_COLOR = "#FFFFFF"    # White background
    FG_COLOR = "#000000"    # Black text
    FONT = ("Courier New", 12, "bold")

    # Set up the main window
    root = tk.Tk()
    root.title("Pitch Pine Trail")
    root.configure(bg=BG_COLOR)
    #root.geometry("1920x1080")  # fall back for full screen
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
        """Reset the game and display the main game screen.
        
        Args:
            frame_to_remove (tk.Frame): Current frame to remove
        """
        game.reset_game()
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
            "assets/zoom_5.png"
        ]

        def show_next_zoom(index=0):
            if index < len(zoom_images):
                img = Image.open(zoom_images[index]).resize((1920, 1080))
                photo = ImageTk.PhotoImage(img)
                img_label.config(image=photo)
                img_label.image = photo  # Prevent garbage collection
                root.after(400, lambda: show_next_zoom(index + 1))
            else:
                # Show zoom_6.png and overlay the button
                img = Image.open("assets/zoom_6.png").resize((1920, 1080))
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
                    command=lambda: [zoom_frame.pack_forget(), show_game_screen()]
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

        # Choose background image based on pine snake achievement
        if game.pine_snakes_colonized:
            bg_img_path = "assets/okay_medal.png"
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
        fire_risk_label = tk.Label(metrics_frame, wraplength=400, justify="left", padx=10, pady=0, bg="#FFFFFF", font=FONT)
        fire_risk_label.pack()
        spb_risk_label = tk.Label(metrics_frame, wraplength=400, justify="left", padx=10, pady=0, bg="#FFFFFF", font=FONT)
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
        fire_risk_label = tk.Label(metrics_frame, wraplength=400, justify="left", padx=10, pady=0, bg="#FFFFFF", font=FONT)
        fire_risk_label.pack()
        spb_risk_label = tk.Label(metrics_frame, wraplength=400, justify="left", padx=10, pady=0, bg="#FFFFFF", font=FONT)
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
            text="The forest's growing stock trees have been depleted!\nWe're supposed to be growing a forest!",
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
        fire_risk_label = tk.Label(metrics_frame, wraplength=400, justify="left", padx=10, pady=0, bg="#FFFFFF", font=FONT)
        fire_risk_label.pack()
        spb_risk_label = tk.Label(metrics_frame, wraplength=400, justify="left", padx=10, pady=0, bg="#FFFFFF", font=FONT)
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
        fire_risk_label = tk.Label(metrics_frame, wraplength=400, justify="left", padx=10, pady=0, bg="#FFFFFF", font=FONT)
        fire_risk_label.pack()
        spb_risk_label = tk.Label(metrics_frame, wraplength=400, justify="left", padx=10, pady=0, bg="#FFFFFF", font=FONT)
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
        fire_risk_label = tk.Label(metrics_frame, wraplength=400, justify="left", padx=10, pady=0, bg="#FFFFFF", font=FONT)
        fire_risk_label.pack()
        spb_risk_label = tk.Label(metrics_frame, wraplength=400, justify="left", padx=10, pady=0, bg="#FFFFFF", font=FONT)
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
            command=lambda: [snake_frame.pack_forget(), show_game_screen()]
        ).pack(pady=0)

    # --- Main Game Screen ---
    def show_game_screen():
        stop_forest_sound()
        play_forest_sound()
        for widget in root.winfo_children():
            widget.pack_forget()

        game_frame = tk.Frame(root, bg=BG_COLOR)
        game_frame.pack(fill="both", expand=True)

        # Load and display the background image in a label
        bg_img = Image.open("assets/Evenagestand.png")
        bg_img = bg_img.resize((1920, 1080))
        bg_photo = ImageTk.PhotoImage(bg_img)
        bg_label = tk.Label(game_frame, image=bg_photo)
        bg_label.image = bg_photo
        bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)

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
        fire_risk_label = tk.Label(metrics_frame, wraplength=400, justify="left", padx=10, pady=0, bg="#FFFFFF", font=FONT)
        fire_risk_label.pack()
        spb_risk_label = tk.Label(metrics_frame, wraplength=400, justify="left", padx=10, pady=0, bg="#FFFFFF", font=FONT)
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
            pine_snakes_before = game.pine_snakes_colonized
            game.update_stand(action)
            event = game.simulate_event()
            game.stand['year'] += 10
            welcome_frame.place_forget()
            update_status_labels()
            if getattr(game.stand, 'catastrophic_wildfire', False) or game.stand.get('catastrophic_wildfire', False):
                show_fire_loss_screen()
                return
            if event == 'SPB outbreak!' and game.stand['SPB_risk'] == 'High':
                show_spb_loss_screen()
                return
            if not pine_snakes_before and game.pine_snakes_colonized:
                show_pine_snake_screen()
                return
            if event:
                narration.set(event)
            else:
                narration.set("What will you do next?")
            if game.is_low_ba_game_over():
                show_low_ba_screen()
                return
            if game.stand['year'] >= 100:
                show_closing_screen()
                return
        update_status_labels()
        for k, v in ACTIONS.items():
            tk.Button(
                button_frame,
                text=f"{k}. {v}",
                width=22, font=("Courier", 14, "bold"),
                bg="#404d6d",
                fg="#05dd4c",
                activebackground="#05dd4c",
                command=lambda k=k: next_turn(k)
            ).pack(pady=5)
        # --- Definitions Button Frame ---
        definitions_frame = tk.Frame(game_frame, bg="#FFFFFF")
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
        fire_risk_label = tk.Label(metrics_frame, wraplength=400, justify="left", padx=10, pady=0, bg="#FFFFFF", font=FONT)
        fire_risk_label.pack()
        spb_risk_label = tk.Label(metrics_frame, wraplength=400, justify="left", padx=10, pady=0, bg="#FFFFFF", font=FONT)
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

    # Start the main event loop
    #show_closing_screen()  # <-- TEMP: Jump directly to screen for testing
    root.mainloop()

#defining sound functions
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

if __name__ == "__main__":
    main()