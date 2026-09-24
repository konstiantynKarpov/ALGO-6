import tkinter as tk
import tkinter.messagebox as messagebox
import time
import random
from copy import deepcopy
import math

class HackenbushGame:
    """Represents the state and logic of a Hackenbush game instance."""
    def __init__(self, nodes_dict, edges_list, ground_set, difficulty='easy'):
        """
        Initializes the game state.
        Args:
            nodes_dict (dict): {node_id: (x, y)} for initial node positions.
            edges_list (list): List of edge tuples [(u, v)].
            ground_set (set): Set of node IDs that are grounded.
            difficulty (str): AI difficulty ('easy', 'medium', 'hard').
        """
        self.difficulty = difficulty
        self.current_player = 0 # 0 for Human, 1 for AI
        self.positions = nodes_dict
        self.nodes = list(nodes_dict.keys())
        self.edges = [tuple(sorted(e)) for e in edges_list]
        self.ground_nodes = ground_set
        if not self.ground_nodes:
             print("Warning: No ground nodes provided to HackenbushGame.")

    def get_possible_moves(self):
        """Returns a list of currently available moves (edges)."""
        return self.edges[:]

    def apply_move(self, edge):
        """
        Removes an edge and any components disconnected from the ground.
        Args: edge (tuple): The edge (u, v) to remove.
        """
        edge_sorted = tuple(sorted(edge))
        if edge_sorted in self.edges:
            self.edges.remove(edge_sorted)
            connected_nodes = find_connected_to_ground(
                self.nodes, self.edges, self.ground_nodes
            )
            self.edges = [e for e in self.edges if e[0] in connected_nodes and e[1] in connected_nodes]
        else:
            print(f"Warning: Tried to remove non-existent edge {edge_sorted}")

    def switch_player(self):
        """Switches the current player between 0 and 1."""
        self.current_player = 1 - self.current_player

    def is_terminal(self):
        """Checks if the game has ended (no edges left)."""
        return len(self.edges) == 0

    def get_winner(self):
        """
        Determines the winner based on the rule: last player to move wins.
        Returns:
            int: The ID of the winning player (0 or 1) if the game is terminal.
            None: If the game is not terminal.
        """
        return self.current_player if self.is_terminal() else None


def find_connected_to_ground(all_nodes, current_edges, ground_nodes_set):
    """
    Finds all nodes connected to any ground node via current edges using BFS.
    Args:
        all_nodes (list): List of all node IDs that *could* exist.
        current_edges (list): List of current edge tuples [(u, v)].
        ground_nodes_set (set): Set of ground node IDs.
    Returns:
        set: A set of node IDs connected to the ground.
    """
    if not ground_nodes_set:
        return set()
    adj = {n: [] for n in all_nodes}
    active_nodes_in_edges = set(n for edge in current_edges for n in edge)
    for u, v in current_edges:
        if u in adj and v in adj:
            adj[u].append(v)
            adj[v].append(u)

    connected = set()
    queue = [gn for gn in ground_nodes_set if gn in adj or gn in active_nodes_in_edges or not current_edges]
    visited = set(queue)

    while queue:
        node = queue.pop(0)
        connected.add(node)
        if node in adj:
             for neighbor in adj[node]:
                 if (neighbor in active_nodes_in_edges or neighbor in ground_nodes_set) and neighbor not in visited:
                     visited.add(neighbor)
                     queue.append(neighbor)
    connected.update(ground_nodes_set)
    return connected.intersection(set(all_nodes))

def evaluate(game_state):
    """
    Simple evaluation function for Hackenbush AI.
    Returns the number of edges remaining.
    """
    return len(game_state.edges)

def alpha_beta_search(game_state, depth, alpha, beta, maximizing_player):
    """
    Performs alpha-beta search for the Hackenbush game.
    Args:
        game_state (HackenbushGame): The current state of the game.
        depth (int): The remaining search depth.
        alpha (float): Alpha value for pruning.
        beta (float): Beta value for pruning.
        maximizing_player (bool): True if the current node is for the maximizing player.
    Returns:
        tuple: (best_score, best_move) found from this state.
    """
    if depth == 0 or game_state.is_terminal():
        score = evaluate(game_state)
        if game_state.is_terminal():
             return -1000 if maximizing_player else 1000, None
        return score, None

    possible_moves = game_state.get_possible_moves()
    if not possible_moves:
         return -1000 if maximizing_player else 1000, None

    best_move = random.choice(possible_moves)

    if maximizing_player:
        value = float('-inf')
        for move in possible_moves:
            new_game = deepcopy(game_state)
            new_game.apply_move(move)
            score, _ = alpha_beta_search(new_game, depth - 1, alpha, beta, False)
            if score > value:
                value = score
                best_move = move
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value, best_move
    else: # Minimizing player
        value = float('inf')
        for move in possible_moves:
            new_game = deepcopy(game_state)
            new_game.apply_move(move)
            score, _ = alpha_beta_search(new_game, depth - 1, alpha, beta, True)
            if score < value:
                value = score
                best_move = move
            beta = min(beta, value)
            if beta <= alpha:
                break
        return value, best_move

def get_ai_move(game):
    """
    Determines the AI's move based on the selected difficulty level.
    Args: game (HackenbushGame): The current game state.
    Returns: tuple: The chosen edge (move), or None if no moves available.
    """
    possible_moves = game.get_possible_moves()
    if not possible_moves: return None

    if game.difficulty == 'easy':
        return random.choice(possible_moves)
    elif game.difficulty == 'medium': depth = 2
    else: depth = 4

    print(f"AI ({game.difficulty}) thinking with depth {depth}...")
    start_time = time.time()
    score, best_move = alpha_beta_search(game, depth, float('-inf'), float('inf'), True)
    end_time = time.time()
    print(f"AI finished thinking in {end_time - start_time:.2f} seconds. (Move: {best_move}, Score: {score})")

    valid_moves_tuples = [tuple(sorted(m)) for m in possible_moves]
    if best_move is None or tuple(sorted(best_move)) not in valid_moves_tuples:
         print(f"Warning: Alpha-beta returned invalid move {best_move}, choosing random.")
         best_move = random.choice(possible_moves) if possible_moves else None

    return best_move

def point_line_distance(px, py, x1, y1, x2, y2):
    """Calculates the perpendicular distance from a point to a line segment."""
    line_len_sq = (x2 - x1)**2 + (y2 - y1)**2
    if line_len_sq == 0: return math.sqrt((px - x1)**2 + (py - y1)**2)
    t = ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / line_len_sq
    t = max(0, min(1, t))
    proj_x = x1 + t * (x2 - x1)
    proj_y = y1 + t * (y2 - y1)
    dist = math.sqrt((px - proj_x)**2 + (py - proj_y)**2)
    return dist

class HackenbushEditorApp:
    """Tkinter application for editing and playing Hackenbush."""
    def __init__(self, root):
        """
        Initializes the GUI application.
        Args: root: The root Tkinter window.
        """
        self.root = root
        self.root.title("Hackenbush Editor & Player")
        self.cell_size = 20
        self.dot_radius = 5
        self.ground_y = 450
        self.click_threshold = 10

        self.editor_nodes = {}
        self.editor_edges = []
        self.editor_ground_nodes = set()
        self.next_node_id = 0
        self.current_mode = tk.StringVar(value="add_node")
        self.selected_node = None
        self.game = None

        main_frame = tk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(main_frame, width=600, height=500, bg="white")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.draw_ground()

        control_panel = tk.Frame(main_frame, width=150)
        control_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)

        mode_frame = tk.LabelFrame(control_panel, text="Mode")
        mode_frame.pack(pady=5, fill=tk.X)
        self.add_node_rb = tk.Radiobutton(mode_frame, text="Add Nodes", variable=self.current_mode, value="add_node", command=self.reset_selection)
        self.add_node_rb.pack(anchor=tk.W)
        self.add_edge_rb = tk.Radiobutton(mode_frame, text="Add Edges", variable=self.current_mode, value="add_edge_start", command=self.reset_selection)
        self.add_edge_rb.pack(anchor=tk.W)
        self.delete_rb = tk.Radiobutton(mode_frame, text="Delete Item", variable=self.current_mode, value="delete_item", command=self.reset_selection)
        self.delete_rb.pack(anchor=tk.W)


        self.play_button = tk.Button(control_panel, text="Play Game", command=self.start_play_mode, state=tk.DISABLED)
        self.play_button.pack(pady=5, fill=tk.X)
        self.clear_button = tk.Button(control_panel, text="Clear All", command=self.clear_all)
        self.clear_button.pack(pady=5, fill=tk.X)
        self.quit_button = tk.Button(control_panel, text="Quit", command=self.root.quit)
        self.quit_button.pack(side=tk.BOTTOM, pady=5, fill=tk.X)

        difficulty_frame = tk.LabelFrame(control_panel, text="Difficulty")
        difficulty_frame.pack(pady=5, fill=tk.X)
        self.difficulty_var = tk.StringVar(value="easy")
        self.diff_radio_buttons = []
        for level in ("easy", "medium", "hard"):
            rb = tk.Radiobutton(difficulty_frame, text=level.capitalize(), variable=self.difficulty_var, value=level)
            rb.pack(anchor=tk.W)
            self.diff_radio_buttons.append(rb)

        self.status_label = tk.Label(control_panel, text="Mode: Add Nodes", relief=tk.SUNKEN, anchor=tk.W, justify=tk.LEFT)
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X, pady=5)

    def draw_ground(self):
        """Draws the ground line."""
        self.root.update_idletasks()
        width = self.canvas.winfo_width()
        if width <= 1: width = 600
        self.canvas.delete("ground_line")
        self.canvas.create_line(0, self.ground_y, width, self.ground_y,
                                dash=(4, 4), fill="gray", tags="ground_line")
        self.canvas.tag_lower("ground_line")

    def redraw_canvas(self):
        """Redraws nodes and edges from the editor state."""
        self.canvas.delete("node")
        self.canvas.delete("edge")
        self.canvas.delete("selection")

        for u, v in self.editor_edges:
            if u in self.editor_nodes and v in self.editor_nodes:
                x1, y1 = self.editor_nodes[u]
                x2, y2 = self.editor_nodes[v]
                self.canvas.create_line(x1, y1, x2, y2, fill="blue", width=2, tags="edge")

        for node_id, (x, y) in self.editor_nodes.items():
            color = "brown" if node_id in self.editor_ground_nodes else "green"
            r = self.dot_radius
            self.canvas.create_oval(x - r, y - r, x + r, y + r, fill=color, outline="black", tags=("node", f"node_{node_id}"))

        if self.selected_node is not None and self.selected_node in self.editor_nodes:
             x, y = self.editor_nodes[self.selected_node]
             r = self.dot_radius + 2
             self.canvas.create_oval(x - r, y - r, x + r, y + r, outline="red", width=2, tags="selection")

        self.canvas.tag_raise("node")
        self.canvas.tag_raise("selection")


    def find_node_at(self, x, y):
        """Finds node ID at click coordinates."""
        nodes_to_check = self.editor_nodes
        for node_id, (nx, ny) in nodes_to_check.items():
            if (x - nx)**2 + (y - ny)**2 <= self.click_threshold**2:
                return node_id
        return None

    def find_edge_at(self, x, y):
         """Finds edge near click coordinates."""
         edges_to_check = self.game.edges if self.game else self.editor_edges
         nodes_to_check = self.game.positions if self.game else self.editor_nodes

         for u, v in edges_to_check:
             if u in nodes_to_check and v in nodes_to_check:
                 x1, y1 = nodes_to_check[u]
                 x2, y2 = nodes_to_check[v]
                 dist = point_line_distance(x, y, x1, y1, x2, y2)
                 if dist < self.click_threshold:
                     return (u, v)
         return None


    def reset_selection(self, redraw=True):
        """Resets node selection and updates status label based on mode."""
        mode = self.current_mode.get()
        self.selected_node = None
        if redraw and mode != "play":
            self.redraw_canvas()

        if mode == "add_node":
             self.status_label.config(text="Mode: Add Nodes. Click to add.")
        elif mode == "add_edge_start":
             self.status_label.config(text="Mode: Add Edges. Click first node.")
        elif mode == "delete_item":
             self.status_label.config(text="Mode: Delete. Click node or edge.")


    def on_canvas_click(self, event):
        """Handles canvas clicks based on the current mode."""
        mode = self.current_mode.get()
        x, y = event.x, event.y

        if mode == "add_node":
            node_id = self.next_node_id
            self.editor_nodes[node_id] = (x, y)
            if y >= self.ground_y - self.click_threshold:
                self.editor_ground_nodes.add(node_id)
                print(f"Node {node_id} added as ground node at ({x},{y}).")
            else:
                print(f"Node {node_id} added at ({x},{y}).")
            self.next_node_id += 1
            self.redraw_canvas()
            self.update_play_button_state()

        elif mode == "add_edge_start":
            clicked_node = self.find_node_at(x, y)
            if clicked_node is not None:
                self.selected_node = clicked_node
                self.current_mode.set("add_edge_end")
                self.redraw_canvas()
                self.status_label.config(text="Mode: Add Edges. Click second node.")
            else:
                 self.status_label.config(text="Mode: Add Edges. Click ON a node to start edge.")

        elif mode == "add_edge_end":
            clicked_node = self.find_node_at(x, y)
            if clicked_node is not None:
                if clicked_node != self.selected_node:
                    edge = tuple(sorted((self.selected_node, clicked_node)))
                    if edge not in self.editor_edges:
                        self.editor_edges.append(edge)
                        print(f"Edge {edge} added.")
                        self.redraw_canvas()
                        self.update_play_button_state()
                    else:
                        print(f"Edge {edge} already exists.")
                    self.reset_selection(redraw=False)
                    self.current_mode.set("add_edge_start")
                else:
                    self.reset_selection()
            else:
                 self.reset_selection()

        elif mode == "delete_item":
            node_to_delete = self.find_node_at(x, y)
            if node_to_delete is not None:
                print(f"Attempting to delete node {node_to_delete}...")
                if node_to_delete in self.editor_nodes:
                    del self.editor_nodes[node_to_delete]
                    self.editor_ground_nodes.discard(node_to_delete)
                    self.editor_edges = [edge for edge in self.editor_edges if node_to_delete not in edge]
                    print(f"Node {node_to_delete} and incident edges deleted.")
                    self.redraw_canvas()
                    self.update_play_button_state()
                else:
                    print("Node not found.")
            else:
                edge_to_delete = self.find_edge_at(x, y)
                if edge_to_delete is not None:
                    edge_tuple_sorted = tuple(sorted(edge_to_delete))
                    if edge_tuple_sorted in self.editor_edges:
                        print(f"Attempting to delete edge {edge_tuple_sorted}...")
                        self.editor_edges.remove(edge_tuple_sorted)
                        print(f"Edge {edge_tuple_sorted} deleted.")
                        self.redraw_canvas()
                        self.update_play_button_state()
                    else:
                        print("Edge not found (already deleted?).")
                else:
                    print("Click not near any node or edge.")

        elif mode == "play":
             if self.game and self.game.current_player == 0: # Human's turn
                 clicked_edge = self.find_edge_at(x,y)
                 if clicked_edge:
                     edge_tuple_sorted = tuple(sorted(clicked_edge))
                     if edge_tuple_sorted in self.game.edges:
                          print(f"Player clicked edge: {edge_tuple_sorted}")
                          self.game.apply_move(edge_tuple_sorted)
                          self.redraw_canvas_for_game()
                          if self.game.is_terminal():
                               self.end_game()
                          else:
                               self.game.switch_player()
                               self.status_label.config(text="AI is thinking...")
                               self.root.update()
                               self.root.after(100, self.ai_turn)
                     else:
                          print(f"Clicked edge {edge_tuple_sorted} does not exist in current game state.")
                 else:
                      print("Click not on any edge.")

    def clear_all(self):
        """Clears the editor and resets state."""
        self.editor_nodes = {}
        self.editor_edges = []
        self.editor_ground_nodes = set()
        self.next_node_id = 0
        self.selected_node = None
        self.game = None
        self.current_mode.set("add_node")
        self.status_label.config(text="Mode: Add Nodes. Click to add.")
        self.canvas.delete("all")
        self.draw_ground()
        self.update_play_button_state()
        self.set_controls_state("normal")
        print("Editor cleared.")

    def update_play_button_state(self):
        """Enables Play button if structure is potentially valid."""
        valid_ground = any(gn in self.editor_nodes for gn in self.editor_ground_nodes)
        valid_edge = any(u in self.editor_nodes and v in self.editor_nodes for u,v in self.editor_edges)
        if valid_ground and valid_edge:
            self.play_button.config(state=tk.NORMAL)
        else:
            self.play_button.config(state=tk.DISABLED)

    def set_controls_state(self, state):
        """Enable/disable editor/difficulty controls."""
        try:
            for rb in [self.add_node_rb, self.add_edge_rb, self.delete_rb]:
                rb.config(state=state)
        except AttributeError:
            pass
        try:
            for rb in self.diff_radio_buttons:
                rb.config(state=state)
        except AttributeError:
            pass
        self.clear_button.config(state=state if state=="normal" else tk.DISABLED)
        if state == "disabled":
            self.play_button.config(state=tk.DISABLED)
        elif self.current_mode.get() != 'play':
             self.update_play_button_state()


    def start_play_mode(self):
        """Validates structure, removes unconnected nodes, and switches to play mode."""
        if not self.editor_ground_nodes or not self.editor_edges:
             messagebox.showwarning("Cannot Play", "The structure must have at least one ground node and one edge.")
             return

        # Filter nodes and edges
        print("Validating structure and removing unconnected nodes...")
        nodes_in_edges = set(n for edge in self.editor_edges for n in edge)
        nodes_to_keep_ids = self.editor_ground_nodes | nodes_in_edges
        nodes_for_game = {nid: pos for nid, pos in self.editor_nodes.items() if nid in nodes_to_keep_ids}
        edges_for_game = [edge for edge in self.editor_edges if edge[0] in nodes_for_game and edge[1] in nodes_for_game]
        ground_for_game = {gn for gn in self.editor_ground_nodes if gn in nodes_for_game}

        if not ground_for_game or not edges_for_game:
             messagebox.showwarning("Cannot Play", "After removing unconnected nodes, the structure is invalid.")
             return

        # Update editor state to match game state for consistent redraw after game
        self.editor_nodes = nodes_for_game
        self.editor_edges = edges_for_game
        self.editor_ground_nodes = ground_for_game
        print("Unconnected nodes removed.")


        print("\n--- Starting Game ---")
        self.current_mode.set("play")
        self.status_label.config(text="Game started! Your turn.")
        self.selected_node = None
        self.set_controls_state("disabled")

        self.game = HackenbushGame(
            nodes_dict=deepcopy(self.editor_nodes), # Use filtered nodes
            edges_list=deepcopy(self.editor_edges), # Use filtered edges
            ground_set=deepcopy(self.editor_ground_nodes), # Use filtered ground
            difficulty=self.difficulty_var.get()
        )
        self.redraw_canvas_for_game()


    def redraw_canvas_for_game(self):
        """Redraws the board according to the current self.game state."""
        self.canvas.delete("node")
        self.canvas.delete("edge")
        self.canvas.delete("selection")

        if not self.game: return

        connected_nodes_in_game = find_connected_to_ground(
            self.game.nodes, self.game.edges, self.game.ground_nodes
        )
        nodes_to_draw = connected_nodes_in_game | self.game.ground_nodes

        for u, v in self.game.edges:
            if u in self.game.positions and v in self.game.positions and u in nodes_to_draw and v in nodes_to_draw:
                x1, y1 = self.game.positions[u]
                x2, y2 = self.game.positions[v]
                self.canvas.create_line(x1, y1, x2, y2, fill="blue", width=2, tags="edge")

        for node_id, (x, y) in self.game.positions.items():
            if node_id in nodes_to_draw:
                color = "brown" if node_id in self.game.ground_nodes else "green"
                r = self.dot_radius
                self.canvas.create_oval(x - r, y - r, x + r, y + r, fill=color, outline="black", tags="node")

        self.canvas.tag_raise("node")


    def ai_turn(self):
         """Handles the AI's turn."""
         if self.game and not self.game.is_terminal() and self.game.current_player == 1:
             move = get_ai_move(self.game)
             if move:
                 print(f"AI plays edge: {move}")
                 edge_tuple_sorted = tuple(sorted(move))
                 if edge_tuple_sorted in self.game.edges:
                     self.game.apply_move(edge_tuple_sorted)
                 else:
                     print(f"Error: AI tried invalid move {edge_tuple_sorted}. Game edges: {self.game.edges}")
                     self.game.switch_player()
                     self.status_label.config(text="AI Error! Your turn.")
                     return

                 self.redraw_canvas_for_game()
                 if self.game.is_terminal():
                      self.end_game()
                 else:
                      self.game.switch_player()
                      self.status_label.config(text="Your turn!")
             else:
                 print("Error: AI failed to find a move, but game is not terminal.")
                 self.end_game()


    def end_game(self):
         """Ends the game, displays the winner, and restores editor state."""
         if not self.game: return

         winner = self.game.get_winner()
         winner_text = ""
         if winner == 0: winner_text = "Game Over! You Win!"
         elif winner == 1: winner_text = "Game Over! AI Wins!"
         else: winner_text = "Game Over!"

         messagebox.showinfo("Game Over", winner_text)

         self.status_label.config(text=winner_text + " Switched back to editor.")
         self.game = None
         self.current_mode.set("add_node")
         self.redraw_canvas()
         self.update_play_button_state() 
         self.set_controls_state("normal")


def main():
    """Main function to start the Tkinter application."""
    root = tk.Tk()
    app = HackenbushEditorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()