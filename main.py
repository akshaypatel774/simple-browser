import socket
import ssl
from datetime import datetime, timedelta

cache = {}

class URL:
    def __init__(self, url):
        self.scheme, url = url.split("://", 1)
        assert self.scheme in ["http", "https", "file"]

        if self.scheme == "file":
            self.path = url.split("/", 1)[-1]
            self.host = ""
        else:
            self.path = "/" + url.split("/", 1)[-1]
            self.host = url.split("/", 1)[0]
            self.port = 80 if self.scheme == "http" else 443
            self.socket = None
            
            if ":" in self.host:
                self.host, port = self.host.split(":", 1)
                self.port = int(port)

    def get_socket(self):
        """Get or create a socket for the URL."""
        if self.socket is None:
            self.socket = socket.socket(
                family=socket.AF_INET,
                type=socket.SOCK_STREAM,
                proto=socket.IPPROTO_TCP,
            )
            self.socket.connect((self.host, self.port))
            if self.scheme == "https":
                ctx = ssl.create_default_context()
                ctx.check_hostname = True
                ctx.verify_mode = ssl.CERT_REQUIRED
                self.socket = ctx.wrap_socket(self.socket, server_hostname=self.host)
        return self.socket
    
    def request(self):
        if "http" in self.scheme:
            max_redirects=5
            redirect_count = 0
            while redirect_count < max_redirects:
                s = self.get_socket()
                request = "GET {} HTTP/1.1\r\n".format(self.path)
                request += "Host: {}\r\n".format(self.host)
                # request += "Connection: keep-alive\r\n"
                request += "Connection: close\r\n"
                request += "User-Agent: SuperFastBrowser/2.5\r\n"
                request += "\r\n"
                s.send(request.encode("utf8"))

                response = s.makefile("r", encoding="utf8", newline="\r\n")
                statusline = response.readline()
                version, status, explanation = statusline.split(" ", 2)
                
                response_headers = {}
                while True:
                    line = response.readline()
                    if line == "\r\n": break
                    header, value = line.split(":", 1)
                    response_headers[header.casefold()] = value.strip()

                if 300 <= int(status) < 400:
                    if 'location' in response_headers:
                        new_url = response_headers['location']
                        if self.host not in new_url:
                            new_url = f"{self.scheme}://{self.host}{new_url}" 
                        self.__init__(new_url)
                        redirect_count += 1
                        continue
                    else:
                        return f"Redirect response received without 'Location' header."
                elif int(status) == 200:
                    if "cache-control" in response_headers:
                        cache_control = response_headers["cache-control"]
                        if "no-store" in cache_control:
                            content = self.read_response(response, response_headers, s)
                            s.close()
                            return content
                        elif "max-age" in cache_control:
                            max_age = int(cache_control.split("max-age=", 1)[1])
                            expires_at = datetime.now() + timedelta(seconds=max_age)
                            cache[self.scheme + "://" + self.host + self.path] = (expires_at, self.read_response(response, response_headers, s))
                            s.close()
                            return cache[self.scheme + "://" + self.host + self.path][1]
                    else:
                        content = self.read_response(response, response_headers, s)
                        s.close()
                        return content
                else:
                    break
            
            s.close()
            return f"Error: {status} {explanation}"
            
        elif self.scheme == "file":
            try:
                with open(self.path, "r") as file:
                    return file.read()
            except FileNotFoundError:
                return f"File not found at: {self.path}"

    def read_response(self, response, response_headers, s):
        if "content-length" in response_headers:
            content_length = int(response_headers["content-length"])
            content = response.read(content_length)
            if len(content) < content_length:
                while len(content) < content_length:
                    data = s.recv(content_length - len(content))
                    if not data:
                        break
                    content += data
        else:
            content = response.read()

        if content == "":
            return "{} is empty".format(self.scheme)
        return content

def remove_tags(body):
    in_tag = False
    for c in body:
        if c == "<":
            in_tag = True
        elif c == ">":
            in_tag = False
        elif not in_tag:
            print(c, end="")

def load(url: URL):
    now = datetime.now()
    if url.scheme + "://" + url.host + url.path in cache:
        expires_at, content = cache[url.scheme + "://" + url.host + url.path]
        if now < expires_at:
            remove_tags(content)
            return
    body = url.request()
    remove_tags(body)

if __name__ == "__main__":
    import sys
    import os
    from dotenv import load_dotenv

    load_dotenv()

    default_file = os.environ.get("DEFAULT_PATH")
    
    if len(sys.argv) == 1:
        load(URL("file://" + default_file))
    elif len(sys.argv) == 2:
        initial_url = sys.argv[1]
        load(URL(initial_url))

        while True:
            new_url = input("Enter a new URL (or 'q' to quit): ")
            if new_url.lower() == 'q':
                break
            load(URL(new_url))
    else:
        print("Usage: python script.py [<url>]")