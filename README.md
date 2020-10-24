# pyMinesweeper
An implementation of Minesweeper in modern Python, and of an algorithm which solves it automatically.

### Requirements
- Python 3.6+
- tkinter
- pygame

### Playing the game
To play the game as it is, run minesweeper.pyw.

Rules:
 - Each square either contains a mine (called bombs in the code), a number, or is empty. A number tells you how many mines are neighbouring a square (including corners)
 - Left-click uncovers a square. If you uncover a mine, you lose. If you uncover all the squares without mines, you win.
 - Right-click places or removes a flag on an uncovered square - you should use them to mark mines. The number in the top left tells you how many mines are left (total number of mines minus the number of flags placed)
 - **Useful feature:** Clicking on a number which has the correct number of flags neighbouring it uncovers all the other squares around that number.

If you want to change the size of the grid or the number of mines (bombs) in the example, you can change the hardcoded parameters passed to the constructor of `MinesweeperGame` at the bottom of the minesweeper.pyw file.

### Including Minesweeper in your progam
You need to import the objects defined in `minesweeper.pyw` into your python program. Make sure minesweeper.pyw is in the same directory as your program, or somewhere where the python import system can find it. Note that minesweeper.pyw imports tkinter as tk, so you don't need to import it again.

A minesweeper game is managed using a `MinesweeperGame` object, which inherits from `tk.Frame`. A `MinesweeperGame` has a top bar rendered with tkinter, and a main game area which is rendered with pygame. This is because using tkinter keeps this code extensible, but tkinter is way too slow to run the actual game, so I had to resort to pygame. Because pygame is used, **one process can only run a single MinesweeperGame instance**.

To use a `MinesweeperGame` in your code, you need to initialise the Tkinter environment, create a `MinesweeperGame` object, and `pack()` it in its parent, and the game is ready to play. It's really that simple - most of the initialisation is contained within the MinesweeperGame class.

For examples, see `all_numbers.pyw`, `game_ui.pyw` and `solveloop.py`, each of which makes use of different features of MinesweeperGame.

## The solver
As opposed to some methods which always start at the corners (see https://dash.harvard.edu/bitstream/handle/1/14398552/BECERRA-SENIORTHESIS-2015.pdf), my solver starts by guessing a square at random. This is because, if you start near a corner, there will be less directions to expand in, so intuitively there is a higher probability of getting stuck and having to guess. I haven't tested this theory empirically.

Once it finds a starting point, the solver first solves the game as far as possible without guessing, then uses a simple heuristic to guess a square with the lowest probability of containing a mine.

### Using the solver in your program
To use the solver, you need to import everything from both `minesweeper.pyw` and `minesweeper_solver.pyw`.

`minesweeper_solver.pyw` defines the `MinesweeperSolver` class and two methods: `cheat_show_bombs` and `cheat_solve`. The `MinesweeperSolver` plays the game fairly, and tries to deduce the location of the mines from what it sees. `cheat_show_bombs` and `cheat_solve` read the internal attributes of a minesweeper game to find out where the mines are (see all_numbers.pyw for an example).

To use the solver, you should set up `MinesweeperGame`, and pass it to the constructor of `MinesweeperSolver`. Then calling `solver.solve()` will start the solver working. By default the solver continues automatically, but waits 100ms between each move. You can change this delay by passing `delay = [number of milliseconds]` to `solve()` (setting the delay to zero is **not** recommended, but not disallowed), or you can disable the autostepping by passing `autostep = False`, in which case you will have to press T to trigger each move.

For an example of using the MinesweeperSolver, and a really satisfying demonstration, see `solveloop.py`.
 
### Credits:
 - This image: https://i1.wp.com/www.crisgdwrites.com/wp-content/uploads/2016/06/minesweeper_tiles.jpg?fit=512%2C384
   from this reddit question: https://www.reddit.com/r/Minesweeper/comments/dc3cjy/bomb_number_colours_question/
 - This SO question: https://stackoverflow.com/questions/23319059/embedding-a-pygame-window-into-a-tkinter-or-wxpython-frame
 (And the people who wrote/made those. You made my life so much easier!)
