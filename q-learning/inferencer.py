import numpy as np
import random
import psutil
import time
import os
import sys
import subprocess
import signal
import pickle
import statistics

NVME = "nvme1n1"

def signal_handler(sig, frame):
    with open('pas-qtable.pickle', 'wb') as handle:
        pickle.dump(a.q_table, handle, protocol=pickle.HIGHEST_PROTOCOL)
    sys.exit(0)

class Agent():

    def __init__(self, epsilon, alpha, gamma, decay):
        self.current_status = "0_0_0_0_0"
        self.q_table = {}
        self.init_qtable()
        self.epsilon = epsilon
        self.alpha = alpha
        self.gamma = gamma
        self.decay = decay
        self.num_actions = 36
        self.up_array = [0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0]
        self.dn_array = [0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 0.99]
        self.up_dn_array = [
            [0, 0], [0, 1], [0, 2], [0, 3], [0, 4], [0, 5],
            [1, 0], [1, 1], [1, 2], [1, 3], [1, 4], [1, 5],
            [2, 0], [2, 1], [2, 2], [2, 3], [2, 4], [2, 5],
            [3, 0], [3, 1], [3, 2], [3, 3], [3, 4], [3, 5],
            [4, 0], [4, 1], [4, 2], [4, 3], [4, 4], [4, 5],
            [5, 0], [5, 1], [5, 2], [5, 3], [5, 4], [5, 5],
        ]
        self.up = 0.01
        self.dn = 0.1

        random.seed(1004)

    def start_scenario(self):
        subprocess.Popen("sudo python3 scenario_runner.py".split(), universal_newlines=True)

    def draw_action(self, k):
        if self.epsilon >= 0 and self.epsilon < random.random():
            return self.q_table[k].index(max(self.q_table[k]))
        else:
            return random.randint(0, self.num_actions - 1)

    def update_qvalue(self, action, __cpu, __first, __second, __third, __forth):
        k = self.current_status
        pnlt_score = 0

        if __first:
            pnlt_score += 2**4
        if __second:
            pnlt_score += 2**3
        if __third:
            pnlt_score += 2**2
        if __forth:
            pnlt_score += 2**1
        if pnlt_score == 0:
            pnlt_score += 2**0
        
        reward = ((1/__cpu) + (1/pnlt_score)) * 10
        old_q = self.q_table[k][action]
        self.q_table[k][action] = old_q + self.alpha * (reward + self.gamma * max(self.q_table[k]) - old_q)

    def init_qtable(self):
        # if len(sys.argv) == 2:
        with open("new_10hours.pickle", "rb") as handle:
            self.q_table = pickle.load(handle)

    def get_pid(self, name):
        return subprocess.check_output(f"pidof {name}", universal_newlines=True, shell=True).strip("\n").split(" ")

    def get_cpu_utilization(self):
        buf = []
        v = 5
        poll_pid = 0
        while(v):
            try:
                pids = self.get_pid("fio")
                poll_pid = int(pids[-2])
                py = psutil.Process(poll_pid)
                cpu_usage = os.popen("ps aux | grep " + str(poll_pid) + " | grep -v grep | awk '{print $3}'").read()
                cpu_usage = cpu_usage.replace("\n", "")
                buf.append(float(cpu_usage))
            except:
                continue
        
            v -= 1
            time.sleep(0.1)
        return int(round((sum(buf) / 5), 1) * 10)
    
    def apply_action(self, up, dn):
        up_apply = f"echo {int(up * 1000)} > /sys/block/{NVME}/queue/pas_up"
        dn_apply = f"echo {int(dn * 1000)} > /sys/block/{NVME}/queue/pas_dn"
        os.system(up_apply)
        os.system(dn_apply)

    def do_action(self, action):
        if action > self.num_actions:
            print("invalid action")
            sys.exit(1)

        idx_up, idx_dn = self.up_dn_array[action][0], self.up_dn_array[action][1]
        self.up = self.up_array[idx_up]
        self.dn = self.dn_array[idx_dn]

        self.apply_action(self.up, self.dn)

    def best_action(self, k):
        return self.q_table[k].index(max(self.q_table[k]))

    def read_sysfs(self, path):
        f = open(path, "r")
        data = f.read()
        f.close()
        return int(data.strip("\n"))

    def update_status(self):
        __cpu = self.get_cpu_utilization()
        __fisrt = int(self.read_sysfs(f"/sys/block/{NVME}/queue/pnlt_first"))
        __second = int(self.read_sysfs(f"/sys/block/{NVME}/queue/pnlt_second"))
        __third = int(self.read_sysfs(f"/sys/block/{NVME}/queue/pnlt_third"))
        __forth = int(self.read_sysfs(f"/sys/block/{NVME}/queue/pnlt_forth"))
        if __cpu == 0:
            __cpu = 1
        if __cpu >= 999:
            __cpu = 999
        
        self.current_status = "_".join([str(__cpu), str(__fisrt), str(__second), str(__third), str(__forth)])
        return __cpu, __fisrt, __second, __third, __forth


def env_setting():
    os.system("/home/kesl/prep.sh")
    os.system("modprobe -r nvme && modprobe nvme poll_queues=16")
    os.system("sleep 5")
    os.system(f"echo 0 > /sys/block/{NVME}/queue/io_poll_delay")
    os.system(f"echo 1 > /sys/block/{NVME}/queue/pas_enabled")

a = Agent(0.9, 0.3, 0.002, 0.00001)

while True:
    __cpu, __first, __second, __third, __forth = a.update_status()
    print(a.current_status)
    action = a.best_action(a.current_status)
    a.do_action(action)