import tkinter as tk
from tkinter import messagebox
import random
import time

class MazeSolverGame:
    def __init__(self, root):
        self.root = root
        self.root.title("MAZE SOLVER")
        self.root.geometry("700x800")
        self.root.configure(bg="#E8F4F8")
        
        # Game variables
        self.difficulty = "Medium"
        self.moves = 0
        self.start_time = time.time()
        self.timer_running = True
        self.maze_size = 15
        self.player_pos = [1, 1]
        self.start_pos = [1, 1]
        self.end_pos = [self.maze_size-2, self.maze_size-2]
        
        # Create UI and generate maze
        self.create_ui()
        self.generate_maze()
        self.draw_maze()
        self.update_timer()
    
    def create_ui(self):
        # Title
        tk.Label(self.root, text="MAZE SOLVER", font=("Arial", 24, "bold"), 
                fg="#2E86AB", bg="#E8F4F8", pady=10).pack()
        
        # Status bar
        self.status_frame = tk.Frame(self.root, bg="#E8F4F8")
        self.status_frame.pack(pady=5)
        
        self.timer_label = tk.Label(self.status_frame, text="Time: 00:00", 
                                   font=("Arial", 14), fg="#A23B72", bg="#E8F4F8")
        self.timer_label.pack(side=tk.LEFT, padx=10)
        
        self.moves_label = tk.Label(self.status_frame, text="Moves: 0", 
                                   font=("Arial", 14), fg="#A23B72", bg="#E8F4F8")
        self.moves_label.pack(side=tk.LEFT, padx=10)
        
        self.score_label = tk.Label(self.status_frame, text="Score: 1000", 
                                   font=("Arial", 14), fg="#A23B72", bg="#E8F4F8")
        self.score_label.pack(side=tk.LEFT, padx=10)
        
        # Canvas for maze
        self.canvas = tk.Canvas(self.root, width=600, height=600, bg="lightgray", bd=2, relief="solid")
        self.canvas.pack(pady=10)
        
        # Bind keyboard events
        self.root.bind("<Key>", self.on_key_press)
        self.root.focus_set()
        
        # Control buttons
        self.button_frame = tk.Frame(self.root, bg="#E8F4F8")
        self.button_frame.pack(pady=10)
        
        tk.Button(self.button_frame, text="Easy", width=10, bg="#FF6F00", fg="white",
                 command=lambda: self.set_difficulty("Easy")).pack(side=tk.LEFT, padx=5)
        tk.Button(self.button_frame, text="Medium", width=10, bg="#FF6F00", fg="white",
                 command=lambda: self.set_difficulty("Medium")).pack(side=tk.LEFT, padx=5)
        tk.Button(self.button_frame, text="Hard", width=10, bg="#FF6F00", fg="white",
                 command=lambda: self.set_difficulty("Hard")).pack(side=tk.LEFT, padx=5)
        tk.Button(self.button_frame, text="Restart", width=10, bg="#A23B72", fg="white",
                 command=self.restart_game).pack(side=tk.LEFT, padx=5)
        
        # Instructions
        tk.Label(self.root, text="🎯 Goal: Reach the green exit!\n⌨️ Controls: Arrow Keys or WASD",
                font=("Arial", 10), fg="#2E7D32", bg="#E8F4F8", justify=tk.LEFT).pack(pady=10)
    
    def set_difficulty(self, level):
        self.difficulty = level
        self.maze_size = 11 if level == "Easy" else 15 if level == "Medium" else 19
        self.restart_game()
    
    def generate_maze(self):
        # Initialize maze with walls
        self.maze = [['#' for _ in range(self.maze_size)] for _ in range(self.maze_size)]
        self.start_pos = [1, 1]
        self.end_pos = [self.maze_size-2, self.maze_size-2]
        
        # Carve paths using DFS
        stack = [self.start_pos]
        self.maze[self.start_pos[0]][self.start_pos[1]] = '.'
        directions = [(-2, 0), (0, 2), (2, 0), (0, -2)]
        
        while stack:
            current = stack[-1]
            y, x = current
            neighbors = []
            for dy, dx in directions:
                ny, nx = y + dy, x + dx
                if 1 <= ny < self.maze_size-1 and 1 <= nx < self.maze_size-1:
                    if self.maze[ny][nx] == '#':
                        neighbors.append((ny, nx, dy//2, dx//2))
            
            if neighbors:
                ny, nx, dy, dx = random.choice(neighbors)
                self.maze[y + dy][x + dx] = '.'
                self.maze[ny][nx] = '.'
                stack.append([ny, nx])
            else:
                stack.pop()
        
        self.maze[self.start_pos[0]][self.start_pos[1]] = 'S'
        self.maze[self.end_pos[0]][self.end_pos[1]] = 'E'
        self.player_pos = self.start_pos[:]
    
    def draw_maze(self):
        self.canvas.delete("all")
        self.cell_size = min(600 // self.maze_size, 40)
        
        # Draw maze cells
        for y in range(self.maze_size):
            for x in range(self.maze_size):
                x1, y1 = x * self.cell_size, y * self.cell_size
                x2, y2 = x1 + self.cell_size, y1 + self.cell_size
                
                if self.maze[y][x] == '#':  # Wall
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill="#1B1B3A", outline="black")
                elif self.maze[y][x] == 'S':  # Start
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill="#FFFF00", outline="black")
                elif self.maze[y][x] == 'E':  # End
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill="#00FF00", outline="black")
                else:  # Path
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill="#FFFFFF", outline="#DDDDDD")
        
        # Draw player
        px, py = self.player_pos[1], self.player_pos[0]
        px1, py1 = px * self.cell_size, py * self.cell_size
        px2, py2 = px1 + self.cell_size, py1 + self.cell_size
        self.canvas.create_oval(px1+5, py1+5, px2-5, py2-5, fill="#0066FF", outline="#0033CC")
    
    def update_status(self):
        # Update moves
        self.moves_label.config(text=f"👣 Moves: {self.moves}")
        
        # Update timer and score
        if self.timer_running:
            elapsed = int(time.time() - self.start_time)
            minutes = elapsed // 60
            seconds = elapsed % 60
            self.timer_label.config(text=f"Time: {minutes:02d}:{seconds:02d}")
            score = max(0, 1000 - (self.moves * 10) - (elapsed * 2))
            self.score_label.config(text=f"Score: {score}")
    
    def update_timer(self):
        self.update_status()
        if self.timer_running:
            self.root.after(1000, self.update_timer)
    
    def move_player(self, dy, dx):
        new_y = self.player_pos[0] + dy
        new_x = self.player_pos[1] + dx
        
        # Check if move is valid
        if 0 <= new_y < self.maze_size and 0 <= new_x < self.maze_size:
            if self.maze[new_y][new_x] != '#':
                self.player_pos = [new_y, new_x]
                self.moves += 1
                self.draw_maze()
                self.update_status()
                
                # Check win condition
                if self.player_pos == self.end_pos:
                    self.win_game()
    
    def on_key_press(self, event):
        key = event.keysym.upper()
        if key in ['UP', 'W']: self.move_player(-1, 0)
        elif key in ['DOWN', 'S']: self.move_player(1, 0)
        elif key in ['LEFT', 'A']: self.move_player(0, -1)
        elif key in ['RIGHT', 'D']: self.move_player(0, 1)
    
    def restart_game(self):
        self.moves = 0
        self.start_time = time.time()
        self.timer_running = True
        self.generate_maze()
        self.draw_maze()
        self.update_status()
    
    def win_game(self):
        self.timer_running = False
        elapsed = int(time.time() - self.start_time)
        score = max(0, 1000 - (self.moves * 10) - (elapsed * 2))
        
        play_again = messagebox.askyesno("🏆 You Won!", 
                                        f"🎉 CONGRATULATIONS!\n\n"
                                        f"Time: {elapsed//60:02d}:{elapsed%60:02d}\n"
                                        f"Moves: {self.moves}\n"
                                        f"Score: {score}\n\n"
                                        "Would you like to play again?")
        
        if play_again: self.restart_game()
        else: self.root.quit()

def main():
    root = tk.Tk()
    game = MazeSolverGame(root)
    root.mainloop()

if __name__ == "__main__":
    main()