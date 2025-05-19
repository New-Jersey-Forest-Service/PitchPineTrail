import tkinter as tk
from tkinter import messagebox
from game_logic import Game

def main():
    game = Game()

    BG_COLOR = "#222244"
    FG_COLOR = "#33FF33"
    FONT = ("Courier New", 12, "bold")

    root = tk.Tk()
    root.title("PitchPineTrail")
    root.configure(bg=BG_COLOR)

    # Top: Graphics/ASCII Art area
    canvas = tk.Canvas(root, width=600, height=120, bg=BG_COLOR, highlightthickness=0)
    canvas.pack(pady=(10,0))
    ascii_art = [
        "   /\\        /\\        /\\        /\\        /\\   ",
        "  /  \\      /  \\      /  \\      /  \\      /  \\  ",
        " /    \\    /    \\    /    \\    /    \\    /    \\ ",
        "/      \\__/      \\__/      \\__/      \\__/      \\",
        "    PITCH PINE TRAIL - NJFS Edition            "
    ]
    for i, line in enumerate(ascii_art):
        canvas.create_text(300, 15 + i*20, text=line, fill=FG_COLOR, font=FONT)

    # Middle: Status/Narration area
    status = tk.StringVar()
    status.set("Welcome to PitchPineTrail! Click an action to begin.")

    status_label = tk.Label(root, textvariable=status, wraplength=600, justify="left",
                        padx=10, pady=10, bg=BG_COLOR, fg=FG_COLOR, font=FONT)
    status_label.pack()

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

    def next_turn(action):
        game.update_stand(action)
        event = game.simulate_event()
        game.stand['year'] += 10
        status.set(game.get_status())
        if event:
            narration.set(event)
        else:
            narration.set("What will you do next?")
        if game.stand['year'] >= 100:
            messagebox.showinfo("Simulation Complete", game.get_summary())
            root.destroy()

    for k, v in ACTIONS.items():
        tk.Button(
            button_frame, text=f"{k}. {v}", width=22, font=FONT,
            bg="#444466", fg=FG_COLOR, activebackground="#333355",
            command=lambda k=k: next_turn(k)
        ).pack(pady=3)

    root.mainloop()

if __name__ == "__main__":
    main()