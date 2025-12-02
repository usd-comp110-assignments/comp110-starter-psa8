import random
import time
import tkinter as tk

# Grid and simulation settings
# DO NOT CHANGE VALUES (for grading consistency)
GRID_SIZE = 8
DIRT_PROB = 0.005      # Probability of food appearing per turn (1 = food, 0 = empty)
TURNS = 200
CELL_SIZE = 60         # Pixel size of each grid cell

# Mouse-themed scoring constants
# DO NOT CHANGE VALUES (only names and comments are mouse/food themed)
ATE_FOOD = 300                          # +300 for eating a piece of food
ATE_EMPTY_TILE = -3 * ATE_FOOD          # -900 for trying to eat where there is no food
MOVE_PENALTY = -15                      # -15 per move
WALL_BUMP = -500                        # -500 for bumping into a wall
STREAK_BONUS = 400                      # +400 for 3 consecutive successful eats
IDLE_PENALTY = -10                      # -10 for staying idle
EXPLORED_NEW_TILE = 10                  # +10 for visiting a new tile
PENALTY_PER_REMAINING_FOOD_AT_END = -200  # -200 per remaining food tile at the end
MOUSE_COLLISION = -10                   # -10 for colliding with another mouse


class Environment:
    """
    Two-mouse environment on a shared grid.

    - The grid is an 8x8 board.
      0 = empty tile, 1 = tile with food.

    - Two mice (A and B) move on the grid and try to eat food.
      Their positions are stored in self.mouse_pos["A"] and ["B"].

    - The GUI draws by default:
        * Food tiles as RED squares
        * Mouse tiles as BLUE squares with big "1" and "2" labels

      If images are available (food.png, mouse1.png, mouse2.png in the same folder),
      it will instead show:
        * food.png on food tiles
        * mouse1.png for Mouse A, mouse2.png for Mouse B
    """

    def __init__(self, canvas, status_callback=None):
        # 0 = empty, 1 = food
        self.grid = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

        # Two mice, each with their own state
        self.mouse_pos = {
            "A": [random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1)],
            "B": [random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1)],
        }
        self.score = {"A": 0, "B": 0}
        self.visited = {"A": set(), "B": set()}
        self.consecutive_clean_count = {"A": 0, "B": 0}

        self.canvas = canvas
        self.rects = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

        # Callback used to update GUI: status_callback(mouse_id, description_str, total_score)
        self.status_callback = status_callback

        # Storage for images (if available)
        self.image_ids = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

        # Try to load images
        self.img_food = None
        self.img_mouseA = None
        self.img_mouseB = None
        self.use_images = False
        try:
            self.img_food = tk.PhotoImage(file="food.png")
            self.img_mouseA = tk.PhotoImage(file="mouse1.png")
            self.img_mouseB = tk.PhotoImage(file="mouse2.png")
            # Only use images if all three loaded successfully
            if self.img_food and self.img_mouseA and self.img_mouseB:
                self.use_images = True
            else:
                print("Image files missing or failed to load; falling back to colored squares.")
        except Exception as e:
            print("Warning: could not load images (food.png, mouse1.png, mouse2.png).")
            print("Reason:", e)
            print("Falling back to colored squares.")

        # For fallback mode (numbers "1" and "2" on mice)
        self.mouse_text_ids = {"A": None, "B": None}

        self.draw_grid()

    def randomly_add_dirt(self):
        """
        Randomly add food to the grid.
        (Name kept for backward compatibility; conceptually this is "randomly add food".)
        """
        for i in range(GRID_SIZE):
            for j in range(GRID_SIZE):
                if random.random() < DIRT_PROB:
                    self.grid[i][j] = 1  # 1 means the tile has food

    def _apply_movement(self, mouse_id, action):
        x, y = self.mouse_pos[mouse_id]

        if action == 'UP' and x > 0:
            self.mouse_pos[mouse_id][0] -= 1
        elif action == 'DOWN' and x < GRID_SIZE - 1:
            self.mouse_pos[mouse_id][0] += 1
        elif action == 'LEFT' and y > 0:
            self.mouse_pos[mouse_id][1] -= 1
        elif action == 'RIGHT' and y < GRID_SIZE - 1:
            self.mouse_pos[mouse_id][1] += 1
        # 'EAT' and 'STAY' do not move

    def perform_actions(self, actionA, actionB, performance_function):
        """
        Perform both mice's actions for a single turn.

        Collision rule:
        - If both mice end on the same tile that has food,
          the food disappears but neither mouse gets the reward.
        - If both mice collide, they are bounced back two spaces unless out of bounds.
        """
        # Save previous positions (for wall-bump / out-of-bounds penalties)
        prevA = tuple(self.mouse_pos["A"])
        prevB = tuple(self.mouse_pos["B"])

        # 1) Move both mice
        self._apply_movement("A", actionA)
        self._apply_movement("B", actionB)

        # 2) Check if they collide
        collision = False
        if self.mouse_pos["A"] == self.mouse_pos["B"]:
            r, c = self.mouse_pos["A"]
            collision = True

            # Bounce both mice back two spaces unless out of bounds
            for mouse_id, prev_pos in [("A", prevA), ("B", prevB)]:
                dr = prev_pos[0] - r
                dc = prev_pos[1] - c
                new_r = prev_pos[0] + 2 * dr
                new_c = prev_pos[1] + 2 * dc

                # Check bounds
                if 0 <= new_r < GRID_SIZE and 0 <= new_c < GRID_SIZE:
                    self.mouse_pos[mouse_id] = [new_r, new_c]
                else:
                    self.mouse_pos[mouse_id] = [max(0, min(GRID_SIZE - 1, new_r)),
                                                max(0, min(GRID_SIZE - 1, new_c))]

        # 3) Apply scoring independently
        deltaA = performance_function(
            self, actionA, prevA,
            mouse_id="A",
            collision=collision
        )
        deltaB = performance_function(
            self, actionB, prevB,
            mouse_id="B",
            collision=collision
        )

        self.score["A"] += deltaA
        self.score["B"] += deltaB

        # 4) Update visuals
        self.update_grid()

    def count_ones(self):
        """Count how many food tiles remain (i.e., how many 1's are in the grid)."""
        return sum(row.count(1) for row in self.grid)

    def draw_grid(self):
        """Initial drawing of the grid cells as white rectangles."""
        for i in range(GRID_SIZE):
            for j in range(GRID_SIZE):
                x0, y0 = j * CELL_SIZE, i * CELL_SIZE
                x1, y1 = x0 + CELL_SIZE, y0 + CELL_SIZE
                self.rects[i][j] = self.canvas.create_rectangle(
                    x0, y0, x1, y1,
                    fill="white", outline="black"
                )
        self.update_grid()

    def update_grid(self):
        """
        Re-draw the grid.

        If images are available (self.use_images == True):

            - each cell has at most one image:
                * Mouse A cell: mouse1.png
                * Mouse B cell: mouse2.png
                * Food cell (without mouse): food.png

        Otherwise (fallback):

            - Food tiles: red fill
            - Mouse positions: blue fill with big "1" and "2"
        """
        posA = self.mouse_pos["A"]
        posB = self.mouse_pos["B"]

        if self.use_images:
            # Clear previous images and redraw background + sprites
            for i in range(GRID_SIZE):
                for j in range(GRID_SIZE):
                    # Base background
                    self.canvas.itemconfig(self.rects[i][j], fill="white")

                    # Remove old image if any
                    if self.image_ids[i][j] is not None:
                        self.canvas.delete(self.image_ids[i][j])
                        self.image_ids[i][j] = None

                    # Decide what image (if any) to draw in this cell
                    image_to_draw = None

                    if [i, j] == posA:
                        image_to_draw = self.img_mouseA
                    elif [i, j] == posB:
                        image_to_draw = self.img_mouseB
                    elif self.grid[i][j] == 1:
                        image_to_draw = self.img_food

                    if image_to_draw is not None:
                        x = j * CELL_SIZE + CELL_SIZE // 2
                        y = i * CELL_SIZE + CELL_SIZE // 2
                        self.image_ids[i][j] = self.canvas.create_image(
                            x, y, image=image_to_draw
                        )

            # In image mode, do NOT show text "1"/"2" on top
            for mouse_id in ["A", "B"]:
                if self.mouse_text_ids[mouse_id] is not None:
                    self.canvas.delete(self.mouse_text_ids[mouse_id])
                    self.mouse_text_ids[mouse_id] = None

        else:
            # Fallback mode: colored squares + text labels
            for i in range(GRID_SIZE):
                for j in range(GRID_SIZE):
                    color = "white"

                    # Food tile is red
                    if self.grid[i][j] == 1:
                        color = "red"

                    # Mice override color to blue
                    if [i, j] == posA or [i, j] == posB:
                        color = "blue"

                    self.canvas.itemconfig(self.rects[i][j], fill=color)

            # Big "1" and "2" text inside mouse cells
            for mouse_id, label in [("A", "1"), ("B", "2")]:
                # Remove old text if exists
                if self.mouse_text_ids[mouse_id] is not None:
                    self.canvas.delete(self.mouse_text_ids[mouse_id])

                r, c = self.mouse_pos[mouse_id]
                x = c * CELL_SIZE + CELL_SIZE // 2
                y = r * CELL_SIZE + CELL_SIZE // 2

                self.mouse_text_ids[mouse_id] = self.canvas.create_text(
                    x, y,
                    text=label,
                    fill="white",
                    font=("Arial", int(CELL_SIZE * 0.6), "bold")
                )

        self.canvas.update()
        time.sleep(.5)


def performance_two_mice(env, action, prev_pos, mouse_id, collision=False):
    """
    Performance function for the two-mouse environment.

    Mouse-story version of the rules:

      +300  ATE_FOOD            (mouse eats food on its tile)
      -900  ATE_EMPTY_TILE      (mouse tries to eat but there's no food)
      -15   MOVE_PENALTY        (every movement)
      -500  WALL_BUMP           (move action but position didn't change)
      +400  STREAK_BONUS        (3 consecutive successful eats)
      -10   IDLE_PENALTY        (STAY)
      +10   EXPLORED_NEW_TILE   (first time on this tile)

    Collision rule for food:
      - If both mice land on the same tile that has food this turn,
        the food disappears BUT neither mouse gets ATE_FOOD or STREAK_BONUS.
    """
    score = 0
    log = []  # used to build a readable description for the GUI

    x, y = env.mouse_pos[mouse_id]
    tile_has_food = (env.grid[x][y] == 1)

    # ---------- COLLISION ----------
    if collision:
        score += MOUSE_COLLISION
        log.append(f"COLLISION +{MOUSE_COLLISION}")


    # ---------- EAT ----------
    if action == 'EAT':
        if tile_has_food and not collision:
            # Successful food eating
            score += ATE_FOOD
            env.grid[x][y] = 0
            env.consecutive_clean_count[mouse_id] += 1
            log.append(f"ATE_FOOD +{ATE_FOOD}")

            if env.consecutive_clean_count[mouse_id] % 3 == 0:
                score += STREAK_BONUS
                log.append(f"STREAK_BONUS +{STREAK_BONUS}")

        elif tile_has_food and collision:
            # Both mice collided on the same food tile:
            # - Food disappears
            # - Nobody gets reward
        #    env.grid[x][y] = 0
            env.consecutive_clean_count[mouse_id] = 0
            log.append("COLLISION (could not eat)")

        else:
            # Tried to eat on an empty tile
            score += ATE_EMPTY_TILE
            env.consecutive_clean_count[mouse_id] = 0
            log.append(f"ATE_EMPTY_TILE {ATE_EMPTY_TILE}")

    # ---------- MOVEMENT ----------
    if action in ['UP', 'DOWN', 'LEFT', 'RIGHT']:
        score += MOVE_PENALTY
        log.append(f"MOVE_PENALTY {MOVE_PENALTY}")

        # Out-of-bounds attempt: action was a move but position didn't change
        if tuple(env.mouse_pos[mouse_id]) == tuple(prev_pos):
            score += WALL_BUMP
            log.append(f"WALL_BUMP {WALL_BUMP}")

        env.consecutive_clean_count[mouse_id] = 0

    # ---------- IDLE ----------
    if action == 'STAY':
        score += IDLE_PENALTY
        env.consecutive_clean_count[mouse_id] = 0
        log.append(f"IDLE_PENALTY {IDLE_PENALTY}")

    # ---------- EXPLORE ----------
    pos_tuple = tuple(env.mouse_pos[mouse_id])
    if pos_tuple not in env.visited[mouse_id]:
        env.visited[mouse_id].add(pos_tuple)
        score += EXPLORED_NEW_TILE
        log.append(f"EXPLORED_NEW_TILE +{EXPLORED_NEW_TILE}")

    # ---------- GUI status callback ----------
    if env.status_callback is not None:
        # desc looks like: "EAT | ATE_FOOD +300 | STREAK_BONUS +400"
        desc_parts = [action]
        if log:
            desc_parts.append(" | ".join(log))
        desc = " | ".join(desc_parts)

        total_score = env.score[mouse_id] + score
        env.status_callback(mouse_id, desc, total_score)

    return score
