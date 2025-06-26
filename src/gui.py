"""
Pitch Pine Trail - Forest Management Simulation Game

NJ Forest Service
William Zipse
Cara Escalona
Justin Gimmillaro

---------------------------------------------------
Graphical user interface for the Pitch Pine Trail forest management simulation.
Provides interactive screens for gameplay, status display, and decision making.
"""

import tkinter as tk
from tkinter import messagebox
from game_logic import Game
from PIL import Image, ImageTk

def main():
    """Initialize and run the main game application."""
    # Initialize game and UI constants
    game = Game()
    BG_COLOR = "#222244"    # Dark blue background
    FG_COLOR = "#33FF33"    # Green text
    FONT = ("Courier New", 12, "bold")

    # Set up the main window
    root = tk.Tk()
    root.title("Pitch Pine Trail")
    root.configure(bg=BG_COLOR)
    root.geometry("1500x1080")  # Updated window size
    
    def create_scrollable_frame(parent):
        """Create a scrollable frame with both vertical and horizontal scrollbars.
        
        Args:
            parent: Parent widget to contain the scrollable frame
            
        Returns:
            tk.Frame: Frame to contain content that will be scrollable
        """
        # Create a canvas with scrollbars
        canvas = tk.Canvas(parent, bg=BG_COLOR)
        v_scrollbar = tk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        h_scrollbar = tk.Scrollbar(parent, orient="horizontal", command=canvas.xview)
        
        # Configure canvas
        canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid layout for scrollbars and canvas
        canvas.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        # Configure parent grid
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        
        # Create frame inside canvas to hold content
        content_frame = tk.Frame(canvas, bg=BG_COLOR)
        
        # Create window in canvas to display the frame
        window_id = canvas.create_window((0, 0), window=content_frame, anchor="nw")
        
        # Update scrollregion when frame size changes
        def update_scrollregion(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        # Update canvas width when window is resized
        def configure_canvas(event):
            canvas.itemconfig(window_id, width=event.width)
            
        content_frame.bind("<Configure>", update_scrollregion)
        canvas.bind("<Configure>", configure_canvas)
        
        return content_frame

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

    def load_image(canvas, img_path, width=1400, height=550, fallback_text="Image not found"):
        """Load and display an image centered on a canvas, preserving aspect ratio."""
        try:
            image = Image.open(img_path)
            img_w, img_h = image.size
            # Calculate the scaling factor to fit the image inside the canvas
            scale = min(width / img_w, height / img_h)
            new_w = int(img_w * scale)
            new_h = int(img_h * scale)
            image = image.resize((new_w, new_h), Image.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            # Center the image in the canvas
            canvas.create_image(width // 2, height // 2, anchor="center", image=photo)
            canvas.image = photo  # Keep a reference to prevent garbage collection
            return True
        except Exception:
            canvas.create_text(width // 2, height // 2, text=fallback_text, fill=FG_COLOR, font=FONT)
            return False

    def restart_game(frame_to_remove):
        """Reset the game and display the main game screen.
        
        Args:
            frame_to_remove (tk.Frame): Current frame to remove
        """
        game.reset_game()
        for widget in root.winfo_children():
            widget.pack_forget()
        show_game_screen()

    def create_fullscreen_image_screen(parent, image_path, overlay_builder):
        """
        Helper to create a fullscreen, resizable image background with overlay widgets.
        Args:
            parent: tk.Frame or tk.Tk to pack the canvas into.
            image_path: Path to the background image.
            overlay_builder: Function that takes the overlay frame and populates it with widgets.
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
        overlay = tk.Frame(canvas, bg="#222244", bd=0)
        overlay_id = canvas.create_window(30, 30, anchor="nw", window=overlay)

        # Let the caller populate the overlay
        overlay_builder(overlay)

    def add_definitions_button(overlay):
        """Add a definitions button to the bottom right of the overlay."""
        btn = tk.Button(
            overlay, text="Definitions", font=FONT, width=14,
            bg="#444466", fg=FG_COLOR, activebackground="#333355",
            command=show_definitions_screen
        )
        btn.place(relx=1.0, rely=1.0, anchor="se", x=-20, y=-20)  # 20px from bottom right

    # --- Intro Screen ---
    intro_frame = tk.Frame(root, bg=BG_COLOR)
    intro_frame.pack(fill="both", expand=True)

    def intro_overlay_builder(overlay):
        tk.Label(
            overlay,
            text="Welcome to Pitch Pine Trail by the New Jersey Forest Service!\nGrow your Pitch Pines for 100 years!",
            bg=BG_COLOR, fg=FG_COLOR, font=("Courier New", 14, "bold"),
            pady=20
        ).pack()
        tk.Button(
            overlay, text="Begin", font=FONT, width=16,
            bg="#444466", fg=FG_COLOR, activebackground="#333355",
            command=lambda: [intro_frame.pack_forget(), show_game_screen()]
        ).pack(pady=5)
        tk.Button(
            overlay, text="Exit", font=FONT, width=16,
            bg="#444466", fg=FG_COLOR, activebackground="#333355",
            command=root.destroy
        ).pack(pady=5)

    create_fullscreen_image_screen(intro_frame, "assets/introscreen.jpeg", intro_overlay_builder)

    # --- Main Game Screen Functions ---
    def show_closing_screen():
        """Display the game's ending screen with final statistics."""
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
        overlay = tk.Frame(canvas, bg="#222244", bd=0)
        overlay_id = canvas.create_window(30, 30, anchor="nw", window=overlay)

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
            wraplength=600, justify="left", pady=10
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
            wraplength=600, justify="left", pady=10
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
        for widget in root.winfo_children():
            widget.pack_forget()
        low_ba_frame = tk.Frame(root, bg=BG_COLOR)
        low_ba_frame.pack(fill="both", expand=True)

        def overlay_builder(overlay):
            tk.Label(
                overlay,
                text="The forest's growing stock trees have been depleted!\nWe're supposed to be growing a forest!",
                bg=BG_COLOR, fg=FG_COLOR, font=("Courier New", 16, "bold"),
                pady=40, wraplength=600, justify="center"
            ).pack()
            tk.Button(
                overlay, text="Try Again", font=FONT, width=16,
                bg="#444466", fg=FG_COLOR, activebackground="#333355",
                command=lambda: restart_game(low_ba_frame)
            ).pack(pady=10)
            tk.Button(
                overlay, text="Exit", font=FONT, width=16,
                bg="#444466", fg=FG_COLOR, activebackground="#333355",
                command=root.destroy
            ).pack(pady=10)

        create_fullscreen_image_screen(low_ba_frame, "assets/LowStocking.png", overlay_builder)

    def show_fire_loss_screen():
        """Display the catastrophic wildfire end screen."""
        for widget in root.winfo_children():
            widget.pack_forget()
        fire_frame = tk.Frame(root, bg=BG_COLOR)
        fire_frame.pack(fill="both", expand=True)

        def overlay_builder(overlay):
            tk.Label(
                overlay,
                text="A catastrophic wildfire has occurred!\nWe might get a new stand of pitch pine, but we're trying to grow a mature stand!",
                bg=BG_COLOR, fg=FG_COLOR, font=("Courier New", 16, "bold"),
                pady=20, wraplength=600, justify="center"
            ).pack()
            tk.Button(
                overlay, text="Try Again", font=FONT, width=16,
                bg="#444466", fg=FG_COLOR, activebackground="#333355",
                command=lambda: restart_game(fire_frame)
            ).pack(pady=5)
            tk.Button(
                overlay, text="Exit", font=FONT, width=16,
                bg="#444466", fg=FG_COLOR, activebackground="#333355",
                command=root.destroy
            ).pack(pady=5)

        create_fullscreen_image_screen(fire_frame, "assets/LossByFire.png", overlay_builder)

    def show_spb_loss_screen():
        """Display the SPB outbreak end screen."""
        for widget in root.winfo_children():
            widget.pack_forget()
        spb_frame = tk.Frame(root, bg=BG_COLOR)
        spb_frame.pack(fill="both", expand=True)

        def overlay_builder(overlay):
            tk.Label(
                overlay,
                text="A Southern Pine Beetle outbreak has devastated your stand!\nWe're trying to grow a healthy forest!",
                bg=BG_COLOR, fg=FG_COLOR, font=("Courier New", 16, "bold"),
                pady=20, wraplength=600, justify="center"
            ).pack()
            tk.Button(
                overlay, text="Try Again", font=FONT, width=16,
                bg="#444466", fg=FG_COLOR, activebackground="#333355",
                command=lambda: restart_game(spb_frame)
            ).pack(pady=5)
            tk.Button(
                overlay, text="Exit", font=FONT, width=16,
                bg="#444466", fg=FG_COLOR, activebackground="#333355",
                command=root.destroy
            ).pack(pady=5)

        create_fullscreen_image_screen(spb_frame, "assets/LossBySPB.png", overlay_builder)

    def show_pine_snake_screen():
        """Display the pine snake colonization event screen."""
        for widget in root.winfo_children():
            widget.pack_forget()
        snake_frame = tk.Frame(root, bg=BG_COLOR)
        snake_frame.pack(fill="both", expand=True)

        def overlay_builder(overlay):
            tk.Label(
                overlay,
                text="Congratulations! This forest is excellent northern pine snake habitat.\nPine snakes are utilizing the stand!",
                bg=BG_COLOR, fg=FG_COLOR, font=("Courier New", 16, "bold"),
                pady=40, wraplength=600, justify="center"
            ).pack()
            tk.Button(
                overlay, text="Continue", font=FONT, width=16,
                bg="#444466", fg=FG_COLOR, activebackground="#333355",
                command=lambda: [snake_frame.pack_forget(), show_game_screen()]
            ).pack(pady=10)

        create_fullscreen_image_screen(snake_frame, "assets/Pinesnake.jpg", overlay_builder)

    # --- Main Game Screen ---
    def show_game_screen():
        """Display the main gameplay screen with forest management options."""
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
        overlay = tk.Frame(canvas, bg="#222244", bd=0)
        # Place overlay frame at the top with some padding
        overlay_id = canvas.create_window(30, 30, anchor="nw", window=overlay)

        # Status display area
        status = tk.StringVar()
        status.set("Welcome to Pitch Pine Trail! Click an action to begin.")

        status_label = tk.Label(
            overlay, textvariable=status, wraplength=600, justify="left",
            padx=10, pady=10, bg=BG_COLOR, fg=FG_COLOR, font=FONT
        )
        status_label.pack()

        ba_label = tk.Label(overlay, bg=BG_COLOR, fg=FG_COLOR, font=FONT)
        ba_label.pack()
        qmd_label = tk.Label(overlay, bg=BG_COLOR, fg=FG_COLOR, font=FONT)
        qmd_label.pack()
        fire_risk_label = tk.Label(overlay, wraplength=600, justify="left", padx=10, pady=0, bg=BG_COLOR, font=FONT)
        fire_risk_label.pack()
        spb_risk_label = tk.Label(overlay, wraplength=600, justify="left", padx=10, pady=0, bg=BG_COLOR, font=FONT)
        spb_risk_label.pack()

        narration = tk.StringVar()
        narration.set("What will you do next?")
        narration_label = tk.Label(
            overlay, textvariable=narration, wraplength=600, justify="left",
            padx=10, pady=5, bg=BG_COLOR, fg=FG_COLOR, font=FONT
        )
        narration_label.pack()

        button_frame = tk.Frame(overlay, bg=BG_COLOR)
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
                text=f"Year: {status_dict['year']} | TPA: {status_dict['TPA']} | Carbon: {status_dict['carbon']:.1f} MT/ac | CI: {status_dict['CI']:.1f}"
            )
            ba_label.config(text=f"Basal Area (BA): {status_dict['BA']:.1f} sqft/acre")
            qmd_label.config(text=f"Quadratic Mean Diameter (QMD): {status_dict['QMD']:.1f} inches")
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
                bg="#444466", fg=FG_COLOR,
                activebackground="#333355",
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

if __name__ == "__main__":
    main()