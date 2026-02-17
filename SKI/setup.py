import random
from colorama import Back, Style
from json_util import save_json

STATE_DIR = "./states"
N = 16
THRESHOLD_SEC = 0.1  # SKI accepts iff all Δt ≤ threshold and all bits are correct



def prf(key, *values, n=N):
    random.seed(hash((key,) + values))
    return [random.randint(0,1) for _ in range(n)]



def Lmu(x, n=N):
    random.seed(x)
    return [random.randint(0,1) for _ in range(n)]



def main():
    secret_x = 987654321
    NV = random.getrandbits(32)
    NP = random.getrandbits(32)
    L = random.getrandbits(16)

    a1 = prf(secret_x, NP, NV, 1, n=N)
    a2 = prf(secret_x, NP, NV, 2, n=N)
    xprime = Lmu(secret_x, n=N)

    ver_state = {
        "n": N, "NV": NV, "NP": NP, "L": L, "a1": a1, "a2": a2, "xprime": xprime, "threshold": THRESHOLD_SEC,
    }
    prv_state = {
        "n": N, "NV": NV, "NP": NP, "L": L, "a1": a1, "a2": a2, "xprime": xprime
    }
    atk_state = {
        "n": N, "NV": NV, "NP": NP, "a1": a1, "a2": a2
    }

    save_json(f"{STATE_DIR}/ski_verifier_state.json", ver_state)
    save_json(f"{STATE_DIR}/ski_prover_state.json", prv_state)
    save_json(f"{STATE_DIR}/ski_attacker_state.json", atk_state)

    print(Back.GREEN +
          "[SKI SETUP] Wrote ski_verifier_state.json, ski_prover_state.json, ski_attacker_state.json"
          + Style.RESET_ALL)



if __name__ == "__main__":
    main()