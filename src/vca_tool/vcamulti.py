# %%
from pathlib import Path
from subprocess import run
import sys, os, re
import click
import itertools
import math
from vca_tool.vcapp import make_vcapp, match_element_name

def combinatorial_list(elements, n_components=None, max_num=10):
    """
    Generate all possible combinations of elements with n_components.
    """
    # Check if the number of components is valid
    if n_components is None:
        n_components = len(elements)
    if n_components < 2 or n_components > len(elements):
        raise ValueError(f"n_components must be between 2 and {len(elements)}")

    # Generate all combinations of elements
    combinations = itertools.combinations(elements, n_components)
    
    # Create a list to store the results
    results = []


    # Iterate over each combination
    for combo in combinations:
        # Generate all possible weight distributions
        for weights in itertools.product(range(1, max_num), repeat=n_components):
            total_weight = sum(weights)
            if total_weight != max_num:
                continue
            # if math.gcd(*weights) != 1:
            #     continue
            results.append((combo, weights))
    return results

# %%
def multiple_vca(pseudos, outdir=None, remove_tmp=True, path_virtual=None,
                  n_components=None, max_num=10):
    if outdir is None:
        outdir = Path.cwd()
    else:
        outdir = Path(outdir)
        if not outdir.exists():
            os.makedirs(outdir)

    elements = [match_element_name(p) for p in pseudos]
    comb_list=combinatorial_list(elements, n_components=n_components, max_num=max_num)
    for combo, weights in comb_list:
        tot_weight = 0
        A=combo[0]+str(weights[0])
        ppa=pseudos[0]
        fname_old=None
        for i in range(len(weights)-1):
            B=combo[i+1]+str(weights[i+1])
            ppb=pseudos[i+1] 
            tot_weight += weights[i]
            x=float(tot_weight)/(tot_weight+weights[i+1])
            # print(f"{A} {B} {x:.3f}")
            fname=outdir/f"{A+B}.UPF"
            print(A,B,f"{x:.3f}",fname)
            if fname_old is None:
                # print(f"make_vcapp({ppa},{ppb},{x:.3f},fname={fname}, path_virtual={path_virtual})")
                make_vcapp(ppa,ppb,x,fname=str(fname), path_virtual=path_virtual)
            else:
                # print(f"make_vcapp({ppa},{ppb},{x:.3f},fname={fname}, path_virtual={path_virtual})")
                make_vcapp(fname_old,ppb,x,fname=str(fname), path_virtual=path_virtual)
                if remove_tmp:
                    print(f"remove {fname_old}")
                    os.remove(fname_old)
            fname_old=fname
            A += B

@click.command()
@click.argument('pseudos', nargs=-1)
@click.option('--outdir', '-o', default=None, help="Output directory")
@click.option('--remove_tmp/--no-remove_tmp', default=True, help="Remove temporary files")
@click.option('--path_virtual', '-v', default=None, help="Path to virtual_v2.x")
@click.option('--n_components', '-n', default=None, type=int, help="Number of components")
@click.option('--max_num', '-m', default=10, type=int, help="Maximum number of components")
def main(pseudos, outdir, remove_tmp, path_virtual, n_components, max_num):
    """
    Generate all possible combinations of elements with n_components.
    """
    # Check if the number of components is valid
    if len(pseudos) < 2:
        raise ValueError(f"At least two pseudos are required")
    if len(pseudos) > 10:
        raise ValueError(f"Maximum number of pseudos is 10")
    
    # Call the function to generate VCA files
    multiple_vca(pseudos, outdir=outdir, remove_tmp=remove_tmp,
                  path_virtual=path_virtual, n_components=n_components,
                  max_num=max_num)
# %%
