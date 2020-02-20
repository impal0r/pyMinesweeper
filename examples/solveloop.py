from sys import path; path.append('..') #import from parent directory
from minesweeper import *
from minesweeper_solver import *

#restore sys.path and move to parent directory
path.remove('..'); from os import chdir; chdir('..'); del chdir, path

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

game = MinesweeperGame(root,110,55,bomb_density=0.13,scale=1)
game.pack()

solver = MinesweeperSolver(game,delay=10)
def solve():
    print('total:',wins+losses,'\twins:',wins,'\tlosses:',losses,'\n')
    game.reset()
    root.after(100,solver.solve)

def win_func(self):
    global wins,losses; wins += 1
    print('WIN')
    root.after(1000,solve)
def lose_func(self, x, y):
    global wins,losses; losses += 1
    print('LOSE',x,y)
    root.after(1000,solve)
game.set_win_func(win_func)
game.set_lose_func(lose_func)

wins = 0
losses = 0
root.after(2000,solve)
root.mainloop()
