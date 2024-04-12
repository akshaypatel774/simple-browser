import tkinter
import tkinter.font
import platform

from url import URL

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


    def load(self, url):
        body = url.request()
        tokens = lex(body)
        self.display_list = Layout(tokens, self.canvas.winfo_width(), self.canvas.winfo_height()).display_list
        self.draw()


    # TODO: Avoid drawing beyong boundaries
    def draw(self):
        self.canvas.delete("all")
        for x, y, c, font in self.display_list:
            if y > self.scroll + self.canvas.winfo_height():
                continue
            if y + VSTEP < self.scroll:
                continue
            self.canvas.create_text(x, y - self.scroll, text=c, font=font, anchor='nw')

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
        self.display_list = Layout(lex(URL(url).request()), e.width, e.height).display_list
        self.draw()

class Text:
    def __init__(self, text):
        self.text = text

    def __repr__(self):
        return f'Text({self.text})'

class Tag:
    def __init__(self, tag):
        self.tag = tag

    def __repr__(self):
        return f'Tag({self.tag})'
    
def lex(body):
    out = []
    buffer = ""
    in_tag = False
    for c in body:
        if c == "<":
            in_tag = True
            if buffer: out.append(Text(buffer))
            buffer = ""
        elif c == ">":
            in_tag = False
            out.append(Tag(buffer))
            buffer = ""
        else:
            buffer += c
    if not in_tag and buffer:
        out.append(Text(buffer))
    return out

FONTS = {}
def get_font(size, weight, slant):
    key = (size, weight, slant)
    if key not in FONTS:
        font = tkinter.font.Font(size=size, weight=weight, slant=slant)
        label = tkinter.Label(font=font)
        FONTS[key] = (font, label)
    return FONTS[key][0]

class Layout:
    def __init__(self, tokens, width, height):
        self.display_list = []
        self.cursor_x = HSTEP
        self.cursor_y = VSTEP
        self.weight = "normal"
        self.style = "roman"
        self.size = 16
        self.line = []
        self.width = width
        for tok in tokens:
            self.token(tok)
        self.flush()

    def token(self, tok):
        if isinstance(tok, Text):
            for word in tok.text.split():
                self.word(word)
        elif tok.tag == "i":
            self.style = "italic"
        elif tok.tag == "/i":
            self.style = "roman"
        elif tok.tag == "b":
            self.weight = "bold"
        elif tok.tag == "/b":
            self.weight = "normal"
        elif tok.tag == "small":
            self.size -= 2
        elif tok.tag == "/small":
            self.size += 2
        elif tok.tag == "big":
            self.size += 4
        elif tok.tag == "/big":
            self.size -= 4
        elif tok.tag == "br":
            self.flush()
        elif tok.tag == "/p":
            self.flush()
            self.cursor_y += VSTEP

    def word(self, word):
        font = get_font(self.size, self.weight, self.style)
        w = font.measure(word)
        if self.cursor_x + w > self.width - HSTEP:
            self.flush()
        self.line.append((self.cursor_x, word, font))
        self.cursor_x += w + font.measure(" ")

    def flush(self):
        if not self.line: return
        metrics = [font.metrics() for _, _, font in self.line]
        max_ascent = max([metric["ascent"] for metric in metrics])
        baseline = self.cursor_y + 1.25 * max_ascent
        for x, word, font in self.line:
            y = baseline - font.metrics("ascent")
            self.display_list.append((x, y, word, font))
        max_descent = max([metric["descent"] for metric in metrics])
        self.cursor_y = baseline + 1.25 * max_descent
        self.cursor_x = HSTEP
        self.line = []
        

if __name__ == "__main__":
    """
        Supports - file, http, https
        TODO: Support re-entering URL
    """
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else "http://example.org/"
    Browser().load(URL(url))
    tkinter.mainloop()