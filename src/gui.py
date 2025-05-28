import tkinter as tk
from tkinter import messagebox
from game_logic import Game
from PIL import Image, ImageTk  # <-- Add this import

def main():
    game = Game()

    BG_COLOR = "#222244"
    FG_COLOR = "#33FF33"
    FONT = ("Courier New", 12, "bold")

    root = tk.Tk()
    root.title("Pitch Pine Trail")
    root.configure(bg=BG_COLOR)

    def get_risk_color(risk):
        if risk == "Low":
            return "#228B22"  # green
        elif risk == "Moderate":
            return "#FFD700"  # yellow
        else:
            return "#B22222"  # red

    # --- Intro Screen ---
    intro_frame = tk.Frame(root, bg=BG_COLOR)
    intro_frame.pack(fill="both", expand=True)

    # Load and display intro image
    try:
        intro_img_path = "assets/introscreen.jpeg"
        intro_image = Image.open(intro_img_path)
        intro_image = intro_image.resize((600, 300), Image.LANCZOS)
        intro_photo = ImageTk.PhotoImage(intro_image)
        intro_canvas = tk.Canvas(intro_frame, width=600, height=300, bg=BG_COLOR, highlightthickness=0)
        intro_canvas.create_image(0, 0, anchor="nw", image=intro_photo)
        intro_canvas.image = intro_photo
        intro_canvas.pack(pady=(10,0))
    except Exception as e:
        intro_canvas = tk.Canvas(intro_frame, width=600, height=300, bg=BG_COLOR, highlightthickness=0)
        intro_canvas.create_text(300, 150, text="Intro image not found", fill=FG_COLOR, font=FONT)
        intro_canvas.pack(pady=(10,0))

    intro_label = tk.Label(
        intro_frame,
        text="Welcome to Pitch Pine Trail by the New Jersey Forest Service!\n Grow your Pitch Pines for 100 years!",
        bg=BG_COLOR, fg=FG_COLOR, font=("Courier New", 14, "bold"),
        pady=20
    )
    intro_label.pack()

    def start_game():
        intro_frame.pack_forget()
        show_game_screen()

    tk.Button(
        intro_frame, text="Begin", font=FONT, width=16,
        bg="#444466", fg=FG_COLOR, activebackground="#333355",
        command=start_game
    ).pack(pady=5)

    tk.Button(
        intro_frame, text="Exit", font=FONT, width=16,
        bg="#444466", fg=FG_COLOR, activebackground="#333355",
        command=root.destroy
    ).pack(pady=5)

    # --- Main Game Screen (hidden until Begin is pressed) ---
    def show_game_screen():
        # Top: Graphics/Image area
        canvas = tk.Canvas(root, width=600, height=300, bg=BG_COLOR, highlightthickness=0)
        canvas.pack(pady=(10,0))

        # Load and display JPG image from assets folder
        try:
            img_path = "assets/banner.jpg"
            image = Image.open(img_path)
            image = image.resize((600, 300), Image.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            canvas.create_image(0, 0, anchor="nw", image=photo)
            canvas.image = photo
        except Exception as e:
            canvas.create_text(300, 60, text="Image not found", fill=FG_COLOR, font=FONT)

        # Middle: Status/Narration area
        status = tk.StringVar()
        status.set("Welcome to Pitch Pine Trail! Click an action to begin.")

        status_label = tk.Label(root, wraplength=600, justify="left", padx=10, pady=10, bg=BG_COLOR, fg=FG_COLOR, font=FONT)
        status_label.pack()

        # Add BA and QMD labels
        ba_label = tk.Label(root, bg=BG_COLOR, fg=FG_COLOR, font=FONT)
        ba_label.pack()
        qmd_label = tk.Label(root, bg=BG_COLOR, fg=FG_COLOR, font=FONT)
        qmd_label.pack()

        fire_risk_label = tk.Label(root, wraplength=600, justify="left", padx=10, pady=0, bg=BG_COLOR, font=FONT)
        fire_risk_label.pack()
        spb_risk_label = tk.Label(root, wraplength=600, justify="left", padx=10, pady=0, bg=BG_COLOR, font=FONT)
        spb_risk_label.pack()

        narration = tk.StringVar()
        narration.set("What will you do next?")
        narration_label = tk.Label(root, textvariable=narration, wraplength=600, justify="left",
                                padx=10, pady=5, bg=BG_COLOR, fg=FG_COLOR, font=FONT)
        narration_label.pack()

        # Bottom: User interaction (buttons)
        button_frame = tk.Frame(root, bg=BG_COLOR)
        button_frame.pack(pady=10)

        ACTIONS = {
            '1': 'Do nothing',
            '2': 'Thin lightly',
            '3': 'Thin heavily',
            '4': 'Prescribed burn'
        }

        def update_status_labels():
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

        # Show starting stand stats in year 0
        update_status_labels()

        def show_closing_screen():
            # Hide all widgets in the root window
            for widget in root.winfo_children():
                widget.pack_forget()
            closing_frame = tk.Frame(root, bg=BG_COLOR)
            closing_frame.pack(fill="both", expand=True)

            # Load and display closing banner image
            try:
                closing_img_path = "assets/ClosingScreen1.png"
                closing_image = Image.open(closing_img_path)
                closing_image = closing_image.resize((600, 300), Image.LANCZOS)
                closing_photo = ImageTk.PhotoImage(closing_image)
                closing_canvas = tk.Canvas(closing_frame, width=600, height=300, bg=BG_COLOR, highlightthickness=0)
                closing_canvas.create_image(0, 0, anchor="nw", image=closing_photo)
                closing_canvas.image = closing_photo
                closing_canvas.pack(pady=(10,0))
            except Exception as e:
                closing_canvas = tk.Canvas(closing_frame, width=600, height=300, bg=BG_COLOR, highlightthickness=0)
                closing_canvas.create_text(300, 150, text="Closing image not found", fill=FG_COLOR, font=FONT)
                closing_canvas.pack(pady=(10,0))

            tk.Label(
                closing_frame,
                text="Thank you for playing Pitch Pine Trail!",
                bg=BG_COLOR, fg=FG_COLOR, font=("Courier New", 16, "bold"),
                pady=40
            ).pack()
            tk.Label(
                closing_frame,
                text=game.get_summary(),
                bg=BG_COLOR, fg=FG_COLOR, font=FONT,
                wraplength=600, justify="left", pady=20
            ).pack()
            tk.Button(
                closing_frame, text="Try Again", font=FONT, width=16,
                bg="#444466", fg=FG_COLOR, activebackground="#333355",
                command=lambda: restart_game(closing_frame)
            ).pack(pady=10)
            tk.Button(
                closing_frame, text="Exit", font=FONT, width=16,
                bg="#444466", fg=FG_COLOR, activebackground="#333355",
                command=root.destroy
            ).pack(pady=10)

        def restart_game(closing_frame):
            game.reset_game()
            closing_frame.destroy()
            show_game_screen()

        def show_low_ba_screen():
            # Hide all widgets in the root window
            for widget in root.winfo_children():
                widget.pack_forget()
            low_ba_frame = tk.Frame(root, bg=BG_COLOR)
            low_ba_frame.pack(fill="both", expand=True)

            # Load and display LowStocking.png
            try:
                img_path = "assets/LowStocking.png"
                image = Image.open(img_path)
                image = image.resize((600, 300), Image.LANCZOS)
                photo = ImageTk.PhotoImage(image)
                canvas = tk.Canvas(low_ba_frame, width=600, height=300, bg=BG_COLOR, highlightthickness=0)
                canvas.create_image(0, 0, anchor="nw", image=photo)
                canvas.image = photo
                canvas.pack(pady=(10,0))
            except Exception as e:
                canvas = tk.Canvas(low_ba_frame, width=600, height=300, bg=BG_COLOR, highlightthickness=0)
                canvas.create_text(300, 150, text="LowStocking image not found", fill=FG_COLOR, font=FONT)
                canvas.pack(pady=(10,0))

            tk.Label(
                low_ba_frame,
                text="The forest's growing stock trees have been depleated!\nWe're supposed to be growing a forest!",
                bg=BG_COLOR, fg=FG_COLOR, font=("Courier New", 16, "bold"),
                pady=40, wraplength=600, justify="center"
            ).pack()
            tk.Button(
                low_ba_frame, text="Try Again", font=FONT, width=16,
                bg="#444466", fg=FG_COLOR, activebackground="#333355",
                command=lambda: restart_game(low_ba_frame)
            ).pack(pady=10)
            tk.Button(
                low_ba_frame, text="Exit", font=FONT, width=16,
                bg="#444466", fg=FG_COLOR, activebackground="#333355",
                command=root.destroy
            ).pack(pady=10)

        def next_turn(action):
            game.update_stand(action)
            event = game.simulate_event()
            game.stand['year'] += 10
            status.set(game.get_status())
            if event:
                narration.set(event)
            else:
                narration.set("What will you do next?")
            if game.is_low_ba_game_over():
                show_low_ba_screen()
                return
            if game.stand['year'] >= 100:
                show_closing_screen()
            update_status_labels()

        for k, v in ACTIONS.items():
            tk.Button(
                button_frame, text=f"{k}. {v}", width=22, font=FONT,
                bg="#444466", fg=FG_COLOR, activebackground="#333355",
                command=lambda k=k: next_turn(k)
            ).pack(pady=3)

    root.mainloop()

if __name__ == "__main__":
    main()