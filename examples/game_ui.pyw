#An example of using minesweeper in another program.
#This simple example is written as a long script, I may refactor it to use OOP in the future

#--------------------------------- IMPORTS ---------------------------------

import sys, os
#trick to import from the parent directory:
sys.path.append('..')

from minesweeper import *

#restore sys.path
sys.path.remove('..')
#move down to parent directory so we can use images from \images\
os.chdir('..')

#---------------------------------- SETUP ----------------------------------

#tkinter initialisation
root = tk.Tk()
root.title('Minesweeper')
root.resizable(False, False)

#create a minesweeper game
game_frame = tk.Frame(root)
game = MinesweeperGame(game_frame, 20, 20, bomb_number=50)
game.pack(side='top')

#------------------------------- OPTION MENU -------------------------------

MAX_DIMENSION = 999

#This callback function validates numbers entered in the boxes
def check_entry(where, why, new_text):
    global width, height, bomb_number
    if new_text.isdigit(): #value should be a number
        num = int(new_text)
        #max value for dimensions is MAX_DIMENSION, max value for bomb_number is the number of cells
        max_value = int(width_entry.get())*int(height_entry.get()) if where=='bombs' else MAX_DIMENSION
        #min value for anything is 1
        min_value = 1
        if num < min_value or num > max_value:
            return False
        else:
            return True
    elif not new_text:
        return False
    else:
        return False
checkCommand = root.register(check_entry)

#Create labels and entry boxes
options_frame = tk.Frame(root)
tk.Label(options_frame, text='Width:  ').grid(row=0, column=0)
tk.Label(options_frame, text='Height:  ').grid(row=1, column=0)
tk.Label(options_frame, text='Number of mines:  ').grid(row=2, column=0)
width_entry = tk.Entry(options_frame)
width_entry.insert(0, '20')
width_entry.config(validate='all', validatecommand=(checkCommand,'width','%V','%P'))
width_entry.grid(row=0, column=1)
height_entry = tk.Entry(options_frame)
height_entry.insert(0, '20')
height_entry.grid(row=1, column=1)
height_entry.config(validate='all', validatecommand=(checkCommand,'height','%V','%P'))
bombs_entry = tk.Entry(options_frame)
bombs_entry.insert(0, '50')
bombs_entry.config(validate='all', validatecommand=(checkCommand,'bombs','%V','%P'))
bombs_entry.grid(row=2, column=1)

#Create button to start a game
def start_game():
    game.reset(new_width=int(width_entry.get()),
               new_height=int(height_entry.get()),
               bomb_number=int(bombs_entry.get()))
    options_frame.pack_forget()
    game_frame.pack()
start_button = tk.Button(options_frame, text='Start game', command=start_game)
start_button.grid(row=3, column=1)

options_frame.pack()

#-------------------------------- GAME SETUP -------------------------------

#add a button to return to option menu
def back_to_menu():
    game_frame.pack_forget()
    options_frame.pack()
    game.stop = True #stop the game running, so tkinter doesn't get glitchy
back_button = tk.Button(game_frame, text='Back to menu', command=back_to_menu)
back_button.pack(side='bottom')

#----------------------------------- MAIN ----------------------------------

root.mainloop()
