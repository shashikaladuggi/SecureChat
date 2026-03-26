# Import required modules
import socket
import threading
import secrets
from tkinter import E
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
PORT = 1234 # to 65535
LISTENER_LIMIT = 5
active_clients = [] # List of all currently connected users

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

# Algorithm names for display
ALGORITHM_NAMES = {
    "1": "DES",
    "2": "ELGAMAL",
    "3": "RSA",
    "4": "CRYSTALS-Kyber",
    "5": "CRYSTALS-Dilithium",
    "6": "Falcon",
    "7": "SABER",
    "8": "NewHope",
    "9": "FrodoKEM",
    "10": "NTRUEncrypt",
    "11": "NTRUPrime",
    "12": "Classic McEliece",
    "13": "BIKE",
    "14": "HQC",
    "15": "Rainbow",
    "16": "SPHINCS+",
    "17": "CSIDH",
    "18": "Picnic"
}

# Track last algorithm used per client for 99.9% probability
client_last_algo = {}

def get_random_algorithm():
    """
    Cryptographically secure random algorithm selection.
    Uses secrets.choice for uniform distribution.
    """
    return secrets.choice(ALGORITHM_POOL)

def get_random_algorithm_with_999_probability(base_algorithm=None):
    """
    Random algorithm selection with 99.9% probability of different algorithm.
    This ensures that consecutive messages almost always use different algorithms.
    
    Args:
        base_algorithm: The algorithm number used in the previous message
        
    Returns:
        Selected algorithm number as string
    """
    # Use cryptographically secure random
    rand_val = secrets.randbelow(10000)  # 0-9999 range
    
    # 99.9% chance (0-9989) to select a different algorithm
    if rand_val < 9990:
        # Exclude the base algorithm if provided
        available_algos = [a for a in ALGORITHM_POOL if a != base_algorithm]
        if not available_algos:  # fallback if only one algorithm
            available_algos = ALGORITHM_POOL
        return secrets.choice(available_algos)
    else:
        # 0.1% chance (9990-9999) to use the same algorithm (unpredictable)
        if base_algorithm:
            return base_algorithm
        return get_random_algorithm()

def get_algorithm_for_message(username, selected_algo=None, use_random_mode=False):
    """
    Determine which algorithm to use for a message.
    
    Args:
        username: The username sending the message
        selected_algo: User-selected algorithm (or None for room default)
        use_random_mode: Whether random mode is enabled
        
    Returns:
        Algorithm number as string
    """
    if use_random_mode:
        # Get last algorithm used by this client
        last_algo = client_last_algo.get(username)
        
        if selected_algo and selected_algo != "RANDOM":
            # Use 99.9% probability to switch from the selected algorithm
            new_algo = get_random_algorithm_with_999_probability(selected_algo)
        else:
            # Pure random selection
            new_algo = get_random_algorithm()
        
        # Update the last algorithm used
        client_last_algo[username] = new_algo
        return new_algo
    elif selected_algo and selected_algo != "RANDOM":
        # Use user-selected algorithm
        client_last_algo[username] = selected_algo
        return selected_algo
    else:
        # Default to room's algorithm
        client_last_algo[username] = flagmethod
        return flagmethod
    
#Function to choose which security method to use
def chooseMethod():
    lst = [
        "DES",
        "ELGAMAL",
        "RSA",
        "CRYSTALS-Kyber",
        "CRYSTALS-Dilithium",
        "Falcon",
        "SABER",
        "NewHope",
        "FrodoKEM",
        "NTRUEncrypt",
        "NTRUPrime",
        "Classic McEliece",
        "BIKE",
        "HQC",
        "Rainbow",
        "SPHINCS+",
        "CSIDH",
        "Picnic"
    ]
    print("---------Welcome to our secure chat")
    print("1- DES (Data encryption standard)")
    print("2- ElGamal encryption system")
    print("3- RSA (Rivest–Shamir–Adleman)")
    print("4- CRYSTALS-Kyber (Post-Quantum KEM)")
    print("5- CRYSTALS-Dilithium (Post-Quantum Signature)")
    print("6- Falcon (Post-Quantum Signature)")
    print("7- SABER (Post-Quantum KEM)")
    print("8- NewHope (Post-Quantum KEM)")
    print("9- FrodoKEM (Post-Quantum KEM)")
    print("10- NTRUEncrypt (Post-Quantum Encryption)")
    print("11- NTRUPrime (Post-Quantum KEM)")
    print("12- Classic McEliece (Post-Quantum KEM)")
    print("13- BIKE (Post-Quantum KEM)")
    print("14- HQC (Post-Quantum KEM)")
    print("15- Rainbow (Post-Quantum Signature)")
    print("16- SPHINCS+ (Post-Quantum Signature)")
    print("17- CSIDH (Post-Quantum Key Exchange)")
    print("18- Picnic (Post-Quantum Signature)")
    print("19- RANDOM MODE (99.9% unpredictable algorithm switching)")
    num = input("Choose the encryption system: ")
    print(lst[int(num)-1] + " mode has been started")
    return num

def getMethod():
    return flagmethod
   
# Function to listen for upcoming messages from a client
def listen_for_messages(client, username, key, elgamapublickey, rsa_string, use_random_mode=False):

    while 1:

        message = client.recv(2048).decode('utf-8')
        print("RECV : ",message)
        if message != '':
            # Determine algorithm for this message
            msg_algo = get_algorithm_for_message(username, flagmethod, use_random_mode)
            
            # Send
            final_msg = username + '~' + message + '~' + key + "~" + msg_algo + "~" + elgamapublickey + "~" + rsa_string
            send_messages_to_all(final_msg)
            print("Message sent with algorithm: ", ALGORITHM_NAMES.get(msg_algo, msg_algo))

        else:
            print(f"The message send from client {username} is empty")


# Function to send message to a single client
def send_message_to_client(client, message):

    client.sendall(message.encode())
    print("SEND : ", message.encode() )

# Function to send any new message to all the clients that
# are currently connected to this server
def send_messages_to_all(message):
    
    for user in active_clients:
        
        # Start the security phase using message then pass the message to client
        send_message_to_client(user[1], message)

# Function to handle client
def client_handler(client, key):
    
    # Server will listen for client message that will
    # Contain the username
    while 1:

        username = client.recv(2048).decode('utf-8')
        print("RECV : ",username)
        if username != '':
            active_clients.append((username, client, key))
            # generate session key
            key = secrets.token_hex(8).upper()

            rsa_string = ""
            elgamalpublickey = ""
            
            # Check if random mode is enabled
            use_random_mode = (flagmethod == "19")

            # Handle key generation based on chosen method
            if flagmethod == "1" or flagmethod == "19":  # DES or Random mode fallback
                pass  # DES handled elsewhere

            elif flagmethod == "2":  # ElGamal
                string_ints = [str(x) for x in ElgamalKey]
                elgamalpublickey = ",".join(string_ints)
                print("elgamal public key", elgamalpublickey)

            elif flagmethod == "3":  # RSA
                n, E, D = RSA.calc()
                print("public and private key parameters: ")
                print("n: ", n)
                print("E: ", E)
                print("D: ", D)
                rsa_string += str(n) + "," + str(E) + "," + str(D) + ","

            elif flagmethod == "4":  # CRYSTALS-Kyber
                public_key, secret_key = kyber.generate_keys()
                rsa_string = public_key.hex()
                elgamalpublickey = secret_key.hex()

            elif flagmethod == "5":  # CRYSTALS-Dilithium
                public_key, secret_key = dilithium.generate_keys()
                rsa_string = public_key.hex()
                elgamalpublickey = secret_key.hex()

            elif flagmethod == "6":  # Falcon
                public_key, secret_key = falcon.generate_keys()
                rsa_string = public_key.hex()
                elgamalpublickey = secret_key.hex()

            elif flagmethod == "7":  # SABER
                public_key, secret_key = saber.generate_keys()
                rsa_string = public_key.hex()
                elgamalpublickey = secret_key.hex()

            elif flagmethod == "8":  # NewHope
                public_key, secret_key = newhope.generate_keys()
                rsa_string = public_key.hex()
                elgamalpublickey = secret_key.hex()

            elif flagmethod == "9":  # FrodoKEM
                public_key, secret_key = frodo.generate_keys()
                rsa_string = public_key.hex()
                elgamalpublickey = secret_key.hex()

            elif flagmethod == "10":  # NTRUEncrypt
                public_key, secret_key = ntru_encrypt.generate_keys()
                rsa_string = public_key.hex()
                elgamalpublickey = secret_key.hex()

            elif flagmethod == "11":  # NTRUPrime
                public_key, secret_key = ntruprime.generate_keys()
                rsa_string = public_key.hex()
                elgamalpublickey = secret_key.hex()

            elif flagmethod == "12":  # Classic McEliece
                public_key, secret_key = classic_mceliece.generate_keys()
                rsa_string = public_key.hex()
                elgamalpublickey = secret_key.hex()

            elif flagmethod == "13":  # BIKE
                public_key, secret_key = bike.generate_keys()
                rsa_string = public_key.hex()
                elgamalpublickey = secret_key.hex()

            elif flagmethod == "14":  # HQC
                public_key, secret_key = hqc.generate_keys()
                rsa_string = public_key.hex()
                elgamalpublickey = secret_key.hex()

            elif flagmethod == "15":  # Rainbow
                public_key, secret_key = rainbow.generate_keys()
                rsa_string = public_key.hex()
                elgamalpublickey = secret_key.hex()

            elif flagmethod == "16":  # SPHINCS+
                public_key, secret_key = sphincsplus.generate_keys()
                rsa_string = public_key.hex()
                elgamalpublickey = secret_key.hex()

            elif flagmethod == "17":  # CSIDH
                public_key, secret_key = csidh.generate_keys()
                rsa_string = public_key.hex()
                elgamalpublickey = secret_key.hex()

            elif flagmethod == "18":  # Picnic
                public_key, secret_key = picnic.generate_keys()
                rsa_string = public_key.hex()
                elgamalpublickey = secret_key.hex()

            else:
                print("Unknown encryption method selected")



            # Send
            mode_info = " (Random Mode: 99.9% unpredictable)" if flagmethod == "19" else ""
            prompt_message = "SERVER~" + f"{username} added to the chat~" + key + "~" + flagmethod + "~" + elgamalpublickey + "~" + rsa_string 
            send_messages_to_all(prompt_message)
            
            print("Sessison key successfully generated for " + f"{username } ==>", key)
            print(f"Encryption mode: {ALGORITHM_NAMES.get(flagmethod, 'Unknown')}{mode_info}")

            break
        else:
            print("Client username is empty")

    threading.Thread(target=listen_for_messages, args=(client, username, key, elgamalpublickey, rsa_string, use_random_mode,)).start()


# Main function
def main():
    global ElgamalKey
    ElgamalKey = el_gamal.generate_public_key()
    # Creating the socket class object
    # AF_INET: we are going to use IPv4 addresses
    # SOCK_STREAM: we are using TCP packets for communication
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    #choose method
    global flagmethod
    flagmethod = chooseMethod()

    # Creating a try catch block
    try:
        server.bind((HOST, PORT))
        print(f"Running the server on {HOST} {PORT}")
    except:
        print(f"Unable to bind to host {HOST} and port {PORT}")
    
    
    # Set server limit
    server.listen(LISTENER_LIMIT)

    # This while loop will keep listening to client connections
    while 1:

        client, address = server.accept()
        print(f"Successfully connected to client {address[0]} {address[1]}")
        key = ""
        threading.Thread(target=client_handler, args=(client,key, )).start()


if __name__ == '__main__':
    main()
