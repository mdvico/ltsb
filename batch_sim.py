#!/home/mvico/Documents/projects/python/ltsb/venv/bin/python

import argparse
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
        if (args.debug):
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
        if (args.debug):
            print("Corners:")
            pp(corners)
            print()
except:
    corners = []
    print("No corner file was supplied, assuming default Spice conditions and/or the ones present on the netlist.")

try:
    with open(args.simulations) as data:
        simulations = yaml.load(data, Loader = yaml.FullLoader)
        if (args.debug):
            print("Simulations:")
            print()
except:
    simulations = []
    print("No simulation file was supplied, assuming simulations present on the netlist.")

sims_run = []
cmdline_extra_switches = ['-ascii']

LTCs = []
for netlist in netlists:
    LTCs.append(SimCommander(netlist["netlist"], parallel_sims = 8))

for LTC in LTCs:
    LTC.add_LTspiceRunCmdLineSwitches(cmdline_extra_switches)
    for corner in corners:
        LTC.add_instructions(f".temp {corner['temperature']}")
        for simulation in simulations:
            if simulation.get("instructions") is not None:
                LTC.add_instructions(f"{simulation['instructions']}")

            print("Before")
            pp(LTC.netlist)
            print(f"{simulation['simulation']}")
            LTC.add_instructions(f"{simulation['simulation']}")
            print("After")
            pp(LTC.netlist)
            # LTspice no toma a 'TEMP' como un parámetro para reemplazar a '.temp'
            # LTC.set_parameters(TEMP = corner["temperature"])
            LTC.set_component_value("VVDD", corner['VDD'])
            # LTC.set_component_value("VVSS", corner['VSS'])
            for value in simulation["values"]:
                for element, values in value.items():
                    for value in values:
                        LTC.set_component_value(element, value)
                        sims_run.append(f"Running file: {netlist} - {simulation['simulation']} - VDD = {corner['VDD']} - TEMP = {corner['temperature']} - Swap/Sweep = {element} = {value}")
                        LTC.run()

            try:
                print(LTC.netlist)
                LTC.remove_instructions(f"{simulation['simulation']}\n")
                print(f"Successfuly removed {simulation['simulation']}")
            except:
                print(f"Tried to remove {simulation['simulation']} and failed on netlist {netlist}")
            # if simulation.get("instructions") is not None:
                try:
                    LTC.remove_instructions(f"{simulation['instructions']}\n")
                    print(f"Successfuly removed {simulation['instructions']}")
                except:
                    print(f"Tried to remove {simulation['instructions']} and failed!")
        try:
            LTC.remove_instructions(f".temp {corner['temperature']}\n")
            print(f"Successfuly removed .temp {corner['temperature']}")
        except:
            print(f"Tried to remove .temp {corner['temperature']} and failed!")
    LTC.wait_completion()  # Waits for the LTSpice simulations to complete
    LTC.reset_netlist()

# LTC.wait_completion()  # Waits for the LTSpice simulations to complete
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
