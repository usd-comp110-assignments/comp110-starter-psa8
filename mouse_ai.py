import random
import tkinter as tk
from config import *

def good_mouse(env, mouse_id):

    return 'STAY' # Placeholder return; replace with actual logic


# Helper functions used by smart_mouse

def count_food_cells(grid, row, col):

    return 0 # Placeholder return; replace with actual logic


def find_first_food(grid):

    return None # Placeholder return; replace with actual logic


def smart_mouse(env, mouse_id):

    return 'STAY' # Placeholder return; replace with actual logic

def custom_mouse(env, mouse_id):

    return 'STAY' # Placeholder return; replace with actual logic

# DO NOT EDIT ANYTHING BELOW THIS LINE 

def lazy_mouse(env, mouse_id):
    """
    A simple reference mouse mouse.

    Behavior:
    1. If the current tile has food → return 'EAT'.
    2. Otherwise, check the four adjacent tiles (UP, DOWN, LEFT, RIGHT).
       If any adjacent tile has food and in-bounds, move toward it.
    3. If neither the current tile nor any adjacent tile has food → return 'STAY'.

    This mouse does not explore or search for distant food. It only reacts
    to food that is directly next to it, which is why we call it the "lazy" mouse.
    """
    r, c = env.mouse_pos[mouse_id]

    # 1. Eat food on current tile if present
    if env.grid[r][c] == 1:
        return 'EAT'

    # 2. Check UP
    if r > 0 and env.grid[r - 1][c] == 1:
        return 'UP'

    # 3. Check DOWN
    if r < len(env.grid) - 1 and env.grid[r + 1][c] == 1:
        return 'DOWN'

    # 4. Check LEFT
    if c > 0 and env.grid[r][c - 1] == 1:
        return 'LEFT'

    # 5. Check RIGHT
    if c < len(env.grid) - 1 and env.grid[r][c + 1] == 1:
        return 'RIGHT'

    # 6. No adjacent food → stay
    return 'STAY'


# Dictionary to store mouse mouse functions
# Instructor can add more can add their own:
#   def custom_mouse(env, mouse_id): ...
#   mice["custom"] = custom_mouse
mice = {
    "Lazy": lazy_mouse,
    "Good": good_mouse,
    "Smart": smart_mouse,
    "Custom": custom_mouse
}

# -------------------------------------------------
# Two-mouse simulation
# -------------------------------------------------


def run_simulation(canvas, mouseA_fn, mouseB_fn, status_callback):
    '''
    Runs the simulation using the mice specified above and the configuration file.
    '''
    env = Environment(canvas, status_callback=status_callback)

    for _ in range(TURNS):
        env.randomly_add_dirt()  # conceptually: randomly add food

        # Each mouse chooses an action based on its own position
        actionA = mouseA_fn(env, "A")
        actionB = mouseB_fn(env, "B")

        # Environment applies both actions, with scoring + collision logic
        env.perform_actions(actionA, actionB, performance_two_mice)

    remaining_food = env.count_ones()

    final_A = env.score["A"] + PENALTY_PER_REMAINING_FOOD_AT_END * remaining_food
    final_B = env.score["B"] + PENALTY_PER_REMAINING_FOOD_AT_END * remaining_food

    print("\nSimulation finished.")
    print("Remaining food tiles:", remaining_food)
    print(f"Penalty for remaining food: {PENALTY_PER_REMAINING_FOOD_AT_END * remaining_food}")
    print(f"Mouse A base score: {env.score['A']}, final with penalty: {final_A}")
    print(f"Mouse B base score: {env.score['B']}, final with penalty: {final_B}")


if __name__ == "__main__":

    # AUTO–GENERATED MENU FROM DICTIONARY
    print("Available mouse mice:")
    mouse_names = list(mice.keys())
    for idx, name in enumerate(mouse_names, start=1):
        print(f"({idx}) {name}")

    # Select Mouse A
    choiceA = input("Enter choice for Mouse 1 (A): ").strip()
    try:
        nameA = mouse_names[int(choiceA) - 1]
    except:
        print("Invalid choice for Mouse A; defaulting to first mouse.")
        nameA = mouse_names[0]

    # Select Mouse B
    choiceB = input("Enter choice for Mouse 2 (B): ").strip()
    try:
        nameB = mouse_names[int(choiceB) - 1]
    except:
        print("Invalid choice for Mouse B; defaulting to first mouse.")
        nameB = mouse_names[0]

    mouseA_fn = mice[nameA]
    mouseB_fn = mice[nameB]

    print(f"\nRunning two-mouse simulation: Mouse 1 = {nameA}, Mouse 2 = {nameB}\n")

    # GUI Setup
    root = tk.Tk()
    root.title("Mouse Food Hunt - Two Mice")

    # Prevent the window from constantly resizing itself based on label text
    root.resizable(False, False)

    # Main frame to hold grid + legend side by side
    main_frame = tk.Frame(root)
    main_frame.pack()

    # Canvas for grid
    canvas = tk.Canvas(main_frame, width=GRID_SIZE * CELL_SIZE, height=GRID_SIZE * CELL_SIZE)
    canvas.grid(row=0, column=0)

    # Legend frame to the right of the grid
    legend_frame = tk.Frame(main_frame)
    legend_frame.grid(row=0, column=1, padx=10, sticky="n")

    # Load legend images separately (so they are always visible)
    legend_mouse1_img = None
    legend_mouse2_img = None
    try:
        legend_mouse1_img = tk.PhotoImage(file="mouse1.png")
        legend_mouse2_img = tk.PhotoImage(file="mouse2.png")
    except Exception as e:
        print("Warning: could not load legend images:", e)

    # Mouse 1 legend
    if legend_mouse1_img is not None:
        mouse1_img_label = tk.Label(legend_frame, image=legend_mouse1_img)
        mouse1_img_label.image = legend_mouse1_img  # keep reference
        mouse1_img_label.pack()
    else:
        mouse1_img_label = tk.Label(legend_frame, text="Mouse 1", font=("Arial", 12, "bold"))
        mouse1_img_label.pack()

    mouse1_text_label = tk.Label(
        legend_frame,
        text=f"Mouse 1: {nameA}",
        font=("Arial", 10)
    )
    mouse1_text_label.pack(pady=(0, 15))

    # Mouse 2 legend
    if legend_mouse2_img is not None:
        mouse2_img_label = tk.Label(legend_frame, image=legend_mouse2_img)
        mouse2_img_label.image = legend_mouse2_img  # keep reference
        mouse2_img_label.pack()
    else:
        mouse2_img_label = tk.Label(legend_frame, text="Mouse 2", font=("Arial", 12, "bold"))
        mouse2_img_label.pack()

    mouse2_text_label = tk.Label(
        legend_frame,
        text=f"Mouse 2: {nameB}",
        font=("Arial", 10)
    )
    mouse2_text_label.pack()

    # Status area frame below everything
    status_frame = tk.Frame(root)
    status_frame.pack(fill="x")

    # Use monospace font and fixed width so the window doesn't jump
    STATUS_WIDTH = 120  # characters, adjust if needed

    label_A = tk.Label(
        status_frame,
        text="",
        font=("Courier New", 10),
        width=STATUS_WIDTH,
        anchor="w",
        justify="left"
    )
    label_A.pack(fill="x")

    label_B = tk.Label(
        status_frame,
        text="",
        font=("Courier New", 10),
        width=STATUS_WIDTH,
        anchor="w",
        justify="left"
    )
    label_B.pack(fill="x")

    # status_callback will format:
    # Mouse1: lazy   | EAT  | ATE_FOOD +300 | Total Score: XXXX |
    def status_callback(mouse_id, desc, total_score):
        """
        Called from performance_two_mice for each mouse every step.
        Fixed-width formatted as:
        Mouse1: lazy   | ACTION | EFFECTS... | Total Score: XXXX |
        """
        # Column widths
        AGENTNAME_COL = 8   # width for "lazy", "good", "smart", etc.
        ACTION_COL = 5      # UP, DOWN, EAT, STAY
        EFFECTS_COL = 60    # combined effect text
        SCORE_COL = 6       # score field width

        mouse_label = "Mouse 1" if mouse_id == "A" else "Mouse 2"
        mouse_name = nameA if mouse_id == "A" else nameB

        # desc looks like: "EAT | ATE_FOOD +300 | STREAK_BONUS +400"
        parts = desc.split(" | ")
        action = parts[0] if parts else ""
        effects = " | ".join(parts[1:]) if len(parts) > 1 else ""

        # Truncate effects if too long
        if len(effects) > EFFECTS_COL:
            effects = effects[:EFFECTS_COL - 3] + "..."

        line = (
            f"{mouse_label}: {mouse_name:<{AGENTNAME_COL}} | "
            f"{action:<{ACTION_COL}} | "
            f"{effects:<{EFFECTS_COL}} | "
            f"Total Score: {total_score:<{SCORE_COL}} |"
        )

        if mouse_id == "A":
            label_A.config(text=line)
        else:
            label_B.config(text=line)

    # Start simulation after GUI loads
    root.after(100, lambda: run_simulation(canvas, mouseA_fn, mouseB_fn, status_callback))

    # Run event loop
    root.mainloop()
