"""받아쓰기 모델 열기 (2026-11-04) — 그래픽카드로 먼저 열고, 안 되는 PC 는 CPU 로 내려간다."""
import os, site, numpy as np
from faster_whisper import WhisperModel


def 귀열기(모델='large-v3-turbo'):
    for 곳 in site.getsitepackages() + [site.getusersitepackages()]:
        폴더 = os.path.join(곳, 'nvidia', 'cublas', 'bin')
        if os.path.isdir(폴더):
            os.add_dll_directory(폴더)
            os.environ['PATH'] = 폴더 + os.pathsep + os.environ['PATH']
    try:
        귀 = WhisperModel(모델, device='cuda', compute_type='float16')
        list(귀.transcribe(np.zeros(16000, dtype=np.float32))[0])  # 부품이 빠졌으면 여기서 실패한다
        print('[받아쓰기] GPU')
        return 귀
    except Exception as e:
        print('[받아쓰기] CPU ·', str(e)[:80])
        return WhisperModel(모델, device='cpu', compute_type='int8')
