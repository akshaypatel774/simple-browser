import tkinter
import platform
import tkinter.font

from browser import URL

WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
SCROLL_STEP = 100
PARAGRAPH_SPACING = 24

class Browser:
    def __init__(self):
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(self.window)
        self.canvas.pack(fill=tkinter.BOTH, expand=True)
        self.scroll = 0
        self.window.bind("<Down>", self.scrolldown)
        self.window.bind("<Up>", self.scrollup)
        self.window.bind("<MouseWheel>", self.on_mouse_scroll)
        if platform.system() == "Linux":
            self.window.bind("<Button-4>", self.scrollup)
            self.window.bind("<Button-5>", self.scrolldown)
        self.window.bind("<Configure>", self.on_window_resize)
        self.bi_times = tkinter.font.Font(
            family="Times",
            size=16,
            # weight="bold",
            # slant="italic",
        )

    def load(self, url):
        body = url.request()
        text = lex(body)
        self.display_list = layout(text, self.canvas.winfo_width(), self.canvas.winfo_height())
        self.draw()

    def draw(self):
        self.canvas.delete("all")

        # TODO: Avoid drawing beyong boundaries
        for x, y, c in self.display_list:
            if y > self.scroll + self.canvas.winfo_height():
                continue
            if y + VSTEP < self.scroll:
                continue
            self.canvas.create_text(x, y - self.scroll, text=c, font=self.bi_times)

    def scrollup(self, e):
        if self.scroll > 0:
            self.scroll = max(self.scroll - SCROLL_STEP, 0)
            self.draw()
    
    def scrolldown(self, e):
        self.scroll += SCROLL_STEP
        self.draw()

    def on_mouse_scroll(self, e):
        if platform.system() == "Darwin":
            self.scroll += e.delta
        else:
            if e.delta > 0:
                self.scrollup(e)
            else:
                self.scrolldown(e)
        self.draw()

    def on_window_resize(self, e):
        self.display_list = layout(lex(URL(url).request()), e.width, e.height)
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

def layout(text, width, height):
    display_list = []
    cursor_x, cursor_y = HSTEP, VSTEP
    for c in text:
        if c == "\n":
            cursor_y += PARAGRAPH_SPACING
            cursor_x = HSTEP
        else:
            display_list.append((cursor_x, cursor_y, c))
            cursor_x += HSTEP
            if cursor_x >= width - HSTEP:
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