import socket
import time
import argparse
import random
from colorama import Back, Style
from json_util import JSONSocket, load_json

HOST = "127.0.0.1"
VERIFIER_PORT = 5001
ATTACKER_PORT = 5003
STATE_DIR = "./states"


# ---------------------------------------
# Distance Fraud (guesses challenge)
# ---------------------------------------

def hk_df(ver_host=HOST, ver_port=VERIFIER_PORT):
    st = load_json(f"{STATE_DIR}/hk_prover_state.json")
    n = st["n"]
    a1, a2 = st["a1"], st["a2"]

    print(Back.YELLOW + "[HK DF] Connecting to verifier..." + Style.RESET_ALL)
    with socket.create_connection((ver_host, ver_port)) as conn:

        js = JSONSocket(conn)

        for i in range(n):
            msg = js.recv()
            assert msg["type"] == "challenge"
            real_ci = msg["ci"]

            guessed_ci = random.choice([1, 2])
            ri = a1[i] if guessed_ci == 1 else a2[i]

            js.send({"type": "response", "round": i, "ri": ri})
            print(f"[HK DF] Round {i+1}: real_ci={real_ci}, guessed_ci={guessed_ci}, ri={ri}")

        final = js.recv()
        if final["decision"] == "ACCEPT":
            print(Back.GREEN + "[HK DF] Distance fraud SUCCESSFUL" + Style.RESET_ALL)
        else:
            print(Back.RED + "[HK DF] Distance fraud rejected" + Style.RESET_ALL)

        js.close()



# ---------------------------------------
# Mafia Fraud (MITM)
# Verifier <-> Attacker <-> Honest Prover
# Attacker/Prover in range!
# ---------------------------------------

def hk_mf_prover_in_range(ver_host=HOST, ver_port=VERIFIER_PORT, atk_listen_port=ATTACKER_PORT):

    # 1) Accept honest prover
    listener = socket.create_server((HOST, atk_listen_port), reuse_port=False)
    print(Back.BLUE + f"[HK MF] Listening on 127.0.0.1:{atk_listen_port} for honest prover..." + Style.RESET_ALL)
    pconn, paddr = listener.accept()
    print(Back.YELLOW + f"[HK MF] Honest prover connected from {paddr}" + Style.RESET_ALL)
    pjs = JSONSocket(pconn)

    # 2) Connect to verifier
    print(Back.BLUE + f"[HK MF] Connecting to verifier {ver_host}:{ver_port} ..." + Style.RESET_ALL)
    vconn = socket.create_connection((ver_host, ver_port))
    vjs = JSONSocket(vconn)
    print(Back.GREEN + "[HK MF] Connected to verifier." + Style.RESET_ALL)

    # Load n (number of DB rounds) - with this, rounds are dynamically adjusted
    st = load_json(f"{STATE_DIR}/hk_prover_state.json")
    n = st["n"]

    # 3) MF loop
    for i in range(n):
        vmsg = vjs.recv()
        assert vmsg["type"] == "challenge"

        # forward challenge
        pjs.send(vmsg)

        # get correct response
        presp = pjs.recv()

        # forward response
        vjs.send(presp)

        print(f"[HK RELAY] Round {i+1}: ci={vmsg['ci']} ri={presp['ri']}")

    # 4) Read final decision from verifier, then FORWARD it to the honest prover
    final = vjs.recv()
    print(f"[HK MF] Verifier final decision: {final}")
    try:
        pjs.send(final)
    except Exception as e:
        print(f"[HK MF] Warning: failed to forward final to prover: {e}")

    if final.get("decision") == "ACCEPT":
        print(Back.GREEN + "[HK MF] Mafia fraud SUCCESSFUL" + Style.RESET_ALL)
    else:
        print(Back.RED + "[HK MF] Mafia fraud rejected" + Style.RESET_ALL)

    vjs.close()
    pjs.close()
    listener.close()



# ---------------------------------------
# Mafia Fraud (MITM)
# Verifier <-> Attacker <-> Honest Prover
# Only Attacker in range!
# ---------------------------------------

def hk_mf_prover_out_of_range(ver_host=HOST, ver_port=VERIFIER_PORT, atk_listen_port=ATTACKER_PORT):
    st = load_json(f"{STATE_DIR}/hk_prover_state.json")
    n = st["n"]
    a1, a2 = st["a1"], st["a2"]

    # 1) Accept honest prover
    listener = socket.create_server((HOST, atk_listen_port), reuse_port=False)
    print(Back.BLUE + f"[HK MF] Listening on 127.0.0.1:{atk_listen_port} for honest prover..." + Style.RESET_ALL)
    pconn, paddr = listener.accept()
    print(Back.YELLOW + f"[HK MF] Honest prover connected from {paddr}" + Style.RESET_ALL)
    pjs = JSONSocket(pconn)

    # 2) Connect to verifier
    print(Back.BLUE + f"[HK MF] Connecting to verifier {ver_host}:{ver_port} ..." + Style.RESET_ALL)
    vconn = socket.create_connection((ver_host, ver_port))
    vjs = JSONSocket(vconn)
    print(Back.GREEN + "[HK MF] Connected to verifier." + Style.RESET_ALL)

    # 3) MF loop
    for i in range(n):
        vmsg = vjs.recv()
        assert vmsg["type"] == "challenge"
        ci = vmsg["ci"]

        # Early guessed response to meet verifier timing
        guessed_ci = random.choice([1, 2])
        early_ri = a1[i] if guessed_ci == 1 else a2[i]
        vjs.send({"type": "response", "round": i, "ri": early_ri})
        print(f"[HK MF] Round {i+1}: real ci={ci}, sent EARLY ri={early_ri} (guess={guessed_ci})")

        # Sending the challenge to the prover
        # If you don't do this, the prover logic doesn't work
        pjs.send(vmsg)
        presp = pjs.recv()
        print(f"[HK MF] Honest prover late ri={presp['ri']}")

    # 4) Read final decision from verifier, then FORWARD it to the honest prover
    final = vjs.recv()
    print(f"[HK MF] Verifier final decision: {final}")
    try:
        pjs.send(final)
    except Exception as e:
        print(f"[HK MF] Warning: failed to forward final to prover: {e}")

    if final.get("decision") == "ACCEPT":
        print(Back.GREEN + "[HK MF] Mafia fraud SUCCESSFUL" + Style.RESET_ALL)
    else:
        print(Back.RED + "[HK MF] Mafia fraud rejected" + Style.RESET_ALL)


    time.sleep(0.25)
    vjs.close()
    pjs.close()
    listener.close()



# ---------------------------------------
# Terrorist Fraud (knows a1,a2)
# ---------------------------------------

def hk_tf(ver_host=HOST, ver_port=VERIFIER_PORT):
    st = load_json(f"{STATE_DIR}/hk_attacker_state.json")
    n = st["n"]
    a1, a2 = st["a1"], st["a2"]

    print(Back.YELLOW + "[HK TF] Connecting to verifier (colluding attacker)..." + Style.RESET_ALL)
    with socket.create_connection((ver_host, ver_port)) as conn:

        js = JSONSocket(conn)

        for i in range(n):
            vmsg = js.recv()
            assert vmsg["type"] == "challenge"
            ci = vmsg["ci"]

            ri = a1[i] if ci == 1 else a2[i]
            js.send({"type": "response", "round": i, "ri": ri})
            print(f"[HK TF] Round {i+1}: ci={ci}, ri={ri}")

        final = js.recv()
        if final["decision"] == "ACCEPT":
            print(Back.GREEN + "[HK TF] Terrorist fraud SUCCESSFUL" + Style.RESET_ALL)
        else:
            print(Back.RED + "[HK TF] Terrorist fraud rejected" + Style.RESET_ALL)

        js.close()



if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["df", "mf_in", "mf_out", "tf"])
    ap.add_argument("--ver-port", type=int, default=VERIFIER_PORT)
    ap.add_argument("--mf-listen", type=int, default=ATTACKER_PORT)
    args = ap.parse_args()

    if args.mode == "df":
        hk_df(ver_port=args.ver_port)
    elif args.mode == "mf_in":
        hk_mf_prover_in_range(ver_port=args.ver_port, atk_listen_port=args.mf_listen)
    elif args.mode == "mf_out":
        hk_mf_prover_out_of_range(ver_port=args.ver_port, atk_listen_port=args.mf_listen)
    elif args.mode == "tf":
        hk_tf(ver_port=args.ver_port)