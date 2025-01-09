import random

def generate_phone_number(country):
    if country == "bangladesh":
        codes = ["013", "014", "015", "016", "017", "018", "019"]
        return f"+88{random.choice(codes)}{random.randint(10000000, 99999999)}"
    elif country == "philippines":
        codes = ["090", "091", "092", "093", "094", "095", "096", "097", "098", "099"]
        return f"+63{random.choice(codes)}{random.randint(1000000, 9999999)}"
    elif country == "indonesia":
        codes = ["081", "082", "083", "085", "087", "088", "089"]
        return f"+62{random.choice(codes)}{random.randint(10000000, 99999999)}"
    elif country == "vietnam":
        codes = ["032", "033", "034", "035", "036", "037", "038", "039", "070", "076", "077"]
        return f"+84{random.choice(codes)}{random.randint(1000000, 9999999)}"
    elif country == "usa":
        codes = ["201", "202", "212", "213", "312", "315", "415", "510", "617", "718", "805", "818", "914"]
        return f"+1{random.choice(codes)}{random.randint(1000000, 9999999)}"
    elif country == "sri lanka":
        codes = ["070", "071", "072", "075", "076", "077", "078"]
        return f"+94{random.choice(codes)}{random.randint(1000000, 9999999)}"
    elif country == "lithuania":
        codes = ["610", "611", "612", "613", "614", "615", "616", "617", "618", "620", "621", "622", "623"]
        return f"+370{random.choice(codes)}{random.randint(10000, 99999)}"
    else:
        codes = ["013", "014", "015", "016", "017", "018", "019"]
        return f"+88{random.choice(codes)}{random.randint(10000000, 99999999)}"