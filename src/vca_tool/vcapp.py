# -*- coding: utf-8 -*-
from subprocess import run
from pathlib import Path
import sys, re
import click

def make_vcapp(ppa, ppb, x:float, dest=None, path_virtual=None, precision=3, location=True):

    if dest is None:
        dest=Path.cwd()
    else:
        dest=Path(dest)

    # Get Path to "virtual_v2.x"
    if path_virtual is None:
        # path_virtual=Path(PATH_VIRTUAL)
        try:
            path_virtual=run("which virtual_v2.x",shell=True, capture_output=True,text=True).stdout.strip()
        except:
            raise FileNotFoundError(f"virtual_v2.x not found. Please specify the path to virtual_v2.x")
        path_virtual=Path(path_virtual)
    else:
        path_virtual=Path(path_virtual)

    if not path_virtual.exists():
        raise FileNotFoundError(f"virtual_v2.x not found at {path_virtual.absolute()}")
    if location:
        # Because virtual_v2.x is sometime broken with absolute path, we convert it to relative path
        path_a=Path(ppa).absolute()
        path_b=Path(ppb).absolute()
        if not path_a.exists():
            raise FileNotFoundError(f"PP {path_a.absolute()} not found")
        if not path_b.exists():
            raise FileNotFoundError(f"PP {path_b.absolute()} not found")
                # Because virtual_v2.x is sometime broken with absolute path, we convert it to relative path
        path_a=Path(ppa).absolute()
        path_b=Path(ppb).absolute()
    else:
        path_a=str(ppa)
        path_b=str(ppb)

    if x<=0.0 or x>1:
        raise ValueError(f"x value must be in (0:1]")
    y=1.0-x
    x='{:.3f}'.format(round(x, 3)).rstrip('0').rstrip('.')

    element_pattern = r'([A-Za-z]{1,2})'
    elem_a = re.match(element_pattern, ppa)
    if elem_a is None:
        raise ValueError(f"Invalid PP name {ppa}")
    elem_a = elem_a.group(1)

    elem_b = re.match(element_pattern, ppb)
    if elem_b is None:
        raise ValueError(f"Invalid PP name {ppb}")
    elem_b = elem_b.group(1)

    # run(["echo",ppa,ppb,x])
    created_name="NewPseudo.UPF"
    new_pp_name=f"{elem_a}_{elem_b}_{x}.UPF"

    # cwd=Path.cwd().absolute()

    if dest.is_dir():
        new_pp_name=str(dest.absolute())+"/"+new_pp_name
        # created_name=str(dest.absolute())+"/"+created_name

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
        virtual_out=run(command1, shell=True, cwd=dest, capture_output=True, text=True).stdout
        inspect_virtual(virtual_out)
    except:
        command1 = f'echo "{path_b}\n{path_a}\n{y}" | {path_virtual.absolute()}'
        virtual_out=run(command1, shell=True, cwd=dest, capture_output=True, text=True).stdout
        inspect_virtual(virtual_out)

    print(f"Run command:\n {command1}")

    command2 = f'mv {created_name} {new_pp_name}'
    # Because UpfData in AiiDA does not accept "Xx" as element symbol,
    # we replace it with the symbol of element A
    command3 = f'sed -i -e "s/Xx/{elem_a}/g" {new_pp_name}'
    run(command2, shell=True, cwd=dest)
    run(command3, shell=True,cwd=dest)
    return new_pp_name

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
@click.option('--dest', '-o', default=None, help="Destination directory")
@click.option('--virtual', '-v', default=None, help="Path to virtual_v2.x")
@click.option('--precision', '-p', default=3, help="Precision of x value")
@click.option('--location/--name', '-l/-n', help="Use location (path) to PP or name of it", default=True)
def main(ppa,ppb,x, dest, virtual, precision, location):
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
    make_vcapp(ppa, ppb, x, dest=dest, path_virtual=virtual, precision=precision, location=location)

if __name__ == "__main__":
    main()