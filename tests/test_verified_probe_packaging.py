import ast
import subprocess

from scripts.build_verified_probe import build


def test_cpu_probe_preserves_ipython_patch_newline_and_git_patch_syntax():
    notebook,_,_=build()
    tree=ast.parse(notebook['cells'][1]['source'])
    call=next(n for n in ast.walk(tree) if isinstance(n,ast.Call)
        and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name)
        and n.func.value.id=='patch' and n.func.attr=='write_text')
    patch=ast.literal_eval(call.args[0])
    assert patch.endswith('\n')
    result=subprocess.run(['git','apply','--stat'],input=patch.encode(),capture_output=True,timeout=10)
    assert result.returncode==0,result.stderr.decode()


def test_cpu_gate_has_no_model_gpu_network_or_competition_dependency():
    notebook,metadata,manifest=build()
    compile(notebook['cells'][1]['source'],'cpu-integration-probe','exec')
    assert metadata['enable_gpu'] is False and metadata['enable_internet'] is False
    assert metadata['model_sources']==metadata['competition_sources']==[]
    assert 'hydra/verified_planning.py' in manifest['files']
