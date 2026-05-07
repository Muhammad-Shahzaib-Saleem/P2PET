import json
import time
import requests

from concurrent.futures import ThreadPoolExecutor

# =========================================================
# LOAD CONFIG
# =========================================================

with open("config.json") as f:
    config = json.load(f)

API_BASE = config["api_base_url"]
POLL_INTERVAL = config["poll_interval"]

with open("rounds.json") as f:
    rounds_data = json.load(f)["rounds"]

# =========================================================
# PHASE ENUMS
# =========================================================

PHASES = {
    0: "DataSubmission",
    1: "Execution",
    2: "EnergyTransfer"
}

# =========================================================
# TRACKERS
# =========================================================

registered_nodes = set()

submitted_rounds = set()

execution_done = set()

# =========================================================
# HELPERS
# =========================================================

def get_status():

    r = requests.get(
        f"{API_BASE}/contract/status"
    )

    return r.json()


# =========================================================
# REGISTER NODE
# =========================================================

def register_node(hostname):

    r = requests.post(
        f"{API_BASE}/dynamic_register",
        params={
            "hostname": hostname
        }
    )

    return r.json()


# =========================================================
# SUBMIT DATA
# =========================================================

def submit_data(hostname, role, energy, price):

    r = requests.post(
        f"{API_BASE}/dynamic_submit_data",
        params={
            "hostname": hostname,
            "role": role,
            "energy": energy,
            "price": price
        }
    )

    return r.json()


# =========================================================
# HASH PARTICIPANTS
# =========================================================

def hash_participants(hostname):

    r = requests.post(
        f"{API_BASE}/Dynamic_hash_participants",
        params={
            "hostname": hostname
        }
    )

    return r.json()


# =========================================================
# SUBMIT EXECUTION RESULT
# =========================================================

def submit_execution(hostname):

    r = requests.post(
        f"{API_BASE}/dynamic_submit_execution_result",
        params={
            "hostname": hostname
        }
    )

    return r.json()


# =========================================================
# VERIFY EXECUTION
# =========================================================

def verify_execution(hostname):

    r = requests.post(
        f"{API_BASE}/dynamic_verify_execution",
        params={
            "hostname": hostname
        }
    )

    return r.json()


# =========================================================
# MAIN LOOP
# =========================================================

def main():

    print("\nStarting Energy Trading Automation...\n")

    while True:

        try:

            # =================================================
            # GET CONTRACT STATUS
            # =================================================

            status = get_status()

            current_round = str(
                status["current_round"]
            )

            current_phase = status[
                "current_phase"
            ]

            time_remaining = status.get(
                "time_remaining",
                0
            )

            print("\n======================================")
            print(f"ROUND           : {current_round}")
            print(f"PHASE           : {PHASES[current_phase]}")
            print(f"TIME REMAINING  : {time_remaining} sec")
            print("======================================")

            # =================================================
            # DATA SUBMISSION PHASE
            # =================================================

            if current_phase == 0:

                if current_round not in submitted_rounds:

                    if current_round in rounds_data:

                        participants = rounds_data[
                            current_round
                        ]

                        total = len(participants)

                        print(
                            f"\nSubmitting data "
                            f"for round {current_round}"
                        )

                        # =============================================
                        # THREAD POOL
                        # =============================================

                        executor = ThreadPoolExecutor(
                            max_workers=2
                        )

                        # =============================================
                        # REGISTER FIRST 2 NODES
                        # =============================================

                        initial_registers = min(2, total)

                        for i in range(initial_registers):

                            hostname = participants[i][
                                "hostname"
                            ]

                            if hostname not in registered_nodes:

                                try:

                                    print(
                                        f"\nInitial register -> "
                                        f"{hostname}"
                                    )

                                    reg_result = register_node(
                                        hostname
                                    )

                                    print(reg_result)

                                    registered_nodes.add(
                                        hostname
                                    )

                                    time.sleep(1)

                                except Exception as e:

                                    print(
                                        f"Initial register error: {e}"
                                    )

                        # =============================================
                        # PIPELINED PARALLEL FLOW
                        # =============================================

                        for i in range(total):

                            current = participants[i]

                            current_hostname = current[
                                "hostname"
                            ]

                            current_role = current[
                                "role"
                            ]

                            current_energy = current[
                                "energy"
                            ]

                            current_price = current[
                                "price"
                            ]

                            futures = []

                            # =========================================
                            # SUBMIT CURRENT NODE
                            # =========================================

                            print(
                                f"\nSubmitting -> "
                                f"{current_hostname}"
                            )

                            futures.append(

                                executor.submit(
                                    submit_data,
                                    current_hostname,
                                    current_role,
                                    current_energy,
                                    current_price
                                )
                            )

                            # =========================================
                            # REGISTER NEXT NODE
                            # =========================================

                            next_index = i + 2

                            if next_index < total:

                                next_hostname = participants[
                                    next_index
                                ]["hostname"]

                                if next_hostname not in registered_nodes:

                                    print(
                                        f"Parallel register -> "
                                        f"{next_hostname}"
                                    )

                                    futures.append(

                                        executor.submit(
                                            register_node,
                                            next_hostname
                                        )
                                    )

                                    registered_nodes.add(
                                        next_hostname
                                    )

                            # =========================================
                            # WAIT FOR THREADS
                            # =========================================

                            for future in futures:

                                try:

                                    result = future.result()

                                    print(result)

                                except Exception as e:

                                    print(
                                        f"Thread error: {e}"
                                    )

                            time.sleep(1)

                        executor.shutdown(wait=True)

                        # =============================================
                        # HASH PARTICIPANTS
                        # =============================================

                        try:

                            leader = participants[0][
                                "hostname"
                            ]

                            print(
                                f"\nHashing participants "
                                f"from leader {leader}"
                            )

                            hash_result = hash_participants(
                                leader
                            )

                            print(hash_result)

                        except Exception as e:

                            print(
                                f"Hash error: {e}"
                            )

                        submitted_rounds.add(
                            current_round
                        )

                    else:

                        print(
                            f"\nNo round data found "
                            f"for round {current_round}"
                        )

            # =================================================
            # EXECUTION PHASE
            # =================================================

            elif current_phase == 1:

                if current_round not in execution_done:

                    print(
                        "\nExecution phase started"
                    )

                    participants = rounds_data.get(
                        current_round,
                        []
                    )

                    # =============================================
                    # SUBMIT EXECUTION RESULTS
                    # MAXIMUM 5 NODES
                    # =============================================

                    executor = ThreadPoolExecutor(
                        max_workers=5
                    )

                    futures = []

                    for p in participants[:5]:

                        hostname = p["hostname"]

                        print(
                            f"\nSubmitting execution "
                            f"from {hostname}"
                        )

                        futures.append(

                            executor.submit(
                                submit_execution,
                                hostname
                            )
                        )

                    # =============================================
                    # WAIT FOR EXECUTION RESULTS
                    # =============================================

                    for future in futures:

                        try:

                            result = future.result()

                            print(result)

                        except Exception as e:

                            print(
                                f"Execution thread error: {e}"
                            )

                    executor.shutdown(wait=True)

                    # =============================================
                    # VERIFY EXECUTION
                    # =============================================

                    try:

                        leader = participants[0][
                            "hostname"
                        ]

                        print(
                            f"\nVerifying execution "
                            f"from leader {leader}"
                        )

                        verify_result = verify_execution(
                            leader
                        )

                        print(verify_result)

                    except Exception as e:

                        print(
                            f"Verify error: {e}"
                        )

                    execution_done.add(
                        current_round
                    )

            # =================================================
            # ENERGY TRANSFER PHASE
            # =================================================

            elif current_phase == 2:

                print(
                    "\nEnergy transfer phase running..."
                )

                print(
                    "Waiting for next round..."
                )

            # =================================================
            # WAIT
            # =================================================

            time.sleep(POLL_INTERVAL)

        except Exception as e:

            print(f"\nMAIN LOOP ERROR: {e}")

            time.sleep(5)


# =========================================================
# START
# =========================================================

if __name__ == "__main__":

    main()