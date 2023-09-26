# pyMinesweeper
A fast, simple implementation of Minesweeper in Python 3.6+.
Includes an API so that the game can be played by an AI.
Also includes an AI solver.

### Requirements
- Python 3.6+
- pygame
- numpy (for the AI)

### How do I install pyMinesweeper?

Make sure you have python 3.6+ on your machine, with the pygame and numpy libraries installed.

This code is portable, so all you have to do is clone the repository and extract the files.

### Playing the game
To play the game yourself, run `minesweeper.pyw`. The grid size and number of mines can be changed in the file `settings.json`.

![screenshot of a game](https://raw.githubusercontent.com/impal0r/pyMinesweeper/main/images/Capture1.png)

Minesweeper Rules:
 - Each square either contains a mine (called bombs in the code), a number, or is empty. The numbers tell you how many mines there are in neighbouring squares (including corners)
 - Left-clicking opens a square. If you open a mined square, you lose. If you open all the unmined squares, you win.
 - Right-clicking toggles the flag on an unopened square - you can use them to mark mines. The number in the top left tells you how many mines are left (total number of mines minus the number of flags placed).
 - **Openings**: Opening a square with zero neighbouring mines will create a large opening - these are important at the start of the game.
 - **Chording**: Try clicking on a number which has the right number of flags on neighbouring squares.
 - **Guessing**: You can find a lot of the mines by solving the riddle of the numbers, but sometimes you just have to make an informed guess.
 - There is a minesweeper wiki online with plenty of information about the game.

## The solver algorithm
To run the solver, run `minesweeper_ai.py`. The grid size and number of mines, as well as other parameters, can be changed in the code at the bottom of this file. By default, 10 games are solved, then the solver stops and prints the number of wins and losses. *This is very satisfying.*    
Keyboard controls:
 - SPACE: pauses and unpauses the solver
 - . (PERIOD key): advances the solver one step at a time, when it is paused

As opposed to starting at the corners (eg https://dash.harvard.edu/bitstream/handle/1/14398552/BECERRA-SENIORTHESIS-2015.pdf), this solver starts by guessing a square at random.

The game position is analysed using some hardcoded rules, which will find all the squares which are definitely mined or safe (except in rare cases, when there is a safe square that the ruleset misses). If there are no such squares found, the algorithm tries to find a square with a low probability of being mined, and guesses. A full depth-first search would find the exact probabilities, at the expense of involving some very large integers and potentially being slow. I'm planning to maybe implement one at some point.

The solver (contained in the `BasicRulesetAI` class) has been written to be subclassable, so that better algorithms could be implemented and compared.

### Credits:
 - This image: https://i1.wp.com/www.crisgdwrites.com/wp-content/uploads/2016/06/minesweeper_tiles.jpg?fit=512%2C384
   from this reddit question: https://www.reddit.com/r/Minesweeper/comments/dc3cjy/bomb_number_colours_question/
 - Keshikan for the DSEG segment fonts: https://www.keshikan.net/fonts-e.html
