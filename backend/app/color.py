import random

random.seed(1)


def RGB_hex(R=0, G=0, B=0):
    return f"#{R:02x}{G:02x}{B:02x}"


def get_color(num=1):
    colors = []
    for i in range(num):
        gap = 190 // (num - 1)
        if i == 0:
            green = 200
        red = 255 - gap * i
        blue = gap * i
        green -= gap if i <= num // 2 else -gap
        colors.append({"red": red, "green": green, "blue": blue})

    color_hex = [
        RGB_hex(color["red"], color["green"], color["blue"]) for color in colors
    ]
    return color_hex


def get_colorRam(num=1, order=False):
    colors = []

    while len(colors) < num:
        red, green, blue = (
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255),
        )
        colorDic = {"red": red, "green": green, "blue": blue}
        if (
            (colorDic in colors)
            or (sum(colorDic.values())) < 400
            or (max(colorDic.values()) - min(colorDic.values()) < 100)
        ):
            continue
        colors.append(colorDic)
    color_hex = [
        RGB_hex(color["red"], color["green"], color["blue"]) for color in colors
    ]
    color_hex = sorted(color_hex, reverse=True) if order else color_hex

    return color_hex
