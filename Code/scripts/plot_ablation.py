import argparse
from witness3d.plotting import plot_ablation

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("index")
    p.add_argument("output")
    args = p.parse_args()
    plot_ablation(args.index, args.output)

