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
from game_logic import Game
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
    root.geometry("1920x1080")  # fall back for full screen
    #root.attributes('-fullscreen', True)  #true fullscreen
    #root.bind("<Escape>", lambda e: root.attributes("-fullscreen", False)) #exit fullscreen on Escape key


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
            return "#FFD700"  # Yellow
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

    # Create a frame for the buttons, centered near the bottom
    button_row = tk.Frame(intro_frame, bg="#663e1d")
    button_row.place(relx=0.798, rely=0.86, anchor="center")  # Adjust rely for vertical position

    tk.Button(
        button_row,
        text="Begin",
        font=("Courier", 14, "bold"),
        width=14,
        bg="#f7d79e",
        fg="#663e1d",
        activebackground="#13471C",
        command=lambda: [intro_frame.pack_forget(), show_game_screen()]
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
        stop_forest_sound()
        play_trumpet_win_sound()
        for widget in root.winfo_children():
            widget.pack_forget()
            
        closing_frame = tk.Frame(root, bg=BG_COLOR)
        closing_frame.pack(fill="both", expand=True)

        # Full-window canvas
        canvas = tk.Canvas(closing_frame, bg=BG_COLOR, highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        # Dynamically resize and display background image
        def update_bg_image(event=None):
            try:
                image = Image.open("assets/ClosingScreen1.png")
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
        overlay = tk.Frame(canvas, bg="#FFFFFF", bd=0)
        overlay_id = canvas.create_window(50, 185, anchor="nw", window=overlay)

        tk.Label(
            overlay,
            text="Thank you for playing Pitch Pine Trail!",
            bg=BG_COLOR, fg=FG_COLOR, font=("Courier New", 16, "bold"),
            pady=20
        ).pack()

        tk.Label(
            overlay,
            text=game.get_summary(),
            bg=BG_COLOR, fg=FG_COLOR, font=FONT,
            wraplength=400, justify="left", pady=10
        ).pack()

        summary = game.get_status_dict()
        tk.Label(
            overlay,
            text=(
                f"Final Stand:\n"
                f"QMD: {summary['QMD']:.1f} inches\n"
                f"TPA: {summary['TPA']}\n"
                f"BA: {summary['BA']:.1f} sqft/acre\n"
                f"Carbon: {summary['carbon']:.1f} MT/ac\n"
                f"CI: {summary['CI']:.1f}\n"
                f"Fire Risk: {summary['fire_risk']}\n"
                f"SPB Risk: {summary['SPB_risk']}\n"
            ),
            bg=BG_COLOR, fg=FG_COLOR, font=FONT,
            wraplength=400, justify="left", pady=10
        ).pack()
        tk.Button(
            overlay, text="Try Again", font=FONT, width=16,
            bg="#444466", fg=FG_COLOR, activebackground="#333355",
            command=lambda: restart_game(closing_frame)
        ).pack(pady=5)
        tk.Button(
            overlay, text="Exit", font=FONT, width=16,
            bg="#444466", fg=FG_COLOR, activebackground="#333355",
            command=root.destroy
        ).pack(pady=5)

    def show_low_ba_screen():
        """Display the game over screen for low basal area condition."""
        stop_forest_sound()
        play_losing_trombone_sound()
        for widget in root.winfo_children():
            widget.pack_forget()
        low_ba_frame = tk.Frame(root, bg=BG_COLOR)
        low_ba_frame.pack(fill="both", expand=True)

        def overlay_builder(overlay):
            tk.Label(
                overlay,
                text="The forest's growing stock trees have been depleted!\nWe're supposed to be growing a forest!",
                bg=BG_COLOR, fg=FG_COLOR, font=("Courier New", 16, "bold"),
                pady=40, wraplength=400, justify="center"
            ).pack()
            tk.Button(
                overlay, text="Try Again", font=FONT, width=16,
                bg="#444466", fg=FG_COLOR, activebackground="#333355",
                command=lambda: [stop_losing_trombone_sound(), restart_game(low_ba_frame)]
            ).pack(pady=10)
            tk.Button(
                overlay, text="Exit", font=FONT, width=16,
                bg="#444466", fg=FG_COLOR, activebackground="#333355",
                command=root.destroy
            ).pack(pady=10)

        create_fullscreen_image_screen(low_ba_frame, "assets/LowStocking.png", overlay_builder)

    def show_fire_loss_screen():
        """Display the catastrophic wildfire end screen."""
        stop_forest_sound()
        play_fire_sound()
        for widget in root.winfo_children():
            widget.pack_forget()
        fire_frame = tk.Frame(root, bg=BG_COLOR)
        fire_frame.pack(fill="both", expand=True)

        def overlay_builder(overlay):
            tk.Label(
                overlay,
                text="A catastrophic wildfire has occurred!\nWe might get a new stand of pitch pine, but we're trying to grow a mature stand!",
                bg=BG_COLOR, fg=FG_COLOR, font=("Courier New", 16, "bold"),
                pady=20, wraplength=400, justify="center"
            ).pack()
            tk.Button(
                overlay, text="Try Again", font=FONT, width=16,
                bg="#444466", fg=FG_COLOR, activebackground="#333355",
                command=lambda: [stop_fire_sound(), restart_game(fire_frame)]
            ).pack(pady=5)
            tk.Button(
                overlay, text="Exit", font=FONT, width=16,
                bg="#444466", fg=FG_COLOR, activebackground="#333355",
                command=root.destroy
            ).pack(pady=5)

        create_fullscreen_image_screen(fire_frame, "assets/LossByFire.png", overlay_builder)

    def show_spb_loss_screen():
        """Display the SPB outbreak end screen."""
        stop_forest_sound()           # Stop the forest sound first
        play_spb_eating_sound()       # Play only the SPB eating sound (looped)
        for widget in root.winfo_children():
            widget.pack_forget()
        spb_frame = tk.Frame(root, bg=BG_COLOR)
        spb_frame.pack(fill="both", expand=True)

        def overlay_builder(overlay):
            tk.Label(
                overlay,
                text="A Southern Pine Beetle outbreak has devastated your stand!\nWe're trying to grow a healthy forest!",
                bg=BG_COLOR, fg=FG_COLOR, font=("Courier New", 16, "bold"),
                pady=20, wraplength=400, justify="center"
            ).pack()
            tk.Button(
                overlay, text="Try Again", font=FONT, width=16,
                bg="#444466", fg=FG_COLOR, activebackground="#333355",
                command=lambda: [stop_spb_eating_sound(), restart_game(spb_frame)]
            ).pack(pady=5)
            tk.Button(
                overlay, text="Exit", font=FONT, width=16,
                bg="#444466", fg=FG_COLOR, activebackground="#333355",
                command=root.destroy
            ).pack(pady=5)

        create_fullscreen_image_screen(spb_frame, "assets/LossBySPB.png", overlay_builder)

    def show_pine_snake_screen():
        """Display the screen for successful pine snake habitat."""
        play_pine_snake_sound()  # <-- Play over forest sound
        for widget in root.winfo_children():
            widget.pack_forget()
        snake_frame = tk.Frame(root, bg=BG_COLOR)
        snake_frame.pack(fill="both", expand=True)

        def overlay_builder(overlay):
            tk.Label(
                overlay,
                text="Congratulations! This forest is excellent northern pine snake habitat.\nPine snakes are utilizing the stand!",
                bg=BG_COLOR, fg=FG_COLOR, font=("Courier New", 16, "bold"),
                pady=40, wraplength=400, justify="center"
            ).pack()
            tk.Button(
                overlay, text="Continue", font=FONT, width=16,
                bg="#546644", fg="#FFFFFF", activebackground="#203B15",
                command=lambda: [snake_frame.pack_forget(), show_game_screen()]
            ).pack(pady=10)

        create_fullscreen_image_screen(snake_frame, "assets/Pinesnake.jpg", overlay_builder, x=70, y=185)

    # --- Main Game Screen ---
    def show_game_screen():
        stop_forest_sound()
        play_forest_sound()

        game_frame = tk.Frame(root, bg=BG_COLOR)
        game_frame.pack(fill="both", expand=True)

        # Create a canvas that fills the window
        canvas = tk.Canvas(game_frame, bg=BG_COLOR, highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        # Load and display the background image, resizing it to fit the window
        def update_bg_image(event=None):
            try:
                image = Image.open("assets/Evenagestand.png")
                # Resize image to fit the canvas
                w = canvas.winfo_width()
                h = canvas.winfo_height()
                if w < 10 or h < 10:
                    return  # Avoid errors on initial small size
                img = image.resize((w, h), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                canvas.photo = photo  # Prevent garbage collection
                if hasattr(canvas, "bg_img_id"):
                    canvas.itemconfig(canvas.bg_img_id, image=photo)
                else:
                    canvas.bg_img_id = canvas.create_image(0, 0, anchor="nw", image=photo)
            except Exception:
                pass

        canvas.bind("<Configure>", update_bg_image)

        # Overlay frame for stats and buttons
        overlay = tk.Frame(canvas, bg="#FFFFFF", bd=0)  # White background
        overlay_id = canvas.create_window(50, 185, anchor="nw", window=overlay)

        # Status display area
        status = tk.StringVar()
        status.set("Welcome to Pitch Pine Trail! \nClick an action to begin.")

        status_label = tk.Label(
            overlay, textvariable=status, wraplength=400, justify="center",
            padx=10, pady=10, bg="#FFFFFF", fg=FG_COLOR, font=FONT
        )
        status_label.pack()


        ba_label = tk.Label(overlay, bg="#FFFFFF", fg=FG_COLOR, font=FONT)
        ba_label.pack()
        qmd_label = tk.Label(overlay, bg="#FFFFFF", fg=FG_COLOR, font=FONT)
        qmd_label.pack()
        fire_risk_label = tk.Label(overlay, wraplength=400, justify="left", padx=10, pady=0, bg="#FFFFFF", font=FONT)
        tpa_label = tk.Label(overlay, bg=BG_COLOR, fg=FG_COLOR, font=FONT)
        tpa_label.pack()
        fire_risk_label.pack()
        spb_risk_label = tk.Label(overlay, wraplength=400, justify="left", padx=10, pady=0, bg="#FFFFFF", font=FONT)
        spb_risk_label.pack()

        # Narration area
        # Narration area
        narration = tk.StringVar()
        narration.set("What will you do next?")
        narration_label = tk.Label(
            overlay, textvariable=narration, wraplength=400, justify="left",
            padx=10, pady=5, bg="#FFFFFF", fg=FG_COLOR, font=FONT
        )
        narration_label.pack()

        button_frame = tk.Frame(overlay, bg="#FFFFFF")
        button_frame.pack(pady=10)

        ACTIONS = {
            '1': 'Do nothing',
            '2': 'Thin lightly',
            '3': 'Thin heavily',
            '4': 'Prescribed burn'
        }

        def update_status_labels():
            status_dict = game.get_status_dict()
            status_label.config(
                text=f"Year: {status_dict['year']} | Carbon: {status_dict['carbon']:.1f} MT/ac | CI: {status_dict['CI']:.1f}"
            )
            # Only show BA, QMD, TPA at the start (year 0)
            if status_dict['year'] == 0:
                ba_label.config(text=f"Basal Area (BA): {status_dict['BA']:.1f} sqft/acre")
                qmd_label.config(text=f"Quadratic Mean Diameter (QMD): {status_dict['QMD']:.1f} inches")
                tpa_label.config(text=f"Trees Per Acre (TPA): {status_dict['TPA']}")
            else:
                ba_label.config(text="")
                qmd_label.config(text="")
                tpa_label.config(text="")
            fire_risk_label.config(
                text=f"Fire Risk: {status_dict['fire_risk']}",
                fg=get_risk_color(status_dict['fire_risk'])
            )
            spb_risk_label.config(
                text=f"SPB Risk: {status_dict['SPB_risk']}",
                fg=get_risk_color(status_dict['SPB_risk'])
            )

        def next_turn(action):
            pine_snakes_before = game.pine_snakes_colonized
            game.update_stand(action)
            event = game.simulate_event()
            game.stand['year'] += 10
            status.set(game.get_status())

            # Catastrophic wildfire ending
            # Catastrophic wildfire ending
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

        update_status_labels()

        for k, v in ACTIONS.items():
            tk.Button(
                button_frame,
                text=f"{k}. {v}",
                width=22, font=FONT,
                bg="#FFFFFF", fg=FG_COLOR,
                activebackground="#DDDDDD",
                command=lambda k=k: next_turn(k)
            ).pack(pady=3)

    def show_definitions_screen():
        """Display a screen with definitions for different terms."""
        for widget in root.winfo_children():
            widget.pack_forget()
        def_frame = tk.Frame(root, bg=BG_COLOR)
        def_frame.pack(fill="both", expand=True)

        def overlay_builder(overlay):
            tk.Label(
                overlay,
                text="Definitions",
                bg=BG_COLOR, fg=FG_COLOR, font=("Courier New", 18, "bold"),
                pady=20
            ).pack()
            # Example definitions (add more as needed)
            tk.Label(
                overlay,
                text=(
                    "BA (Basal Area): The cross-sectional area of all trees per acre, in square feet.\n\n"
                    "QMD (Quadratic Mean Diameter): A measure of average tree diameter.\n\n"
                    "TPA (Trees Per Acre): The number of trees per acre.\n\n"
                    "Carbon: Estimated metric tons of carbon stored per acre.\n\n"
                    "CI (Competition Index): A measure of how crowded the stand is.\n\n"
                    "Fire Risk: The likelihood of a wildfire event.\n\n"
                    "SPB Risk: The likelihood of a Southern Pine Beetle outbreak."
                ),
                bg=BG_COLOR, fg=FG_COLOR, font=FONT,
                wraplength=900, justify="left", pady=10
            ).pack()
            tk.Button(
                overlay, text="Back", font=FONT, width=16,
                bg="#444466", fg=FG_COLOR, activebackground="#333355",
                command=lambda: [def_frame.pack_forget(), show_game_screen()]
            ).pack(pady=20)

        create_fullscreen_image_screen(def_frame, "assets/introscreen.jpeg", overlay_builder)

    # Start the main event loop
    root.mainloop()

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
        pygame.mixer.music.load("assets/trumpet_win.wav")
        pygame.mixer.music.play()
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

if __name__ == "__main__":
    main()