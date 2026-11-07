"""Run reproducible demos and save transcripts. MOCK_LLM=true; no API keys are read."""
import os,sys,json,subprocess
os.environ['MOCK_LLM']='true'; os.environ['CREWAI_DISABLE_TELEMETRY']='true'; os.environ['OTEL_SDK_DISABLED']='true'
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def run(name,cmd):
    p=subprocess.run([sys.executable,*cmd],cwd=ROOT,text=True,capture_output=True)
    (ROOT/'transcripts'/f'{name}.txt').write_text(p.stdout+'\nSTDERR:\n'+p.stderr+f'\nEXIT_CODE={p.returncode}\n',encoding='utf-8')
    if p.returncode: print(f'FAILED {name}: {p.stderr}'); raise SystemExit(p.returncode)
    print(f'PASS {name}')

def main():
    run('dataset_validation',['-m','dataset.dataset'])
    run('rag_threshold_calibration',['-m','rag.calibrate'])
    run('rag_precision_recall',['-m','evaluation.rag_evaluation'])
    run('rag_grounded_generation',['-m','evaluation.rag_demo'])
    run('smoke_demo',['-m','demos.smoke_demo'])
    run('crew_demo',['-m','demos.crew_demo'])
    run('memory_demo',['-m','demos.memory_demo'])
    run('autogen_review_demo',['-m','demos.autogen_demo'])
    run('scale_evaluation',['-m','evaluation.scale_evaluation'])
    print('All offline demos completed. Optional dependency integration is separately tested by tests/test_optional_integrations.py.')
if __name__=='__main__': main()
