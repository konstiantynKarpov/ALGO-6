import tkinter as tk
import random
from copy import deepcopy


class HackenbushGame:
    def __init__(self, difficulty='easy'):
        self.difficulty = difficulty
        self.current_player = 0  # 0 => Human, 1 => AI

        self.nodes = list(range(12))

        # Positions for a connected structure
        # Ground: 0,1,2 at bottom
        self.positions = {
            0: (150, 400),  # Ground node 0
            1: (300, 400),  # Ground node 1
            2: (450, 400),  # Ground node 2
            3: (120, 300),
            4: (180, 300),
            5: (270, 300),
            6: (330, 300),
            7: (420, 300),
            8: (150, 200),
            9: (300, 200),
            10: (450, 200),
            11: (300, 100),
        }

        # Edges: ground connections + bridging so that all nodes are reachable
        self.edges = [
            # Ground connections
            (0, 3), (0, 4),
            (1, 5), (1, 6),
            (2, 7),

            # Top row bridging
            (3, 4), (4, 5), (5, 6), (6, 7),

            # Second row bridging
            (4, 8), (5, 9), (6, 9), (7, 10),

            # More connections in the upper region
            (8, 9), (9, 10), (9, 11), (10, 11),
        ]

    def get_possible_moves(self):
        return self.edges[:]

    def apply_move(self, edge):
        """Remove the chosen edge, then drop any subgraph not connected to ground nodes."""
        if edge in self.edges:
            self.edges.remove(edge)
        connected = find_connected_to_ground(self.nodes, self.edges, ground_nodes=[0, 1, 2])
        self.edges = [e for e in self.edges if e[0] in connected and e[1] in connected]

    def switch_player(self):
        self.current_player = 1 - self.current_player

    def is_terminal(self):
        """Game ends when no edges remain."""
        return len(self.edges) == 0

    def get_winner(self):
        """
        Last player to make a valid move wins,
        so if it's terminal now, the other player won.
        """
        return 1 - self.current_player if self.is_terminal() else None


def find_connected_to_ground(nodes, edges, ground_nodes):
    # Build adjacency
    graph = {n: [] for n in nodes}
    for (n1, n2) in edges:
        graph[n1].append(n2)
        graph[n2].append(n1)

    def bfs(start):
        visited = set()
        stack = [start]
        while stack:
            node = stack.pop()
            if node not in visited:
                visited.add(node)
                for neighbor in graph[node]:
                    if neighbor not in visited:
                        stack.append(neighbor)
        return visited

    connected = set()
    for g in ground_nodes:
        connected |= bfs(g)
    return connected



def alpha_beta_search(game, depth, alpha, beta, maximizing_player):
    if depth == 0 or game.is_terminal():
        return evaluate(game), None

    moves = game.get_possible_moves()
    if not moves:
        return evaluate(game), None

    if maximizing_player:
        value = float('-inf')
        best_move = None
        for move in moves:
            new_game = deepcopy(game)
            new_game.apply_move(move)
            new_game.switch_player()

            score, _ = alpha_beta_search(new_game, depth - 1, alpha, beta, False)
            if score > value:
                value = score
                best_move = move
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value, best_move
    else:
        value = float('inf')
        best_move = None
        for move in moves:
            new_game = deepcopy(game)
            new_game.apply_move(move)
            new_game.switch_player()

            score, _ = alpha_beta_search(new_game, depth - 1, alpha, beta, True)
            if score < value:
                value = score
                best_move = move
            beta = min(beta, value)
            if beta <= alpha:
                break
        return value, best_move


def evaluate(game):
    """
    Simple heuristic: the more edges remain, the better for the current (max) player.
    """
    return len(game.edges)


def get_ai_move(game):
    """Select a move based on difficulty."""
    moves = game.get_possible_moves()
    if not moves:
        return None

    if game.difficulty == 'easy':
        return random.choice(moves)
    elif game.difficulty == 'medium':
        _, move = alpha_beta_search(game, depth=2, alpha=float('-inf'), beta=float('inf'),
                                    maximizing_player=True)
        return move
    else:  # 'hard'
        _, move = alpha_beta_search(game, depth=4, alpha=float('-inf'), beta=float('inf'),
                                    maximizing_player=True)
        return move


class HackenbushGUI:

    def __init__(self, canvas, info_label, game, on_game_end):
        self.canvas = canvas
        self.info_label = info_label
        self.game = game
        self.on_game_end = on_game_end

        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.draw()

    def draw(self):
        self.canvas.delete("all")

        # Draw a dashed line for the "ground" near y=400
        self.canvas.create_line(50, 400, 550, 400, dash=(4, 4), fill="gray")

        # Edges
        for e in self.game.edges:
            x1, y1 = self.game.positions[e[0]]
            x2, y2 = self.game.positions[e[1]]
            self.canvas.create_line(x1, y1, x2, y2, fill="blue", width=2)

        # Nodes
        for n in self.game.nodes:
            x, y = self.game.positions[n]
            color = "brown" if n in (0, 1, 2) else "green"
            r = 10
            self.canvas.create_oval(x - r, y - r, x + r, y + r, fill=color, outline="black")

        # Check game state
        if self.game.is_terminal():
            winner = self.game.get_winner()
            if winner == 0:
                self.info_label.config(text="Game over! Player 0 (you) win!")
            elif winner == 1:
                self.info_label.config(text="Game over! Player 1 (AI) wins!")
            else:
                self.info_label.config(text="Game over!")
            self.on_game_end()  # let the main app know the game is done
        else:
            if self.game.current_player == 0:
                self.info_label.config(text="Your turn! Click an edge to remove it.")
            else:
                self.info_label.config(text="AI is thinking...")
                self.canvas.after(500, self.ai_turn)

    def on_canvas_click(self, event):
        # No moves if game ended or AI's turn
        if self.game.is_terminal() or self.game.current_player == 1:
            return
        clicked_edge = self.get_edge_at_position(event.x, event.y)
        if clicked_edge:
            self.game.apply_move(clicked_edge)
            self.game.switch_player()
            self.draw()

    def get_edge_at_position(self, x, y):
        for e in self.game.edges:
            x1, y1 = self.game.positions[e[0]]
            x2, y2 = self.game.positions[e[1]]
            dist = point_line_distance(x, y, x1, y1, x2, y2)
            if dist < 6:
                return e
        return None

    def ai_turn(self):
        if not self.game.is_terminal():
            move = get_ai_move(self.game)
            if move:
                self.game.apply_move(move)
            self.game.switch_player()
            self.draw()


def point_line_distance(px, py, x1, y1, x2, y2):
    line_len_sq = (x2 - x1) ** 2 + (y2 - y1) ** 2
    if line_len_sq == 0:
        return ((px - x1) ** 2 + (py - y1) ** 2) ** 0.5
    t = max(0, min(1, ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / line_len_sq))
    proj_x = x1 + t * (x2 - x1)
    proj_y = y1 + t * (y2 - y1)
    return ((px - proj_x) ** 2 + (py - proj_y) ** 2) ** 0.5



class HackenbushApp:
    """
    A single window with:
      - 3 difficulty radio buttons
      - a single "Play" button
      - a canvas for the board
      - a label for status
    Node 0,1,2 are on the ground. Total 12 nodes.
    """

    def __init__(self, root):
        self.root = root
        self.root.title("Hackenbush (12 Nodes, 3 on Ground)")

        # Difficulty selection
        difficulty_frame = tk.Frame(self.root)
        difficulty_frame.pack(pady=5)

        tk.Label(difficulty_frame, text="Difficulty:").pack(side=tk.LEFT)
        self.difficulty_var = tk.StringVar(value="easy")
        for level in ("easy", "medium", "hard"):
            rb = tk.Radiobutton(
                difficulty_frame,
                text=level.capitalize(),
                variable=self.difficulty_var,
                value=level
            )
            rb.pack(side=tk.LEFT)

        # Single "Play" button
        self.play_button = tk.Button(self.root, text="Play", command=self.on_play_clicked)
        self.play_button.pack(pady=5)

        # Canvas + label
        self.canvas = tk.Canvas(self.root, width=600, height=500, bg="white")
        self.canvas.pack()

        self.info_label = tk.Label(self.root, text="", font=("Helvetica", 12))
        self.info_label.pack()

        # Track if a game is in progress
        self.game_in_progress = False
        self.gui = None

    def on_play_clicked(self):
        """Start a new game if none is in progress, or after finishing one."""
        if self.game_in_progress:
            # Ignore if game is currently running
            return

        chosen_difficulty = self.difficulty_var.get()
        game = HackenbushGame(difficulty=chosen_difficulty)

        # If there's an old GUI, clear it
        if self.gui:
            self.canvas.delete("all")
            self.gui = None

        # Create the new GUI
        self.gui = HackenbushGUI(
            canvas=self.canvas,
            info_label=self.info_label,
            game=game,
            on_game_end=self.on_game_end
        )

        # Disable difficulty while game runs
        self.set_difficulty_controls_state("disabled")
        self.game_in_progress = True

    def on_game_end(self):
        """Called by HackenbushGUI when the game finishes."""
        self.game_in_progress = False
        # Re-enable difficulty for next time
        self.set_difficulty_controls_state("normal")

    def set_difficulty_controls_state(self, state):
        """Enable or disable the radio buttons for difficulty."""
        for child in self.root.winfo_children():
            if isinstance(child, tk.Frame):
                for rb in child.winfo_children():
                    if isinstance(rb, tk.Radiobutton):
                        rb.config(state=state)


def main():
    root = tk.Tk()
    app = HackenbushApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
