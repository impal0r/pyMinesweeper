import sys, random, os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide" #don't print pygame welcome msg
import tkinter as tk
import pygame, pygame.font
from pygame.locals import *
#Fix blurriness on high DPI screens in Windows
import platform
if platform.system() == 'Windows':
    import ctypes; ctypes.windll.shcore.SetProcessDpiAwareness(1); del ctypes
del platform
#Define constants for pygame MOUSEBUTTONUP and MOUSEBUTTONDOWN events
LEFT = 1
RIGHT = 3

SCALE = 2
class MinesweeperGame(tk.Frame):
    BOMB_LIST_ERRORS = False
    # if True, will raise exceptions on invalid bombs list passes to __init__ or reset
    # Use for debugging purposes
    IMG_SIZE = 16 #images are squares with side length of IMG_SIZE

    def _load_images(self):
        size = (self.SQUARE,self.SQUARE)
        scale = pygame.transform.scale
        img_load = pygame.image.load
        img_name = lambda s: os.path.join('images', s)
        clear = scale(img_load(img_name('clear.png')),size)
        _1    = scale(img_load(img_name('1.png')),size)
        _2    = scale(img_load(img_name('2.png')),size)
        _3    = scale(img_load(img_name('3.png')),size)
        _4    = scale(img_load(img_name('4.png')),size)
        _5    = scale(img_load(img_name('5.png')),size)
        _6    = scale(img_load(img_name('6.png')),size)
        _7    = scale(img_load(img_name('7.png')),size)
        _8    = scale(img_load(img_name('8.png')),size)
        bomb  = scale(img_load(img_name('bomb.png')),size)
        self.imgs = (clear,_1,_2,_3,_4,_5,_6,_7,_8,*(None for i in range(7)),bomb)
        #index into imgs list will give image for that number
        self.xbomb_img   = scale(img_load(img_name('xbomb.png')),size)
        self.redbomb_img = scale(img_load(img_name('redbomb.png')),size)
        self.flagged_img = scale(img_load(img_name('flagged.png')),size)
        self.btn_img     = scale(img_load(img_name('btn.png')),size)

    def neighbours(self, x, y): #NB: Must return an iterable.
        '''Returns an iterable of two-tuples representing
        the squares adjacent to (x, y) by a side or a corner'''
        if (x,y) in self._saved_neighbours:
            return self._saved_neighbours[x,y]
        else:
            f = filter(self._square_filter, ((x-1,y-1),(x,y-1),
                                             (x+1,y-1),(x-1,y),(x+1,y),
                                             (x-1,y+1),(x,y+1),(x+1,y+1)))
            self._saved_neighbours[x,y] = f = tuple(f)
            return f

    def _mouse_sq(self, mouse_pos):
        return (mouse_pos[0]//self.SQUARE, mouse_pos[1]//self.SQUARE)

    def __init__(self, master, width, height,
                 bomb_number=None, bomb_density=1/6, bombs=None, seed=None,
                 scale=SCALE):
        '''
        Create a MinesweeperGame instance which can be embedded in any tkinter window,
        width and height are in tiles,
        the 16x16px tiles are scaled by SCALE (useful for HDPI displays).
        If bombs (list of 2-tuples of integer coords) specified, bombs will be placed
        at these coordinates. Otherwise they will be randomly generated based on either
        bomb_density (proportion of tiles with a bomb) or bomb_number. In this case seed
        is passed to random.seed() if it is not None.
        '''
        #SET UP LOGICAL GRID
        #initialise grid
        self.width = int(width)
        self.height = int(height)
        assert self.width > 0 and self.height > 0, 'Grid dimensions must be positive'
        self._grid = [[0 for j in range(self.height)] for i in range(self.width)]
        #For each entry in the grid, counting from least significant end:
        #bits 0-3: cell number (#bombs in vicinity 0-8); should be 0 if bomb
        #bit 4: bomb?
        #bit 5: flagged?
        #bit 6: button removed?

        if seed is not None:
            random.seed(seed)
        #initialise bombs
        self.bombs = []
        self.randombombs = True
        if bombs is not None: #if list specified set bombs from list
            self.randombombs = False
            for bomb in bombs:
                #sanitise co-ordinates from list
                if len(bomb)!=2:
                    if BOMB_LIST_ERRORS:
                        raise ValueError(f"Each element of bombs must be a 2-tuple "
                                         f"of integer co-ordinates, not '{bomb}'")
                    continue
                if bomb[0]<0 or bomb[0]>=self.width or bomb[1]<0  or bomb[1]>=self.height:
                    if BOMB_LIST_ERRORS:
                        raise ValueError(f"Invalid bomb co-ordinates '{bomb}'")
                    continue
                self._grid[bomb[0]][bomb[1]] = 16 #denotes bomb
                self.bombs.append(bomb)
        #init bomb number
        # if passed as a parameter, will be set to that
        # if bombs list specified as well (both parameters set),
        #   extra bombs will be generated if bomb_number > len(bombs)
        # if bombs list specified but not number,
        #   will be set to number of valid bombs in list (as worked out above)
        # if neither is specified, bomb_density of squares will become bombs
        #   (NB. otherwise bomb_density will be ignored)
        if bomb_density is None: bomb_density = 0.15
        if bomb_number is None and bombs is None:
            assert 0 <= bomb_density <= 1, 'Bomb density must be a number between 0 and 1'
            self.bomb_number = int(width*height * bomb_density)
        elif bomb_number is None:
            self.bomb_number = len(self.bombs)
        else:
            self.bomb_number = int(bomb_number)
            assert self.bomb_number >= 0, 'Number of bombs cannot be negative'
            assert self.bomb_number <= self.width * self.height, \
                   "Number of bombs can't be more than the number of squares"
        #generate bombs
        i = len(self.bombs) #if bombs already specified, make up the difference
        while i<self.bomb_number:
            x = random.randint(0,self.width-1)
            y = random.randint(0,self.height-1)
            if (x,y) not in self.bombs:
                self._grid[x][y] = 16 #denotes bomb
                self.bombs.append((x,y))
                i += 1

        #init dict to speed up neighbours function
        self._saved_neighbours = {}
        self._square_filter = lambda sq:                                      \
            not(sq[0]<0 or sq[1]<0 or sq[0]==self.width or sq[1]==self.height)

        #GAME WINDOW
        super().__init__(master)
        #top bar
        self.topBar = tk.Frame(self, bg='#eee')
        self.bomb_ctr = self.bomb_number
        self.bombCounter = tk.Label(self.topBar, bg='black', relief='sunken', border=2,
                                    font=("System",14,'bold'), fg='red',
                                    padx=0,pady=0,width=3, text=str(self.bomb_number))
        self.bombCounter.pack(side='left')
        self.time = 0
        self.timer = tk.Label(self.topBar, bg='black', relief='sunken', border=2,
                              font=("System",14,'bold'), fg='red',
                              padx=0,pady=0,width=4, text='0:00')
        self.timer.pack(side='right')
        self.reset_btn = tk.Button(self.topBar, text='Reset', font=('System',11,'bold'),
                                   command=self.reset)
        self.reset_btn.place(relx=.5,rely=.5,anchor='c')
        self.topBar.pack(expand=1,fill='both')
        #main game area (pygame)
        self.scale = scale
        self.SQUARE = round(self.IMG_SIZE*scale+.5) #size of square in px (round up)
        self.game_width = self.SQUARE*self.width    #height of actual game
        self.game_height = self.SQUARE*self.height  #width  of actual game
        self.embed = tk.Frame(self, width=self.game_width, height=self.game_height)
        self.embed.pack() #create embed frame for pygame window
        os.environ['SDL_WINDOWID'] = str(self.embed.winfo_id())
        self.SCREEN = pygame.display.set_mode((self.game_width,self.game_height))
        self.SCREEN.fill((0xdd,0xdd,0xdd))
        #get images as Surface objects
        self._load_images()
        #draw grid (and put bomb count in cells)
        for i in range(self.width):
            for j in range(self.height):
                if not self._grid[i][j]: #not a bomb -> still 0
                    #work out number in square
                    count = 0
                    for x,y in self.neighbours(i,j):
                        if self._grid[x][y] == 16:
                            count += 1
                    self._grid[i][j] = count
                self.SCREEN.blit(self.btn_img, (self.SQUARE*i,self.SQUARE*j))

        self.lose_func = lambda x,y:None
        self.win_func = lambda:None

        self.last_leftbtndown_sq = None
        self.last_rightbtndown_sq = None
        self.buttons_left = self.width*self.height
        self.stop = False
        #ONLY start timer after first click!
        self._runtimer = False
        self._virgin = True #has the playing field been touched?
        self.won = False
        self.lost = False
        
        self._run()

    def set_win_func(self, function):
        '''`function` will be executed whenever the game is lost.
        It must take 1 argument, `self`,
        as it is treated as a class method.
        Use to define extra custom behaviour'''
        from types import MethodType
        self.win_func = MethodType(function, self)

    def set_lose_func(self, function):
        '''`function` will be executed whenever the game is won.
        It must take 3 arguments, `self, x, y`.
        `self` is this MinesweeperGame object (function is treated as a class method)
        x and y are the co-ordinates of the last bomb that was clicked
        Use to define extra custom behaviour'''
        from types import MethodType
        self.lose_func = MethodType(function, self)

    def reset(self, new_width=None, new_height=None,
              bomb_number=None, bomb_density=None, bombs=None,
              seed=None, scale=None):
        change_dimensions = False
        if new_width is not None:
            self.width = int(new_width)
            assert self.width > 0, 'Grid dimensions must be positive'
            change_dimensions = True
        if new_height is not None:
            self.height = int(new_height)
            assert self.height > 0, 'Grid dimensions must be positive'
            change_dimensions = True
        if scale is not None:
            if not change_dimensions:
                raise ValueError('A scale can only be passed to reset if new dimensions are specified')
            self.scale = scale

        #Reset grid and place new bombs, unless no arguments are specified
        if bombs is not None:
            #reset logical grid
            self._grid = [[0 for j in range(self.height)] for i in range(self.width)]
            self.bombs = []
            for bomb in bombs:
                #sanitise co-ordinates from list
                if len(bomb)!=2:
                    if BOMB_LIST_ERRORS:
                        raise ValueError("Each element of bombs must be a 2-tuple "
                                         f"of integer co-ordinates, not '{bomb}'")
                    continue
                if bomb[0]<0 or bomb[0]>=self.width or bomb[1]<0  or bomb[1]>=self.height:
                    if BOMB_LIST_ERRORS:
                        raise ValueError(f"Invalid bomb co-ordinates '{bomb}'")
                    continue
                self._grid[bomb[0]][bomb[1]] = 16 #denotes bomb
                self.bombs.append(bomb)
            if bomb_number is None:
                self.bomb_number = len(self.bombs)
                self.randombombs = False
        elif bomb_number is not None:
            self.bomb_number = int(bomb_number)
            assert self.bomb_number >= 0, 'Number of bombs cannot be negative'
            assert self.bomb_number <= self.width * self.height, \
                   "Number of bombs can't be more than the number of squares"
            self.randombombs = True
        elif bomb_density is not None:
            assert 0 <= bomb_density <= 1, 'Bomb density must be between 0 and 1'
            self.bomb_number = int(width*height * bomb_density)
            self.randombombs = True

        if seed is not None:
            if not self.randombombs:
                raise TypeError('A seed can only be passed to reset if new bombs are to be randomly generated')
            random.seed(seed)

        if self.randombombs:
            #reset logical grid
            self._grid = [[0 for j in range(self.height)] for i in range(self.width)]
            #generate bombs
            self.bombs = []
            i = 0
            while i<self.bomb_number:
                x = random.randint(0,self.width-1)
                y = random.randint(0,self.height-1)
                if (x,y) not in self.bombs:
                    self._grid[x][y] = 16 #denotes bomb
                    self.bombs.append((x,y))
                    i += 1

        if change_dimensions:
            #reset dict which speeds up neighbours function
            self._saved_neighbours = {}
            #reset game area
            self.SQUARE = round(self.IMG_SIZE*self.scale+.5) #size of square in px (round up)
            self.game_width = self.SQUARE*self.width    #height of actual game
            self.game_height = self.SQUARE*self.height  #width  of actual game
            self.embed.config(width=self.game_width, height=self.game_height)
            self.SCREEN = pygame.display.set_mode((self.game_width,self.game_height))
            self.SCREEN.fill((0xdd,0xdd,0xdd))

        #work out bomb numbers if regenerated, and reset grid
        for i in range(self.width):
            for j in range(self.height):
                if not self._grid[i][j]: #not a bomb -> still 0
                    #work out number in square
                    count = 0
                    for x,y in self.neighbours(i,j):
                        if self._grid[x][y] == 16:
                            count += 1
                    self._grid[i][j] = count
                self.SCREEN.blit(self.btn_img, (self.SQUARE*i,self.SQUARE*j))

        self.bomb_ctr = self.bomb_number
        self.bombCounter.config(text=str(self.bomb_ctr))
        self.stop = False
        self._runtimer = False
        self.time = 0
        self.timer.config(text='0:00')
        self.buttons_left = self.width*self.height
        self._virgin = True
        self.won = False
        self.lost = False

        self._run()

    def _run_timer(self):
        if self._runtimer:
            mins = str(self.time//60)
            secs = '{:0>2d}'.format(self.time%60)
            self.timer.config(text=mins+':'+secs)
            self.time += 1
            self.after(1000,self._run_timer)

    def _lose(self, x, y): #x and y are coordinates of bomb clicked
        for bomb in self.bombs:
            self.hide_button(*bomb)
        self.SCREEN.blit(self.redbomb_img, (self.SQUARE*x,self.SQUARE*y))

        #mark incorrect flags
        for i in range(self.width):
            for j in range(self.height):
                #if flagged and not a bomb
                if self._grid[i][j] & 0b100000 and not self._grid[i][j] & 0b10000:
                    self.SCREEN.blit(self.xbomb_img, (self.SQUARE*i,self.SQUARE*j))

        self.stop = True
        self._runtimer = False
        self.lost = True
        
        self.lose_func(x,y)

    def _flash_win(self):
        if self.stop:
            if self.bombCounter.cget('text')=='':
                self.bombCounter.config(text='WIN!')
            else:
                self.bombCounter.config(text='')
            self.after(500,self._flash_win)
        else:
            self.bombCounter.config(width=3)

    def _win(self):
        self.bombCounter.config(width=4,text='WIN!')
        self.stop = True
        self._runtimer = False
        self.won = True
        self._flash_win()

        self.win_func()

    def _run(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                self.stop = True
            elif not self.stop:
                if event.type == MOUSEBUTTONDOWN:
                    if event.button == LEFT:
                        self.last_leftbtndown_sq = self._mouse_sq(pygame.mouse.get_pos())
                    elif event.button == RIGHT:
                        self.last_rightbtndown_sq = self._mouse_sq(pygame.mouse.get_pos())
                elif event.type == MOUSEBUTTONUP:
                    x, y = self._mouse_sq(pygame.mouse.get_pos())
                    if event.button == LEFT and (x,y) == self.last_leftbtndown_sq:
                        if self._grid[x][y] & 0b1000000: #if button removed
                            self.num_click(x, y)
                        else:
                            self.button_click(x, y)
                    elif event.button == RIGHT and (x,y) == self.last_rightbtndown_sq:
                        if self._grid[x][y] & 0b1000000: #if button removed
                            self.num_click(x, y)
                        else:
                            self.button_flag(x, y)
        pygame.display.update()
        #pygame needs an explicit mainloop to constantly check for events.
        #This function makes sure it is called again after a short delay
        #so that pygame can process events in the event queue
        if not self.stop:
            self.after(2, self._run)

    def clear_space(self, x, y):
        #self.hide_button(x,y)
        new_all = [(x,y)]
        new_nums = []
        Q = [(x,y)]
        while Q:
            for i,j in self.neighbours(*Q.pop(0)):
                #if not already exposed OR flagged
                if not self._grid[i][j] & 0b1100000:
                    self.hide_button(i, j)
                    #in any case, add to new squares exposed
                    new_all.append((i,j))
                    if not self._grid[i][j] & 0b11111: #only check number
                        Q.append((i,j))
                    else: #if square does have number > 0, add to new_nums
                        new_nums.append((i,j))
        return new_nums, new_all

    def button_click(self, x, y):
        ret = [], []
        if not self._grid[x][y] & 0b1100000: #if not flagged or removed
            ret = [(x,y)], [(x,y)]
            self.hide_button(x, y)
            #if bomb, lose
            if self._grid[x][y] & 0b11111 > 15:
                if self._virgin: #soft rules: move bomb if first click
                    self.remove_bomb(x,y) #make not bomb
                    i = random.randint(0,self.width-1)
                    j = random.randint(0,self.height-1)
                    #make sure we don't hit this square again
                    if i==x and j==y: i=(i+1)%self.width
                    while not self.add_bomb(i,j):
                        i = random.randint(0,self.width-1)
                        j = random.randint(0,self.height-1)
                        #make sure we don't hit this square again
                        if i==x and j==y: i=(i+1)%self.width
                else:
                    self._lose(x,y)
            #if number is 0 clear space
            if not self._grid[x][y] & 0b11111: #only check number
                ret = self.clear_space(x,y)
            #if all spaces cleared, win
            if self.buttons_left == self.bomb_number:
                self._win()
            if self._virgin:
                #start timer after first click
                self._runtimer = True
                self._run_timer()
                self._virgin = False
        return ret

    def hide_button(self, x, y):
        if not self._grid[x][y] & 0b1000000: #if not removed already
            self.SCREEN.blit(self.imgs[self._grid[x][y]&0b11111],(self.SQUARE*x,self.SQUARE*y))
            self._grid[x][y] |= 0b1000000 #set removed bit
            self.buttons_left -= 1

    def button_flag(self, x, y):
        if self._grid[x][y] & 0b0100000: #if flagged
            self.SCREEN.blit(self.btn_img,(self.SQUARE*x,self.SQUARE*y))
            self._grid[x][y] &= 0b1011111 #clear flagged bit
            self.bomb_ctr += 1
            self.bombCounter.config(text=str(self.bomb_ctr))
        else:
            self.SCREEN.blit(self.flagged_img,(self.SQUARE*x,self.SQUARE*y))
            self._grid[x][y] |= 0b0100000 #set flagged bit
            self.bomb_ctr -= 1
            self.bombCounter.config(text=str(self.bomb_ctr))

    def num_click(self, x, y):
        #find number of cells flagged around this cell
        flags = 0
        for i,j in self.neighbours(x,y):
            if self._grid[i][j] & 0b0100000: #flagged
                flags += 1

        if self._grid[x][y] & 0b1111 is flags: #if right number of cells flagged (=number)
            for i,j in ((x-1,y-1),(x,y-1),(x+1,y-1),
                        (x-1,y),(x+1,y),
                        (x-1,y+1),(x,y+1),(x+1,y+1)):
                if not(i<0 or j<0 or i==self.width or j==self.height):
                    if not self._grid[i][j] & 0b0100000: #not flagged
                        self.button_click(i,j)

    def get_number(self, x, y):
        '''Return the number in the cell (x,y)
           or -1 if cell is mine, or co-ordinates are invalid'''
        if x<0 or y<0 or x>=self.width or y>=self.height: #invalid coords
            return -1
        elif self._grid[x][y] & 0b10000: #if bomb
            return -1
        else:
            return self._grid[x][y] & 0b1111 #get just number

    def is_exposed(self, x, y):
        '''Return whether this grid square has had the button removed'''
        assert x>=0 or y>=0 or x<self.width or y<self.height, 'invalid co-ordinates'
        return self._grid[x][y] & 0b1000000 #button removed bit

    def is_flagged(self, x, y):
        '''Return whether this grid square is flagged'''
        assert x>=0 or y>=0 or x<self.width or y<self.height, 'invalid co-ordinates'
        return self._grid[x][y] & 0b0100000 #flagged bit
        #assuming that if button has been removed, flagged bit will be 0
        #because we don't remove flagged buttons

    def add_bomb(self, x, y):
        '''Set (x,y) to a mine if the button has not been removed
           Returns boolean based on success of operation'''
        if self._grid[x][y] & 0b1010000: #if button removed or bomb already
            return False
        else:
            self._grid[x][y] |= 0b10000 #set bomb bit
            self._grid[x][y] &= 0b1110000 #set number to 0
            self.bombs.append((x,y))
            self.bomb_number += 1
            self.bomb_ctr += 1
            self.bombCounter.config(text=str(self.bomb_ctr))
            if self.buttons_left == self.bomb_number:
                self._win() #if the new bomb number means we win, win
            #update numbers of neighbours
            for i,j in self.neighbours(x,y):
                if not self._grid[i][j] & 0b10000: #if not bomb
                    self._grid[i][j] += 1 #increment number
                    if self._grid[i][j] & 0b1000000: #if number exposed
                        self.SCREEN.blit(self.imgs[self._grid[i][j]&0b1111],
                                         (i*self.SQUARE,j*self.SQUARE))
            return True

    def remove_bomb(self, x, y):
        '''If there is a mine in square (x,y), get rid of it
           If (x,y) is not a mine, return False
           If operation successful, return True'''
        if not self._grid[x][y] & 0b10000: #if not a bomb return false
            return False
        else:
            self._grid[x][y] &= 0b1100000 #clear bomb bit and set number to 0
            self.bombs.remove((x,y))
            self.bomb_number -= 1
            self.bomb_ctr -= 1
            self.bombCounter.config(text=str(self.bomb_ctr))
            #calculate number and update numbers of neighbours
            count = 0
            for i,j in self.neighbours(x,y):
                if not self._grid[i][j] & 0b10000: #if not bomb
                    self._grid[i][j] -= 1 #decrement number
                    if self._grid[i][j] & 0b1000000: #if number exposed show on screen
                        self.SCREEN.blit(self.imgs[self._grid[i][j]&0b1111],
                                         (i*self.SQUARE,j*self.SQUARE))
                else: #if bomb
                    count += 1
            self._grid[x][y] += count
            if self._grid[x][y] & 0b1000000: #if exposed show on screen
                self.SCREEN.blit(self.imgs[self._grid[x][y]&0b1111],(x*self.SQUARE,y*self.SQUARE))
            return True

    def __del__(self):
        pygame.quit()

if __name__=='__main__':
    root = tk.Tk()
    root.title('Minesweeper')
    root.resizable(False, False)

    #Create a game instance in the Tkinter window and run it
    #`seed` is passed to random.seed() if it is not None
    #`scale` parameter changes the size of the grid (default=2)
    #In this example, the mine (bomb) density is specified as a fraction
    # `bomb_number` can be used to say how many bombs should appear
    # or a list of co-ordinates can be passed with `bombs` to create the same game
    game = MinesweeperGame(root, width=30, height=27, bomb_density=1/8,
                           seed=None, scale=SCALE)
    #Note `seed` and `scale` have these values by default and are only included here for better documentation
    game.pack()
    root.mainloop()
