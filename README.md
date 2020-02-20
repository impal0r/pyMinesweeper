# pyMinesweeper
The ultimate minesweeper game and solving algorithm, in Python 3.

Requirements: Python 3.6+, tkinter, pygame

# Usage

## To use just the minesweeper game:
 - Add `from minesweeper import *` at the top of your python program (minesweeper.py imports tkinter as tk so no need to import it again)
 - Create a tkinter window - making it non-resizable is recommended (`root = tk.Tk(); root.resizable(False, False)`)
 - You can now initialise a MinesweeperGame `MinesweeperGame(root, [options])` and show it in the window!

## To use the solver
 - The minesweeper_solver.py file doesn't implicitly import minesweeper.py, so you will need both `from minesweeper import *; from minesweeper_solver import *`
 - Create a tkinter window and minesweeper game as above
 - Create a solver for the game: `solver = MinesweeperSolver(game, [options])`
 - Call `solver.solve()` to start the solver!
 
# Credits:
 - Me
 - This image: https://i1.wp.com/www.crisgdwrites.com/wp-content/uploads/2016/06/minesweeper_tiles.jpg?fit=512%2C384
   from this reddit question: https://www.reddit.com/r/Minesweeper/comments/dc3cjy/bomb_number_colours_question/
 - This SO question: https://stackoverflow.com/questions/23319059/embedding-a-pygame-window-into-a-tkinter-or-wxpython-frame
 (And the people who wrote/made those. You saved my day!)
