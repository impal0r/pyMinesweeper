import sys, os
#trick to import from the parent directory:
sys.path.append('..')

from minesweeper import *
from minesweeper_solver import *

#restore sys.path
sys.path.remove('..')
#move down to parent directory so we can use images from \images\
os.chdir('..')

root = tk.Tk()
root.title('Minesweeper')

size1 = (4,7)
bombs1 = ((0,0),(1,0),(2,0),(3,0),
          (0,1),(2,1),
          (0,2),(1,2),(2,2),(3,2),
          (0,3),
          (0,4),(1,4),(2,4),(3,4),
          (0,5))

spacer = tk.Frame(root, width=300)
spacer.pack()
game1 = MinesweeperGame(root, *size1, bombs=bombs1)
game1.pack(fill='x',expand=1)
cheat_solve(game1)

root.mainloop()
