import re

def is_valid_email(email):
    # Regular expression for a basic email validation
    email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'

    # Use re.match() to check if the email matches the pattern
    if re.match(email_pattern, email):
        return True
    else:
        return False

# Example usage:
email = "example@email.co"
if is_valid_email(email):
    print(f"{email} is a valid email address.")
else:
    print(f"{email} is not a valid email address.")
