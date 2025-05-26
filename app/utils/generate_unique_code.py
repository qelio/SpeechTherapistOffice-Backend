import random
import string

def generate_unique_code(length=8):
    characters = string.ascii_letters + string.digits  # Буквы (верхний и нижний регистр) + цифры
    random_string = ''.join(random.choice(characters) for _ in range(length))
    return random_string
