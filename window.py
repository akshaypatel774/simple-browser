import tkinter
from browser import URL

WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
SCROLL_STEP = 100

class Browser:
    def __init__(self):
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(
            self.window, 
            width=WIDTH,
            height=HEIGHT
        )
        self.canvas.pack()
        self.scroll = 0
        self.window.bind("<Down>", self.scrolldown)
        self.window.bind("<Up>", self.scrollup)
    
    def load(self, url):
        body = url.request()
        text = lex(body)
        self.display_list = layout(text)
        self.draw()

    def draw(self):
        self.canvas.delete("all")

        # TODO: Avoid drawing beyong boundaries
        for x, y, c in self.display_list:
            if y > self.scroll + HEIGHT: continue
            if y + VSTEP < self.scroll: continue
            self.canvas.create_text(x, y - self.scroll, text=c)

    def scrollup(self, e):
        if (self.scroll - SCROLL_STEP) > SCROLL_STEP:
            self.scroll -= SCROLL_STEP
        else:
            self.scroll = 0
        self.draw()
    
    def scrolldown(self, e):
        self.scroll += SCROLL_STEP
        self.draw()

def lex(body):
    text = ""
    in_tag = False
    for c in body:
        if c == "<":
            in_tag = True
        elif c == ">":
            in_tag = False
        elif not in_tag:
            text += c
    return text

def layout(text):
    display_list = []
    cursor_x, cursor_y = HSTEP, VSTEP
    for c in text:
        display_list.append((cursor_x, cursor_y, c))
        cursor_x += HSTEP
        if cursor_x >= WIDTH - HSTEP:
            cursor_y += VSTEP
            cursor_x = HSTEP
    return display_list


if __name__ == "__main__":
    """
        Supports - file, http, https
        TODO: Support re-entering URL
    """
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else "http://example.org/"
    Browser().load(URL(url))
    tkinter.mainloop()