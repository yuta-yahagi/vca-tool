# -*- coding: utf-8 -*-
from subprocess import run
from pathlib import Path
import sys, re
import click

def make_vcapp(ppa_path, ppb_path, x:float, dest=None, path_virtual=None, precision=3):

    ppa=Path(ppa_path)
    ppb=Path(ppb_path)

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
    if not ppa.exists():
        raise FileNotFoundError(f"PP {ppa.absolute()} not found")
    if not ppb.exists():
        raise FileNotFoundError(f"PP {ppb.absolute()} not found")

    if x<=0.0 or x>1:
        raise ValueError(f"x value must be in (0:1]")
    y=1.0-x
    x='{:.3f}'.format(round(x, 3)).rstrip('0').rstrip('.')

    element_pattern = r'([A-Za-z]{1,2})'
    elem_a = re.match(element_pattern, ppa.name)
    if elem_a is None:
        raise ValueError(f"Invalid PP name {ppa.name}")
    elem_a = elem_a.group(1)

    elem_b = re.match(element_pattern, ppb.name)
    if elem_b is None:
        raise ValueError(f"Invalid PP name {ppb.name}")
    elem_b = elem_b.group(1)

    # run(["echo",ppa,ppb,x])
    created_name="NewPseudo.UPF"
    new_pp_name=f"{elem_a}_{elem_b}_{x}.UPF"

    # cwd=Path.cwd().absolute()

    if dest.is_dir():
        new_pp_name=str(dest.absolute())+"/"+new_pp_name
        # created_name=str(dest.absolute())+"/"+created_name


    # With VCA, for the reason of interpolation, mesh of PP_A should be larger than that of PP_B
    size_a=extract_mesh_size(ppa)
    size_b=extract_mesh_size(ppb)
    if size_a > size_b:
        command1 = f'echo "{ppa.absolute()}\n{ppb.absolute()}\n{x}" | {path_virtual.absolute()}'
    else:
        command1 = f'echo "{ppb.absolute()}\n{ppa.absolute()}\n{y}" | {path_virtual.absolute()}'
    command2 = f'mv {created_name} {new_pp_name}'
    # Because UpfData in AiiDA does not accept "Xx" as element symbol,
    # we replace it with the symbol of element A
    command3 = f'sed -i -e "s/Xx/{elem_a}/g" {new_pp_name}'
    print(f"Run command {command1}")
    virtual_out=run(command1, shell=True, cwd=dest, capture_output=True, text=True).stdout
    inspect_virtual(virtual_out)
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
def main(ppa,ppb,x, dest, virtual, precision):
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
    make_vcapp(ppa, ppb, x, dest=dest, path_virtual=virtual, precision=precision)

if __name__ == "__main__":
    main()