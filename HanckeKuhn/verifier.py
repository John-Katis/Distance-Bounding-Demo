import socket, time
from json_util import JSONSocket, load_json
from colorama import Back, Style

HOST = "127.0.0.1"
PORT = 5001
STATE_DIR = "./states"
OK = "\033[32mOK\033[0m"
BAD = "\033[31mBAD\033[0m"
LATE = "\033[31mLATE\033[0m"



def main():
    st = load_json(f"{STATE_DIR}/hk_verifier_state.json")
    n = st["n"]
    thr = st["threshold"]
    a1, a2 = st["a1"], st["a2"]

    print(Back.BLUE + f"\n[HK Verifier] Listening on {HOST}:{PORT}" + Style.RESET_ALL)
    with socket.create_server((HOST, PORT), reuse_port=False) as srv:
        conn, addr = srv.accept()
        print(Back.GREEN + f"[HK Verifier] Connected by {addr}\n" + Style.RESET_ALL)

        js = JSONSocket(conn)
        results = []

        for i in range(n):
            ci = 1 if (i + 1) % 2 else 2  # deterministic; you can randomize if you prefer
            js.send({"type": "challenge", "round": i, "ci": ci})
            t0 = time.perf_counter()
            resp = js.recv()
            t1 = time.perf_counter()

            dt = t1 - t0
            ri = resp.get("ri")
            expected = a1[i] if ci == 1 else a2[i]
            ok_bit = (ri == expected)
            ok_time = (dt <= thr)

            print(f"[HK V] Round {i+1}/{n}: ci={ci} | ri={ri} | expected={expected} | Δt={dt:.6f}s | bit={OK if ok_bit else BAD} | time={OK if ok_time else LATE}")

            results.append({"round": i + 1, "ci": ci, "ri": ri, "expected": expected, "dt": dt,
                            "ok_bit": ok_bit, "ok_time": ok_time})

        all_bits_ok = all(r["ok_bit"] for r in results)
        all_times_ok = all(r["ok_time"] for r in results)

        print(Back.BLUE + "\n[HK V] Summary:" + Style.RESET_ALL)
        print(f"  All bits correct?  {all_bits_ok}")
        print(f"  All times within?  {all_times_ok}  (threshold={thr}s)")

        if all_bits_ok and all_times_ok:
            print(Back.GREEN + "  ==> ACCEPT ✔ (HK proximity & knowledge verified)\n" + Style.RESET_ALL)
            js.send({"type": "final", "decision": "ACCEPT"})
        else:
            print(Back.RED + "  ==> REJECT ✘\n" + Style.RESET_ALL)
            js.send({"type": "final", "decision": "REJECT"})
        
        time.sleep(0.5)
        js.close()



if __name__ == "__main__":
    main()