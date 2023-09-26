import numpy as np
import math, itertools

class GroupNode:
    #node in a graph structure representing the cell groups and their intersections
    #edges are bidirectional
    def __init__(self, cells, num_mines, group_i):
        self.cells = cells
        self.num_mines = num_mines
        self.id = group_i
        self.edges = [] #contains references to other GroupNode's
    def add_edge(self, edge):
        #possible TODO: check for duplicates (shouldn't be neccesary at the moment)
        self.edges.append(edge)
    def remove_edge(self, edge):
        #possible TODO: remove duplicates too
        self.edges.remove(edge)
    def num_edges(self):
        return len(self.edges)
    def __repr__(self):
        return "GroupNode(" + ', '.join(
            (repr(self.cells), repr(self.num_mines), str(self.id),
             'edges=('+','.join(str(g.id) for g in self.edges)+'))'
        ))

def analyse_with_ruleset(grid, num_mines, debug=False, verbose=False):
    '''Determine which cells definitely do/don't contain mines, and consolidate
    the information we know about the rest in `cell_groups`. If position is
    impossible, False is returned as the first value in the tuple.
    -> is_possible, unexplored_cells, cell_groups, sure_mine_positions, sure_safe_positions'''
    if debug:
        print(f'analyse_with_ruleset() called with debug output, and {verbose = }')
    #make a list of unexplored cells
    unexplored_cells = []
    sure_mine_positions = set()
    for (i, j), val in np.ndenumerate(grid):
        if val == -1:
            unexplored_cells.append((i, j))
        elif val == -2:
            sure_mine_positions.add(len(unexplored_cells))
            unexplored_cells.append((i, j))

    def get_adjacent_for_group(i, j):
         #returns a set of indices of unexplored cells adjacent to (i, j)
        adj = set()
        for k, l in ((i-1,j-1), (i-1,j), (i-1,j+1), (i, j-1), (i,j+1),
                     (i+1, j-1), (i+1, j), (i+1,j+1)):
            if (0 <= k < grid.shape[0] and 0 <= l < grid.shape[1]
                and grid[k, l] in (-1, -2)):
                adj.add(unexplored_cells.index((k, l)))
        return adj

    #make a list of groups (they encompass the information given to us by
    # the numbers in explored cells)
    cell_groups = dict()
    cell_groups_list = []
    group_i = 0
    for (i, j), val in np.ndenumerate(grid):
        if val > 0:
            new_group = GroupNode(get_adjacent_for_group(i, j), val, group_i)
            if new_group not in cell_groups_list:
                cell_groups[group_i] = new_group
                cell_groups_list.append(new_group)
                group_i += 1

    #add 'hyper'links between groups that intersect (connect graph nodes with edges)
    for i, group in enumerate(cell_groups_list):
        for other_group in cell_groups_list[i+1:]:
            if group.cells & other_group.cells: #if there is an intersection
                group.add_edge(other_group)
                other_group.add_edge(group)
    del cell_groups_list

    #Simplify the problem by finding sure locations of mines (and safe cells), using a simple ruleset
    # Note this ruleset will not always find all sure mined/safe positions - it is not mathematically sufficient.
    # However it will always mark positions correctly, and is sufficient to solve the vast majority of cases.
    sure_mine_positions = sure_mine_positions #prob = 1
    sure_safe_positions = set()               #prob = 0
    active_groups = list(range(group_i))#[g.id for g in cell_groups_list] #a queue
    #keep going until the queue is empty
    while active_groups:
        gid = active_groups.pop(0)
        try:
            group = cell_groups[gid]
        except KeyError:
            continue
        delete = False
        done_sth = False
        #update group with previously found mines and safe positions
        #(this isn't done straight away when sure mine/safe positions updated - lazy update)
        xm = group.cells & sure_mine_positions
        xs = group.cells & sure_safe_positions
        group.cells = group.cells - xm - xs
        group.num_mines -= len(xm)
        if xm or xs:
            done_sth = True
        #"checks for triviality"
        if len(group.cells) == group.num_mines: #number of cells equals number of mines -> they are all mines
            delete = True
            done_sth = True
            sure_mine_positions.update(group.cells)
        elif len(group.cells) == 0: #empty group
            delete = True
            done_sth = True
        elif group.num_mines == 0: #group with no mines
            sure_safe_positions.update(group.cells)
            delete = True
            done_sth = True
        #rules involving intersecting groups
        else:
            #Constructing a new list from group.edges (a list) in the top line of the for loop avoids RuntimeErrors
            #when we try to remove items of group.edges ("set size changed during iteration")
            # - we check if groups still intersect in this for loop, and delete edges if they don't.
            #In Python's internals, this new list is constructed once at the start of the for loop,
            #making it a snapshot of group.edges before the loop runs. This means we can iterate over all the edges
            #originally in the set, while being allowed to delete some of them.
            for other_group in list(group.edges): 
                #check if they still intersect (lazy update of graph edges)
                if not (group.cells & other_group.cells):
                    group.remove_edge(other_group)
                    other_group.remove_edge(group)
                    continue
                #if group is a superset of another
                if group.cells.issuperset(other_group.cells):
                    if group.num_mines == other_group.num_mines:
                        #numbers equal: the bigger group is spurious
                        sure_safe_positions.update(group.cells - other_group.cells)
                        delete = True
                        done_sth = True
                    elif group.num_mines - other_group.num_mines == len(group.cells) - len(other_group.cells):
                        #difference in numbers = difference in sizes: difference is all mines
                        sure_mine_positions.update(group.cells - other_group.cells)
                        delete = True
                        done_sth = True
                    else: #otherwise: split to avoid overlap
                        group.cells -= other_group.cells
                        group.num_mines -= other_group.num_mines
                        done_sth = True
                #check for another special condition ("1 of 2, 2 of 3")
                else:
                    x = group.cells & other_group.cells #set intersection
                    if (group.num_mines == len(x) - 1 and other_group.num_mines == len(other_group.cells - x) + group.num_mines):
                        sure_mine_positions.update(other_tail := other_group.cells - x)
                        other_group.cells -= other_tail
                        other_group.num_mines -= len(other_tail)
                        sure_safe_positions.update(group.cells - x)
                        delete = True
                        done_sth = True
        if delete:
            del cell_groups[group.id]
            for other_group in group.edges:
                other_group.remove_edge(group)
        if done_sth:
            if not delete:
                active_groups.append(group.id)
            for other_group in group.edges:
                active_groups.append(other_group.id)
    
    cell_groups = [item[1] for item in cell_groups.items()] #convert back to list
    
    if debug and verbose:
        print('Cell groups:', cell_groups)
        print('Sure mine positions:', sure_mine_positions)
        print('Sure safe positions:', sure_safe_positions)
    
    num_mines_unsure = num_mines - len(sure_mine_positions)
    if num_mines_unsure < 0:
        if debug:
            print('not enough mines for sure mine positions')
        return False, None, None, None, None

    return True, unexplored_cells, cell_groups, sure_mine_positions, sure_safe_positions

def estimate_probs(grid, unexplored_cells, cell_groups, num_mines_unsure,
                   sure_mine_positions, sure_safe_positions):
    '''Estimate probability of each square being a mine.'''
    mine_probs = np.zeros_like(grid, dtype=float)
    #very very simple but vaguely gets ok numbers
    cell_groups = list(cell_groups)
    cell_groups.sort(key=lambda g: g.num_mines, reverse=True)
    for group in cell_groups:
        p = group.num_mines / len(group.cells)
        for cell_index in group.cells:
            cell_coord = unexplored_cells[cell_index]
            mine_probs[cell_coord] = p
    #which cells are not adjacent to any opened cells?
    remaining_cells = (set(range(len(unexplored_cells))) -
                       set(sure_mine_positions) - set(sure_safe_positions))
    remaining_cells -= set().union(*(g.cells for g in cell_groups))
    num_remaining_cells = len(remaining_cells)
    if num_remaining_cells:
        #how to estimate probability of these being mined?
        #below code overestimates it
        num_mines_remaining = num_mines_unsure - int(np.sum(mine_probs))
        p = num_mines_remaining / num_remaining_cells
        for cell_index in remaining_cells:
            cell_coord = unexplored_cells[cell_index]
            mine_probs[cell_coord] = p
    #already mined & explored cells
    for cell_i in sure_mine_positions:
        i, j = unexplored_cells[cell_i]
        mine_probs[i, j] = 1.0
    for (i, j), val in np.ndenumerate(grid):
        if val not in (-1, -2): #-1: unexplored cell, -2: flagged cell, all others are explored
            mine_probs[i, j] = 2.0 #will never be the lowest probability
##    from pprint import pprint
##    pprint(mine_probs)
    return mine_probs

class BasicRulesetAI:
    name = 'Basic Ruleset AI'
    def __init__(self, move_delay=50, newgame_delay=1000, num_games=None):
        self.move_delay = move_delay #limited to 1 move per frame
        self.newgame_delay = newgame_delay
        self.stopped = True
        self.win_count = 0
        self.loss_count = 0
        #Will stop after this number of games (or go forever if is None)
        self.num_games = num_games

        self.app = None
        self.game = None
        self.attached = False

        self.grid = None
        self.to_flag = []
        self.to_open = []

    def reset_solver(self):
        self.grid = np.zeros((self.game.grid_width, self.game.grid_height),
                             dtype=int)
        self.to_flag = []
        self.to_open = []

    def attach(self, minesweeper_app):
        self.app = minesweeper_app
        self.game = minesweeper_app.minesweeper_grid
        self.attached = True
        self.reset_solver()
        
        self.app.bind_key(K_SPACE, False, False, False, self.pause_play)
        self.app.bind_key(K_PERIOD, False, False, False, self.single_move_if_stopped)
        self.app.set_win_callback(lambda app_self: self.reset_solver())
        self.app.set_lose_callback(lambda app_self: self.reset_solver())

    def _clean_lists(self):
        i = 0
        while i < len(self.to_open):
            j = self.to_open[i]
            x, y = self.unexplored_cells[j]
            if self.game.is_opened(x, y):
                self.to_open.remove(j)
            else:
                i += 1
        i = 0
        while i < len(self.to_flag):
            j = self.to_flag[i]
            x, y = self.unexplored_cells[j]
            if self.game.is_flagged(x, y):
                self.to_flag.remove(j)
            else:
                i += 1

    def single_move(self):
        if not (self.to_flag or self.to_open):
            self.game.get_grid(self.grid)
            num_mines = self.game.get_mine_number()
            (is_possible, unexplored_cells, cell_groups,
             sure_mine_positions, sure_safe_positions
            ) = analyse_with_ruleset(self.grid, num_mines)
            if not is_possible:
                raise Exception("No possible positions: there's been a mistake")
            self.unexplored_cells = unexplored_cells
            self.sure_mine_positions = sure_mine_positions
            self.to_flag = list(sure_mine_positions)
            self.sure_safe_positions = sure_safe_positions
            self.to_open = list(sure_safe_positions)
            self.cell_groups = cell_groups
            #remove already flagged/open squares from to_flag and to_open
            self._clean_lists()

        if self.to_flag:
            x, y = self.unexplored_cells[self.to_flag.pop()]
            self.game.set_flag(x, y)
        elif self.to_open:
            x, y = self.unexplored_cells[self.to_open.pop()]
            self.game.open_square_with_splash(x, y)
            self._clean_lists()
        else:
            #need to guess - try to find a low-risk square without
            # knowing exact probabilities
            mine_probs = estimate_probs(
                self.grid, self.unexplored_cells, self.cell_groups,
                self.game.get_mine_counter(),
                self.sure_mine_positions, self.sure_safe_positions
            )
            min_prob = np.min(mine_probs)
            x_indices, y_indices = np.where(mine_probs == min_prob)
            i = random.randint(0, len(x_indices)-1)
            #print('guess', min_prob)
            self.game.open_square_with_splash(x_indices[i], y_indices[i])
            self._clean_lists()
        if self.game.lost:
            self.loss_count += 1
        if self.game.won:
            self.win_count += 1
        if self.game.lost or self.game.won and not self.stopped:
            self.stop()
            #start a new game
            if (self.num_games is None
                or self.win_count + self.loss_count < self.num_games):
                self.delayed_new_game()
            if self.win_count + self.loss_count == self.num_games:
                print('Wins:', ai_player.win_count)
                print('Losses:', ai_player.loss_count)

    def start(self):
        self.app.add_delayed_action(self.name + ': running',
            self.move_delay, self.single_move, repeat=True
        )
        self.stopped = False

    def stop(self):
        self.app.cancel_delayed_action(self.name + ': running')
        self.stopped = True

    def pause_play(self):
        if not (self.game.won or self.game.lost):
            if self.stopped:
                self.start()
            else:
                self.stop()

    def single_move_if_stopped(self):
        if not (self.game.won or self.game.lost):
            if self.stopped:
                self.single_move()

    def new_game(self):
        self.app.new_game()
##        self.reset_solver() #not needed because we have set win/lose callbacks
        self.app.add_delayed_action(self.name + ': solve new game',
            100, self.start
        )

    def delayed_new_game(self):
        self.app.add_delayed_action(self.name + ': delay for new game',
            self.newgame_delay, self.new_game)

if __name__ == '__main__':
    from minesweeper import *
    pygame.init()
    pygame.font.init()
    window = pygame.display.set_mode((800, 500))
    settings = Settings(SETTINGS_FILEPATH)
    #Change specific settings on this instance only
    settings.ui_scale = 2
    settings.grid_scale = 1
    settings.grid_width = 30
    settings.grid_height = 30
    #For debugging specific games:
##    settings.mine_density = None
##    settings.mine_locations = [(2, 2), (2, 3), (7, 8), (5, 4), (5, 2), (2, 0),
##                               (0, 2), (6, 3), (7, 7), (4, 5), (0, 5), (8, 4),
##                               (3, 3), (9, 5), (5, 6), (8, 2), (4, 8)]

    ai_player = BasicRulesetAI(move_delay=0, newgame_delay=500, num_games=10)
    app = MinesweeperApp(window, settings, ai_player=True,
                         ai_player_name = ai_player.name,
                         block_gui=False)
    ai_player.attach(app)
    app.add_delayed_action('start AI', 1000, ai_player.start, [])

    app.run()
    pygame.quit()
