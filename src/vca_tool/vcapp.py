# -*- coding: utf-8 -*-
from subprocess import run
from pathlib import Path
import sys, os, re
import click

def match_element_name(name):
    """
    Match the element name in the UPF file.
    """
    element_pattern = r'([A-Za-z]{1,2})'
    match = re.match(element_pattern, name)
    if match:
        return match.group(1)
    else:
        raise ValueError(f"Invalid PP name {name}")

def make_vcapp(ppa, ppb, x:float, fname=None, path_virtual=None):

    # Get Path to "virtual_v2.x"
    if path_virtual is not None:
        path_virtual=Path(path_virtual)
    elif os.getenv("PATH_VIRTUAL") is not None:
        # Read from environment variable
        path_virtual = Path(os.getenv("PATH_VIRTUAL"))
    else:
        # Try to find virtual_v2.x in the system path
        try:
            path_virtual=run("which virtual_v2.x",shell=True, capture_output=True,text=True).stdout.strip()
            path_virtual=Path(path_virtual)
        except:
            raise FileNotFoundError(f"virtual_v2.x not found. Please specify the path to virtual_v2.x")
    if not path_virtual.exists():
        raise FileNotFoundError(f"Path to virtual_v2.x {path_virtual.absolute()} not found")
    
    path_a=Path(ppa).absolute()
    path_b=Path(ppb).absolute()
        
    if not path_a.exists():
        raise FileNotFoundError(f"PP {path_a.absolute()} not found")
    if not path_b.exists():
        raise FileNotFoundError(f"PP {path_b.absolute()} not found")


    if x<=0.0 or x>1:
        raise ValueError(f"x value must be in (0:1]")
    y=1.0-x
    x='{:.3f}'.format(round(x, 3)).rstrip('0').rstrip('.')


    elem_a = match_element_name(ppa)
    elem_b = match_element_name(ppb)

    # run(["echo",ppa,ppb,x])
    created_name="NewPseudo.UPF"
    default_name=f"{elem_a}_{elem_b}_{x}.UPF"

    if fname is None:
        dest=Path.cwd()
        fname=default_name

    if Path(fname).is_dir():
        if not fname.exists():
            os.makedirs(fname)
        dest = Path(fname).absolute()
        fname=default_name
    else:
        dest = Path(fname).absolute().parent
        fname= Path(fname).name
        fname=fname.replace("$A", elem_a)
        fname=fname.replace("$B", elem_b)
        fname=fname.replace("$x", x)
        if not fname.endswith(".UPF"):
            fname=fname + ".UPF"
    # With VCA, for the reason of interpolation, mesh of PP_A should be larger than that of PP_B
    # NOT TRUE: It seems depending on a machine(?!) 

    # size_a=extract_mesh_size(ppa)
    # size_b=extract_mesh_size(ppb)
    # if size_a > size_b:
    #     command1 = f'echo "{path_a}\n{path_b}\n{x}" | {path_virtual.absolute()}'
    # else:
    #     command1 = f'echo "{path_b}\n{path_a}\n{y}" | {path_virtual.absolute()}'
    
    # Just run it twice
    try:
        command1 = f'echo "{path_a}\n{path_b}\n{x}" | {path_virtual.absolute()}'
        print(f"Running command: {command1}")
        virtual_out=run(command1, shell=True, cwd=dest, capture_output=True, text=True).stdout
        inspect_virtual(virtual_out)
    except:
        command1 = f'echo "{path_b}\n{path_a}\n{y}" | {path_virtual.absolute()}'
        print("Failed. Try again.")
        print(f"Running command: {command1}")
        virtual_out=run(command1, shell=True, cwd=dest, capture_output=True, text=True).stdout
        inspect_virtual(virtual_out)

    # print(f"Run command:\n {command1}")

    command2 = f'mv {created_name} {fname}'
    # Because UpfData in AiiDA does not accept "Xx" as element symbol,
    # we replace it with the symbol of element A
    command3 = f'sed -i -e "s/Xx/{elem_a}/g" {fname}'
    print(f"Running command: {command2}")
    run(command2, shell=True, cwd=dest)
    print(f"Running command: {command3}")
    run(command3, shell=True,cwd=dest)
    return fname

def extract_mesh_size(pp_path):
    with open(pp_path, 'r') as f:
        lines = f.readlines()
    
    for line in lines:
        if line.strip().startswith('<PP_MESH'):
            mesh_line=line
            break

    pattern = r'mesh\s*=\s*"([^"]+)"'
    match = re.search(pattern, mesh_line)
    try:
        mesh_size = match.group(1)
        return int(mesh_size)
    except:
        raise ValueError(f"Faild to find mesh size on {mesh_line} in {pp_path}")
    
def inspect_virtual(out):
    if "Error" in out:
        if "different rinner" in out:
            raise ValueError("Error in routine Virtual (3):\ndifferent rinner are not implemented (yet)")
        else:
            raise ValueError("Error in routine Virtual")
    
@click.command()
@click.argument('ppa')
@click.argument('ppb')
@click.argument('x', type=float)
@click.option('--file', '-f', default=None, help="Output file or directory")
# @click.option('--dest', '-o', default=None, help="Destination directory")
@click.option('--path_virtual', '-v', default=None, help="Path to virtual_v2.x")
# @click.option('--location/--name', '-l/-n', help="Use location (path) to PP or name of it", default=True)
def main(ppa,ppb,x, file, path_virtual):
    # if len(sys.argv) < 4:
    #     raise ValueError("Usage: python make_vcapp.py A.UPF B.UPF <x value [0:1] of Ax+B(1-x)>")
    # ppa=Path(sys.argv[1])
    # ppb=Path(sys.argv[2])
    # try:
    #     x=(float(sys.argv[3]))
    # except:
    #     raise ValueError(f"x value must be a float")
    
    # try:
    #     dest=sys.argv[4]
    # except:
    #     dest="./"
    make_vcapp(ppa, ppb, x, fname=file, path_virtual=path_virtual)

if __name__ == "__main__":
    main()