def encrypt_odd_even(s: str) -> str:
    s = s.replace(" ", "")
    return s[0::2] + s[1::2]

FAKE_FLAG = "CTF{ORDER_HIDES_THE_TRUTH}"

if __name__ == "__main__":
    print("Shoshilma. Harflar ham o‘z navbati bilan gapiradi")
    print(encrypt_odd_even(FAKE_FLAG))
    print("\nType anything to see its encryption:")
    s = input("> ").rstrip("\n")
    print(encrypt_odd_even(s))

