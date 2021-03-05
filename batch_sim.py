#!/home/mvico/projects/ltsb/venv/bin/python

import argparse
import os
import pdb
import sys
from pathlib import Path
from pprint import pprint as pp

import yaml
from PyLTSpice.LTSpice_RawRead import LTSpiceRawRead
from PyLTSpice.LTSpiceBatch import SimCommander

parser = argparse.ArgumentParser(description = "Schedule batch simulations for LTSpice.")
parser.add_argument("--netlist", type = str, dest = "netlist", required = True, help = "'asc' or 'net'. Input file.")
parser.add_argument("--simulations", type = str, dest = "simulations", required = False, help = "'yaml' file with simulation instructions. Input file.")
parser.add_argument("--corners", type = str, dest = "corners", required = False, help = "'yaml' file with corners for simulations. Input file.")
parser.add_argument("--debug", action = "store_true", default = False, required = False, help = "Increase verbosity and see internal values.")
args = parser.parse_args()

try:
    with open(args.netlist) as data:
        netlists = yaml.load(data, Loader = yaml.FullLoader)
        if args.debug:
            print("Netlists:")
            pp(netlists)
            print()
except:
    netlists = []
    print("No netlist file was supplied, resuming.")
    exit()

try:
    with open(args.corners) as data:
        corners = yaml.load(data, Loader = yaml.FullLoader)
        if args.debug:
            print("Corners:")
            pp(corners)
            print()
except:
    corners = []
    print("No corner file was supplied, assuming default Spice conditions and/or the ones present on the netlist.")

try:
    with open(args.simulations) as data:
        simulations = yaml.load(data, Loader = yaml.FullLoader)
        if args.debug:
            print("Simulations:")
            pp(simulations)
            print()
except:
    simulations = []
    print("No simulation file was supplied, assuming simulations present on the netlist.")

sims_run = []
cmdline_extra_switches = ["-ascii"]
verbose = False

def post_proc(raw, log):
    # print(a)
    # print(b)
    global verbose
    print("Finished simulation. Raw file: {} - Log file: {}".format(raw, log) if verbose else '')

LTCs = []
for netlist in netlists:
    LTCs.append(SimCommander(netlist["netlist"], parallel_sims = 12))

for LTC in LTCs:
    LTC.add_LTspiceRunCmdLineSwitches(cmdline_extra_switches)

    if args.debug:
        print("Original netlist:")
        pp(LTC.netlist)

    for corner in corners:
        if corner.get("temperature") is not None:
            LTC.add_instructions(f".TEMP {corner['temperature']}")
        for simulation in simulations:
            if simulation.get("instructions") is not None:
                LTC.add_instructions(f"{simulation['instructions']}")

            if simulation.get("simulation") is None:
                print("No simulation type is present. Please check your simulation YAML file.")
                exit()
            LTC.add_instructions(f"{simulation['simulation']}")

            # LTspice no toma a 'TEMP' como un parámetro para reemplazar a '.temp'
            # LTC.set_parameters(TEMP = corner["temperature"])

            if corner.get("VDD") is not None:
                try:
                    LTC.set_component_value("VVDD", corner['VDD'])
                except Exception as e:
                    print(f"WARNING: {e}")

            if corner.get("VSS") is not None:
                try:
                    LTC.set_component_value("VVSS", corner['VSS'])
                except Exception as e:
                    print(f"WARNING: {e}")

            if simulation.get("values") is not None:
                for value in simulation["values"]:
                    for element, values in value.items():
                        for value in values:
                            LTC.set_component_value(element, value)
                            sims_run.append(f"Running file: {netlist} - {simulation['simulation']} - VDD = {corner['VDD']} - TEMP = {corner['temperature']} - Swap/Sweep = {element} = {value}")

                            if args.debug:
                                print("Modified netlist about to run:")
                                pp(LTC.netlist)
                                input("Ready?")

                            circuit_path, _ = os.path.split(LTC.netlist_file)
                            netlist_safe_name = simulation.get("description").replace(" ", "-").replace(".", "")
                            temp = corner.get("temperature")
                            volt = corner.get("VDD")

                            netlist_final_path = circuit_path + os.path.sep + netlist_safe_name + f"_{temp}_" + f"{volt}_" + f"{element}_" + f"{value}"
                            netlist_final_path = f"{netlist_final_path.replace('.', 'p')}.net"

                            LTC.run(run_filename = netlist_final_path, callback = post_proc)

            try:
                LTC.remove_instructions(f"{simulation['simulation']}")
                # print(f"Successfuly removed {simulation['simulation']}")
            except:
                print(f"WARNING: Tried to remove {simulation['simulation']} and failed on netlist {netlist}")
            if simulation.get("instructions") is not None:
                try:
                    LTC.remove_instructions(f"{simulation['instructions']}")
                    # print(f"Successfuly removed {simulation['instructions']}")
                except:
                    print(f"WARNING: Tried to remove {simulation['instructions']} and failed!")
        try:
            LTC.remove_instructions(f".TEMP {corner['temperature']}")
            # print(f"Successfuly removed .TEMP {corner['temperature']}")
        except:
            print(f"WARNING: Tried to remove .TEMP {corner['temperature']} and failed!")
    LTC.wait_completion()  # Waits for the LTSpice simulations to complete
    # LTC.reset_netlist()

    if args.debug:
        pp(sims_run)

    print(f"Total Simulations: {LTC.runno}")
    print(f"Successful Simulations: {LTC.okSim}")
    print(f"Failed Simulations: {LTC.failSim}")

def sim_scheduler(LTC, simulation, temperature, instructions, VDD, values, **kwargs):
    LTC.add_instructions(f"{simulation}", f".temp {temperature}")
    LTC.add_instructions(f"{instructions}")
    LTC.set_component_value("VVDD", VDD)
    for value in values:
        for element, val in value.items():
            LTC.set_component_value(element, val)
            return LTC

# for model in ("BAT54", "BAT46WJ"):
#     LTC.set_element_model("D1", model)  # Sets the Diode D1 model
for netlist in netlists:
    # LTC = SimCommander(netlist["netlist"], parallel_sims = 8)
    for simulation in simulations:
        for corner in corners:
            pass
            # pp(netlist)
            # pp(simulation)
            # pp(corner)
            # sim_scheduler(LTC, **simulation, **corner)
            # LTC.run()
            # LTC.wait_completion()  # Waits for the LTSpice simulations to complete

if __name__ == "__main__":
    pass
