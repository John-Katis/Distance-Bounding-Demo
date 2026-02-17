import socket, argparse, time
from json_util import JSONSocket, load_json
from colorama import Back, Style

HOST = "127.0.0.1"
VERIFIER_PORT = 5001
STATE_DIR = "./states"



def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default=HOST)
    ap.add_argument("--port", type=int, default=VERIFIER_PORT)
    ap.add_argument("--delay-ms", type=float, default=0.0, help="Delay each response (simulate distant/dishonest prover)")
    args = ap.parse_args()

    st = load_json(f"{STATE_DIR}/hk_prover_state.json")
    a1, a2 = st["a1"], st["a2"]
    n = st["n"]

    with socket.create_connection((args.host, args.port)) as conn:

        js = JSONSocket(conn)
        print(Back.YELLOW + f"[HK Prover] Connected to {args.host}:{args.port}\n" + Style.RESET_ALL)

        for _ in range(n):
            msg = js.recv()
            assert msg["type"] == "challenge"

            i, ci = msg["round"], msg["ci"]
            ri = (
                a1[i] if ci == 1 else a2[i]
            )

            if args.delay_ms > 0:
                time.sleep(args.delay_ms / 1000.0)

            js.send({"type": "response", "round": i, "ri": ri})
            print(f"[HK P] Responded round {i+1} with ri={ri} (ci={ci})")

        final = js.recv()
        if final["decision"] == "ACCEPT":
            print(Back.GREEN + "[HK P] Verifier accepted! (proximity & knowledge verified)" + Style.RESET_ALL)
        else:
            print(Back.RED + "[HK P] Verifier rejected!" + Style.RESET_ALL)

        js.close()

if __name__ == "__main__":
    main()