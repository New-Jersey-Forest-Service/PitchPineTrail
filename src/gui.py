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
    root.geometry("800x600")  # Initial window size
    
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

    def load_image(canvas, img_path, width=600, height=300, fallback_text="Image not found"):
        """Load and display an image on a canvas.
        
        Args:
            canvas (tk.Canvas): Canvas to display image on
            img_path (str): Path to image file
            width (int): Width to resize image to
            height (int): Height to resize image to
            fallback_text (str): Text to display if image can't be loaded
            
        Returns:
            bool: True if image loaded successfully, False otherwise
        """
        try:
            image = Image.open(img_path)
            image = image.resize((width, height), Image.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            canvas.create_image(0, 0, anchor="nw", image=photo)
            canvas.image = photo  # Keep a reference to prevent garbage collection
            return True
        except Exception:
            canvas.create_text(width//2, height//2, text=fallback_text, fill=FG_COLOR, font=FONT)
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

    # --- Intro Screen ---
    intro_frame = tk.Frame(root, bg=BG_COLOR)
    intro_frame.pack(fill="both", expand=True)
    intro_content = create_scrollable_frame(intro_frame)

    # Load and display intro image
    intro_canvas = tk.Canvas(intro_content, width=600, height=300, bg=BG_COLOR, highlightthickness=0)
    intro_canvas.pack(pady=(10, 0))
    load_image(intro_canvas, "assets/introscreen.jpeg", fallback_text="Intro image not found")

    intro_label = tk.Label(
        intro_content,
        text="Welcome to Pitch Pine Trail by the New Jersey Forest Service!\n Grow your Pitch Pines for 100 years!",
        bg=BG_COLOR, fg=FG_COLOR, font=("Courier New", 14, "bold"),
        pady=20
    )
    intro_label.pack()

    def start_game():
        """Hide intro screen and show the main game screen."""
        intro_frame.pack_forget()
        show_game_screen()

    tk.Button(
        intro_content, text="Begin", font=FONT, width=16,
        bg="#444466", fg=FG_COLOR, activebackground="#333355",
        command=start_game
    ).pack(pady=5)

    tk.Button(
        intro_content, text="Exit", font=FONT, width=16,
        bg="#444466", fg=FG_COLOR, activebackground="#333355",
        command=root.destroy
    ).pack(pady=5)

    # --- Main Game Screen Functions ---
    def show_closing_screen():
        """Display the game's ending screen with final statistics."""
        for widget in root.winfo_children():
            widget.pack_forget()
            
        closing_frame = tk.Frame(root, bg=BG_COLOR)
        closing_frame.pack(fill="both", expand=True)
        closing_content = create_scrollable_frame(closing_frame)

        # Display closing banner
        closing_canvas = tk.Canvas(closing_content, width=600, height=300, bg=BG_COLOR, highlightthickness=0)
        closing_canvas.pack(pady=(5, 0))
        load_image(closing_canvas, "assets/ClosingScreen1.png", fallback_text="Closing image not found")

        tk.Label(
            closing_content,
            text="Thank you for playing Pitch Pine Trail!",
            bg=BG_COLOR, fg=FG_COLOR, font=("Courier New", 16, "bold"),
            pady=20
        ).pack()

        # Display game summary (includes events)
        tk.Label(
            closing_content,
            text=game.get_summary(),
            bg=BG_COLOR, fg=FG_COLOR, font=FONT,
            wraplength=600, justify="left", pady=10
        ).pack()

        # Add a summary with explicit units for BA and QMD
        summary = game.get_status_dict()
        tk.Label(
            closing_content,
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
            wraplength=600, justify="left", pady=10  # Reduced padding
        ).pack()
        tk.Button(
            closing_content, text="Try Again", font=FONT, width=16,
            bg="#444466", fg=FG_COLOR, activebackground="#333355",
            command=lambda: restart_game(closing_frame)
        ).pack(pady=5)  # Reduced padding
        tk.Button(
            closing_content, text="Exit", font=FONT, width=16,
            bg="#444466", fg=FG_COLOR, activebackground="#333355",
            command=root.destroy
        ).pack(pady=5)  # Reduced padding

    def show_low_ba_screen():
        """Display the game over screen for low basal area condition."""
        for widget in root.winfo_children():
            widget.pack_forget()
            
        low_ba_frame = tk.Frame(root, bg=BG_COLOR)
        low_ba_frame.pack(fill="both", expand=True)
        low_ba_content = create_scrollable_frame(low_ba_frame)

        # Load and display LowStocking image
        low_ba_canvas = tk.Canvas(low_ba_content, width=600, height=300, bg=BG_COLOR, highlightthickness=0)
        low_ba_canvas.pack(pady=(10, 0))
        load_image(low_ba_canvas, "assets/LowStocking.png", fallback_text="LowStocking image not found")

        tk.Label(
            low_ba_content,
            text="The forest's growing stock trees have been depleted!\nWe're supposed to be growing a forest!",
            bg=BG_COLOR, fg=FG_COLOR, font=("Courier New", 16, "bold"),
            pady=40, wraplength=600, justify="center"
        ).pack()
        
        tk.Button(
            low_ba_content, text="Try Again", font=FONT, width=16,
            bg="#444466", fg=FG_COLOR, activebackground="#333355",
            command=lambda: restart_game(low_ba_frame)
        ).pack(pady=10)
        
        tk.Button(
            low_ba_content, text="Exit", font=FONT, width=16,
            bg="#444466", fg=FG_COLOR, activebackground="#333355",
            command=root.destroy
        ).pack(pady=10)

    def show_fire_loss_screen():
        """Display the catastrophic wildfire end screen."""
        for widget in root.winfo_children():
            widget.pack_forget()
        fire_frame = tk.Frame(root, bg=BG_COLOR)
        fire_frame.pack(fill="both", expand=True)
        fire_content = create_scrollable_frame(fire_frame)

        # Display LossByFire.png
        fire_canvas = tk.Canvas(fire_content, width=600, height=300, bg=BG_COLOR, highlightthickness=0)
        fire_canvas.pack(pady=(5, 0))
        load_image(fire_canvas, "assets/LossByFire.png", fallback_text="LossByFire image not found")

        tk.Label(
            fire_content,
            text="A catastrophic wildfire has occurred!\nWe might get a new stand of pitch pine, but we're trying to grow a mature stand!",
            bg=BG_COLOR, fg=FG_COLOR, font=("Courier New", 16, "bold"),
            pady=20, wraplength=600, justify="center"
        ).pack()
        tk.Button(
            fire_content, text="Try Again", font=FONT, width=16,
            bg="#444466", fg=FG_COLOR, activebackground="#333355",
            command=lambda: restart_game(fire_frame)
        ).pack(pady=5)
        tk.Button(
            fire_content, text="Exit", font=FONT, width=16,
            bg="#444466", fg=FG_COLOR, activebackground="#333355",
            command=root.destroy
        ).pack(pady=5)

    def show_spb_loss_screen():
        """Display the SPB outbreak end screen."""
        for widget in root.winfo_children():
            widget.pack_forget()
        spb_frame = tk.Frame(root, bg=BG_COLOR)
        spb_frame.pack(fill="both", expand=True)
        spb_content = create_scrollable_frame(spb_frame)

        # Display LossBySPB.png
        spb_canvas = tk.Canvas(spb_content, width=600, height=300, bg=BG_COLOR, highlightthickness=0)
        spb_canvas.pack(pady=(5, 0))
        load_image(spb_canvas, "assets/LossBySPB.png", fallback_text="LossBySPB image not found")

        tk.Label(
            spb_content,
            text="A Southern Pine Beetle outbreak has devastated your stand!\nWe're trying to grow a healthy forest!",
            bg=BG_COLOR, fg=FG_COLOR, font=("Courier New", 16, "bold"),
            pady=20, wraplength=600, justify="center"
        ).pack()
        tk.Button(
            spb_content, text="Try Again", font=FONT, width=16,
            bg="#444466", fg=FG_COLOR, activebackground="#333355",
            command=lambda: restart_game(spb_frame)
        ).pack(pady=5)
        tk.Button(
            spb_content, text="Exit", font=FONT, width=16,
            bg="#444466", fg=FG_COLOR, activebackground="#333355",
            command=root.destroy
        ).pack(pady=5)

    def show_pine_snake_screen():
        """Display the pine snake colonization event screen."""
        for widget in root.winfo_children():
            widget.pack_forget()
        snake_frame = tk.Frame(root, bg=BG_COLOR)
        snake_frame.pack(fill="both", expand=True)
        snake_content = create_scrollable_frame(snake_frame)

        # Display Pinesnake.jpg
        snake_canvas = tk.Canvas(snake_content, width=600, height=300, bg=BG_COLOR, highlightthickness=0)
        snake_canvas.pack(pady=(10, 0))
        load_image(snake_canvas, "assets/Pinesnake.jpg", fallback_text="Pine snake image not found")

        tk.Label(
            snake_content,
            text="Congratulations! This forest is excellent northern pine snake habitat.\nPine snakes are utilizing the stand!",
            bg=BG_COLOR, fg=FG_COLOR, font=("Courier New", 16, "bold"),
            pady=40, wraplength=600, justify="center"
        ).pack()
        tk.Button(
            snake_content, text="Continue", font=FONT, width=16,
            bg="#444466", fg=FG_COLOR, activebackground="#333355",
            command=lambda: [snake_frame.pack_forget(), show_game_screen()]
        ).pack(pady=10)

    # --- Main Game Screen ---
    def show_game_screen():
        """Display the main gameplay screen with forest management options."""
        game_frame = tk.Frame(root, bg=BG_COLOR)
        game_frame.pack(fill="both", expand=True)
        game_content = create_scrollable_frame(game_frame)
        
        # Top: Graphics/Image area
        canvas = tk.Canvas(game_content, width=600, height=300, bg=BG_COLOR, highlightthickness=0)
        canvas.pack(pady=(10, 0))
        load_image(canvas, "assets/Evenagestand.png", fallback_text="Image not found")

        # Middle: Status display area
        status = tk.StringVar()
        status.set("Welcome to Pitch Pine Trail! Click an action to begin.")

        status_label = tk.Label(
            game_content, 
            wraplength=600, justify="left", 
            padx=10, pady=10, 
            bg=BG_COLOR, fg=FG_COLOR, 
            font=FONT
        )
        status_label.pack()

        # Stand metrics display
        ba_label = tk.Label(game_content, bg=BG_COLOR, fg=FG_COLOR, font=FONT)
        ba_label.pack()
        
        qmd_label = tk.Label(game_content, bg=BG_COLOR, fg=FG_COLOR, font=FONT)
        qmd_label.pack()

        fire_risk_label = tk.Label(
            game_content, 
            wraplength=600, justify="left", 
            padx=10, pady=0, 
            bg=BG_COLOR, font=FONT
        )
        fire_risk_label.pack()
        
        spb_risk_label = tk.Label(
            game_content, 
            wraplength=600, justify="left", 
            padx=10, pady=0, 
            bg=BG_COLOR, font=FONT
        )
        spb_risk_label.pack()

        # Narration area
        narration = tk.StringVar()
        narration.set("What will you do next?")
        narration_label = tk.Label(
            game_content, 
            textvariable=narration, 
            wraplength=600, justify="left",
            padx=10, pady=5, 
            bg=BG_COLOR, fg=FG_COLOR, 
            font=FONT
        )
        narration_label.pack()

        # Bottom: User interaction (buttons)
        button_frame = tk.Frame(game_content, bg=BG_COLOR)
        button_frame.pack(pady=10)

        ACTIONS = {
            '1': 'Do nothing',
            '2': 'Thin lightly',
            '3': 'Thin heavily',
            '4': 'Prescribed burn'
        }

        def update_status_labels():
            """Update all status labels with current forest stand information."""
            status = game.get_status_dict()
            status_label.config(
                text=f"Year: {status['year']} | TPA: {status['TPA']} | Carbon: {status['carbon']:.1f} MT/ac | CI: {status['CI']:.1f}"
            )
            ba_label.config(
                text=f"Basal Area (BA): {status['BA']:.1f} sqft/acre"
            )
            qmd_label.config(
                text=f"Quadratic Mean Diameter (QMD): {status['QMD']:.1f} inches"
            )
            fire_risk_label.config(
                text=f"Fire Risk: {status['fire_risk']}",
                fg=get_risk_color(status['fire_risk'])
            )
            spb_risk_label.config(
                text=f"SPB Risk: {status['SPB_risk']}",
                fg=get_risk_color(status['SPB_risk'])
            )

        def next_turn(action):
            """Process a player's action choice and advance the game.
            
            Args:
                action (str): The action code selected ('1'-'4')
            """
            pine_snakes_before = game.pine_snakes_colonized
            game.update_stand(action)
            event = game.simulate_event()
            game.stand['year'] += 10
            status.set(game.get_status())

            # Catastrophic wildfire ending
            if getattr(game.stand, 'catastrophic_wildfire', False) or game.stand.get('catastrophic_wildfire', False):
                show_fire_loss_screen()
                return

            # SPB outbreak at high risk ending
            if event == 'SPB outbreak!' and game.stand['SPB_risk'] == 'High':
                show_spb_loss_screen()
                return

            # Pine snake colonization event
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

        # Show starting stand stats in year 0
        update_status_labels()

        # Create action buttons
        for k, v in ACTIONS.items():
            tk.Button(
                button_frame, 
                text=f"{k}. {v}", 
                width=22, font=FONT,
                bg="#444466", fg=FG_COLOR, 
                activebackground="#333355",
                command=lambda k=k: next_turn(k)
            ).pack(pady=3)

    # Start the main event loop
    root.mainloop()

if __name__ == "__main__":
    main()