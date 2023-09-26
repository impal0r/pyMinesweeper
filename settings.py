import json

class Settings:
    def __init__(self, filepath):
        self.load_from_file(filepath)
        self.filepath = filepath

    def load_from_file(self, filepath):
        with open(filepath) as file:
            save_obj = json.load(file)
        self.ui_scale = save_obj['other']['ui_scale']
        self.grid_scale = save_obj['other']['grid_scale']
        self.max_framerate = save_obj['other']['max_framerate']
        self.max_name_len = save_obj['other']['max_name_len']
        self.image_path = save_obj['other']['image_path']
        self.font_path = save_obj['other']['font_path']
        self.default_font = save_obj['style']['default_font']
        self.background_col = save_obj['colours']['background']
        self.lcd_background_col = save_obj['colours']['lcd_background']
        self.lcd_text_col = save_obj['colours']['lcd_text']
        self.button_background_col = save_obj['colours']['button_background']
        self.button_hover_col = save_obj['colours']['button_hover']
        self.button_click_col = save_obj['colours']['button_click']
        self.button_text_col = save_obj['colours']['button_text']
        self.button_flash_col = save_obj['colours']['button_flash']
        self.ai_panel_bg_col = save_obj['colours']['ai_panel_background']
        self.grid_width = save_obj['game']['grid_width']
        self.grid_height = save_obj['game']['grid_height']
        self.mine_density = save_obj['game']['mine_density']
        self.mine_number = save_obj['game']['mine_number']
        self.mine_locations = save_obj['game']['mine_locations']
        self.seed = save_obj['game']['seed']

    def save_to_file(self, filepath=None):
        if filepath is None:
            filepath = self.filepath
        save_obj = {'style' : {}, 'colours' : {},
                    'game' : {}, 'other' : {} }
        save_obj['other']['ui_scale'] = self.ui_scale
        save_obj['other']['grid_scale'] = self.grid_scale
        save_obj['other']['max_framerate'] = self.max_framerate
        save_obj['other']['max_name_len'] = self.max_name_len
        save_obj['other']['image_path'] = self.image_path
        save_obj['other']['font_path'] = self.font_path
        save_obj['style']['default_font'] = self.default_font
        save_obj['colours']['background'] = self.background_col
        save_obj['colours']['lcd_background'] = self.lcd_background_col
        save_obj['colours']['lcd_text'] = self.lcd_text_col
        save_obj['colours']['button_background'] = self.button_background_col
        save_obj['colours']['button_hover'] = self.button_hover_col
        save_obj['colours']['button_click'] = self.button_click_col
        save_obj['colours']['button_text'] = self.button_text_col
        save_obj['colours']['button_flash'] = self.button_flash_col
        save_obj['colours']['ai_panel_background'] = self.ai_panel_bg_col
        save_obj['game']['grid_width'] = self.grid_width
        save_obj['game']['grid_height'] = self.grid_height
        save_obj['game']['mine_density'] = self.mine_density
        save_obj['game']['mine_number'] = self.mine_number
        save_obj['game']['mine_locations'] = self.mine_locations
        save_obj['game']['seed'] = self.seed
        with open(filepath, mode='w') as file:
            json.dump(save_obj, file, indent=4)

    def restore_default(self):
        self.ui_scale = 2
        self.grid_scale = 2
        self.max_framerate = 60 #frames per second
        self.max_name_len = 30 #max length of ai player name
        self.image_path = 'images'
        self.font_path = 'fonts'
        self.default_font = 'arial'
        self.background_col = '#d0d0d0'
        self.lcd_background_col = 'black'
        self.lcd_text_col = 'red'
        self.button_background_col = '#e0e0e0'
        self.button_hover_col = '#e8e8e8'
        self.button_click_col = '#c0c0c0'
        self.button_text_col = 'black'
        self.button_flash_col = '#70ff70'
        self.ai_panel_bg_col = '#c0c0c0'
        self.grid_width = 20
        self.grid_height = 20
        self.mine_density = 0.17
        self.mine_number = None
        self.mine_locations = None
        self.seed = None
