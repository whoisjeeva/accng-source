from util.colorify import cyan, light_green, light_blue, white, gray, yellow, light_gray
from core.version import VERSION


def print_banner():
        banner = f"""
⠀█████╗  ██████╗ ██████╗{yellow("███╗   ██╗")}{cyan(" ██████╗ ")}
██╔══██╗██╔════╝██╔════╝{yellow("████╗  ██║")}{cyan("██╔════╝ ")}
███████║██║     ██║     {yellow("██╔██╗ ██║")}{cyan("██║  ███╗")}
██╔══██║██║     ██║     {yellow("██║╚██╗██║")}{cyan("██║   ██║")}
██║  ██║╚██████╗╚██████╗{yellow("██║ ╚████║")}{cyan("╚██████╔╝")}
╚═╝  ╚═╝ ╚═════╝ ╚═════╝{yellow("╚═╝  ╚═══╝")}{cyan(" ╚═════╝")}
   {light_gray("↪")} {gray("[")}{light_blue(f" v{VERSION} ")}{gray("]")}""".strip()
        banner += white(light_green(" https://t.me/whoisjeeva ")) + light_gray("↩")
        print(f"\n{banner}\n")
