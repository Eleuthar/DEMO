# uppercase in range(65, 90)
# lowercase in range(97, 122)


def encrypt():
    # if the encrypted letter's ASCII code is bigger than "z", reduce the offset value until "z" 
    # and use the remainder as offset at the start of the alphabet, 
    # otherwise add the offset to the character code

    encrypted = ""
    text = input("Enter the text to be encrypted\n")
    key = input("Enter an encryption key between 1 - 25\n")

    # ask user for encryption key to offset letters
    while not key.isnumeric() and key not in range(1, 26):
        key = input("Enter an encryption key between 1 - 25\n")
    key = int(key)

    # encrypt only characters
    for ch in text:
        if not ch.isalpha():
            encrypted += ch

        # translate upper case character to ASCII code
        elif ch.isalpha() and ch.isupper():
            if ord(ch) + key > 90:
                offset = key - (90 - ord(ch))
                encrypted += chr(65 + offset - 1)
            else:
                encrypted += chr(ord(ch) + key)

        # translate lower case character to ASCII code
        elif ch.isalpha() and ch.islower():
            if ord(ch) + key > 122:
                offset = key - (122 - ord(ch))
                encrypted += chr(97 + offset - 1)
            else:
                encrypted += chr(ord(ch) + key)

    print(encrypted)


def decrypt():
    # if the derypted letter's ASCII code is lower than "a", reduce the offset value until "a" 
    # and use the remainder as offset from the end of the alphabet towards the start, 
    # otherwise decrease the offset of the encrypted character code

    decrypted = ""
    text = input("Enter the text to be decrypted\n")
    key = input("Enter the decryption key between 1 - 25\n")

    # ask user for decryption key to offset letters
    while not key.isnumeric() and key not in range(1, 26):
        key = input("Enter an decryption key between 1 - 25\n")
    key = int(key)

    # decrypt only characters
    for ch in text:
        if not ch.isalpha():
            decrypted += ch

        # translate upper case character to ASCII code
        elif ch.isalpha() and ch.isupper():
            if ord(ch) - key < 65:
                offset = key - (ord(ch) - 65)
                decrypted += chr(90 - offset + 1)
            else:
                decrypted += chr(ord(ch) - key)

        # translate lower case character to ASCII code
        elif ch.isalpha() and ch.islower():
            if ord(ch) - key < 97:
                offset = key - (ord(ch) - 97)
                decrypted += chr(122 - offset + 1)
            else:
                decrypted += chr(ord(ch) - key)

    print(decrypted)


def show_menu():
    try:
        option = int(input("\n\t1. Encrypt\n\t2. Decrypt\n\t3. Leave Kansas\n"))
        if option == 1:
            encrypt()

        elif option == 2:
            decrypt()

        elif option == 3:
            raise SystemExit()

        else:
            raise ValueError

    except ValueError:
        print("You must choose correctly, Neo!\nErgo, try again\n")
        showMenu()


# Start Game:

print("Wake up, Neo\nWhich pill will you take?")
while True:
    show_menu()
    print("\nWhat now?")
