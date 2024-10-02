#!./venv/bin/python3

import bcrypt
import sys
from getpass import getpass

def hashpass(password):
    # Convert password to array of bytes
    bytes_password = password.encode('utf-8')
    # Generate salt
    salt = bcrypt.gensalt()
    # Hash the password
    hashed_password = bcrypt.hashpw(bytes_password, salt)
    
    return hashed_password.decode('utf-8')

def update_users(username, fullname, hashed_password, newuser, changepass):
    updated_lines = []
    
    # Read from the users-file and check if user allready exist
    with open('users', "r") as file:
        users = file.readlines()
    
    for line in users:
        #if username exists
        if line.startswith(username):
            db_username, db_fullname, db_hashed_password, db_changepass= line.strip().split(":")
            #add new password hash
            line = (f"{db_username}:{db_fullname}:{hashed_password}:{changepass}\n")
            updated_lines.append(line)
        else:
            updated_lines.append(line)

    if newuser: 
        updated_lines.append(f"{username}:{fullname}:{hashed_password}:{changepass}\n")
    
    #write changes to users-file
    with open('users', "w") as file:
        file.writelines(updated_lines)

def is_newuser(username): 
    with open('users', "r") as file:
        for line in file: 
            if line.startswith(username):
                return False
          
    return True


def main():
    # Check if the script has been given the right number of arguments
    if len(sys.argv) != 2 or sys.argv[1] == "--help" or  sys.argv[1] == "-h":
        print("Add new OLA user or change password of existing user")
        print(f"Usage: {sys.argv[0]} [USERNAME]")
        exit()

    username = sys.argv[1]
    
    #check if username exists
    newuser = is_newuser(username) 
    
    if newuser:
        fullname = input("Full name: ")
    else:
        #only change password for existing user if confirmation is given
        proceed = input("Username already exists!\nDo you want to change password? (Y/n): " )
        if proceed == "Y" or proceed == "y" or proceed == "": 
            fullname = "Existing User"
        else: 
            print ("No changes made!") 
            exit()

    password = getpass("New password: ")
    retype_pass = getpass ("Retype new password: ")

    if password != retype_pass:
        print ("Entered passwords do not match!")
        exit()
    
    changepass = input("Require user to change password on login? (Y/n): ")
    if changepass == "Y" or changepass == "y" or changepass == "":
        changepass = "1"
    elif changepass == "N" or changepass == "n" or changepass == "":
        changepass = "0"
    else:
        print ("No changes made!")
        exit()




    #generate passwordhash
    hashed_password = hashpass(password)
    
    update_users(username, fullname, hashed_password, newuser, changepass)



if __name__ == "__main__":
    main()
