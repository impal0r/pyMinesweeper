import os, random
#don't print pygame welcome message
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

import pygame, pygame.font
from pygame.locals import *
from pygame.time import Clock
from dataclasses import dataclass
from typing import Callable
from types import MethodType

#Fix blurriness on high DPI screens in Windows
import platform
if platform.system() == 'Windows':
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
    del ctypes
del platform

# Things that could be improved in the future
# - replacing the 'New game' button with an authentic smiley face
# - making the window resizeable
# - choosing a nicer defualt font (calibri is fine...)
# - the graphical layout is hardcoded and arguably a bit janky
#   (no anchors, variable text alignment, or automatic evaluation algo)
#   However, it works well for the simple app that this is, so I'm probably not
#   changing it.

#-------------------------------- LOCAL IMPORTS --------------------------------

from settings import *
SETTINGS_FILEPATH = 'settings.json'

from gui import * #custom UI elements (buttons and text displays)

#------------------------------- MINESWEEPER APP -------------------------------

@dataclass
class DelayedAction:
    name : str
    repeat : bool
    delay_in_ms : int
    function : Callable
    args : list

    def __post_init__(self):
        self.delay_left = self.delay_in_ms

    def reset(self):
        self.__post_init__()

class MinesweeperApp:
    def __init__(self, window, settings,
                 ai_player=False, ai_player_name='', block_gui=False):
        '''block_gui: mouse input on the grid can be optionally blocked
        when an AI is playing the game. block_gui has no effect when ai_player
        is False. An AI player means any program using the API, rather than
        the graphical interface, to manipulate the game.'''
        self.window = window
        self.settings = settings
        self.has_ai_player = ai_player
        self.ai_player_name = ai_player_name
        self.block_gui = block_gui if ai_player else False
        
        segment_font_path = os.path.join(settings.font_path,
                                         'DSEG14Classic-Bold.ttf')
        self.segment_font = pygame.font.Font(segment_font_path,
                                             int(12*settings.ui_scale))
        self.default_font = pygame.font.SysFont('calibri',
                                                int(10*settings.ui_scale))
        
        self.initialised = False

        #Mechanism for delayed function calls:
        #Adding to the below list results in the call function(*args)
        # after the specified delay
        #To cancel a repeating action, remove it from self.delayed_actions manually
        # or by calling .cancel_delayed_action('name')
        #Note delays are approximate as the updates are only done every frame
        self.delayed_actions = []
        #need to initialise the above first as it is used by
        # MinesweeperGrid.__init__ below
        
        #Also allow key binding
        self.bound_keys = dict()

        # Initialise app's gui objects
        PAD = int(4 * settings.ui_scale)
        TEXTPAD = int(2.5 * settings.ui_scale)
        self.minesweeper_grid = MinesweeperGrid(
            self, window, 0, 24*settings.ui_scale,
            settings.grid_width, settings.grid_height,
            mine_density = settings.mine_density,
            mine_number = settings.mine_number,
            mine_locations = settings.mine_locations,
            scale = settings.grid_scale,
            allow_gui = not self.block_gui
        )
        self.mine_counter = TextRect(
            window, PAD, PAD, -1, -1,
            settings.lcd_background_col, settings.lcd_text_col,
            self.segment_font, '000', TEXTPAD, TEXTPAD
        ) #always three digits (padded with 0's)
        self.newgame_btn = Button(
            window, 100, PAD, -1, -1,
            settings.button_background_col, settings.button_text_col,
            settings.button_click_col, settings.button_text_col,
            settings.button_hover_col, settings.button_text_col,
            self.default_font, 'New game', TEXTPAD, TEXTPAD,
            (lambda:None) if self.block_gui else self.new_game
        )
        self.timer_display = TextRect(
            window, 200, PAD, -1, -1,
            settings.lcd_background_col, settings.lcd_text_col,
            self.segment_font, '00:00.00', TEXTPAD, TEXTPAD
        ) #get correct width by adding an extra zero. Then remove it for consistency
        self.timer_display.set_text('0:00.00')
        if self.has_ai_player:
            max_len = settings.max_name_len
            if len(self.ai_player_name) > max_len:
                self.display_ai_player_name = self.ai_player_name[:max_len-3] + ' ...'
            elif not self.ai_player_name:
                self.display_ai_player_name = 'Unnamed AI player'
            else:
                self.display_ai_player_name = self.ai_player_name
            self.ai_panel_background = Rectangle(
                window, 0, int(24*settings.ui_scale), 0, 0,
                settings.ai_panel_bg_col
            )
            self.ai_display = TextRect(
                window, 200, int(28*settings.ui_scale), -1, -1,
                None, 'black', self.default_font,
                'Currently playing: ' + self.display_ai_player_name,
                TEXTPAD, TEXTPAD
            )

        #layout calculations (and move objects to right places)
        win_size = self.evaluate_layout()
        #resize window to correct size, and set window title
        pygame.display.set_mode(win_size)
        pygame.display.set_caption('PyMinesweeper')
        #create list of gui objects, in correct z-order
        self.gui_objects = [self.mine_counter, self.newgame_btn,
                            self.timer_display, self.minesweeper_grid]
        if self.has_ai_player:
            self.gui_objects.append(self.ai_panel_background)
            self.gui_objects.append(self.ai_display)

        #Other state variables:
        #game timer
        self.time = 0 #milliseconds (pygame gives us time in ms -> easier)
        self.timer_running = False
        #boolean used for flashing the 'WIN' message
        self.flash_on = True
        #used for dragging. references object being clicked, until it's released
        self.held_obj = None
        #used for keeping track of which object mouse is hovering over
        self.hover_obj = None

        #Callback functions used by AI players
        self.lose_callback = lambda: None
        self.win_callback = lambda: None
        
        self.quit_ = False
        
        self.initialised = True

    def evaluate_layout(self):
        scale = self.settings.ui_scale
        PAD = int(4 * scale)
        LINE = int(24 * scale) #scale could be a float
        grid_w, grid_h = self.minesweeper_grid.get_size()
        btn_w = self.newgame_btn.get_width()
        timer_w = self.timer_display.get_width()
        min_w = btn_w + 2 * (PAD + timer_w + PAD)
        win_w, win_h = max(grid_w, min_w), grid_h + LINE
        if self.has_ai_player:
            win_h += LINE #accommodate ai display
##            #center ai player name display horizontally
##            ai_w = self.ai_display.get_width()
##            self.ai_display.set_pos(((win_w - ai_w) // 2, 28 * scale))
            #left-adjust ai player name display
            self.ai_display.set_pos((PAD, LINE + PAD))
            #stretch ai display background to fit
            self.ai_panel_background.set_size((win_w, int(23 * scale)))
        #center new game button horizontally
        self.newgame_btn.set_pos(((win_w - btn_w) // 2, PAD))
        #put timer display at the right edge
        self.timer_display.set_pos((win_w - timer_w - PAD, PAD))
        #center grid horizontally, and accommodate ai display
        grid_y = 2 * LINE if self.has_ai_player else LINE
        self.minesweeper_grid.set_pos(((win_w - grid_w) // 2, grid_y))
        return (win_w, win_h)

    def cancel_delayed_action(self, action_name):
        '''Cancels a delayed action by name
        If name is not unique (it should be!), first instance will be cancelled'''
        success = False
        for action in self.delayed_actions:
            if action.name == action_name:
                self.delayed_actions.remove(action)
                success = True
                break
        return success

    def add_delayed_action(self, action_name, delay_ms, function,
                           repeat=False, args=[]):
        self.delayed_actions.append(
            DelayedAction(action_name, repeat, delay_ms, function, args))

    def set_win_callback(self, function):
        '''`function` will be executed whenever the game is lost.
        It must take 1 argument, `self`,
        and is treated as a class method of this MinesweeperApp instance.
        Use to define extra custom behaviour, and/or as callback for AI players'''
        self.win_callback = MethodType(function, self)

    def set_lose_callback(self, function):
        '''`function` will be executed whenever the game is won.
        It must take 1 argument, `self`,
        and is treated as a class method of this MinesweeperApp instance.
        Use to define extra custom behaviour, and/or as callback for AI players'''
        self.lose_callback = MethodType(function, self)

    @staticmethod
    def time_to_text(time_ms):
        mins, ms_rem = divmod(time_ms, 60000)
        secs, ms_rem = divmod(ms_rem, 1000)
        centisecs = (ms_rem + 5) // 10 #round to nearest centisecond
        return '{:d}:{:0>2d}.{:0>2d}'.format(mins, secs, centisecs)

    def start_timer(self):
        self.timer_running = True

    def stop_timer(self):
        self.timer_running = False

    def reset_timer(self):
        self.timer_running = False
        self.time = 0
        self.timer_display.set_text(self.time_to_text(self.time))

    def update_mine_counter(self, num_mines):
        if self.initialised:
            self.mine_counter.set_text('{:0>3d}'.format(num_mines))

    def new_game(self):
        self.reset_timer()
        self.minesweeper_grid.new_game()
        self.cancel_delayed_action('flash-win')
        self.cancel_delayed_action('flash-lose')
        self.mine_counter.set_text('000')
        self.flash_on = True
        self.newgame_btn.colour = self.settings.button_background_col

    def _flash_endgame(self, win:bool):
        if self.flash_on:
            if win:
                self.mine_counter.set_text('000')
            self.newgame_btn.colour = self.settings.button_background_col
            self.flash_on = False
        else:
            if win:
                self.mine_counter.set_text('WIN')
            self.newgame_btn.colour = self.settings.button_flash_col
            self.flash_on = True

    def win(self):
        self.stop_timer()
        self.mine_counter.set_text('WIN')
        self.newgame_btn.colour = self.settings.button_flash_col
        self.add_delayed_action(
            'flash-win', 700, self._flash_endgame, args=[True], repeat=True
        )
        self.win_callback()

    def lose(self):
        self.stop_timer()
        self.newgame_btn.colour = self.settings.button_flash_col
        self.add_delayed_action(
            'flash-lose', 700, self._flash_endgame, args=[False], repeat=True
        )
        self.lose_callback()

    def bind_key(self, key, ctrl, shift, alt, func, args=[]):
        self.bound_keys[(key, ctrl, shift, alt)] = (func, args)

    def unbind_key(self, key, ctrl, shift, alt):
        del self.bound_keys[(key, ctrl, shift, alt)]

    def on_keydown(self, key, ctrl, shift, alt, mouse_pos):
        try:
            action = self.bound_keys[(key, ctrl, shift, alt)]
            action[0](*action[1])
        except KeyError:
            pass

    def on_keyup(self, key, ctrl, shift, alt, mouse_pos):
        pass

    def update_hover(self, pos):
        '''Should be called when mouse buttons are released'''
        #which object is mouse currently over?
        #(only care about last obj in z order)
        last_obj = None
        for obj in self.gui_objects:
            if obj.contains_coords(pos):
                last_obj = obj
        if self.hover_obj is not last_obj:
            if self.hover_obj is not None and self.hover_obj.hoverable:
                self.hover_obj.on_leave_hover(pos)
            if last_obj is not None:
                self.hover_obj = last_obj
                if last_obj.hoverable:
                    last_obj.on_hover(pos)
        if last_obj is None:
            self.hover_obj = None

    def on_mousedown(self, mouse_button, pos):
        if mouse_button == BUTTON_LEFT:
            #implement z-order by only acting on
            # last clickable object in this pos
            last_obj = None
            for obj in self.gui_objects:
                if obj.contains_coords(pos):
                    last_obj = obj
            if last_obj is not None:
                assert self.hover_obj is not None
                assert self.hover_obj is last_obj
                if last_obj.clickable:
                    last_obj.on_click(pos)
                    last_obj.is_being_clicked = True
                self.held_obj = last_obj
                self.drag_start_pos = pos
                self.started_dragging = True#False
        elif mouse_button == BUTTON_RIGHT:
            #only right click if left button is not down
            if not self.started_dragging:
                last_obj = None
                for obj in self.gui_objects:
                    if obj.clickable and obj.contains_coords(pos):
                        last_obj = obj
                if last_obj is not None:
                    if last_obj.clickable and last_obj.right_clickable:
                        last_obj.on_right_click(pos)

    def on_mousemove(self, pos):
        if self.held_obj is not None:
            if not self.held_obj.contains_coords(pos):
                self.held_obj.is_being_clicked = False
        else:
            self.update_hover(pos)

    def on_mouseup(self, mouse_button, pos):
        if mouse_button == BUTTON_LEFT:
            if self.held_obj is not None:
                self.held_obj.is_being_clicked = False
                self.held_obj = None
                self.started_dragging = False
            self.update_hover(pos)

    def update(self, time_passed_ms):
        '''Return 0 or False to keep mainloop going,
        return True or any other number to exit the app'''
        if self.timer_running:
            self.time += time_passed_ms
            self.timer_display.set_text(self.time_to_text(self.time))
        old_delayed_actions = self.delayed_actions.copy()
        spent_delayed_actions = []
        for delayed_action in old_delayed_actions:
            delayed_action.delay_left -= time_passed_ms
            if delayed_action.delay_left <= 0:
                delayed_action.function(*delayed_action.args)
                if delayed_action.repeat:
                    delayed_action.reset()
                else:
                    spent_delayed_actions.append(delayed_action.name)
        for name in spent_delayed_actions:
            self.cancel_delayed_action(name)
        
        return self.quit_

    def draw(self):
        self.window.fill(self.settings.background_col)
        for obj in self.gui_objects:
            obj.draw()

    def run(self):
        clock = Clock()
        go = True
        while go:
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    go = False
                    break

                #handle keypresses
                elif event.type == KEYDOWN:
                    mods = pygame.key.get_mods()
                    ctrl, shift, alt = mods & KMOD_CTRL, mods & KMOD_SHIFT, mods & KMOD_ALT
                    self.on_keydown(event.key, ctrl, shift, alt, pygame.mouse.get_pos())

                elif event.type == KEYUP:
                    mods = pygame.key.get_mods()
                    ctrl, shift, alt = mods & KMOD_CTRL, mods & KMOD_SHIFT, mods & KMOD_ALT
                    self.on_keyup(event.key, ctrl, shift, alt, pygame.mouse.get_pos())

                #handle mouse movement/buttons
                elif event.type == MOUSEMOTION:
                    self.on_mousemove(event.pos)

                elif event.type == MOUSEBUTTONDOWN:
                    self.on_mousedown(event.button, event.pos)

                elif event.type == MOUSEBUTTONUP:
                    self.on_mouseup(event.button, event.pos)

            #update
            if (not go) or self.update(clock.get_time()):
                break

            #render
            self.draw()
            pygame.display.update()

            #wait for next frame
            clock.tick(self.settings.max_framerate)

    def quit(self):
        self.quit_ = True

#------------------------------- MINESWEEPER GRID ------------------------------

class MineGenerator:
    def __init__(self, grid_width, grid_height, initial_seed=None):
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.num_cells = grid_width * grid_height
        if initial_seed is not None:
            random.seed(seed)

    def use_settings(self, mine_locations=None, mine_number=None, mine_density=None):
        '''
        mine_locations - a list of squares that must be mined
        mine_number    - the total number of mines
        mine_density   - the proportion of squares that should be mined
        Returns -> None
        Notes:
        1. All three arguments are optional but at least one must be specified.
        2. If both mine_number and mine_density are given, mine_density is ignored.
        3. If both mine_locations and mine_number are given, mine_number must be at
        least len(mine_locations). Extra mines will be randomly placed. The same applies
        for mine_density except mine number is calculated as
        num = mine_density * (grid_width * grid_height).
        4. If mine_locations is not given, mines will be randomly placed.
        5. Call .get_mines() to retrieve generated mine locations.
        '''

        self.mine_locations = mine_locations
        if self.mine_locations is None:
            self.mine_locations = []

        self.num_random_mines = 0
        if mine_number is not None:
            assert 0 <= mine_number <= self.num_cells
            self.total_mine_number = mine_number
            self.num_random_mines = self.total_mine_number
        elif mine_density is not None:
            assert 0.0 <= mine_density <= 1.0
            self.total_mine_number = round(mine_density * self.num_cells)
            self.num_random_mines = self.total_mine_number
        if mine_locations is not None:
            for mine_loc in mine_locations:
                assert 0 <= mine_loc[0] < self.grid_width
                assert 0 <= mine_loc[1] < self.grid_height
                mine_loc = tuple(mine_loc)
            if self.num_random_mines:
                self.num_random_mines -= len(mine_locations)
            else:
                self.total_mine_number = len(mine_locations)
        assert self.num_random_mines >= 0, 'See note 3 in function docstring'

        if self.num_random_mines > 0:
            #get list of potential mine locations
            self.potential_mines = []
            for i in range(self.grid_width):
                for j in range(self.grid_height):
                    if (i, j) not in self.mine_locations:
                        self.potential_mines.append((i, j))

    def get_mines(self):
        '''-> list of 2-tuples representing co-ordinates of all mines.
        .use_settings(...) must be called first
        If random generation is required, a new set of mines will be generated
        every time this function is called.'''
        mines = self.mine_locations.copy()
        if self.num_random_mines > 0:
            #take a random sample and add to mine locations
            mines.extend(random.sample(self.potential_mines,
                                       self.num_random_mines))
        return mines

class MinesweeperGrid:
    # if True, will raise exceptions on invalid mines list passes to
    #  __init__ or reset
    # Use for debugging purposes
    MINE_LIST_ERRORS = False
    
    IMG_SIZE = 16 #images are squares with side length of IMG_SIZE

    def __init__(self, app, window, pos_x, pos_y, grid_width, grid_height,
                 mine_number=None, mine_density=0.17, mine_locations=None,
                 seed=None, scale=2, allow_gui=True):
        '''
        width and height are in squares (aka tiles),
        the 16x16px tiles are scaled by `scale` (useful for HDPI displays).
        If `mine_locations` (list of 2-tuples of integer coords) is specified,
        mines will be placed at these coordinates. Otherwise they will be
        randomly generated based on either mine_density (proportion of tiles
        with a mine) or mine_number. In this case `seed` is passed to random.seed()
        if it is not None.
        '''
        # GUI Interaction through the App class
        self.app = app
        self.window = window
        self.clickable = True
        self.right_clickable = True
        self.hoverable = False
        self.draggable = False
        self.is_being_clicked = False #automatically modified by app
        #graphical interface interactions can be blocked by the app
        # if the player is an AI using the API functions
        self.allow_gui = allow_gui

        # Other parameters
        self.grid_width = int(grid_width)
        self.grid_height = int(grid_height)
        assert self.grid_width > 0 and self.grid_height > 0,\
               'Grid dimensions must be positive'
        self.generator = MineGenerator(self.grid_width, self.grid_height,
                                       initial_seed=seed)
        self.generator.use_settings(mine_locations, mine_number, mine_density)

        # Setup before .neighbours function can be used
        self._saved_neighbours = {}
        self._square_filter = \
            lambda sq: not(sq[0] < 0 or sq[1] < 0 or
                           sq[0] == self.grid_width or sq[1] == self.grid_height)

        # Set up visual grid
        self.scale = scale
        self.SQUARE = round(self.IMG_SIZE * scale + .5) #size of square in px (round up)
        px_width = self.SQUARE * self.grid_width    #height in px on screen
        px_height = self.SQUARE * self.grid_height  #width  of actual game
        self.rect = [pos_x, pos_y, px_width, px_height]
        # load images as Surface objects
        self._load_images()

        # Set up logical grid & gameplay variables
        self.new_game()

        #MinesweeperGrid initialised before the mine counter display
        #So add a delayed action with zero delay - this will be run next time
        # app.update() is called, which will be before the first draw() call,
        # and after everything is initialised
        self.app.add_delayed_action('initial-update-mine-counter',
            0, self.app.update_mine_counter, args=[self.mine_counter]
        )

    def _load_images(self):
        size = (self.SQUARE, self.SQUARE)
        scale = pygame.transform.scale
        load = pygame.image.load
        img_path = self.app.settings.image_path
        mkpath = lambda fname: os.path.join(img_path, fname)
        clear = scale(load(mkpath('clear.png')), size)
        _1    = scale(load(mkpath('1.png')), size)
        _2    = scale(load(mkpath('2.png')), size)
        _3    = scale(load(mkpath('3.png')), size)
        _4    = scale(load(mkpath('4.png')), size)
        _5    = scale(load(mkpath('5.png')), size)
        _6    = scale(load(mkpath('6.png')), size)
        _7    = scale(load(mkpath('7.png')), size)
        _8    = scale(load(mkpath('8.png')), size)
        bomb  = scale(load(mkpath('bomb.png')), size)
        self.imgs = (clear, _1, _2, _3, _4, _5, _6, _7, _8,
                     *(None for i in range(7)), bomb)
        #index into imgs list will give image for that number
        self.xbomb_img   = scale(load(mkpath('xbomb.png')), size)
        self.redbomb_img = scale(load(mkpath('redbomb.png')), size)
        self.flagged_img = scale(load(mkpath('flagged.png')), size)
        self.btn_img     = scale(load(mkpath('btn.png')), size)

    def new_game(self, mine_locations=None, mine_number=None, mine_density=None):
        # Mine generation settings
        if (mine_number is not None
            or mine_density is not None
            or mine_locations is not None):
            self.generator.use_settings(mine_locations,
                                        mine_number,
                                        mine_density)

        # Mine generation
        self.mines = self.generator.get_mines()
        self.mine_number = len(self.mines)
        self._update_mine_counter(self.mine_number)

        #For each entry in the grid, counting from least significant bit:
        #bits 0-3: adjacent mine number (#mines in adj. squares, from 0-8)
        #          should be zeroed for a mine
        #bit 4: is square mined?
        #bit 5: flagged?
        #bit 6: opened?
        self._grid = [[0 for j in range(self.grid_height)]
                      for i in range(self.grid_width)]
        for mined_square in self.mines:
            #set the flag for a mine
            self._grid[mined_square[0]][mined_square[1]] = 16
            #add to the counts of neighbouring unmined squares
            for i, j in self.neighbours(*mined_square):
                if (i, j) not in self.mines:
                    self._grid[i][j] += 1
        
        # Gameplay
        self.buttons_left = self.grid_width * self.grid_height
        self.is_virgin = True #set to False when player makes first move
        self.won = False
        self.lost = False

    #****************** UTILITY FUNCTIONS FOR GAME MECHANICS *******************

    def neighbours(self, x, y): #NB: Must return an iterable.
        '''Returns an iterable of two-tuples representing
        the squares adjacent to (x, y) by a side or a corner'''
        if (x, y) in self._saved_neighbours:
            return self._saved_neighbours[x, y]
        else:
            f = filter(self._square_filter, ((x-1,y-1),(x,y-1),
                                             (x+1,y-1),(x-1,y),(x+1,y),
                                             (x-1,y+1),(x,y+1),(x+1,y+1)))
            self._saved_neighbours[x,y] = f = tuple(f)
            return f

    def _win(self):
        self.won = True
        self.app.win()

    def _lose(self, x, y): #x and y are coordinates of last mine clicked
        self.lost = True
        self.app.lose()

    def check_valid_coords(self, x, y):
        is_valid = True
        error = ''
        if x % 1 or y % 1:
            is_valid = False
            error = 'coords should be integers'
        elif (x < 0 or x >= self.grid_width or
              y < 0 or y >= self.grid_height):
            is_valid = False
            error = f'invalid co-ordinates {x}, {y}'
        return is_valid, error

    def _update_mine_counter(self, new_mine_counter):
        '''Should always be used when changing the mine counter,
        as it also calls back to the app to update the display'''
        self.mine_counter = new_mine_counter
        self.app.update_mine_counter(new_mine_counter)

    def _increment_mine_counter(self):
        self._update_mine_counter(self.mine_counter + 1)

    def _decrement_mine_counter(self):
        self._update_mine_counter(self.mine_counter - 1)

    def _open(self, x, y):
        '''Opens a single square. No input sanitisation or first click protection'''
        if not self._grid[x][y] & 0b1000000: #if not opened already
            self._grid[x][y] |= 0b1000000 #set 'opened' bit
            self.buttons_left -= 1

    def _is_opened(self, x, y):
        '''No input sanitisation'''
        return self._grid[x][y] & 0b1000000 #'opened' bit

    def _is_mine(self, x, y):
        '''No input sanitisation'''
        return self._grid[x][y] & 0b10000 #'mined' bit

    def _get_number(self, x, y):
        '''No input sanitisation; will return number even if square is unopened
        If square is mined, will return -1'''
        if self._is_mine(x, y):
            return -1
        else:
            return self._grid[x][y] & 0b1111

    def _add_mine(self, x, y):
        '''Put a mine at (x, y) if the square is still unopened
           Returns True if successful, False if not'''
        if self._grid[x][y] & 0b1010000: #if button removed or mined already
            return False
        else:
            self._grid[x][y] |= 0b10000 #set 'mined' bit
            self._grid[x][y] &= 0b1110000 #set number to 0
            self.mines.append((x, y))
            self.mine_number += 1
            self._increment_mine_counter()
            #if the mine was added on the last unopened square, then you win
            if self.buttons_left == self.mine_number:
                self._win() 
            #update numbers of neighbours
            for i, j in self.neighbours(x, y):
                if not self._grid[i][j] & 0b10000: #if not mined
                    self._grid[i][j] += 1 #increment number
            return True

    def _remove_mine(self, x, y):
        '''If there is a mine in square (x, y), get rid of it
           If (x, y) is not a mine, return False
           If operation successful, return True'''
        if not self._grid[x][y] & 0b10000: #if not a mine return false
            return False
        else:
            self._grid[x][y] &= 0b1100000 #clear 'mined' bit and set number to 0
            self.mines.remove((x, y))
            self.mine_number -= 1
            self._decrement_mine_counter()
            #calculate number and update numbers of neighbours
            count = 0
            for i,j in self.neighbours(x,y):
                if not self._grid[i][j] & 0b10000: #if not mine
                    self._grid[i][j] -= 1 #decrement number
                else: #if mined
                    count += 1
            self._grid[x][y] += count
            return True

    def _splash(self, x, y):
        '''Should be called on an 'empty' square with no neighbouring mines.
        Opens all neighbouring empty squares and their neighbours'''
        #self._open(x, y)
        new_all = [(x, y)]
        new_nums = []
        Q = [(x,y)]
        while Q:
            for i,j in self.neighbours(*Q.pop(0)):
                #if not already exposed OR flagged
                if not self._grid[i][j] & 0b1100000:
                    self._open(i, j)
                    #in any case, add to new squares exposed
                    new_all.append((i,j))
                    if not self._grid[i][j] & 0b11111: #only check number
                        Q.append((i,j))
                    else: #if square does have number > 0, add to new_nums
                        new_nums.append((i,j))
        return new_nums, new_all

    def _attempt_chord_with_splash(self, x, y):
        '''Attempts to chord at square (x, y).
        If an empty (number=0) square is opened, splash automatically applied.
        Should only be called on an opened square (not checked)'''
        #find number of cells flagged around this cell
        num_flags = 0
        for i, j in self.neighbours(x, y):
            if self._is_flagged(i, j):
                num_flags += 1
        #if num flagged neighbours == number in square,
        # open all the unflagged neighbours
        if self._get_number(x, y) == num_flags:
            for i, j in self.neighbours(x, y):
                if not self._is_flagged(i, j):
                    self._open(i, j)
                    num = self._get_number(i, j) #return -1 for mines
                    if num == -1:
                        self._lose(i, j)
                        break
                    elif num == 0:
                        self._splash(i, j)
        if self.buttons_left == self.mine_number:
            self._win()

    def _is_flagged(self, x, y):
        '''No input sanitisation'''
        return self._grid[x][y] & 0b0100000 #flagged bit
        #if square is opened, flagged bit should be 0

    def _set_flag(self, x, y):
        '''No input sanitisation. Updates mine counter'''
        if not self._is_flagged(x, y):
            self._decrement_mine_counter()
        self._grid[x][y] |= 0b0100000 #set 'flagged' bit

    def _clear_flag(self, x, y):
        '''No input sanitisation. Updates mine counter'''
        if self._is_flagged(x, y):
            self._increment_mine_counter()
        self._grid[x][y] &= 0b1011111 #clear 'flagged' bit

    def _toggle_flag(self, x, y):
        '''No input sanitisation. Updates mine counter'''
        if self._is_flagged(x, y):
            self._clear_flag(x, y)
        else:
            self._set_flag(x, y)

    #******************** API FUNCTIONS FOR PLAYING THE GAME *******************

    def get_mine_counter(self):
        '''Returns the number shown in the top left corner'''
        return self.mine_counter

    def get_mine_number(self):
        '''Returns the total number of mines in the grid'''
        return self.mine_number

    def is_opened(self, x, y):
        '''Return whether this grid square has been opened
        (ie number is visible, either because it has been clicked,
        or it is part of a large opening)'''
        valid, error = self.check_valid_coords(x, y)
        if not valid:
            raise AssertionError(error)
        return self._is_opened(x, y)

    def is_flagged(self, x, y):
        '''Returns whether this grid square is flagged'''
        valid, error = self.check_valid_coords(x, y)
        if not valid:
            raise AssertionError(error)
        return self._is_flagged(x, y)

    def set_flag(self, x, y):
        '''Sets flag on square. Should only be called on an unopened square'''
        valid, error = self.check_valid_coords(x, y)
        if not valid:
            raise AssertionError(error)
        if self._is_opened(x, y):
            raise AssertionError(f'square {x}, {y} is opened. Cannot set flag')
        self._set_flag(x, y)

    def clear_flag(self, x, y):
        '''Clears flag from square. Should only be called on an unopened square'''
        valid, error = self.check_valid_coords(x, y)
        if not valid:
            raise AssertionError(error)
        if self._is_opened(x, y):
            raise AssertionError(f'square {x}, {y} is opened. Cannot set/clear flag')
        self._clear_flag(x, y)

    def toggle_flag(self, x, y):
        '''Toggles flag on square. Should only be called on an unopened square'''
        valid, error = self.check_valid_coords(x, y)
        if not valid:
            raise AssertionError(error)
        if self._is_opened(x, y):
            raise AssertionError(f'square {x}, {y} is opened. Cannot toggle flag')
        self._toggle_flag()

    def get_number(self, x, y):
        '''Return the number in the square (x, y).
        Should only be called on an opened square'''
        valid, error = self.check_valid_coords(x, y)
        if not valid:
            raise AssertionError(error)
        if not self._is_opened(x, y):
            raise AssertionError(f'square {x}, {y} is unopened. Cannot get number')
        return self._get_number(x, y)

    def open_square(self, x, y, do_splash=False):
        '''Open an unopened square.
        -> 1 if you opened a mined square, else 0'''
        valid, error = self.check_valid_coords(x, y)
        if not valid:
            raise AssertionError(error)
        if self._is_opened(x, y):
            raise AssertionError(f'square {x}, {y} is already opened')
        if self._is_flagged(x, y):
            raise AssertionError(f'flagged square {x}, {y} cannot be opened')
        
        self._open(x, y)
##        ret = [(x, y)], [(x, y)]

        lost = False
        #if you clicked on a mine, you lose
        if self._is_mine(x, y):
            #BUT if this is the first click, the game will
            # move the mine for you because it's nice :)
            if (self.is_virgin and
                self.mine_number < self.grid_width * self.grid_height):
                self._remove_mine(x, y) #make not mine
                #random new square for this mine
                i = random.randint(0, self.grid_width - 1)
                j = random.randint(0, self.grid_height - 1)
                #make sure we don't put it back in the same square
                if (i, j) == (x, y):
                    i = (i + 1) % self.width
                #keep trying until we find a square without a mine in it
                while not self._add_mine(i, j):
                    i = random.randint(0, self.grid_width - 1)
                    j = random.randint(0, self.grid_height - 1)
                    if (i, j) == (x, y):
                        i = (i + 1) % self.grid_width
            else:
                self._lose(x, y)
                lost = True
        #if number is 0, and splash enabled, clear the whole opening
        if do_splash and self._get_number(x, y) == 0:
##            ret = self._splash(x, y)
            self._splash(x, y)
        #if all unmined cells are opened, then you win
        if self.buttons_left == self.mine_number:
            self._win()
        #if this is the player's first move, start the timer
        if self.is_virgin:
            #start timer after first click
            self.app.reset_timer() #sanity check the timer to zero
            self.app.start_timer()
            self.is_virgin = False
##        return ret

        return 1 if lost else 0

    def open_square_with_splash(self, x, y):
        return self.open_square(x, y, do_splash=True)

    def get_grid(self, output_grid):
        '''Copy the grid (as the player sees it) to output_grid.
        Modifies output_grid in-place, placing -1 for unopened cells,
        -2 for flagged cells, and the cell's number for opened cells.
        output_grid should already have the correct dimensions.
        Should only be used while game is in progress (not won or lost)'''
        def convert_code(internal_code):
            if internal_code & 0b1000000: #is opened
                return internal_code & 0b1111 #number
            elif internal_code & 0b100000: #is flagged
                return -2
            else:
                return -1
            #no cells should be opened and mined
        for i in range(self.grid_width):
            for j in range(self.grid_height):
                output_grid[i][j] = convert_code(self._grid[i][j])

    #****************************** GUI FUNCTIONS ******************************

    def get_pos(self):
        '''Window pixel co-ordinate of the top left corner
        -> (x, y)'''
        return self.rect[0:2]
    def set_pos(self, pos):
        '''Move the grid. See MinesweeperGrid.get_pos()'''
        self.rect[0], self.rect[1] = pos

    def get_size(self):
        '''Returns the size of the grid in pixels
        -> (width, height)'''
        return self.rect[2:]

    def contains_coords(self, pos):
        return (self.rect[0] <= pos[0] < self.rect[0] + self.rect[2] and
                self.rect[1] <= pos[1] < self.rect[1] + self.rect[3])

    def pos_to_square(self, mouse_pos):
        return ((mouse_pos[0] - self.rect[0]) // self.SQUARE,
                (mouse_pos[1] - self.rect[1]) // self.SQUARE)

    def square_to_pos(self, x, y):
        return (self.rect[0] + self.SQUARE * x,
                self.rect[1] + self.SQUARE * y)

    def on_click(self, pos):
        '''Called on left click only (ie mouse button down)'''
        if self.allow_gui:
            if not (self.won or self.lost):
                square = self.pos_to_square(pos)
                if self._is_opened(*square):
                    self._attempt_chord_with_splash(*square)
                elif not self._is_flagged(*square):
                    self.open_square_with_splash(*square)

    def on_right_click(self, pos):
        '''Called on right mouse button down'''
        if self.allow_gui:
            if not (self.won or self.lost):
                square = self.pos_to_square(pos)
                if self._is_opened(*square):
                    self._attempt_chord_with_splash(*square)
                else:
                    self._toggle_flag(*square)

    def draw(self):
        for i in range(self.grid_width):
            for j in range(self.grid_height):
                if self.lost and self._is_mine(i, j):
                    img = self.redbomb_img
                elif self.lost and self._is_flagged(i, j):
                    img = self.xbomb_img
                else:
                    if self._is_opened(i, j):
                        num = self._get_number(i, j)
                        img = self.imgs[num]
                    elif self._is_flagged(i, j):
                        img = self.flagged_img
                    else:
                        img = self.btn_img
                self.window.blit(img, self.square_to_pos(i, j))

def open_all(minesweeper_grid):
    '''For demonstration purposes only'''
    for i in range(minesweeper_grid.grid_width):
        for j in range(minesweeper_grid.grid_height):
            minesweeper_grid._open(i, j)

#------------------------------------ MAINLOOP ---------------------------------

if __name__ == '__main__':
    pygame.init()
    pygame.font.init()
    window = pygame.display.set_mode((800, 500))

    settings = Settings(SETTINGS_FILEPATH)

    ############################
    # Only uncomment the 2 lines below if adding or removing a setting in Settings,
    # and you need to change the structure of the settings.json file.
    # To do this:
    #   1. change Settings.restore_default() and Settings.save_to_file()
    #      to save your new setting with its default value
    #   2. uncomment the two lines below and run this code
    #   3. comment out the two lines below and
    #      change Settings.load_from_file() to load your new setting
    #   4. run this file again and check that the program works as expected

##    settings.restore_default()
##    settings.save_to_file()

    ############################

    app = MinesweeperApp(window, settings)
    app.run()
    pygame.quit()


