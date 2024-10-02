#!./venv/bin/python3
#passchecker makes sure that passwords in OLA follow 
#the set requirements for password complexity

#Lenght between 14 and 128 characters
#Minimum 2 out of the following categories: 
# 1. Capitol letter
# 2. Small letter
# 3. Number between 0 and 9
# 4. Contain special character

def is_strong_password(password):
    # checks if the password is between 14 and 128 characters
    if len(password) < 14 or len(password) >= 128:
        return False
    
    # A variable that keeps track of how many requirements the password fullfills
    numTrue=0
    
    if any(char.isupper() for char in password):
        numTrue+=1   
    if any(char.islower() for char in password):
        numTrue+=1
    if any(char.isdigit() for char in password):
        numTrue+=1
    if any(not char.isalnum() for char in password):
        numTrue+=1
    
    if numTrue <2:
        return False
    else:
        return True

