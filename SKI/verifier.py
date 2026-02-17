import socket, random, time
from colorama import Back, Style
from json_util import JSONSocket, load_json

HOST = "127.0.0.1"
PORT = 6001
STATE_DIR = "./states"
OK = "\033[32mOK\033[0m"
BAD = "\033[31mBAD\033[0m"
LATE = "\033[31mLATE\033[0m"


def main():
    st = load_json(f"{STATE_DIR}/ski_verifier_state.json")
    n = st["n"]
    a1, a2, xprime = st["a1"], st["a2"], st["xprime"]
    thr = st["threshold"]

    print(Back.BLUE + f"\n[SKI Verifier] Listening on {HOST}:{PORT}" + Style.RESET_ALL)
    with socket.create_server((HOST, PORT), reuse_port=False) as srv:
        conn, addr = srv.accept()
        print(Back.GREEN + f"[SKI Verifier] Connected by {addr}\n" + Style.RESET_ALL)

        js = JSONSocket(conn)
        results = []

        for i in range(n):
            ci = random.choice([1,2,3])
            js.send({"type":"challenge","round":i,"ci":ci})

            t0 = time.perf_counter()
            resp = js.recv()
            t1 = time.perf_counter()
            dt = t1 - t0

            ri = resp.get("ri")
            
            expected = (
                a1[i] if ci == 1 else
                a2[i] if ci == 2 else
                (xprime[i] ^ a1[i] ^ a2[i])
            )

            ok_bit = (ri == expected)
            ok_time = (dt <= thr)

            print(f"[HK V] Round {i+1}/{n}: ci={ci} | ri={ri} | expected={expected} | Δt={dt:.6f}s | bit={OK if ok_bit else BAD} | time={OK if ok_time else LATE}")

            results.append({"round": i + 1, "ci": ci, "ri": ri, "expected": expected, "dt": dt,
                            "ok_bit": ok_bit, "ok_time": ok_time})

        all_bits_ok = all(r["ok_bit"] for r in results)
        all_times_ok = all(r["ok_time"] for r in results)

        if all_bits_ok and all_times_ok:
            print(Back.GREEN + "  ==> ACCEPT ✔ (HK proximity & knowledge verified)\n" + Style.RESET_ALL)
            js.send({"type": "final", "decision": "ACCEPT"})
        else:
            print(Back.RED + "  ==> REJECT ✘\n" + Style.RESET_ALL)
            js.send({"type": "final", "decision": "REJECT"})


        # allow client to read final frame
        time.sleep(0.1)
        js.close()



if __name__ == "__main__":
    main()