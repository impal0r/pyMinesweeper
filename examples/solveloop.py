import sys, os
#trick to import from the parent directory:
sys.path.append('..')

from minesweeper import *
from minesweeper_solver import *

#restore sys.path
sys.path.remove('..')
#move down to parent directory so we can use images from \images\
os.chdir('..')

#Set up Tkinter
root = tk.Tk()
root.title('Minesweeper')
root.resizable(False, False)

##def window_pos():
##    w = root.winfo_width()
##    h = root.winfo_height()
##    x = 20
##    y = 20
##    root.geometry(f'{w}x{h}+{x}+{y}')
##root.after(200,window_pos)

#Initialise minesweeper game (with hardcoded parameters)
game = MinesweeperGame(root,110,55,bomb_density=0.13,scale=1)
game.pack()

#Set up automatic solver
solver = MinesweeperSolver(game,delay=10)

def solve():
    print('total:',wins+losses,'\twins:',wins,'\tlosses:',losses,'\n')
    game.reset()
    root.after(100,solver.solve)

#Callback functions so that the solver keeps playing new games forever
def win_func(self):
    global wins,losses; wins += 1
    print('WIN')
    root.after(1000,solve) #wait 1 second before doing a new game
def lose_func(self, x, y):
    global wins,losses; losses += 1
    print('LOSE',x,y)
    root.after(1000,solve)
game.set_win_func(win_func)
game.set_lose_func(lose_func)

wins = 0
losses = 0
root.after(2000,solve) #wait 2 seconds before starting to give time to init
root.mainloop()
