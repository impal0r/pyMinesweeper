import pygame

class BasicUIElement:
    clickable = False
    hoverable = False
    draggable = False
    
    def __init__(self, window, x, y, width, height):
        self.window = window
        self.rect = [x, y, width, height]

    def get_pos(self):
        '''Returns pixel coordinates of top left corner in window
        -> (x, y)'''
        return self.rect[:2]
    def set_pos(self, new_pos):
        '''Move the whole object.
        Anchors to top left corner'''
        self.rect[0], self.rect[1] = new_poa

    def get_size(self):
        '''Returns width and height in pixels
        -> (width, height)'''
        return self.rect[2:]
    def get_width(self):
        '''Returns width in pixels'''
        return self.rect[2]
    def get_height(self):
        '''Returns height in pixels'''
        return self.rect[3]
    def set_size(self, new_size):
        '''Changes width and height (in pixels)'''
        self.rect[2], self.rect[3] = new_size

    @property
    def left(self):
        '''-> x-coordinate of left edge in window (pixels)'''
        return self.rect[0]
    @property
    def top(self):
        '''-> y-coordinate of top edge in window (pixels)'''
        return self.rect[1]
    @property
    def right(self):
        '''-> x-coordinate of right edge in window (pixels)'''
        return self.rect[0] + self.rect[2]
    @property
    def bottom(self):
        '''-> y-coordinate of bottom edge in window (pixels)'''
        return self.rect[1] + self.rect[3]

    def contains_coords(self, pos):
        '''Used by the app to determine whether the mouse is over
        this UI element'''
        return (self.rect[0] <= pos[0] < self.rect[0] + self.rect[2] and
                self.rect[1] <= pos[1] < self.rect[1] + self.rect[3])

    def draw(self):
        pass

class ClickableUIElement(BasicUIElement):
    clickable = True
    right_clickable = False
    hoverable = True
    draggable = False

    def __init__(self, window, x, y, width, height):
        BasicUIElement.__init__(self, window, x, y, width, height)
        self._is_being_clicked = False #automatically modified by app

    def on_click(self, mouse_pos):
        pass

    def on_hover(self, mouse_pos):
        pass

    def on_leave_hover(self, mouse_pos):
        pass

class Rectangle(BasicUIElement):
    def __init__(self, window, x, y, width, height, colour):
        BasicUIElement.__init__(self, window, x, y, width, height)
        self.colour = colour

    def draw(self):
        pygame.draw.rect(self.window, self.colour, self.rect)

class TextRect(BasicUIElement):
    '''A sized container for text - allows text to be positioned
    relative to other objects, and padded'''
    def __init__(self, window, x, y, width, height,
                 colour, text_colour,
                 font, text, horiz_pad, vert_pad):
        '''x, y, width, height, padding are in pixels.
        Set colour=None for transparency.
        Text alignment is hardcoded to be right-aligned'''
        self.window = window

        #Drawing
        self.colour = colour #can be None for transparency (rect not drawn)
        self.text_colour = text_colour #cannot be None - has to be valid colour
        self.font = font

        #Text
        self.text = text
        self.text_surf = font.render(text, True, text_colour)
        self.vert_pad = vert_pad
        self.horiz_pad = horiz_pad

        #if width and/or height are -1, calculate min size
        if width == -1:
            width = self.get_min_rect_size()[0]
        if height == -1:
            height = self.get_min_rect_size()[1]

        #Location
        self.rect = [x, y, width, height]
        self._recalculate_text_pos()
        self.hidden = False

    @staticmethod
    def _calculate_text_pos(text_size, rect, horiz_pad, vert_pad):
        rect_x, rect_y, width, height = rect
        #text is always aligned right (for minesweeper)
        x = rect_x + width - text_size[0] - horiz_pad
        y = rect_y + height - text_size[1] - horiz_pad
        return (x, y)

    def _recalculate_text_pos(self):
        self.text_pos = self._calculate_text_pos(
            self.get_text_size(), self.rect,
            self.horiz_pad, self.vert_pad
        )

    def hide(self):
        self.hidden = True

    def show(self):
        self.hidden = False

    def get_text_size(self):
        '''-> (w, h)'''
        return self.text_surf.get_size()
    def get_min_rect_size(self):
        '''-> (w, h)
        Minimum size that fits text and padding'''
        w, h = self.get_text_size()
        return (w + 2 * self.horiz_pad,
                h + 2 * self.vert_pad)

    def set_pos(self, pos):
        '''Move the whole TextRect, with the text.
        Anchors to top left corner of rect'''
        self.rect[0], self.rect[1] = pos
        self._recalculate_text_pos()

    def set_size(self, new_size):
        '''Change the whole TextRect's size while the top left corner is fixed.
        Text is automatically moved as per alignment'''
        self.rect[2], self.rect[3] = new_size
        self._recalculate_text_pos()

    def set_text(self, new_text):
        self.text_surf = self.font.render(new_text, True, self.text_colour)
        self._recalculate_text_pos()

    def draw(self):
        if not self.hidden:
            if self.colour is not None:
                pygame.draw.rect(self.window, self.colour, self.rect)
            self.window.blit(self.text_surf, self.text_pos)

class Button(ClickableUIElement):
    '''Coloured button with set text. Can change colours when clicked.
    Can be hidden, meaning that button is not drawn and cannot be clicked'''
    #Implementation of hide/show is overall not perfect - because when
    # hidden, a button is not taken out of app's z-order. So it can block
    # something below it from being clicked. However I have tried to
    # write app so that interactive objects never normally overlap, and
    # overlapping objects isn't really necessary unless showing a popup
    def __init__(self, window, x, y, width, height,
                 colour, text_colour, click_colour, click_text_colour,
                 hover_colour, hover_text_colour,
                 font, text, horiz_pad, vert_pad,
                 on_click_call=lambda:None):
        #User interaction
        ClickableUIElement.__init__(self, window, x, y, width, height)
        self.is_being_clicked = False #automatically modified by app
        self.is_being_hovered = False #not modified by app
        self.on_click_call = on_click_call

        #Colours
        self.colour = colour
        self.text_colour = text_colour
        self.click_colour = click_colour
        self.click_text_colour = click_text_colour
        self.hover_colour = hover_colour
        self.hover_text_colour = hover_text_colour

        #Text
        self.text = text
        self.text_surf = font.render(text, True, text_colour)
        self.click_text_surf = font.render(text, True, click_text_colour)
        self.hover_text_surf = font.render(text, True, hover_text_colour)
        self.text_size = self.text_surf.get_size()

        #if width and/or height are -1, calculate min size
        if width == -1:
            width = self.text_size[0] + 2 * horiz_pad
        if height == -1:
            height = self.text_size[1] + 2 * vert_pad

        #Location
        self.hidden = False
        self.rect = [x, y, width, height]
        self._recalculate_text_pos()

    def get_text_size(self):
        return self.text_size

    @staticmethod
    def _calculate_text_pos(text_size, btn_rect):
        '''Center text in button rect'''
        x, y, width, height = btn_rect
        return (x + (width - text_size[0]) // 2,
                y + (height - text_size[1]) // 2)
    def _recalculate_text_pos(self):
        '''Call this function whenever button pos/size/text is changed'''
        self.text_pos = self._calculate_text_pos(self.text_size, self.rect)

    def set_pos(self, pos):
        '''Move the button'''
        self.rect[0], self.rect[1] = pos
        self._recalculate_text_pos()

    def set_size(self, new_size):
        '''Set a new size for button (text will still be centered)'''
        self.rect[2], self.rect[3] = new_size
        self._recalculate_text_pos()

    def hide(self):
        '''When button is hidden it is not drawn and cannot be clicked.
        No effect if button is already hidden.'''
        self.hidden = True
    def show(self):
        '''Un-hide button. No effect if button is not hidden'''
        self.hidden = False

    def on_click(self, pos):
        '''Called by app when left mouse btn is clicked,
        and self.contains_coords(mouse_pos) returns True'''
        if not self.hidden:
            self.on_click_call()

    def on_hover(self, pos):
        self.is_being_hovered = True

    def on_leave_hover(self, pos):
        self.is_being_hovered = False

    def draw(self):
        '''Draw coloured rect and text directly on window'''
        if not self.hidden:
            if self.is_being_clicked:
                pygame.draw.rect(self.window, self.click_colour, self.rect)
                self.window.blit(self.click_text_surf, self.text_pos)
            elif self.is_being_hovered:
                pygame.draw.rect(self.window, self.hover_colour, self.rect)
                self.window.blit(self.hover_text_surf, self.text_pos)
            else:
                pygame.draw.rect(self.window, self.colour, self.rect)
                self.window.blit(self.text_surf, self.text_pos)
