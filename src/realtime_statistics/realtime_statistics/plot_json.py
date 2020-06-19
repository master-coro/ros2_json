# Copyright 2020 Erwin Lejeune ; Sampreet Sarkar
# Under MIT Licence

import rclpy
from rclpy.node import Node
import matplotlib.pyplot as plt
import json
import argparse
import sys
import subprocess
import random
import pathlib


MODE = 0 # 0 for Driver, 1 for Controller stats

cmd1 = subprocess.Popen(['dmesg'], stdout=subprocess.PIPE)
cmd2 = subprocess.Popen(['grep', '-i', 'xenomai'], stdin=cmd1.stdout, stdout=subprocess.PIPE)
output, err = cmd2.communicate()

if "Xenomai" in str(output):
    RT = 1
else:
    RT = 0

def get_args():
    parser = argparse.ArgumentParser(
        description="Real-Time Statistics Plotter."
    )
    parser.add_argument("-n", "--node",
                        action="store",
                        type=str,
                        required=True,
                        help="Choose 'controller' or 'driver' stats.",
                        default="controller")
    return parser.parse_args(sys.argv[4:])

class PlotJson(Node):

    def __init__(self):
        super().__init__('node')

        default_path = str(pathlib.Path(__file__).parent.absolute())
        default_path = default_path.replace('/build/realtime_statistics/realtime_statistics', '')

        self.default_data_path = default_path + "/ros2_realtime_statistics/data/"

        if RT == 0:
            self.driver_stats_path = default_path + "/ros2_realtime_statistics/data/driver_nrt_stats.json"
            self.controller_stats_path = default_path + "/ros2_realtime_statistics/data//controller_nrt_stats.json"
        else:
            self.driver_stats_path = default_path + "/ros2_realtime_statistics/data/driver_rt_stats.json"
            self.controller_stats_path = default_path + "/ros2_realtime_statistics/data//controller_rt_stats.json"

        self.plot_from_json()

    def read_json_file(self, path):
        with open(path, "r") as file:
            data = json.load(file)
        return data

    def plot_from_json(self, filepath):
        json_data = self.read_json_file(filepath)
        nlist = self.sorted_data_from_json(json_data)
        if MODE == 1:
            label = "Controller"
        elif MODE == 0:
            label = "Driver"
        else:
            print("Error : mode not supported")
            self.destroy_node()
        self.plot_from_sorted_data(nlist, label)
    
    def sorted_data_from_json(self, json_data):
        n_pts = range(0, int(list(json_data.keys())[-1]) + 1)
        for number_key in json_data:
            for category in json_data[number_key]:
                self.dict_json_sorted[category] = dict()
                for data in json_data[number_key][category]:
                    self.dict_json_sorted[category][data] = []

        for number_key in json_data:
            for category in json_data[number_key]:
                for data in json_data[number_key][category]:
                    self.dict_json_sorted[category][data].append(json_data[number_key][category][data])

        return n_pts
    
    def plot_from_sorted_data(self, n_pts_list, label):
        rt_label = ""
        if RT == 0:
            rt_label = "(NRT Linux) "
        elif RT == 1: 
            rt_label = "(Xenomai) "
        else:
            print("Error, RT mode should be 0 or 1")
            exit()

        self.fig, self.axs = plt.subplots(2, 2, figsize=(12, 8))
        self.fig.suptitle("Real Time " + rt_label + label + " Statistics - Inverted Pendulum")
        rdn_category_key = random.choice(list(self.dict_json_sorted.keys()))
        self.axs[0, 0].plot(n_pts_list, self.dict_json_sorted[rdn_category_key]["jitter_mean_usec"])
        self.axs[0, 0].set_title("Mean Jitters (µs)")
        self.axs[0, 1].plot(n_pts_list, self.dict_json_sorted[rdn_category_key]["jitter_std_usec"])
        self.axs[0, 1].set_title("STD Jitters (µs)")
        self.axs[1, 1].plot(n_pts_list, self.dict_json_sorted[rdn_category_key]["involuntary_context_switches"])
        self.axs[1, 1].set_title("Involuntary Context Switches")
        self.axs[1, 0].plot(n_pts_list, self.dict_json_sorted[rdn_category_key]["jitter_max_usec"])
        self.axs[1, 0].set_title("Max Jitters (µs)")
        if (RT == 0):
            plt.savefig(self.default_data_path + "nrt_" + label + '.png')
        else:
            plt.savefig(self.default_data_path + "rt_" + label + '.png')
        plt.show()

def main(args=get_args):
    rclpy.init(args=args)

    plt_json = PlotJson()

    rclpy.spin_once(plt_json)

    # Destroy the node explicitly
    # (cmdional - otherwise it will be done automatically
    # when the garbage collector destroys the node object)
    plt_json.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
