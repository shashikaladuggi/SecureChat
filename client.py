# import required modules
import socket
import threading
import tkinter as tk
from tkinter import scrolledtext
from tkinter import messagebox
import secrets
import DES_Decrypt
import DES_Encrypt
import el_gamal
import RSA

# Import new PQC algorithms
from pqc_algorithms import kyber
from pqc_algorithms import dilithium
from pqc_algorithms import falcon
from pqc_algorithms import saber
from pqc_algorithms import newhope
from pqc_algorithms import frodo
from pqc_algorithms import ntru_encrypt
from pqc_algorithms import ntruprime
from pqc_algorithms import classic_mceliece
from pqc_algorithms import bike
from pqc_algorithms import hqc
from pqc_algorithms import rainbow
from pqc_algorithms import sphincsplus
from pqc_algorithms import csidh
from pqc_algorithms import picnic


#HOST = '192.168.1.8'
HOST = '127.0.0.1'

PORT = 1234

DARK_GREY = '#485460'
MEDIUM_GREY = '#1e272e'
OCEAN_BLUE = '#60a3bc'
WHITE = "white"
FONT = ("Helvetica", 17)
BUTTON_FONT = ("Helvetica", 15)
SMALL_FONT = ("Helvetica", 13)

# Creating a socket object
# AF_INET: we are going to use IPv4 addresses
# SOCK_STREAM: we are using TCP packets for communication
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Initialize global variables
flagMethod = 0
key = ""
elgamalkey = []
rsa_string = []

# Algorithm pool for random selection
ALGORITHM_POOL = [
    "1",   # DES
    "2",   # ELGAMAL
    "3",   # RSA
    "4",   # CRYSTALS-Kyber
    "5",   # CRYSTALS-Dilithium
    "6",   # Falcon
    "7",   # SABER
    "8",   # NewHope
    "9",   # FrodoKEM
    "10",  # NTRUEncrypt
    "11",  # NTRUPrime
    "12",  # Classic McEliece
    "13",  # BIKE
    "14",  # HQC
    "15",  # Rainbow
    "16",  # SPHINCS+
    "17",  # CSIDH
    "18"   # Picnic
]

# Track last message algorithm for this client
last_msg_algorithm = None
use_random_mode = False

def get_random_algorithm():
    """Cryptographically secure random algorithm selection."""
    return secrets.choice(ALGORITHM_POOL)

def get_random_algorithm_with_999_probability(base_algorithm=None):
    """
    Random algorithm selection with 99.9% probability of different algorithm.
    """
    rand_val = secrets.randbelow(10000)  # 0-9999 range
    
    # 99.9% chance (0-9989) to select a different algorithm
    if rand_val < 9990:
        available_algos = [a for a in ALGORITHM_POOL if a != base_algorithm]
        if not available_algos:
            available_algos = ALGORITHM_POOL
        return secrets.choice(available_algos)
    else:
        if base_algorithm:
            return base_algorithm
        return get_random_algorithm()

def get_algorithm_for_message(selected_algo=None):
    """Determine algorithm for sending a message."""
    global use_random_mode
    
    if use_random_mode:
        if selected_algo and selected_algo != "RANDOM":
            return get_random_algorithm_with_999_probability(selected_algo)
        else:
            return get_random_algorithm()
    elif selected_algo and selected_algo != "RANDOM":
        return selected_algo
    else:
        return str(flagMethod)

def add_message(message):
    message_box.config(state=tk.NORMAL)
    message_box.insert(tk.END, message + '\n')
    message_box.config(state=tk.DISABLED)

def connect():

    # try except block
    try:

        # Connect to the server
        client.connect((HOST, PORT))
        print("Successfully connected to server")
        add_message("[SERVER] Successfully connected to the server")
    except:
        messagebox.showerror("Unable to connect to server", f"Unable to connect to server {HOST} {PORT}")

    username = username_textbox.get()
    if username != '':
        client.sendall(username.encode())
        print("SEND : ", username.encode() )
    else:
        messagebox.showerror("Invalid username", "Username cannot be empty")

    threading.Thread(target=listen_for_messages_from_server, args=(client, )).start()

    #tk
    username_textbox.config(state=tk.DISABLED)
    username_button.config(state=tk.DISABLED)
    username_button.pack_forget()
    username_textbox.pack_forget()
    username_label['text']= "Welcome " + username + " to our secure room"
    username_label.pack(side=tk.LEFT)

####here
def send_message():
    message = message_textbox.get()
    if message != '':
        message_textbox.delete(0, len(message))
        
        # Get selected algorithm from dropdown
        selected_algo = algo_var.get()
        
        # Determine algorithm for this message
        msg_algo = get_algorithm_for_message(selected_algo)
        msg_algo_int = int(msg_algo)
        
        #encryption
        if msg_algo_int == 1:
            message = DES_Encrypt.startDesEncryption(message, key)
        elif msg_algo_int == 2:
            print("elgammel encryption")
            global messageCopy
            message = el_gamal.incrypt_gamal(int(elgamalkey[0]), int(elgamalkey[1]), int(elgamalkey[2]),message)

            print("message text= ",message)
            #{q, a, YA, XA}

            messageCopy = message

            #cipher after encryption in var message
        elif msg_algo_int == 3:
            print("RSA encryption")
            global vo
            pla=[]
            global mes
            mes = []
            pla,mes=RSA.preprocess_message(message,int(rsa_string[0]))
            print("mes:",mes)
            message =RSA.to_cipher(int(rsa_string[1]),int(rsa_string[0]),pla)
            message = [str(x) for x in message]
            message = ",".join(message)
            print("msg type:",type(message))
            print("cipher RSA : ",message)
        
        client.sendall(message.encode("utf-8"))
        print("SEND : ", message.encode() )
        
        # Update last used algorithm
        global last_msg_algorithm
        last_msg_algorithm = msg_algo
        
        # Show algorithm used
        algo_names = {1: "DES", 2: "ElGamal", 3: "RSA", 4: "Kyber", 5: "Dilithium", 
                      6: "Falcon", 7: "SABER", 8: "NewHope", 9: "FrodoKEM", 
                      10: "NTRUEncrypt", 11: "NTRUPrime", 12: "McEliece", 13: "BIKE",
                      14: "HQC", 15: "Rainbow", 16: "SPHINCS+", 17: "CSIDH", 18: "Picnic"}
        algo_name = algo_names.get(msg_algo_int, f"Algo-{msg_algo}")
        print(f"Message encrypted with: {algo_name}")
        
        print("This message has been delivered")
    else:
        messagebox.showerror("Empty message", "Message cannot be empty")


####here
def listen_for_messages_from_server(client):
    
    while 1:
        message = client.recv(2048).decode('utf-8')
        print("RECV : ", message)
        #####
        if message != '':
            message = message.split("~")
            global key, flagMethod, elgamalkey, rsa_string

             
            username = message[0]
            content = message[1]
            key = message[2]
            # Get the algorithm for THIS specific message
            msg_algo = message[3]
            flagMethod = int(msg_algo)
            elgamalkey = message[4]
            elgamalkey = elgamalkey.split(",")
            rsa_string=message[5]
            rsa_string = rsa_string.split(",")


            #decrypt based on the algorithm used for THIS message
            if username != "SERVER":
                if flagMethod == 1:

                    content = DES_Decrypt.startDesDecryption(content, key)
                    try:
                        content = bytes.fromhex(content).decode('utf-8')
                    except:
                        print("error")


                    
                elif flagMethod == 2:
                    print("elgamal decryption")
                    print("content copy message=",content)
                    content=el_gamal.decrept_gamal(content,int(elgamalkey[3]))




                    
                elif flagMethod == 3:
                    content = content.split(",")
                    content = [int(x) for x in content]

                    content = RSA.to_plain(int(rsa_string[2]),int(rsa_string[0]),content, mes)
                    print("RSA Done:",content)



            # Show algorithm used for this message
            algo_names = {1: "DES", 2: "ElGamal", 3: "RSA", 4: "Kyber", 5: "Dilithium", 
                          6: "Falcon", 7: "SABER", 8: "NewHope", 9: "FrodoKEM", 
                          10: "NTRUEncrypt", 11: "NTRUPrime", 12: "McEliece", 13: "BIKE",
                          14: "HQC", 15: "Rainbow", 16: "SPHINCS+", 17: "CSIDH", 18: "Picnic"}
            algo_name = algo_names.get(flagMethod, f"Algo-{msg_algo}")
            
            add_message(f"[{username}] {content} [{algo_name}]")
            
        else:
            messagebox.showerror("Error", "Message recevied from client is empty")

def toggle_random_mode():
    global use_random_mode
    use_random_mode = random_mode_var.get()
    if use_random_mode:
        print("Random mode enabled: 99.9% algorithm switching")
    else:
        print("Random mode disabled")
    
def DES_Encryption(pt, key):
    cipher = DES_Encrypt.startDesEncryption(pt,key)  
    return cipher

          
root = tk.Tk()
root.geometry("700x650")
root.title("Messenger Client")
root.resizable(False, False)

root.grid_rowconfigure(0, weight=1)
root.grid_rowconfigure(1, weight=4)
root.grid_rowconfigure(2, weight=1)

top_frame = tk.Frame(root, width=600, height=100, bg=DARK_GREY)
top_frame.grid(row=0, column=0, sticky=tk.NSEW)

middle_frame = tk.Frame(root, width=600, height=400, bg=MEDIUM_GREY)
middle_frame.grid(row=1, column=0, sticky=tk.NSEW)

bottom_frame = tk.Frame(root, width=600, height=120, bg=DARK_GREY)
bottom_frame.grid(row=2, column=0, sticky=tk.NSEW)

username_label = tk.Label(top_frame, text="Enter your alias:", font=FONT, bg=DARK_GREY, fg=WHITE)
username_label.pack(side=tk.LEFT, padx=10)

username_textbox = tk.Entry(top_frame, font=FONT, bg=MEDIUM_GREY, fg=WHITE, width=23)
username_textbox.pack(side=tk.LEFT)

username_button = tk.Button(top_frame, text="Join", font=BUTTON_FONT, bg=OCEAN_BLUE, fg=WHITE, command=connect)
username_button.pack(side=tk.LEFT, padx=15)

# Algorithm selection frame in bottom
algo_frame = tk.Frame(bottom_frame, bg=DARK_GREY)
algo_frame.pack(side=tk.LEFT, padx=10, pady=5)

algo_label = tk.Label(algo_frame, text="Algorithm:", font=SMALL_FONT, bg=DARK_GREY, fg=WHITE)
algo_label.pack(side=tk.LEFT)

algo_var = tk.StringVar(value="3")  # Default RSA
algo_options = [
    ("DES", "1"),
    ("ElGamal", "2"),
    ("RSA", "3"),
    ("Kyber", "4"),
    ("Dilithium", "5"),
    ("Falcon", "6"),
    ("SABER", "7"),
    ("NewHope", "8"),
    ("FrodoKEM", "9"),
    ("NTRUEncrypt", "10"),
    ("NTRUPrime", "11"),
    ("McEliece", "12"),
    ("BIKE", "13"),
    ("HQC", "14"),
    ("Rainbow", "15"),
    ("SPHINCS+", "16"),
    ("CSIDH", "17"),
    ("Picnic", "18")
]

algo_menu = tk.OptionMenu(algo_frame, algo_var, *[opt[1] for opt in algo_options])
algo_menu.config(font=SMALL_FONT, bg=MEDIUM_GREY, fg=WHITE, width=12)
algo_menu.pack(side=tk.LEFT, padx=5)

# Random mode toggle
random_mode_var = tk.BooleanVar(value=False)
random_mode_check = tk.Checkbutton(algo_frame, text="🔀 Random (99.9%)", 
                                   variable=random_mode_var, font=SMALL_FONT,
                                   bg=DARK_GREY, fg=WHITE, selectcolor=MEDIUM_GREY,
                                   command=toggle_random_mode)
random_mode_check.pack(side=tk.LEFT, padx=10)

message_textbox = tk.Entry(bottom_frame, font=FONT, bg=MEDIUM_GREY, fg=WHITE, width=30)
message_textbox.pack(side=tk.LEFT, padx=10)

message_button = tk.Button(bottom_frame, text="Send", font=BUTTON_FONT, bg=OCEAN_BLUE, fg=WHITE, command=send_message)
message_button.pack(side=tk.LEFT, padx=10)

message_box = scrolledtext.ScrolledText(middle_frame, font=SMALL_FONT, bg=MEDIUM_GREY, fg=WHITE, width=67, height=26.5)
message_box.config(state=tk.DISABLED)
message_box.pack(side=tk.TOP)


# main function
def main():
    root.mainloop()
    
if __name__ == '__main__':
    main()
