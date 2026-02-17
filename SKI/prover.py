# SKI/prover.py
import socket, argparse, time
from colorama import Back, Style
from json_util import JSONSocket, load_json

HOST = "127.0.0.1"
VERIFIER_PORT = 6001
STATE_DIR = "./states"



def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default=HOST)
    ap.add_argument("--port", type=int, default=VERIFIER_PORT)
    ap.add_argument("--delay-ms", type=float, default=0.0)
    args = ap.parse_args()

    st = load_json(f"{STATE_DIR}/ski_prover_state.json")
    n = st["n"]
    a1, a2, xprime = st["a1"], st["a2"], st["xprime"]

    with socket.create_connection((args.host, args.port)) as conn:
        js = JSONSocket(conn)

        print(Back.YELLOW +
              f"[SKI Prover] Connected to {args.host}:{args.port}\n" + Style.RESET_ALL)

        for _ in range(n):
            msg = js.recv()
            assert msg["type"] == "challenge"

            i, ci = msg["round"], msg["ci"]
            ri = (
                a1[i] if ci == 1 else
                a2[i] if ci == 2 else
                (xprime[i] ^ a1[i] ^ a2[i])
            )

            if args.delay_ms > 0:
                time.sleep(args.delay_ms/1000.0)

            js.send({"type":"response","round":i,"ri":ri})
            print(f"[SKI P] Responded round {i+1} with ri={ri} (ci={ci})")

        final = js.recv()
        if final["decision"] == "ACCEPT":
            print(Back.GREEN + "[SKI P] Verifier accepted!" + Style.RESET_ALL)
        else:
            print(Back.RED + "[SKI P] Verifier rejected!" + Style.RESET_ALL)

        js.close()



if __name__ == "__main__":
    main()