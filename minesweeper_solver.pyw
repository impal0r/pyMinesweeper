import random

class MinesweeperSolver:
    def __init__(self, game, delay=100, autostep=True):#delay of 0 NOT recommended.
        self.game = game
        self.width = game.width
        self.height = game.height
        self.delay = delay #milliseconds between each move
        self.AUTOSTEP = autostep

    @staticmethod
    def inc_wrap(i, max_):
        '''Increment i (modulo max_+1)
        Returns 0 is i is max_, and i+1 otherwise'''
        if i==max_:
            return 0
        else:
            return i + 1


    def _update_groups_with_new_nums(self, new_nums, groups, boxmap):
        for x, y in new_nums:
            grp = {'number':self.game.get_number(x,y), 'boxes':set(), 'active':True}
            #for each neighbouring box
            for i, j in self.game.neighbours(x,y):
                #add to group if unflagged
                if not( self.game.is_exposed(i,j) or self.game.is_flagged(i,j) ):
                    grp['boxes'].add((i,j))
                    #remove from list of untouched squares
                    if (i,j) in self.hidden:
                        self.hidden.remove((i,j))
                    #add to boxmap
                    if (i,j) in boxmap:
                        boxmap[i,j].append(len(groups)) #current index
                    else:
                        boxmap[i,j] = [len(groups)] #current index
                #adjust number if flagged
                elif (not self.game.is_exposed(i,j)) and self.game.is_flagged(i,j):
                    grp['number'] -= 1
            # just make sure we have no duplicates in groups
            if grp in groups:
                # if it is a duplicate don't add it
                # and remove incorrect pointers from boxmap
                for i, j in self.game.neighbours(x,y):
                    if not (self.game.is_exposed(i,j) or self.game.is_flagged(i,j)):
                        boxmap[i,j].remove(len(groups))
            else:
                groups.append(grp)

        return (groups, boxmap)

    def _flag_and_update(self, x, y, groups, boxmap):
##        if self.game.is_flagged(x,y):
##            print('WARNING:', x, y, 'HAS ALREADY BEEN FLAGGED')
        self.game.button_flag(x,y)
        #update neighbouring groups
        for index in boxmap[x,y]:
            if 'done' not in groups[index]:
                groups[index]['number'] -= 1
                groups[index]['boxes'].remove((x,y))
                groups[index]['active'] = True
        #remove box from boxmap as we'll no longer need it
        del boxmap[x,y]
        return (groups, boxmap)

    def _click_and_update(self, x, y, groups, boxmap):
        if not self.game.is_exposed(x,y):
            new_nums, new_all = self.game.button_click(x,y)
            #remove exposed squares from list of untouched squares
            for sq in new_all:
                if sq in self.hidden:
                    self.hidden.remove(sq)
            #create new groups from new nums, and add mappings from boxes
            groups, boxmap = self._update_groups_with_new_nums(new_nums, groups, boxmap)

            #update all neighbouring groups, and remove redundant boxmaps
            for sq in new_all:
                if sq in boxmap:
                    for index in boxmap[sq]:
                        if 'done' not in groups[index]:
                            groups[index]['boxes'].remove(sq)
                            groups[index]['active'] = True
                    del boxmap[sq]

        return (groups, boxmap)

    def _step(self, groups, boxmap, i):
        #get to an active group
        orig = i; doneloop = False
        while 'done' in groups[i] or not groups[i]['active']:
            #get next index
            i = self.inc_wrap(i, len(groups)-1)
            #check if we have gone all the way around the carousel
            if i==orig:
                doneloop = True
                break
        if doneloop:
            #guessing
##            print('Groups:')
##            for group in groups:
##                if 'done' not in group:
##                    print(group)
##            print('\nBoxmap:')
##            pprint(boxmap)
            #find best group to guess
            lowest = 1; lowest_grp = None
            remaining = self.game.bomb_ctr #how many bombs unaccounted for
            for grp in groups:
                if 'done' not in grp:
                    x = grp['number'] / len(grp['boxes'])
                    if x < lowest:
                        lowest = x
                        lowest_grp = grp['boxes']
                    #check if it overlaps with others
                    overlap = False
                    for box in grp['boxes']:
                        if len(boxmap[box]) > 1:
                            overlap = True
                            break
                    #only count number if not overlapping
                    if not overlap:
                        remaining -= grp['number']
            #squares left over:
            if self.hidden:
                x = remaining / len(self.hidden) #remaining is an upper bound
                if x < lowest: #so if probability less than lowest, is definitely best
                    lowest = x
                    lowest_grp = self.hidden
            #guess random square in lowest_grp
            box = next(iter(lowest_grp)) #get a box from lowest_grp
##            print('Taking a guess...',*box)
            groups, boxmap = self._click_and_update(*box, groups, boxmap)
            if self.game.lost or self.game.won: #did it work?
                return
            else: #continue with delay
                self.game.after(self.delay, lambda:self._step(groups, boxmap, 0))
        else:
            num = groups[i]['number']
            boxes = groups[i]['boxes'].copy()
            num_boxes = len(groups[i]['boxes'])
            changed_visible = True; done_sth = False
            # 1. If no boxes left, delete group
            if not num_boxes:
                groups[i]['done'] = 1
                changed_visible = False
                done_sth = True
            # 2. If number == 0, break all boxes, and delete group
            elif not num:
                for x, y in boxes:
                    groups, boxmap = self._click_and_update(x, y, groups, boxmap)
                groups[i]['done'] = 1
                done_sth = True
            # 3. If number == #boxes, flag all boxes, and delete group
            elif num == num_boxes:
                for x, y in boxes:
                    groups, boxmap = self._flag_and_update(x, y, groups, boxmap)
                groups[i]['done'] = 1
                done_sth = True
            else:
                # Get neighbouring groups
                neighbouring_groups = []
                for box in boxes:
                    for grp_index in boxmap[box]:
                        if grp_index not in neighbouring_groups:
                            neighbouring_groups.append(grp_index)
                #Neighbouring groups DOES NOT include this one!
                neighbouring_groups.remove(i)
                # For each neighbouring group:
                for j in neighbouring_groups:
                    # 4. If this set contains a neighbouring set
                    if groups[i]['boxes'].issuperset(groups[j]['boxes']):
                        # 4a. If numbers equal, break remaining boxes, and delete this group
                        if num == groups[j]['number']:
                            iter_boxes = groups[i]['boxes'] - groups[j]['boxes']
                            for x, y in iter_boxes:
                                groups, boxmap = self._click_and_update(x, y, groups, boxmap)
                            groups[i]['done'] = 1
                        # 4b. If numbers differ by difference in size, flag remaining boxes,
                        #     and delete this group
                        elif num-groups[j]['number'] == num_boxes-len(groups[j]['boxes']):
                            iter_boxes = groups[i]['boxes'] - groups[j]['boxes']
                            for x, y in iter_boxes:
                                groups, boxmap = self._flag_and_update(x, y, groups, boxmap)
                            groups[i]['done'] = 1
                        # 4c. Else, this num -= that num, this set -= that set (splitting)
                        else:
                            #update boxmap
                            for box in groups[j]['boxes']:
                                boxmap[box].remove(i)
                            groups[i]['number'] -= groups[j]['number']
                            groups[i]['boxes'] -= groups[j]['boxes']
                        done_sth = True
                        break #don't do several things at once
                    # 5. "1 of 3, 2 of 3":
                    #    If thisnum==size(intersect)-1 and thatnum==size(thatset-intersect)+thisnum,
                    #    then break extras of this set and flag extras of other set, and del group
                    intersect = groups[i]['boxes'] & groups[j]['boxes']
                    if ((num == len(intersect) - 1) and
                        (groups[j]['number'] == len(groups[j]['boxes']-intersect) + num)):
                        iter_boxes = groups[j]['boxes'] - intersect
                        for x, y in iter_boxes:
                            groups, boxmap = self._flag_and_update(x, y, groups, boxmap)
                        iter_boxes = groups[i]['boxes'] - intersect
                        for x, y in iter_boxes:
                            groups, boxmap = self._click_and_update(x, y, groups, boxmap)
                        groups[i]['done'] = 1
                        done_sth = True
                        break #don't do several things at once

            if not done_sth:
                groups[i]['active'] = False
                changed_visible = False
            if 'done' in groups[i]: #update boxmap if we have deleted a group
                #there will still be some boxes left if we have \
                # deleted a group in the second stage because it was a duplicate
                for box in groups[i]['boxes']:
                    boxmap[box].remove(i)
                    if not boxmap[box]:
                        del boxmap[box]

            if self.game.won:
                return
            nexti = self.inc_wrap(i, len(groups)-1)
            if self.AUTOSTEP:
                #AUTO STEP
                if changed_visible: #continue with delay
                    self.game.after(self.delay, lambda:self._step(groups, boxmap, nexti))
                else: #continue without delay
                    self._step(groups, boxmap, nexti)
            else:
                #MANUAL STEP
                self.i = nexti
                #groups and boxmap are synonymous with self.groups and self.boxmap
                #as they point to the same objects

    def _step_proxy(self, evt):
        self._step(self.groups, self.boxmap, self.i)

    def solve(self, start=None):
        # initialise list of clear boxes that aren't in a group (at the start, all the boxes)
        self.hidden = [(i,j) for i in range(self.width) for j in range(self.height)]

        #first click
        if start is None:
            x, y = 0, 0#self.width//2, self.height//2
        else:
            x, y = start
        groups, boxmap = self._click_and_update(x,y,[],{}) #(cannot lose on first click)
        self.groups = groups #these will point to the same object
        self.boxmap = boxmap #ie. updating either will change both

        if self.AUTOSTEP:
            #AUTO STEP
            self._step(groups, boxmap, 0)
        else:
            #MANUAL STEP
            self.i = 0
            self.game.bind('t', self._step_proxy)
            print("Press 'T' to step the algorithm once")

    def __del__(self):
        self.game.unbind('t', self._step_proxy)

def show_bombs(game):
    '''Toggle flags on all bombs in game'''
    for bomb in game.bombs:
        game.button_flag(*bomb)

def cheat_solve(game):
    '''Just flag all bombs and clear all spaces'''
    for i in range(game.width):
        for j in range(game.height):
            if game.stop: game.stop = False #so it definitely flags all bombs
            if game.grid[i][j] & 0b10000: #bomb
                game.button_flag(i,j)
            else:
                game.button_click(i,j)
    game.stop = True

if __name__=='__main__':
    from minesweeper import *
    root = tk.Tk()
    root.title('Minesweeper')
    root.resizable(False, False)

    testbombs = [(12, 4), (5, 24), (16, 16), (7, 24), (4, 10), (9, 15), (24, 11),
                 (11, 15), (20, 23), (24, 1), (3, 15), (23, 12), (2, 24), (6, 21),
                 (26, 13), (15, 10), (1, 23), (19, 5), (29, 1), (8, 0), (28, 0),
                 (14, 23), (7, 7), (17, 10), (17, 20), (6, 11), (1, 6), (17, 11),
                 (15, 22), (0, 8), (14, 16), (0, 4), (15, 5), (21, 18), (7, 2),
                 (4, 4), (22, 16), (23, 7), (26, 1), (4, 21), (17, 1), (18, 10),
                 (29, 19), (22, 9), (24, 17), (16, 3), (15, 18), (29, 8), (28, 3),
                 (25, 5), (2, 16), (28, 5), (19, 12), (1, 18), (13, 20), (26, 17),
                 (4, 6), (1, 15), (22, 0), (13, 2), (24, 3), (8, 2), (5, 13),
                 (19, 7), (21, 6), (19, 8), (12, 19), (14, 20), (1, 12), (16, 0),
                 (10, 15), (8, 4), (0, 23), (28, 8), (8, 21), (1, 9), (23, 24),
                 (29, 20), (7, 0), (8, 13), (1, 21), (20, 21), (19, 10), (23, 19),
                 (10, 6), (21, 12), (14, 5), (6, 13), (12, 6), (22, 14), (3, 4),
                 (28, 19), (29, 0), (6, 1), (12, 14), (25, 2), (17, 0), (16, 14),
                 (26, 12), (21, 22), (19, 9), (23, 8), (11, 20), (5, 10), (21, 21),
                 (0, 5), (0, 21)] #for testing start at (10,10)
    game = MinesweeperGame(root,30,20,bomb_density=1/7)
    #game.randombombs = False
    game.pack()
    solver = MinesweeperSolver(game,delay=10,autostep=True)
    solver.solve()

    root.mainloop()
