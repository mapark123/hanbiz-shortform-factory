"""파이썬 도구가 쓰는 영상 인코더 고르기: NVENC(엔비디아) → AMF(AMD) → CPU 순으로, 실제로 한 번 돌려 보고 되는 것을 쓴다.
ffmpeg 목록에 나오는 것만 믿으면 안 된다(엔비디아 없는 PC 에서도 h264_nvenc 가 목록에 뜬다).
환경변수 렌더CPU=1 이면 CPU 로 강제."""
import os, subprocess

_고른것 = None


def _됨(코덱):
    r = subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-f', 'lavfi', '-i', 'color=c=black:s=256x256:d=0.1:r=5',
                        '-c:v', 코덱, '-f', 'null', '-'], capture_output=True)
    return r.returncode == 0


def 종류():
    global _고른것
    if _고른것 is None:
        if os.environ.get('렌더CPU') == '1': _고른것 = 'cpu'
        elif _됨('h264_nvenc'): _고른것 = 'nvenc'
        elif _됨('h264_amf'): _고른것 = 'amf'
        else: _고른것 = 'cpu'
        print('[묶기]', _고른것)
    return _고른것


def 컷옵션():
    """컷본(대표 확인용 h264)."""
    k = 종류()
    if k == 'nvenc': return ['-c:v', 'h264_nvenc', '-preset', 'p5', '-cq', '19']
    if k == 'amf': return ['-c:v', 'h264_amf', '-usage', 'transcoding', '-quality', 'quality', '-rc', 'cqp', '-qp_i', '19', '-qp_p', '19', '-qp_b', '19']
    return ['-c:v', 'libx264', '-preset', 'medium', '-crf', '18']


def 최종옵션():
    """최종본(4K hevc)."""
    k = 종류()
    if k == 'nvenc': return ['-c:v', 'hevc_nvenc', '-preset', 'p6', '-tune', 'hq', '-rc', 'vbr', '-cq', '18', '-b:v', '0', '-maxrate', '70M', '-bufsize', '140M', '-tag:v', 'hvc1']
    if k == 'amf': return ['-c:v', 'hevc_amf', '-usage', 'transcoding', '-quality', 'quality', '-rc', 'cqp', '-qp_i', '18', '-qp_p', '20', '-tag:v', 'hvc1']
    return ['-c:v', 'libx265', '-preset', 'medium', '-crf', '18', '-tag:v', 'hvc1']
