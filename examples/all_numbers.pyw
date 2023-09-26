import sys, os
#import from the parent directory:
sys.path.append('..')
from minesweeper import *
#restore sys.path
sys.path.remove('..')
#move down to parent directory so we can use images from \images\
os.chdir('..')

pygame.init()
pygame.font.init()
window = pygame.display.set_mode((800, 500))

settings = Settings(SETTINGS_FILEPATH)
settings.grid_width = 4
settings.grid_height = 7
settings.ui_scale = 3
settings.mine_density = None
settings.mine_locations = [(0, 0), (1, 0), (2, 0), (3, 0),
                           (0, 1), (2, 1),
                           (0, 2), (1, 2), (2, 2), (3, 2),
                           (0, 3),
                           (0, 4), (1, 4), (2, 4), (3, 4),
                           (0, 5)]

app = MinesweeperApp(window, settings)
app.add_delayed_action('cheat solve', 0,
                       open_all, args=[app.minesweeper_grid])
app.run()
pygame.quit()
